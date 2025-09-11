"""
API Rate Limiting Middleware
Professional rate limiting with Redis backend
"""

import time
import json
import hashlib
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

import redis
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configuration
REDIS_URL = "redis://redis:6379/1"
DEFAULT_RATE_LIMIT = 100  # requests per minute
DEFAULT_WINDOW = 60  # seconds

class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

class RateLimitTier(Enum):
    """User tiers with different limits"""
    ANONYMOUS = ("anonymous", 50, 60)      # 50 req/min
    FREE = ("free", 100, 60)               # 100 req/min
    PREMIUM = ("premium", 500, 60)         # 500 req/min
    ENTERPRISE = ("enterprise", 2000, 60)  # 2000 req/min
    UNLIMITED = ("unlimited", -1, 60)      # No limit
    
    def __init__(self, tier_name: str, limit: int, window: int):
        self.tier_name = tier_name
        self.limit = limit
        self.window = window

class RateLimiter:
    """Main rate limiter class"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
        default_limit: int = DEFAULT_RATE_LIMIT,
        default_window: int = DEFAULT_WINDOW
    ):
        self.redis = redis_client or redis.from_url(REDIS_URL, decode_responses=True)
        self.strategy = strategy
        self.default_limit = default_limit
        self.default_window = default_window
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/v1/auth/login": (5, 60),           # 5 attempts per minute
            "/api/v1/auth/register": (3, 60),        # 3 registrations per minute
            "/api/v1/auth/reset-password": (3, 300), # 3 resets per 5 minutes
            "/api/v1/questions/generate": (10, 60),  # 10 generations per minute
            "/api/v1/ai/chat": (20, 60),            # 20 AI queries per minute
            "/api/v1/export/pdf": (5, 60),          # 5 PDF exports per minute
            "/api/v1/analytics/report": (10, 60),   # 10 reports per minute
        }
        
        # IP-based blacklist/whitelist
        self.whitelist = set()  # IPs that bypass rate limiting
        self.blacklist = set()  # Blocked IPs
        
    def get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Priority: User ID > API Key > IP Address
        
        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def get_user_tier(self, request: Request) -> RateLimitTier:
        """Determine user's rate limit tier"""
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            if user.role == "admin":
                return RateLimitTier.UNLIMITED
            elif user.subscription == "enterprise":
                return RateLimitTier.ENTERPRISE
            elif user.subscription == "premium":
                return RateLimitTier.PREMIUM
            else:
                return RateLimitTier.FREE
        return RateLimitTier.ANONYMOUS
    
    def get_limits(self, request: Request) -> tuple[int, int]:
        """Get rate limits for request"""
        path = request.url.path
        
        # Check endpoint-specific limits
        for pattern, limits in self.endpoint_limits.items():
            if path.startswith(pattern):
                return limits
        
        # Get tier-based limits
        tier = self.get_user_tier(request)
        if tier.limit == -1:  # Unlimited
            return (-1, self.default_window)
        
        return (tier.limit, tier.window)
    
    async def check_rate_limit(self, request: Request) -> tuple[bool, Dict[str, Any]]:
        """Check if request exceeds rate limit"""
        client_id = self.get_client_id(request)
        
        # Check whitelist/blacklist
        ip = client_id.split(":")[-1]
        if ip in self.whitelist:
            return True, {"allowed": True, "tier": "whitelisted"}
        if ip in self.blacklist:
            return False, {"allowed": False, "reason": "blacklisted"}
        
        limit, window = self.get_limits(request)
        
        # Unlimited tier
        if limit == -1:
            return True, {"allowed": True, "tier": "unlimited"}
        
        # Apply rate limiting based on strategy
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window(client_id, limit, window)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket(client_id, limit, window)
        elif self.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return await self._leaky_bucket(client_id, limit, window)
        else:  # FIXED_WINDOW
            return await self._fixed_window(client_id, limit, window)
    
    async def _sliding_window(
        self, client_id: str, limit: int, window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting"""
        now = time.time()
        key = f"rate_limit:sliding:{client_id}"
        
        pipeline = self.redis.pipeline()
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window)
        # Add current request
        pipeline.zadd(key, {str(now): now})
        # Count requests in window
        pipeline.zcount(key, now - window, now)
        # Set expiry
        pipeline.expire(key, window + 1)
        
        results = pipeline.execute()
        request_count = results[2]
        
        if request_count > limit:
            return False, {
                "allowed": False,
                "limit": limit,
                "window": window,
                "requests": request_count,
                "retry_after": window
            }
        
        return True, {
            "allowed": True,
            "limit": limit,
            "window": window,
            "requests": request_count,
            "remaining": limit - request_count
        }
    
    async def _fixed_window(
        self, client_id: str, limit: int, window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting"""
        window_start = int(time.time() / window) * window
        key = f"rate_limit:fixed:{client_id}:{window_start}"
        
        pipeline = self.redis.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, window)
        
        results = pipeline.execute()
        request_count = results[0]
        
        if request_count > limit:
            retry_after = window_start + window - int(time.time())
            return False, {
                "allowed": False,
                "limit": limit,
                "window": window,
                "requests": request_count,
                "retry_after": max(1, retry_after)
            }
        
        return True, {
            "allowed": True,
            "limit": limit,
            "window": window,
            "requests": request_count,
            "remaining": limit - request_count
        }
    
    async def _token_bucket(
        self, client_id: str, limit: int, window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting"""
        key = f"rate_limit:token:{client_id}"
        refill_rate = limit / window  # tokens per second
        
        # Get current bucket state
        bucket_data = self.redis.hgetall(key)
        now = time.time()
        
        if bucket_data:
            tokens = float(bucket_data.get("tokens", limit))
            last_refill = float(bucket_data.get("last_refill", now))
            
            # Refill tokens
            time_passed = now - last_refill
            tokens = min(limit, tokens + time_passed * refill_rate)
        else:
            tokens = limit
            last_refill = now
        
        if tokens >= 1:
            # Consume a token
            tokens -= 1
            self.redis.hset(key, mapping={
                "tokens": tokens,
                "last_refill": now
            })
            self.redis.expire(key, window * 2)
            
            return True, {
                "allowed": True,
                "limit": limit,
                "tokens_remaining": int(tokens),
                "refill_rate": refill_rate
            }
        
        # Calculate retry after
        tokens_needed = 1 - tokens
        retry_after = tokens_needed / refill_rate
        
        return False, {
            "allowed": False,
            "limit": limit,
            "tokens_remaining": 0,
            "retry_after": int(retry_after) + 1
        }
    
    async def _leaky_bucket(
        self, client_id: str, limit: int, window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Leaky bucket rate limiting"""
        key = f"rate_limit:leaky:{client_id}"
        leak_rate = limit / window  # requests per second
        
        # Get current bucket state
        bucket_data = self.redis.hgetall(key)
        now = time.time()
        
        if bucket_data:
            volume = float(bucket_data.get("volume", 0))
            last_leak = float(bucket_data.get("last_leak", now))
            
            # Leak the bucket
            time_passed = now - last_leak
            volume = max(0, volume - time_passed * leak_rate)
        else:
            volume = 0
            last_leak = now
        
        if volume < limit:
            # Add to bucket
            volume += 1
            self.redis.hset(key, mapping={
                "volume": volume,
                "last_leak": now
            })
            self.redis.expire(key, window * 2)
            
            return True, {
                "allowed": True,
                "limit": limit,
                "bucket_volume": volume,
                "capacity_remaining": limit - volume
            }
        
        # Bucket is full
        retry_after = 1 / leak_rate
        
        return False, {
            "allowed": False,
            "limit": limit,
            "bucket_volume": volume,
            "retry_after": int(retry_after) + 1
        }
    
    def block_ip(self, ip: str, duration: int = 3600):
        """Block an IP address"""
        self.blacklist.add(ip)
        # Store in Redis with expiry
        key = f"blacklist:{ip}"
        self.redis.setex(key, duration, "blocked")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blacklist.discard(ip)
        self.redis.delete(f"blacklist:{ip}")
    
    def whitelist_ip(self, ip: str):
        """Add IP to whitelist"""
        self.whitelist.add(ip)
        self.redis.sadd("whitelist", ip)
    
    def get_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit statistics for a client"""
        stats = {
            "client_id": client_id,
            "current_requests": {},
            "historical": []
        }
        
        # Get current window stats
        for strategy in RateLimitStrategy:
            key_pattern = f"rate_limit:{strategy.value}:{client_id}*"
            keys = self.redis.keys(key_pattern)
            for key in keys:
                if strategy == RateLimitStrategy.SLIDING_WINDOW:
                    count = self.redis.zcard(key)
                else:
                    count = self.redis.get(key)
                stats["current_requests"][key] = count
        
        return stats

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: Optional[RateLimiter] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(request)
        
        if not allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {info.get('retry_after', 60)} seconds",
                    "retry_after": info.get("retry_after", 60)
                },
                headers={
                    "X-RateLimit-Limit": str(info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + info.get("retry_after", 60))),
                    "Retry-After": str(info.get("retry_after", 60))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + info.get("window", 60))
        )
        
        return response

def rate_limit(
    requests: int = 100,
    window: int = 60,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
):
    """Decorator for endpoint-specific rate limiting"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            rate_limiter = RateLimiter(strategy=strategy)
            
            # Override default limits for this endpoint
            rate_limiter.endpoint_limits[request.url.path] = (requests, window)
            
            allowed, info = await rate_limiter.check_rate_limit(request)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Retry after {info.get('retry_after', 60)} seconds",
                    headers={
                        "Retry-After": str(info.get("retry_after", 60))
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

# Usage example:
# @app.post("/api/v1/expensive-operation")
# @rate_limit(requests=5, window=300)  # 5 requests per 5 minutes
# async def expensive_operation(request: Request):
#     return {"status": "success"}