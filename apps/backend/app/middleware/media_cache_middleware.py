"""
Transparent Media Cache Middleware
Provides transparent caching for media endpoints with automatic cache management
"""

import asyncio
import time
from datetime import datetime
from typing import Callable, Optional
from pathlib import Path
import logging

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.config import settings
from ..services.media_cache_service import media_cache_service, CachedMediaItem, CompressionType
from ..services.media_metrics_service import media_metrics_service

logger = logging.getLogger(__name__)

class MediaCacheMiddleware(BaseHTTPMiddleware):
    """Transparent caching middleware for media endpoints"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cache_service = media_cache_service
        self.metrics_service = media_metrics_service
        
        # Paths that should be cached
        self.cacheable_paths = [
            "/media/images/",
            "/api/v1/media/images/"
        ]
        
        # Paths that should be excluded from caching
        self.exclude_paths = [
            "/media/metrics",
            "/media/stats",
            "/media/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method"""
        start_time = time.time()
        
        # Check if this is a cacheable media request
        if not self._is_cacheable_request(request):
            return await call_next(request)
        
        try:
            # Extract cache parameters from request
            cache_params = self._extract_cache_parameters(request)
            if not cache_params:
                return await call_next(request)
            
            # Try to serve from cache first
            cached_response = await self._serve_from_cache(request, cache_params, start_time)
            if cached_response:
                return cached_response
            
            # Not in cache, proceed with original request
            response = await call_next(request)
            
            # Cache successful responses
            if response.status_code == 200 and hasattr(response, 'body'):
                await self._cache_response(request, response, cache_params, start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in media cache middleware: {e}")
            # Fallback to original request on any error
            return await call_next(request)
    
    def _is_cacheable_request(self, request: Request) -> bool:
        """Check if request is cacheable"""
        path = request.url.path
        
        # Check if path is cacheable
        is_cacheable_path = any(cacheable in path for cacheable in self.cacheable_paths)
        if not is_cacheable_path:
            return False
        
        # Check if path should be excluded
        is_excluded = any(excluded in path for excluded in self.exclude_paths)
        if is_excluded:
            return False
        
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        return True
    
    def _extract_cache_parameters(self, request: Request) -> Optional[dict]:
        """Extract cache parameters from request"""
        try:
            path = request.url.path
            
            # Parse path to extract image type and path
            # Expected format: /media/images/{image_type}/{image_path}
            # or /api/v1/media/images/{image_type}/{image_path}
            
            path_parts = [part for part in path.split('/') if part]
            
            # Find the images part
            images_index = -1
            for i, part in enumerate(path_parts):
                if part == 'images':
                    images_index = i
                    break
            
            if images_index == -1 or len(path_parts) < images_index + 3:
                return None
            
            image_type = path_parts[images_index + 1]
            image_path = '/'.join(path_parts[images_index + 2:])
            
            # Extract resize parameters from query string
            width = request.query_params.get('width')
            height = request.query_params.get('height')
            
            return {
                'image_type': image_type,
                'image_path': image_path,
                'width': int(width) if width and width.isdigit() else None,
                'height': int(height) if height and height.isdigit() else None,
                'full_path': path
            }
            
        except Exception as e:
            logger.warning(f"Error extracting cache parameters: {e}")
            return None
    
    async def _serve_from_cache(self, request: Request, cache_params: dict, start_time: float) -> Optional[Response]:
        """Try to serve response from cache"""
        try:
            cached_item = await self.cache_service.get_cached_media(
                cache_params['image_type'],
                cache_params['image_path'],
                cache_params.get('width'),
                cache_params.get('height')
            )
            
            if not cached_item:
                return None
            
            # Decompress data if needed
            response_data = self._decompress_cached_data(cached_item)
            
            # Create response headers
            headers = self._create_cache_response_headers(request, cached_item)
            
            # Check if client has cached version (304 Not Modified)
            if self._check_client_cache(request, headers):
                return Response(status_code=304, headers=headers)
            
            # Create streaming response for large files
            if len(response_data) > 1024 * 1024:  # 1MB threshold
                return StreamingResponse(
                    self._stream_data(response_data),
                    media_type=cached_item.mime_type,
                    headers=headers
                )
            else:
                return Response(
                    content=response_data,
                    media_type=cached_item.mime_type,
                    headers=headers
                )
                
        except Exception as e:
            logger.error(f"Error serving from cache: {e}")
            return None
    
    def _decompress_cached_data(self, cached_item: CachedMediaItem) -> bytes:
        """Decompress cached data"""
        try:
            if cached_item.compression_type == CompressionType.NONE:
                return cached_item.data
            else:
                return self.cache_service._decompress_data(
                    cached_item.data, 
                    cached_item.compression_type
                )
        except Exception as e:
            logger.error(f"Error decompressing cached data: {e}")
            return cached_item.data
    
    def _create_cache_response_headers(self, request: Request, cached_item: CachedMediaItem) -> dict:
        """Create response headers for cached content"""
        headers = {
            'Content-Type': cached_item.mime_type,
            'Cache-Control': f'public, max-age={settings.MEDIA_CACHE_TTL}',
            'ETag': cached_item.etag,
            'Last-Modified': cached_item.last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-Cache': 'HIT',
            'X-Cache-Created': cached_item.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-Cache-Accessed': cached_item.last_accessed.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-Cache-Access-Count': str(cached_item.access_count),
            'X-Content-Type-Options': 'nosniff',
            'Vary': 'Accept-Encoding'
        }
        
        # Add compression info if applicable
        if cached_item.compression_type != CompressionType.NONE:
            headers['X-Cache-Compression'] = cached_item.compression_type.value
            headers['X-Cache-Compression-Ratio'] = f"{cached_item.cached_size / cached_item.original_size:.3f}"
        
        return headers
    
    def _check_client_cache(self, request: Request, headers: dict) -> bool:
        """Check if client has valid cached version"""
        # Check If-None-Match header (ETag)
        if_none_match = request.headers.get('if-none-match')
        if if_none_match and headers.get('ETag') in if_none_match:
            return True
        
        # Check If-Modified-Since header
        if_modified_since = request.headers.get('if-modified-since')
        if if_modified_since:
            try:
                client_time = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                server_time = datetime.strptime(headers.get('Last-Modified'), '%a, %d %b %Y %H:%M:%S GMT')
                if server_time <= client_time:
                    return True
            except (ValueError, TypeError):
                pass
        
        return False
    
    async def _stream_data(self, data: bytes, chunk_size: int = 8192):
        """Stream data in chunks"""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
            # Allow other tasks to run
            await asyncio.sleep(0)
    
    async def _cache_response(self, request: Request, response: Response, 
                            cache_params: dict, start_time: float):
        """Cache the response for future requests"""
        try:
            # Only cache successful responses
            if response.status_code != 200:
                return
            
            # Get response body
            response_body = await self._get_response_body(response)
            if not response_body:
                return
            
            # Extract content type
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            # Generate ETag
            etag = response.headers.get('etag')
            if not etag:
                import hashlib
                etag = f'"{hashlib.md5(response_body).hexdigest()}"'
            
            # Cache the response
            await self.cache_service.cache_media(
                cache_params['image_type'],
                cache_params['image_path'],
                response_body,
                content_type,
                etag,
                cache_params.get('width'),
                cache_params.get('height')
            )
            
            # Add cache headers to response
            response.headers['X-Cache'] = 'MISS'
            response.headers['X-Cache-Created'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    async def _get_response_body(self, response: Response) -> Optional[bytes]:
        """Extract body from response"""
        try:
            if hasattr(response, 'body'):
                return response.body
            elif hasattr(response, 'content'):
                return response.content
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting response body: {e}")
            return None


class MediaPrefetchMiddleware(BaseHTTPMiddleware):
    """Middleware for intelligent media prefetching"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cache_service = media_cache_service
        self.prefetch_enabled = settings.MEDIA_PREFETCH_ENABLED
        self.prefetch_limit = settings.MEDIA_PREFETCH_LIMIT
        
        # Common patterns for prefetching
        self.prefetch_patterns = {
            'question': ['option_a', 'option_b', 'option_c', 'option_d'],
            'option_a': ['option_b', 'option_c', 'option_d'],
            'option_b': ['option_c', 'option_d'],
            'option_c': ['option_d']
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method"""
        response = await call_next(request)
        
        # Only prefetch on successful requests
        if (self.prefetch_enabled and 
            response.status_code == 200 and 
            self._is_media_request(request)):
            
            # Schedule prefetch in background
            asyncio.create_task(self._schedule_prefetch(request))
        
        return response
    
    def _is_media_request(self, request: Request) -> bool:
        """Check if this is a media request"""
        return any(path in request.url.path for path in ["/media/images/", "/api/v1/media/images/"])
    
    async def _schedule_prefetch(self, request: Request):
        """Schedule intelligent prefetching based on request patterns"""
        try:
            # Extract parameters
            cache_params = self._extract_cache_parameters(request)
            if not cache_params:
                return
            
            image_type = cache_params.get('image_type')
            image_path = cache_params.get('image_path')
            
            if not image_type or not image_path:
                return
            
            # Get related images to prefetch
            related_types = self.prefetch_patterns.get(image_type, [])
            
            # Extract base path (without extension)
            base_path = str(Path(image_path).with_suffix(''))
            
            prefetch_count = 0
            for related_type in related_types:
                if prefetch_count >= self.prefetch_limit:
                    break
                
                # Try different extensions
                for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    related_path = f"{base_path}{ext}"
                    
                    # Check if already cached
                    cached_item = await self.cache_service.get_cached_media(
                        related_type, related_path
                    )
                    
                    if not cached_item:
                        # Schedule prefetch
                        await self._prefetch_image(related_type, related_path)
                        prefetch_count += 1
                        break
            
        except Exception as e:
            logger.error(f"Error in prefetch scheduling: {e}")
    
    def _extract_cache_parameters(self, request: Request) -> Optional[dict]:
        """Extract cache parameters from request"""
        try:
            path = request.url.path
            path_parts = [part for part in path.split('/') if part]
            
            images_index = -1
            for i, part in enumerate(path_parts):
                if part == 'images':
                    images_index = i
                    break
            
            if images_index == -1 or len(path_parts) < images_index + 3:
                return None
            
            return {
                'image_type': path_parts[images_index + 1],
                'image_path': '/'.join(path_parts[images_index + 2:])
            }
            
        except Exception as e:
            logger.warning(f"Error extracting cache parameters for prefetch: {e}")
            return None
    
    async def _prefetch_image(self, image_type: str, image_path: str):
        """Prefetch a specific image"""
        try:
            # This would typically make an internal request to load and cache the image
            # For now, we'll just log the prefetch attempt
            logger.debug(f"Prefetching image: {image_type}/{image_path}")
            
            # In a real implementation, you might:
            # 1. Check if file exists in the filesystem
            # 2. Load the file
            # 3. Cache it using the cache service
            # 4. Record prefetch metrics
            
        except Exception as e:
            logger.error(f"Error prefetching image {image_type}/{image_path}: {e}")


def setup_media_cache_middleware(app):
    """Setup media cache middleware"""
    app.add_middleware(MediaCacheMiddleware)
    if settings.MEDIA_PREFETCH_ENABLED:
        app.add_middleware(MediaPrefetchMiddleware)
    
    logger.info("Media cache middleware configured")