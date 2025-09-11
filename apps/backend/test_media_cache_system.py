"""
Comprehensive Test Suite for Media Cache System
Tests cache functionality, metrics, optimization, and background services
"""

import asyncio
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json
import io
from typing import Dict, Any

from PIL import Image
import redis.asyncio as aioredis

from app.services.media_cache_service import (
    MediaCacheService, CachedMediaItem, CacheMetrics, CacheStatus, CompressionType
)
from app.services.media_metrics_service import (
    MediaMetricsService, AlertSeverity, MetricType
)
from app.services.media_optimization_service import (
    MediaOptimizationService, OptimizationLevel, OptimizationSettings, ImageFormat
)
from app.services.media_background_service import (
    MediaBackgroundService, TaskType, TaskPriority
)
from app.middleware.media_cache_middleware import MediaCacheMiddleware

class TestMediaCacheService:
    """Test media cache service functionality"""
    
    @pytest.fixture
    async def cache_service(self):
        """Create cache service for testing"""
        service = MediaCacheService()
        # Mock Redis connection for testing
        service.redis_pool = Mock()
        service.sync_redis = Mock()
        return service
    
    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data for testing"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_generate_cache_key(self, cache_service):
        """Test cache key generation"""
        key = cache_service._generate_cache_key('question', 'math/algebra.png', 800, 600)
        
        assert 'img:' in key
        assert 'question' in key
        assert '800' in key
        assert '600' in key
        assert len(key.split(':')) == 5  # img:type:hash:width:height
    
    def test_compress_data(self, cache_service, sample_image_data):
        """Test data compression"""
        compressed, compression_type = cache_service._compress_data(
            sample_image_data, CompressionType.ZLIB
        )
        
        assert compression_type == CompressionType.ZLIB
        assert len(compressed) < len(sample_image_data)
    
    def test_decompress_data(self, cache_service, sample_image_data):
        """Test data decompression"""
        compressed, compression_type = cache_service._compress_data(
            sample_image_data, CompressionType.ZLIB
        )
        
        decompressed = cache_service._decompress_data(compressed, compression_type)
        assert decompressed == sample_image_data
    
    @pytest.mark.asyncio
    async def test_cache_media_item(self, cache_service, sample_image_data):
        """Test caching media items"""
        with patch.object(cache_service, 'get_redis') as mock_redis:
            mock_conn = AsyncMock()
            mock_redis.return_value.__aenter__.return_value = mock_conn
            
            success = await cache_service.cache_media(
                'question',
                'test/image.png',
                sample_image_data,
                'image/png',
                '"test-etag"'
            )
            
            assert success
            mock_conn.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_media(self, cache_service, sample_image_data):
        """Test retrieving cached media"""
        # Create mock cached item
        cached_item = CachedMediaItem(
            data=sample_image_data,
            mime_type='image/png',
            original_size=len(sample_image_data),
            cached_size=len(sample_image_data),
            compression_type=CompressionType.NONE,
            etag='"test-etag"',
            last_modified=datetime.utcnow(),
            created_at=datetime.utcnow(),
            access_count=1,
            last_accessed=datetime.utcnow()
        )
        
        with patch.object(cache_service, 'get_redis') as mock_redis:
            mock_conn = AsyncMock()
            mock_redis.return_value.__aenter__.return_value = mock_conn
            mock_conn.get.return_value = pickle.dumps(cached_item)
            
            result = await cache_service.get_cached_media('question', 'test/image.png')
            
            assert result is not None
            assert result.mime_type == 'image/png'
            assert result.access_count == 2  # Should increment
    
    @pytest.mark.asyncio
    async def test_health_check(self, cache_service):
        """Test cache health check"""
        with patch.object(cache_service, 'get_redis') as mock_redis:
            mock_conn = AsyncMock()
            mock_redis.return_value.__aenter__.return_value = mock_conn
            mock_conn.set.return_value = True
            mock_conn.get.return_value = b'test_data'
            mock_conn.delete.return_value = True
            mock_conn.info.return_value = {'used_memory_human': '1MB'}
            
            health = await cache_service.health_check()
            
            assert health['healthy'] is True
            assert health['redis_connected'] is True

class TestMediaMetricsService:
    """Test media metrics service"""
    
    @pytest.fixture
    def metrics_service(self):
        """Create metrics service for testing"""
        service = MediaMetricsService()
        service.redis_pool = Mock()
        return service
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics data"""
        return [
            {
                'key': 'img:question:test1:0:0',
                'image_type': 'question',
                'status': CacheStatus.HIT.value,
                'response_time_ms': 150.0,
                'file_size': 50000,
                'cache_size': 30000,
                'compression_ratio': 0.6,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'key': 'img:option_a:test2:0:0',
                'image_type': 'option_a',
                'status': CacheStatus.MISS.value,
                'response_time_ms': 300.0,
                'file_size': 75000,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'key': 'img:question:test1:0:0',
                'image_type': 'question',
                'status': CacheStatus.HIT.value,
                'response_time_ms': 120.0,
                'file_size': 50000,
                'cache_size': 30000,
                'compression_ratio': 0.6,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
    
    def test_calculate_cache_metrics(self, metrics_service, sample_metrics):
        """Test cache metrics calculation"""
        result = metrics_service._calculate_cache_metrics(sample_metrics)
        
        assert result['total_requests'] == 3
        assert result['hits'] == 2
        assert result['misses'] == 1
        assert result['hit_ratio'] == 2/3
        assert result['miss_ratio'] == 1/3
        
        # Check by image type
        assert 'question' in result['by_image_type']
        assert 'option_a' in result['by_image_type']
        assert result['by_image_type']['question']['hits'] == 2
        assert result['by_image_type']['option_a']['misses'] == 1
    
    @pytest.mark.asyncio
    async def test_get_top_requested_images(self, metrics_service, sample_metrics):
        """Test top requested images calculation"""
        result = await metrics_service._get_detailed_top_requested(sample_metrics)
        
        assert len(result) > 0
        # The question image should be top (2 requests)
        top_image = result[0]
        assert top_image['total_requests'] == 2
        assert top_image['cache_key'] == 'img:question:test1:0:0'
        assert top_image['hit_ratio'] == 1.0  # Both were hits
    
    def test_calculate_performance_metrics(self, metrics_service, sample_metrics):
        """Test performance metrics calculation"""
        result = metrics_service._calculate_performance_metrics(sample_metrics)
        
        assert result['avg_response_time_ms'] == (150 + 300 + 120) / 3
        assert result['min_response_time_ms'] == 120.0
        assert result['max_response_time_ms'] == 300.0
        assert result['bandwidth_saved_bytes'] == (50000 - 30000) * 2  # 2 compressed items

class TestMediaOptimizationService:
    """Test media optimization service"""
    
    @pytest.fixture
    def optimization_service(self):
        """Create optimization service for testing"""
        return MediaOptimizationService()
    
    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data for testing"""
        img = Image.new('RGB', (800, 600), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    @pytest.mark.asyncio
    async def test_optimize_image(self, optimization_service, sample_image_data):
        """Test image optimization"""
        optimized_data, result = await optimization_service.optimize_image(
            sample_image_data,
            'question',
            OptimizationLevel.BASIC
        )
        
        assert len(optimized_data) > 0
        assert result.original_size == len(sample_image_data)
        assert result.optimized_size == len(optimized_data)
        assert result.compression_ratio <= 1.0  # Should be same or smaller
        assert result.optimization_level == OptimizationLevel.BASIC
    
    def test_resize_image(self, optimization_service, sample_image_data):
        """Test image resizing"""
        with Image.open(io.BytesIO(sample_image_data)) as img:
            resized = optimization_service._resize_image(img, 400, 300)
            
            assert resized.size[0] <= 400
            assert resized.size[1] <= 300
            # Should maintain aspect ratio
            original_ratio = img.width / img.height
            new_ratio = resized.width / resized.height
            assert abs(original_ratio - new_ratio) < 0.01
    
    @pytest.mark.asyncio
    async def test_generate_lazy_load_placeholder(self, optimization_service, sample_image_data):
        """Test lazy load placeholder generation"""
        placeholder_data = await optimization_service.generate_lazy_load_placeholder(
            sample_image_data, 'question'
        )
        
        assert len(placeholder_data) > 0
        assert len(placeholder_data) < len(sample_image_data)  # Should be smaller
        
        # Verify it's a valid image
        with Image.open(io.BytesIO(placeholder_data)) as placeholder:
            assert placeholder.size[0] <= 50  # Default placeholder size
            assert placeholder.size[1] <= 50
    
    @pytest.mark.asyncio
    async def test_progressive_images(self, optimization_service, sample_image_data):
        """Test progressive image generation"""
        progressive_images = await optimization_service.generate_progressive_images(
            sample_image_data, 'question'
        )
        
        assert len(progressive_images) > 0
        assert 20 in progressive_images  # Should have low quality version
        assert 100 in progressive_images  # Should have high quality version
        
        # Lower quality should be smaller
        if 20 in progressive_images and 100 in progressive_images:
            assert len(progressive_images[20]) <= len(progressive_images[100])

class TestMediaBackgroundService:
    """Test media background service"""
    
    @pytest.fixture
    def background_service(self):
        """Create background service for testing"""
        service = MediaBackgroundService()
        service.celery_app = None  # Disable Celery for testing
        return service
    
    @pytest.mark.asyncio
    async def test_schedule_task(self, background_service):
        """Test task scheduling"""
        task_id = await background_service.schedule_task(
            TaskType.CACHE_INVALIDATION,
            TaskPriority.NORMAL,
            {'pattern': 'test:*'},
            delay_seconds=0
        )
        
        assert task_id is not None
        assert len(background_service.task_queue) == 1
        
        task = background_service.task_queue[0]
        assert task.task_type == TaskType.CACHE_INVALIDATION
        assert task.priority == TaskPriority.NORMAL
        assert task.parameters['pattern'] == 'test:*'
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, background_service):
        """Test task cancellation"""
        task_id = await background_service.schedule_task(
            TaskType.CLEANUP,
            TaskPriority.LOW,
            {'type': 'expired'}
        )
        
        success = await background_service.cancel_task(task_id)
        
        assert success is True
        assert len(background_service.task_queue) == 0
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, background_service):
        """Test task status retrieval"""
        task_id = await background_service.schedule_task(
            TaskType.METRICS_FLUSH,
            TaskPriority.NORMAL,
            {}
        )
        
        status = await background_service.get_task_status(task_id)
        
        assert status is not None
        assert status['id'] == task_id
        assert status['type'] == TaskType.METRICS_FLUSH.value
        assert status['status'] == 'pending'

class TestMediaCacheMiddleware:
    """Test media cache middleware"""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware for testing"""
        app = Mock()
        return MediaCacheMiddleware(app)
    
    def test_is_cacheable_request(self, middleware):
        """Test cacheable request detection"""
        # Create mock request
        request = Mock()
        request.method = 'GET'
        request.url.path = '/api/v1/media/images/question/test.png'
        
        assert middleware._is_cacheable_request(request) is True
        
        # Test non-GET request
        request.method = 'POST'
        assert middleware._is_cacheable_request(request) is False
        
        # Test non-media request
        request.method = 'GET'
        request.url.path = '/api/v1/users'
        assert middleware._is_cacheable_request(request) is False
    
    def test_extract_cache_parameters(self, middleware):
        """Test cache parameter extraction"""
        request = Mock()
        request.url.path = '/api/v1/media/images/question/math/algebra.png'
        request.query_params = {'width': '800', 'height': '600'}
        
        params = middleware._extract_cache_parameters(request)
        
        assert params is not None
        assert params['image_type'] == 'question'
        assert params['image_path'] == 'math/algebra.png'
        assert params['width'] == 800
        assert params['height'] == 600

class TestIntegration:
    """Integration tests for the complete media cache system"""
    
    @pytest.mark.asyncio
    async def test_full_cache_cycle(self):
        """Test complete cache cycle: store, retrieve, invalidate"""
        # This would test the full integration between services
        # For now, we'll create a simplified test
        
        cache_service = MediaCacheService()
        cache_service.redis_pool = Mock()
        cache_service.sync_redis = Mock()
        
        # Mock successful operations
        with patch.object(cache_service, 'get_redis') as mock_redis:
            mock_conn = AsyncMock()
            mock_redis.return_value.__aenter__.return_value = mock_conn
            
            # Test caching
            mock_conn.setex.return_value = True
            success = await cache_service.cache_media(
                'question', 'test.png', b'test_data', 'image/png', '"etag"'
            )
            assert success
            
            # Test retrieval
            from pickle import dumps
            cached_item = CachedMediaItem(
                data=b'test_data',
                mime_type='image/png',
                original_size=9,
                cached_size=9,
                compression_type=CompressionType.NONE,
                etag='"etag"',
                last_modified=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            mock_conn.get.return_value = dumps(cached_item)
            
            result = await cache_service.get_cached_media('question', 'test.png')
            assert result is not None
            assert result.data == b'test_data'
    
    @pytest.mark.asyncio
    async def test_metrics_and_alerts_integration(self):
        """Test metrics collection and alert generation"""
        metrics_service = MediaMetricsService()
        metrics_service.redis_pool = Mock()
        
        # Create sample metrics that should trigger alerts
        bad_metrics = [
            {
                'status': CacheStatus.MISS.value,
                'response_time_ms': 1500.0,  # High response time
                'timestamp': datetime.utcnow().isoformat()
            } for _ in range(10)
        ]
        
        # Mock Redis operations
        with patch.object(metrics_service, 'get_redis') as mock_redis:
            mock_conn = AsyncMock()
            mock_redis.return_value.__aenter__.return_value = mock_conn
            mock_conn.get.return_value = None  # No existing alerts
            mock_conn.setex.return_value = True
            
            await metrics_service.check_and_create_alerts(bad_metrics)
            
            # Should have created alerts for high miss rate and response time
            mock_conn.setex.assert_called()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])