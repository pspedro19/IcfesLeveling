import redis
from typing import Any, Optional, Union, List, Dict
import json
import pickle
from datetime import timedelta
import logging
from functools import wraps
import hashlib

from ..core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=False  # We'll handle encoding/decoding ourselves
        )
        self.default_ttl = 3600  # 1 hour default
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key based on prefix and parameters"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # For complex objects, use a hash
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage in Redis"""
        try:
            # Try JSON first (for simple data structures)
            return json.dumps(data).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from Redis"""
        if not data:
            return None
        
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    # Basic cache operations
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            data = self.redis_client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL"""
        try:
            serialized = self._serialize(value)
            if ttl is None:
                ttl = self.default_ttl
            
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key"""
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    # Pattern-based operations
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern}: {e}")
            return 0
    
    def get_keys(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Error getting keys for pattern {pattern}: {e}")
            return []
    
    # Specialized cache methods
    def cache_user_profile(self, user_id: str, profile_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache user profile data"""
        key = self._generate_key("user:profile", user_id)
        return self.set(key, profile_data, ttl)
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile data"""
        key = self._generate_key("user:profile", user_id)
        return self.get(key)
    
    def invalidate_user_profile(self, user_id: str) -> bool:
        """Invalidate user profile cache"""
        key = self._generate_key("user:profile", user_id)
        return self.delete(key)
    
    def cache_battle_state(self, battle_id: str, state: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache battle state (30 minutes default)"""
        key = self._generate_key("battle:state", battle_id)
        return self.set(key, state, ttl)
    
    def get_battle_state(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """Get cached battle state"""
        key = self._generate_key("battle:state", battle_id)
        return self.get(key)
    
    def cache_question_pool(self, subject_id: str, difficulty: int, questions: List[Dict[str, Any]], ttl: int = 7200) -> bool:
        """Cache question pool for a subject and difficulty"""
        key = self._generate_key("questions:pool", subject_id, difficulty=difficulty)
        return self.set(key, questions, ttl)
    
    def get_question_pool(self, subject_id: str, difficulty: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached question pool"""
        key = self._generate_key("questions:pool", subject_id, difficulty=difficulty)
        return self.get(key)
    
    def cache_leaderboard(self, leaderboard_type: str, data: List[Dict[str, Any]], ttl: int = 300) -> bool:
        """Cache leaderboard data (5 minutes default)"""
        key = self._generate_key("leaderboard", leaderboard_type)
        return self.set(key, data, ttl)
    
    def get_leaderboard(self, leaderboard_type: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached leaderboard data"""
        key = self._generate_key("leaderboard", leaderboard_type)
        return self.get(key)
    
    def cache_analytics_result(self, user_id: str, analytics_type: str, period: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache analytics results"""
        key = self._generate_key("analytics", user_id, type=analytics_type, period=period)
        return self.set(key, data, ttl)
    
    def get_analytics_result(self, user_id: str, analytics_type: str, period: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics results"""
        key = self._generate_key("analytics", user_id, type=analytics_type, period=period)
        return self.get(key)
    
    # Atomic operations
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Atomically increment a counter"""
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Atomically decrement a counter"""
        try:
            return self.redis_client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {e}")
            return None
    
    # Rate limiting
    def is_rate_limited(self, identifier: str, limit: int, window: int) -> bool:
        """Check if an identifier is rate limited"""
        key = self._generate_key("ratelimit", identifier)
        try:
            current = self.redis_client.get(key)
            if current is None:
                # First request in window
                pipe = self.redis_client.pipeline()
                pipe.setex(key, window, 1)
                pipe.execute()
                return False
            
            current_count = int(current)
            if current_count >= limit:
                return True
            
            self.redis_client.incr(key)
            return False
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            return False
    
    # Session management
    def set_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store session data"""
        key = self._generate_key("session", session_id)
        return self.set(key, data, ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = self._generate_key("session", session_id)
        return self.get(key)
    
    def extend_session(self, session_id: str, ttl: int = 3600) -> bool:
        """Extend session TTL"""
        key = self._generate_key("session", session_id)
        return self.expire(key, ttl)
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        key = self._generate_key("session", session_id)
        return self.delete(key)
    
    # Pub/Sub operations
    def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel"""
        try:
            serialized = self._serialize(message)
            return self.redis_client.publish(channel, serialized)
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return 0
    
    def subscribe(self, channels: List[str]):
        """Subscribe to channels (returns pubsub object)"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(*channels)
        return pubsub
    
    # Cache decorator
    def cached(self, prefix: str, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # Check cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result, ttl or self.default_ttl)
                logger.debug(f"Cached result for {cache_key}")
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # Check cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result, ttl or self.default_ttl)
                logger.debug(f"Cached result for {cache_key}")
                
                return result
            
            # Return appropriate wrapper
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    # Bulk operations
    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple values at once"""
        try:
            values = self.redis_client.mget(keys)
            return [self._deserialize(v) if v else None for v in values]
        except Exception as e:
            logger.error(f"Error in mget: {e}")
            return [None] * len(keys)
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs at once"""
        try:
            # Serialize all values
            serialized_mapping = {k: self._serialize(v) for k, v in mapping.items()}
            
            if ttl is None:
                return self.redis_client.mset(serialized_mapping)
            else:
                # Use pipeline for atomic operation with TTL
                pipe = self.redis_client.pipeline()
                for key, value in serialized_mapping.items():
                    pipe.setex(key, ttl or self.default_ttl, value)
                pipe.execute()
                return True
        except Exception as e:
            logger.error(f"Error in mset: {e}")
            return False
    
    # Health check
    def ping(self) -> bool:
        """Check if Redis connection is alive"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

# Import asyncio if needed
try:
    import asyncio
except ImportError:
    asyncio = None

# Singleton instance
cache_service = CacheService()