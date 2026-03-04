import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import os
import logging

logger = logging.getLogger("icfes.cache")

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=False
        )
        self.default_ttl = 3600  # 1 hour

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL"""
        try:
            serialized = pickle.dumps(value)
            if ttl is None:
                ttl = self.default_ttl
            return bool(self.redis_client.setex(key, ttl, serialized))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def get(self, key: str) -> Any:
        """Get a value from cache"""
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0

    # Specialized cache methods
    def cache_user_stats(self, user_id: str, stats: dict) -> bool:
        """Cache user statistics"""
        return self.set(f"user_stats:{user_id}", stats, 1800)  # 30 min

    def get_user_stats(self, user_id: str) -> Optional[dict]:
        """Get cached user statistics"""
        return self.get(f"user_stats:{user_id}")

    def cache_leaderboard(self, board_type: str, data: list) -> bool:
        """Cache leaderboard data"""
        return self.set(f"leaderboard:{board_type}", data, 600)  # 10 min

    def get_leaderboard(self, board_type: str) -> Optional[list]:
        """Get cached leaderboard"""
        return self.get(f"leaderboard:{board_type}")

    def cache_study_plan(self, user_id: str, subject_id: str, plan: dict) -> bool:
        """Cache study plan"""
        return self.set(f"study_plan:{user_id}:{subject_id}", plan, 3600)

    def get_study_plan(self, user_id: str, subject_id: str) -> Optional[dict]:
        """Get cached study plan"""
        return self.get(f"study_plan:{user_id}:{subject_id}")

    def cache_diagnostic_results(self, user_id: str, subject_id: str, results: dict) -> bool:
        """Cache diagnostic test results"""
        return self.set(f"diagnostic:{user_id}:{subject_id}", results, 7200)  # 2 hours

    def get_diagnostic_results(self, user_id: str, subject_id: str) -> Optional[dict]:
        """Get cached diagnostic results"""
        return self.get(f"diagnostic:{user_id}:{subject_id}")

    def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache for a user"""
        return self.clear_pattern(f"*:{user_id}:*") + self.clear_pattern(f"*:{user_id}")

# Global cache instance
cache = RedisCache()


def get_redis():
    """Get the raw Redis client for direct operations."""
    try:
        client = cache.redis_client
        client.ping()
        return client
    except Exception:
        return None

# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = ""):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator