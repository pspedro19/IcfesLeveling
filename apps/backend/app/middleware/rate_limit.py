from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import asyncio
from typing import Dict, Tuple
from collections import defaultdict, deque
import redis
import os

class RateLimiter:
    def __init__(self):
        # Try to use Redis if available, otherwise use in-memory
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 1)),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=True
            )
            self.redis_client.ping()
            self.use_redis = True
        except:
            self.use_redis = False
            # In-memory fallback
            self.memory_store: Dict[str, deque] = defaultdict(deque)
            self.cleanup_interval = 300  # 5 minutes
            asyncio.create_task(self._cleanup_memory_store())

    async def _cleanup_memory_store(self):
        """Clean up expired entries from memory store"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            current_time = time.time()
            for key in list(self.memory_store.keys()):
                # Remove entries older than 1 hour
                while (self.memory_store[key] and 
                       current_time - self.memory_store[key][0] > 3600):
                    self.memory_store[key].popleft()
                # Remove empty queues
                if not self.memory_store[key]:
                    del self.memory_store[key]

    async def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Unique identifier (e.g., IP address, user ID)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, metadata)
        """
        current_time = time.time()
        
        if self.use_redis:
            return await self._redis_check(key, limit, window, current_time)
        else:
            return await self._memory_check(key, limit, window, current_time)

    async def _redis_check(self, key: str, limit: int, window: int, current_time: float) -> Tuple[bool, Dict]:
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            results = pipe.execute()
            
            request_count = results[1]
            
            if request_count < limit:
                return True, {
                    "allowed": True,
                    "limit": limit,
                    "remaining": limit - request_count - 1,
                    "reset_time": current_time + window
                }
            else:
                return False, {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": current_time + window,
                    "retry_after": window
                }
        except Exception as e:
            # Fallback to allowing request if Redis fails
            print(f"Redis rate limit error: {e}")
            return True, {"allowed": True, "limit": limit, "remaining": limit}

    async def _memory_check(self, key: str, limit: int, window: int, current_time: float) -> Tuple[bool, Dict]:
        """Memory-based rate limiting"""
        requests = self.memory_store[key]
        
        # Remove old requests outside the window
        while requests and current_time - requests[0] > window:
            requests.popleft()
        
        if len(requests) < limit:
            requests.append(current_time)
            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": limit - len(requests),
                "reset_time": current_time + window
            }
        else:
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_time": requests[0] + window,
                "retry_after": int(requests[0] + window - current_time)
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Decorator for rate limiting endpoints
def rate_limit(limit: int = 100, window: int = 60, key_func=None):
    """
    Rate limiting decorator
    
    Args:
        limit: Max requests per window
        window: Time window in seconds
        key_func: Function to generate rate limit key
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                client_ip = request.client.host
                key = f"rate_limit:{client_ip}:{func.__name__}"
            
            # Check rate limit
            allowed, metadata = await rate_limiter.is_allowed(key, limit, window)
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {limit} per {window} seconds",
                        "retry_after": metadata.get("retry_after", window)
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(metadata.get("remaining", 0)),
                        "X-RateLimit-Reset": str(int(metadata.get("reset_time", 0))),
                        "Retry-After": str(metadata.get("retry_after", window))
                    }
                )
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(metadata.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(int(metadata.get("reset_time", 0)))
            
            return response
        return wrapper
    return decorator

# User-based rate limiting
def user_rate_limit(limit: int = 1000, window: int = 3600):
    """Rate limit by user ID"""
    def key_func(request: Request):
        # Extract user ID from token or session
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Extract user ID from JWT token
                import jwt
                token = auth_header[7:]
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("user_id", request.client.host)
                return f"user_rate_limit:{user_id}"
            except:
                pass
        return f"ip_rate_limit:{request.client.host}"
    
    return rate_limit(limit, window, key_func)

# IP-based rate limiting  
def ip_rate_limit(limit: int = 100, window: int = 60):
    """Rate limit by IP address"""
    def key_func(request: Request):
        return f"ip_rate_limit:{request.client.host}"
    
    return rate_limit(limit, window, key_func)

# Endpoint-specific rate limiting
def endpoint_rate_limit(endpoint: str, limit: int = 50, window: int = 60):
    """Rate limit by endpoint and user/IP"""
    def key_func(request: Request):
        identifier = request.client.host
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import jwt
                token = auth_header[7:]
                payload = jwt.decode(token, options={"verify_signature": False})
                identifier = payload.get("user_id", identifier)
            except:
                pass
        return f"endpoint_rate_limit:{endpoint}:{identifier}"
    
    return rate_limit(limit, window, key_func)