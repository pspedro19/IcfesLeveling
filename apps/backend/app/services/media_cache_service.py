"""
Advanced Redis Cache Service for Media with Compression and Metrics
Provides comprehensive caching solutions for media files with performance optimization
"""

import os
import json
import gzip
import zlib
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import redis
from PIL import Image
import io

from ..core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

class CacheStatus(Enum):
    HIT = "hit"
    MISS = "miss"
    ERROR = "error"
    EXPIRED = "expired"

class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"

@dataclass
class CacheMetrics:
    """Cache metrics data structure"""
    key: str
    image_type: str
    status: CacheStatus
    response_time_ms: float
    file_size: int
    cache_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class CachedMediaItem:
    """Cached media item structure"""
    data: bytes
    mime_type: str
    original_size: int
    cached_size: int
    compression_type: CompressionType
    etag: str
    last_modified: datetime
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()

class MediaCacheService:
    """Advanced Redis cache service for media files with compression and metrics"""
    
    def __init__(self):
        self.redis_pool = None
        self.sync_redis = None
        self.metrics_buffer: List[CacheMetrics] = []
        self.metrics_flush_size = 100
        self.compression_level = settings.MEDIA_CACHE_COMPRESSION_LEVEL
        self.max_cache_size = settings.MEDIA_CACHE_MAX_SIZE
        
        # Cache key patterns
        self.cache_key_pattern = f"{settings.MEDIA_CACHE_PREFIX}:{{type}}:{{hash}}:{{width}}:{{height}}"
        self.metrics_key_pattern = f"{settings.MEDIA_CACHE_PREFIX}_metrics:{{date}}"
        self.stats_key_pattern = f"{settings.MEDIA_CACHE_PREFIX}_stats"
        
        # Initialize Redis connection
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connections"""
        try:
            # Async Redis pool
            self.redis_pool = aioredis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECTION_TIMEOUT,
                retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                decode_responses=False
            )
            
            # Sync Redis for background tasks
            self.sync_redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECTION_TIMEOUT,
                retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                decode_responses=False
            )
            
            logger.info("Redis connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_pool = None
            self.sync_redis = None
    
    @asynccontextmanager
    async def get_redis(self):
        """Get async Redis connection from pool"""
        if not self.redis_pool:
            raise Exception("Redis pool not initialized")
        
        redis_conn = aioredis.Redis(connection_pool=self.redis_pool)
        try:
            yield redis_conn
        finally:
            await redis_conn.close()
    
    def _generate_cache_key(self, image_type: str, image_path: str, 
                          width: Optional[int] = None, height: Optional[int] = None) -> str:
        """Generate cache key for image"""
        path_hash = hashlib.md5(image_path.encode()).hexdigest()[:16]
        w = width or 0
        h = height or 0
        return self.cache_key_pattern.format(
            type=image_type,
            hash=path_hash,
            width=w,
            height=h
        )
    
    def _compress_data(self, data: bytes, compression_type: CompressionType = CompressionType.ZLIB) -> Tuple[bytes, CompressionType]:
        """Compress data based on type and size"""
        if len(data) < 1024:  # Don't compress small files
            return data, CompressionType.NONE
        
        try:
            if compression_type == CompressionType.GZIP:
                compressed = gzip.compress(data, compresslevel=self.compression_level)
            elif compression_type == CompressionType.ZLIB:
                compressed = zlib.compress(data, level=self.compression_level)
            else:
                return data, CompressionType.NONE
            
            # Only use compression if it reduces size significantly
            if len(compressed) < len(data) * 0.9:
                return compressed, compression_type
            else:
                return data, CompressionType.NONE
                
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return data, CompressionType.NONE
    
    def _decompress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data"""
        try:
            if compression_type == CompressionType.GZIP:
                return gzip.decompress(data)
            elif compression_type == CompressionType.ZLIB:
                return zlib.decompress(data)
            else:
                return data
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise
    
    def _detect_file_changes(self, file_path: str, cached_item: CachedMediaItem) -> bool:
        """Detect if file has changed since caching"""
        try:
            path = Path(file_path)
            if not path.exists():
                return True
            
            stat_info = path.stat()
            current_mtime = datetime.fromtimestamp(stat_info.st_mtime)
            
            return current_mtime > cached_item.last_modified
            
        except Exception as e:
            logger.warning(f"File change detection failed for {file_path}: {e}")
            return True
    
    async def _resize_image(self, image_data: bytes, width: int, height: int, 
                          mime_type: str) -> Tuple[bytes, str]:
        """Resize image to specified dimensions"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Calculate aspect ratio preserving resize
                img_ratio = img.width / img.height
                target_ratio = width / height
                
                if img_ratio > target_ratio:
                    # Image is wider
                    new_width = width
                    new_height = int(width / img_ratio)
                else:
                    # Image is taller
                    new_height = height
                    new_width = int(height * img_ratio)
                
                # Resize image
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert back to bytes
                output = io.BytesIO()
                format_map = {
                    'image/jpeg': 'JPEG',
                    'image/jpg': 'JPEG',
                    'image/png': 'PNG',
                    'image/webp': 'WEBP',
                    'image/gif': 'GIF'
                }
                
                format_name = format_map.get(mime_type, 'JPEG')
                resized.save(output, format=format_name, optimize=True)
                
                return output.getvalue(), mime_type
                
        except Exception as e:
            logger.error(f"Image resize failed: {e}")
            return image_data, mime_type
    
    async def get_cached_media(self, image_type: str, image_path: str, 
                              width: Optional[int] = None, height: Optional[int] = None) -> Optional[CachedMediaItem]:
        """Get cached media item"""
        start_time = datetime.utcnow()
        
        try:
            cache_key = self._generate_cache_key(image_type, image_path, width, height)
            
            async with self.get_redis() as redis_conn:
                cached_data = await redis_conn.get(cache_key)
                
                if not cached_data:
                    # Record cache miss
                    await self._record_metric(CacheMetrics(
                        key=cache_key,
                        image_type=image_type,
                        status=CacheStatus.MISS,
                        response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                        file_size=0
                    ))
                    return None
                
                # Deserialize cached item
                cached_item = pickle.loads(cached_data)
                
                # Check if we need to validate file changes
                if hasattr(cached_item, 'etag') and self._detect_file_changes(image_path, cached_item):
                    # File changed, invalidate cache
                    await redis_conn.delete(cache_key)
                    await self._record_metric(CacheMetrics(
                        key=cache_key,
                        image_type=image_type,
                        status=CacheStatus.EXPIRED,
                        response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                        file_size=cached_item.original_size
                    ))
                    return None
                
                # Update access info
                cached_item.access_count += 1
                cached_item.last_accessed = datetime.utcnow()
                
                # Update cache with new access info
                serialized = pickle.dumps(cached_item)
                await redis_conn.setex(
                    cache_key, 
                    settings.MEDIA_CACHE_TTL, 
                    serialized
                )
                
                # Record cache hit
                await self._record_metric(CacheMetrics(
                    key=cache_key,
                    image_type=image_type,
                    status=CacheStatus.HIT,
                    response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                    file_size=cached_item.original_size,
                    cache_size=cached_item.cached_size,
                    compression_ratio=cached_item.cached_size / cached_item.original_size if cached_item.original_size > 0 else 1.0
                ))
                
                return cached_item
                
        except Exception as e:
            logger.error(f"Error getting cached media: {e}")
            await self._record_metric(CacheMetrics(
                key=f"error:{image_path}",
                image_type=image_type,
                status=CacheStatus.ERROR,
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                file_size=0
            ))
            return None
    
    async def cache_media(self, image_type: str, image_path: str, 
                         file_data: bytes, mime_type: str, etag: str,
                         width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """Cache media item with compression"""
        start_time = datetime.utcnow()
        
        try:
            # Resize image if dimensions specified
            processed_data = file_data
            if width and height and settings.MEDIA_RESIZE_ENABLED:
                processed_data, mime_type = await self._resize_image(
                    file_data, width, height, mime_type
                )
            
            # Check size limit
            if len(processed_data) > self.max_cache_size:
                logger.warning(f"File too large to cache: {len(processed_data)} bytes")
                return False
            
            # Compress data
            compressed_data, compression_type = self._compress_data(
                processed_data, 
                CompressionType.ZLIB if settings.MEDIA_CACHE_COMPRESSION else CompressionType.NONE
            )
            
            # Create cached item
            cached_item = CachedMediaItem(
                data=compressed_data,
                mime_type=mime_type,
                original_size=len(file_data),
                cached_size=len(compressed_data),
                compression_type=compression_type,
                etag=etag,
                last_modified=datetime.fromtimestamp(Path(image_path).stat().st_mtime),
                created_at=datetime.utcnow(),
                access_count=1,
                last_accessed=datetime.utcnow()
            )
            
            # Serialize and cache
            cache_key = self._generate_cache_key(image_type, image_path, width, height)
            serialized = pickle.dumps(cached_item)
            
            async with self.get_redis() as redis_conn:
                await redis_conn.setex(
                    cache_key,
                    settings.MEDIA_CACHE_TTL,
                    serialized
                )
            
            # Record caching metrics
            await self._record_metric(CacheMetrics(
                key=cache_key,
                image_type=image_type,
                status=CacheStatus.MISS,  # This was a miss that led to caching
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                file_size=len(file_data),
                cache_size=len(compressed_data),
                compression_ratio=len(compressed_data) / len(file_data) if len(file_data) > 0 else 1.0
            ))
            
            logger.debug(f"Cached media: {cache_key} ({len(compressed_data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error caching media: {e}")
            return False
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            if not self.sync_redis:
                return 0
                
            keys = self.sync_redis.keys(f"{settings.MEDIA_CACHE_PREFIX}:*{pattern}*")
            if keys:
                return self.sync_redis.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0
    
    async def _record_metric(self, metric: CacheMetrics):
        """Record cache metric"""
        self.metrics_buffer.append(metric)
        
        # Flush metrics buffer if it's full
        if len(self.metrics_buffer) >= self.metrics_flush_size:
            await self._flush_metrics()
    
    async def _flush_metrics(self):
        """Flush metrics buffer to Redis"""
        if not self.metrics_buffer:
            return
        
        try:
            async with self.get_redis() as redis_conn:
                # Group metrics by date
                daily_metrics = {}
                
                for metric in self.metrics_buffer:
                    date_key = metric.timestamp.strftime("%Y-%m-%d")
                    if date_key not in daily_metrics:
                        daily_metrics[date_key] = []
                    daily_metrics[date_key].append(asdict(metric))
                
                # Store daily metrics
                for date_key, metrics in daily_metrics.items():
                    metrics_key = self.metrics_key_pattern.format(date=date_key)
                    
                    # Get existing metrics
                    existing_data = await redis_conn.get(metrics_key)
                    existing_metrics = []
                    
                    if existing_data:
                        existing_metrics = json.loads(existing_data)
                    
                    # Add new metrics
                    existing_metrics.extend(metrics)
                    
                    # Store updated metrics
                    await redis_conn.setex(
                        metrics_key,
                        86400 * settings.MEDIA_METRICS_RETENTION_DAYS,  # Keep for retention days
                        json.dumps(existing_metrics, default=str)
                    )
                
                # Clear buffer
                self.metrics_buffer.clear()
                
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            async with self.get_redis() as redis_conn:
                # Get Redis info
                redis_info = await redis_conn.info()
                
                # Calculate date range for metrics
                today = datetime.utcnow().strftime("%Y-%m-%d")
                yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
                
                # Get recent metrics
                today_key = self.metrics_key_pattern.format(date=today)
                yesterday_key = self.metrics_key_pattern.format(date=yesterday)
                
                today_data = await redis_conn.get(today_key)
                yesterday_data = await redis_conn.get(yesterday_key)
                
                today_metrics = json.loads(today_data) if today_data else []
                yesterday_metrics = json.loads(yesterday_data) if yesterday_data else []
                
                all_metrics = today_metrics + yesterday_metrics
                
                # Calculate statistics
                stats = {
                    "redis_info": {
                        "used_memory": redis_info.get('used_memory_human', 'N/A'),
                        "connected_clients": redis_info.get('connected_clients', 0),
                        "total_commands_processed": redis_info.get('total_commands_processed', 0),
                        "keyspace_hits": redis_info.get('keyspace_hits', 0),
                        "keyspace_misses": redis_info.get('keyspace_misses', 0)
                    },
                    "cache_metrics": self._calculate_cache_metrics(all_metrics),
                    "top_requested": await self._get_top_requested_images(all_metrics),
                    "performance": self._calculate_performance_metrics(all_metrics),
                    "compression_stats": self._calculate_compression_stats(all_metrics)
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {"error": str(e)}
    
    def _calculate_cache_metrics(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Calculate cache hit/miss ratios and other metrics"""
        if not metrics:
            return {"total_requests": 0, "hit_ratio": 0.0, "miss_ratio": 0.0}
        
        total = len(metrics)
        hits = sum(1 for m in metrics if m.get('status') == CacheStatus.HIT.value)
        misses = sum(1 for m in metrics if m.get('status') == CacheStatus.MISS.value)
        errors = sum(1 for m in metrics if m.get('status') == CacheStatus.ERROR.value)
        expired = sum(1 for m in metrics if m.get('status') == CacheStatus.EXPIRED.value)
        
        # Group by image type
        by_type = {}
        for metric in metrics:
            img_type = metric.get('image_type', 'unknown')
            if img_type not in by_type:
                by_type[img_type] = {'hits': 0, 'misses': 0, 'total': 0}
            
            by_type[img_type]['total'] += 1
            if metric.get('status') == CacheStatus.HIT.value:
                by_type[img_type]['hits'] += 1
            elif metric.get('status') == CacheStatus.MISS.value:
                by_type[img_type]['misses'] += 1
        
        # Calculate hit ratios by type
        for img_type in by_type:
            total_type = by_type[img_type]['total']
            if total_type > 0:
                by_type[img_type]['hit_ratio'] = by_type[img_type]['hits'] / total_type
            else:
                by_type[img_type]['hit_ratio'] = 0.0
        
        return {
            "total_requests": total,
            "hits": hits,
            "misses": misses,
            "errors": errors,
            "expired": expired,
            "hit_ratio": hits / total if total > 0 else 0.0,
            "miss_ratio": misses / total if total > 0 else 0.0,
            "error_ratio": errors / total if total > 0 else 0.0,
            "by_image_type": by_type
        }
    
    async def _get_top_requested_images(self, metrics: List[Dict]) -> List[Dict]:
        """Get top requested images"""
        # Count requests by key
        key_counts = {}
        for metric in metrics:
            key = metric.get('key', '')
            if key not in key_counts:
                key_counts[key] = {
                    'count': 0,
                    'image_type': metric.get('image_type', 'unknown'),
                    'total_response_time': 0,
                    'total_file_size': 0
                }
            
            key_counts[key]['count'] += 1
            key_counts[key]['total_response_time'] += metric.get('response_time_ms', 0)
            key_counts[key]['total_file_size'] += metric.get('file_size', 0)
        
        # Sort by count and get top N
        top_images = sorted(
            key_counts.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:settings.MEDIA_METRICS_TOP_LIMIT]
        
        result = []
        for key, stats in top_images:
            avg_response_time = stats['total_response_time'] / stats['count'] if stats['count'] > 0 else 0
            avg_file_size = stats['total_file_size'] / stats['count'] if stats['count'] > 0 else 0
            
            result.append({
                'cache_key': key,
                'image_type': stats['image_type'],
                'request_count': stats['count'],
                'avg_response_time_ms': round(avg_response_time, 2),
                'avg_file_size_bytes': int(avg_file_size)
            })
        
        return result
    
    def _calculate_performance_metrics(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not metrics:
            return {"avg_response_time_ms": 0, "bandwidth_saved_bytes": 0}
        
        response_times = [m.get('response_time_ms', 0) for m in metrics]
        file_sizes = [m.get('file_size', 0) for m in metrics]
        
        # Calculate bandwidth savings from compression
        bandwidth_saved = 0
        for metric in metrics:
            if metric.get('cache_size') and metric.get('file_size'):
                bandwidth_saved += metric['file_size'] - metric['cache_size']
        
        return {
            "avg_response_time_ms": round(sum(response_times) / len(response_times), 2),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "total_bandwidth_bytes": sum(file_sizes),
            "bandwidth_saved_bytes": bandwidth_saved,
            "avg_file_size_bytes": round(sum(file_sizes) / len(file_sizes), 2)
        }
    
    def _calculate_compression_stats(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Calculate compression statistics"""
        compressed_metrics = [
            m for m in metrics 
            if m.get('compression_ratio') and m.get('compression_ratio') < 1.0
        ]
        
        if not compressed_metrics:
            return {"compression_enabled": False, "avg_compression_ratio": 1.0}
        
        ratios = [m['compression_ratio'] for m in compressed_metrics]
        
        return {
            "compression_enabled": True,
            "total_compressed_items": len(compressed_metrics),
            "avg_compression_ratio": round(sum(ratios) / len(ratios), 3),
            "best_compression_ratio": round(min(ratios), 3),
            "total_space_saved_bytes": sum(
                m.get('file_size', 0) - m.get('cache_size', 0) 
                for m in compressed_metrics
            )
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache service"""
        try:
            async with self.get_redis() as redis_conn:
                # Test basic operations
                test_key = f"{settings.MEDIA_CACHE_PREFIX}:health_check"
                test_value = "test_data"
                
                await redis_conn.set(test_key, test_value, ex=60)
                retrieved = await redis_conn.get(test_key)
                await redis_conn.delete(test_key)
                
                is_healthy = retrieved.decode() == test_value
                
                # Get connection info
                redis_info = await redis_conn.info()
                
                return {
                    "healthy": is_healthy,
                    "redis_connected": True,
                    "used_memory": redis_info.get('used_memory_human', 'N/A'),
                    "connected_clients": redis_info.get('connected_clients', 0),
                    "uptime_seconds": redis_info.get('uptime_in_seconds', 0)
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "redis_connected": False,
                "error": str(e)
            }

# Global instance
media_cache_service = MediaCacheService()