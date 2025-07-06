"""Redis cache implementation."""

import json
import redis
from typing import Optional, Any
from datetime import timedelta
from app.config import get_settings

settings = get_settings()


class RedisCache:
    """Redis cache manager."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        self.default_ttl = settings.cache_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError):
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized)
        except (redis.RedisError, ValueError, TypeError):
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError:
            return False
    
    def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.redis_client.ping()
        except redis.RedisError:
            return False
    
    def clear_all(self) -> bool:
        """Clear all keys in the current database."""
        try:
            return self.redis_client.flushdb()
        except redis.RedisError:
            return False


# Cache key generators
def get_performance_cache_key(start_date: str, end_date: str) -> str:
    """Generate cache key for index performance."""
    return f"index:performance:{start_date}:{end_date}"


def get_composition_cache_key(date: str) -> str:
    """Generate cache key for index composition."""
    return f"index:composition:{date}"


def get_changes_cache_key(start_date: str, end_date: str) -> str:
    """Generate cache key for composition changes."""
    return f"index:changes:{start_date}:{end_date}"


# Global cache instance
cache = RedisCache()