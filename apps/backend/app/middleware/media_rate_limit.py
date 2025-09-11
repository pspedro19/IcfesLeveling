"""
Advanced Rate Limiting Middleware for Media Endpoints
Provides sophisticated rate limiting with different tiers and abuse protection
"""

import time
import hashlib
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
import redis
import json
import logging

from fastapi import HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio

logger = logging.getLogger(__name__)

class MediaRateLimiter:
    """Advanced rate limiter for media endpoints with abuse detection"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = None
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis connected for rate limiting")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory rate limiting: {e}")
        
        # In-memory fallback
        self._memory_store: Dict[str, Dict] = defaultdict(dict)
        self._request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Rate limiting configurations
        self.limits = {
            'images_per_minute': 60,
            'images_per_hour': 1000,
            'images_per_day': 5000,
            'bandwidth_mb_per_hour': 500,  # 500MB per hour
            'burst_requests_per_second': 10,
            'suspicious_threshold': 200,  # Requests per minute that trigger abuse detection
        }
        
        # Abuse detection patterns
        self.abuse_patterns = {
            'rapid_fire_threshold': 20,  # requests per second
            'path_enumeration_threshold': 50,  # different paths per minute
            'error_rate_threshold': 0.8,  # 80% error rate
            'suspicious_user_agents': [
                'bot', 'crawler', 'spider', 'scraper', 'wget', 'curl'
            ]
        }
        
        # Blocked IPs and temporary bans
        self._blocked_ips: Dict[str, datetime] = {}
        self._temp_bans: Dict[str, datetime] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Generate unique client identifier"""
        ip = get_remote_address(request)
        user_agent = request.headers.get('user-agent', 'unknown')
        forwarded = request.headers.get('x-forwarded-for', '')
        
        # Create hash of identifying information
        client_data = f"{ip}:{user_agent}:{forwarded}"
        return hashlib.md5(client_data.encode()).hexdigest()[:16]
    
    def _is_blocked(self, client_id: str, ip: str) -> Tuple[bool, Optional[str]]:
        """Check if client is blocked"""
        now = datetime.now()
        
        # Check permanent blocks
        if ip in self._blocked_ips:
            if self._blocked_ips[ip] > now:
                return True, "IP permanently blocked due to abuse"
        
        # Check temporary bans
        if client_id in self._temp_bans:
            if self._temp_bans[client_id] > now:
                ban_time = self._temp_bans[client_id]
                return True, f"Temporarily banned until {ban_time.isoformat()}"
            else:
                # Ban expired, remove it
                del self._temp_bans[client_id]
        
        return False, None
    
    def _get_rate_limit_data(self, key: str) -> Dict:
        """Get rate limit data for a key"""
        if self.redis_client:
            try:
                data = self.redis_client.get(f"rate_limit:{key}")
                return json.loads(data) if data else {}
            except:
                pass
        
        return self._memory_store.get(key, {})
    
    def _set_rate_limit_data(self, key: str, data: Dict, ttl: int = 3600):
        """Set rate limit data for a key"""
        if self.redis_client:
            try:
                self.redis_client.setex(f"rate_limit:{key}", ttl, json.dumps(data))
                return
            except:
                pass
        
        self._memory_store[key] = data
    
    def _increment_counter(self, key: str, window: int = 60) -> int:
        """Increment counter with sliding window"""
        now = int(time.time())
        window_start = now - window
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {str(now): now})
                pipe.zcount(key, window_start, now)
                pipe.expire(key, window + 10)
                result = pipe.execute()
                return result[2]
            except:
                pass
        
        # Memory fallback with sliding window
        data = self._get_rate_limit_data(key)
        requests = data.get('requests', [])
        
        # Remove old requests
        requests = [req for req in requests if req > window_start]
        requests.append(now)
        
        data['requests'] = requests
        self._set_rate_limit_data(key, data)
        
        return len(requests)
    
    def _detect_abuse(self, request: Request, client_id: str) -> Tuple[bool, Optional[str]]:
        """Detect abuse patterns"""
        now = datetime.now()
        ip = get_remote_address(request)
        user_agent = request.headers.get('user-agent', '').lower()
        
        # Check suspicious user agents
        for suspicious in self.abuse_patterns['suspicious_user_agents']:
            if suspicious in user_agent:
                return True, f"Suspicious user agent: {suspicious}"
        
        # Get request history for this client
        history = self._request_history[client_id]
        
        # Add current request
        history.append({
            'timestamp': now,
            'path': request.url.path,
            'ip': ip,
            'user_agent': user_agent
        })
        
        # Analyze recent requests (last minute)
        recent_requests = [
            req for req in history 
            if (now - req['timestamp']).seconds < 60
        ]
        
        if len(recent_requests) > self.abuse_patterns['rapid_fire_threshold']:
            return True, "Rapid fire requests detected"
        
        # Path enumeration detection
        unique_paths = set(req['path'] for req in recent_requests)
        if len(unique_paths) > self.abuse_patterns['path_enumeration_threshold']:
            return True, "Path enumeration attack detected"
        
        # Error rate analysis (simplified for this context)
        # In a real implementation, you'd track response codes
        
        return False, None
    
    def _apply_temporary_ban(self, client_id: str, duration_minutes: int = 15):
        """Apply temporary ban to client"""
        ban_until = datetime.now() + timedelta(minutes=duration_minutes)
        self._temp_bans[client_id] = ban_until
        logger.warning(f"Applied {duration_minutes}min ban to client {client_id}")
    
    def _cleanup_expired_bans(self):
        """Clean up expired bans and blocks"""
        now = datetime.now()
        
        # Clean temporary bans
        expired_bans = [
            client_id for client_id, ban_time in self._temp_bans.items()
            if ban_time <= now
        ]
        for client_id in expired_bans:
            del self._temp_bans[client_id]
        
        # Clean permanent blocks (if they have expiry)
        expired_blocks = [
            ip for ip, block_time in self._blocked_ips.items()
            if block_time <= now
        ]
        for ip in expired_blocks:
            del self._blocked_ips[ip]
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Optional[Dict]]:
        """
        Check if request should be rate limited
        Returns: (should_limit, limit_info)
        """
        try:
            self._cleanup_expired_bans()
            
            client_id = self._get_client_id(request)
            ip = get_remote_address(request)
            
            # Check if client is blocked
            is_blocked, block_reason = self._is_blocked(client_id, ip)
            if is_blocked:
                return True, {
                    'reason': 'blocked',
                    'message': block_reason,
                    'retry_after': 3600
                }
            
            # Detect abuse patterns
            is_abuse, abuse_reason = self._detect_abuse(request, client_id)
            if is_abuse:
                logger.warning(f"Abuse detected for {client_id}: {abuse_reason}")
                self._apply_temporary_ban(client_id, 15)
                return True, {
                    'reason': 'abuse_detected',
                    'message': abuse_reason,
                    'retry_after': 900  # 15 minutes
                }
            
            # Check rate limits
            limits_exceeded = []
            
            # Per minute limit
            minute_key = f"{client_id}:minute:{int(time.time()) // 60}"
            minute_count = self._increment_counter(minute_key, 60)
            if minute_count > self.limits['images_per_minute']:
                limits_exceeded.append({
                    'limit': 'per_minute',
                    'current': minute_count,
                    'max': self.limits['images_per_minute'],
                    'retry_after': 60
                })
            
            # Per hour limit
            hour_key = f"{client_id}:hour:{int(time.time()) // 3600}"
            hour_count = self._increment_counter(hour_key, 3600)
            if hour_count > self.limits['images_per_hour']:
                limits_exceeded.append({
                    'limit': 'per_hour',
                    'current': hour_count,
                    'max': self.limits['images_per_hour'],
                    'retry_after': 3600
                })
            
            # Burst protection (per second)
            second_key = f"{client_id}:second:{int(time.time())}"
            second_count = self._increment_counter(second_key, 1)
            if second_count > self.limits['burst_requests_per_second']:
                limits_exceeded.append({
                    'limit': 'burst_protection',
                    'current': second_count,
                    'max': self.limits['burst_requests_per_second'],
                    'retry_after': 1
                })
            
            if limits_exceeded:
                # Choose the most restrictive limit
                most_restrictive = max(limits_exceeded, key=lambda x: x['retry_after'])
                
                # Apply temporary ban for repeated violations
                if minute_count > self.limits['suspicious_threshold']:
                    self._apply_temporary_ban(client_id, 30)
                    most_restrictive['retry_after'] = 1800  # 30 minutes
                
                return True, {
                    'reason': 'rate_limit_exceeded',
                    'limit_info': most_restrictive,
                    'all_limits': limits_exceeded,
                    'retry_after': most_restrictive['retry_after']
                }
            
            return False, None
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - don't block if rate limiting fails
            return False, None
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        stats = {
            'active_bans': len(self._temp_bans),
            'blocked_ips': len(self._blocked_ips),
            'memory_store_size': len(self._memory_store),
            'limits': self.limits,
            'abuse_patterns': self.abuse_patterns
        }
        
        if self.redis_client:
            try:
                stats['redis_connected'] = True
                stats['redis_info'] = self.redis_client.info('memory')
            except:
                stats['redis_connected'] = False
        else:
            stats['redis_connected'] = False
        
        return stats

# Global rate limiter instance
media_rate_limiter = MediaRateLimiter()

async def media_rate_limit_middleware(request: Request, call_next):
    """Middleware function for media rate limiting"""
    # Only apply to media endpoints
    if not request.url.path.startswith('/api/v1/media/'):
        return await call_next(request)
    
    # Check rate limits
    should_limit, limit_info = await media_rate_limiter.check_rate_limit(request)
    
    if should_limit:
        logger.warning(f"Rate limit exceeded: {limit_info}")
        
        retry_after = limit_info.get('retry_after', 60)
        raise HTTPException(
            status_code=429,
            detail={
                'message': 'Rate limit exceeded',
                'info': limit_info,
                'retry_after': retry_after
            },
            headers={'Retry-After': str(retry_after)}
        )
    
    return await call_next(request)