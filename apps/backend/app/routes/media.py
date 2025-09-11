"""
Secure Media Service Endpoint for ICFES Leveling System
Provides secure, validated media serving with advanced caching and security features
"""

import os
import mimetypes
import gzip
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from ..core.database import get_db
from ..core.config import settings
from ..services.image_mapping_service import image_mapping_service, ImageMapping
from ..middleware.rate_limit import rate_limiter

# Setup logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/media", tags=["media"])

# Security configurations
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
CACHE_MAX_AGE = 3600  # 1 hour
CACHE_STALE_WHILE_REVALIDATE = 86400  # 24 hours
COMPRESSION_THRESHOLD = 1024  # 1KB

# Rate limiting configurations
RATE_LIMIT_PER_MINUTE = "60/minute"
RATE_LIMIT_PER_HOUR = "1000/hour"

class MediaSecurityValidator:
    """Handles security validation for media requests"""
    
    @staticmethod
    def validate_image_type(image_type: str) -> bool:
        """Validate image type parameter"""
        valid_types = {'question', 'option_a', 'option_b', 'option_c', 'option_d', 'placeholder'}
        return image_type in valid_types
    
    @staticmethod
    def validate_path_security(image_path: str) -> tuple[bool, Optional[str]]:
        """
        Comprehensive path security validation
        Returns: (is_valid, error_message)
        """
        if not image_path:
            return False, "Empty path"
        
        # Check for directory traversal attempts
        dangerous_patterns = ['../', '..\\', '../', '..\\', '/..', '\\..', '~/', '~\\']
        for pattern in dangerous_patterns:
            if pattern in image_path:
                logger.warning(f"Directory traversal attempt: {image_path} from {get_remote_address}")
                return False, "Directory traversal detected"
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '|', '*', '?', '"', '\x00', '\n', '\r']
        for char in dangerous_chars:
            if char in image_path:
                return False, f"Dangerous character detected: {char}"
        
        # Check path length
        if len(image_path) > 1000:
            return False, "Path too long"
        
        # Check for suspicious file extensions in path
        suspicious_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.js', '.jar']
        for ext in suspicious_extensions:
            if ext.lower() in image_path.lower():
                return False, f"Suspicious file extension: {ext}"
        
        return True, None
    
    @staticmethod
    def validate_file_integrity(file_path: str) -> tuple[bool, Optional[str]]:
        """Validate file integrity and type"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, "File does not exist"
            
            if not path.is_file():
                return False, "Path is not a file"
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return False, f"File too large: {file_size} bytes"
            
            # Check file extension
            extension = path.suffix.lower().lstrip('.')
            if extension not in ALLOWED_IMAGE_TYPES:
                return False, f"Invalid file type: {extension}"
            
            # Basic image validation using PIL
            try:
                from PIL import Image
                with Image.open(path) as img:
                    img.verify()
            except Exception:
                return False, "Invalid image file"
            
            return True, None
            
        except Exception as e:
            logger.error(f"File validation error for {file_path}: {e}")
            return False, f"Validation error: {str(e)}"

class MediaCacheManager:
    """Handles caching logic for media responses"""
    
    @staticmethod
    def generate_etag(file_path: str) -> str:
        """Generate ETag for file"""
        try:
            path = Path(file_path)
            stat_info = path.stat()
            etag_data = f"{path.name}-{stat_info.st_size}-{stat_info.st_mtime}"
            return f'"{hashlib.md5(etag_data.encode()).hexdigest()}"'
        except Exception:
            return f'"{hashlib.md5(str(datetime.now()).encode()).hexdigest()}"'
    
    @staticmethod
    def check_if_modified(request: Request, etag: str, last_modified: datetime) -> bool:
        """Check if file was modified since last request"""
        # Check If-None-Match header
        if_none_match = request.headers.get('if-none-match')
        if if_none_match and etag in if_none_match:
            return False
        
        # Check If-Modified-Since header
        if_modified_since = request.headers.get('if-modified-since')
        if if_modified_since:
            try:
                client_time = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                if last_modified <= client_time:
                    return False
            except ValueError:
                pass
        
        return True
    
    @staticmethod
    def get_cache_headers(etag: str, last_modified: datetime) -> dict:
        """Get cache control headers"""
        return {
            'Cache-Control': f'public, max-age={CACHE_MAX_AGE}, stale-while-revalidate={CACHE_STALE_WHILE_REVALIDATE}',
            'ETag': etag,
            'Last-Modified': last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'Vary': 'Accept-Encoding',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        }

class MediaCompressionHandler:
    """Handles media compression for optimal delivery"""
    
    @staticmethod
    def should_compress(file_path: str, file_size: int, accept_encoding: str) -> bool:
        """Determine if file should be compressed"""
        if file_size < COMPRESSION_THRESHOLD:
            return False
        
        if 'gzip' not in accept_encoding.lower():
            return False
        
        # Don't compress already compressed image formats
        extension = Path(file_path).suffix.lower()
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return False
        
        return True
    
    @staticmethod
    async def compress_file(file_path: str) -> bytes:
        """Compress file content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return gzip.compress(content)
        except Exception as e:
            logger.error(f"Compression error for {file_path}: {e}")
            raise HTTPException(status_code=500, detail="Compression failed")

# Initialize validators and managers
security_validator = MediaSecurityValidator()
cache_manager = MediaCacheManager()
compression_handler = MediaCompressionHandler()

@router.get("/images/{image_type}/{image_path:path}")
@rate_limiter.limit(RATE_LIMIT_PER_MINUTE)
@rate_limiter.limit(RATE_LIMIT_PER_HOUR)
async def serve_image(
    request: Request,
    image_type: str,
    image_path: str,
    db: Session = Depends(get_db)
):
    """
    Secure image serving endpoint with comprehensive validation and caching
    
    Args:
        image_type: Type of image (question, option_a, option_b, option_c, option_d, placeholder)
        image_path: Path to the image file (will be mapped from CSV to physical location)
    
    Returns:
        FileResponse with optimized headers and caching
    
    Examples:
        - /api/v1/media/images/question/Matematicas/algebra/ecuacion_001.png
        - /api/v1/media/images/option_a/Ciencias/quimica/molecula_h2o.jpg
        - /api/v1/media/images/placeholder/matematicas/default.png
    """
    try:
        # Step 1: Validate image type
        if not security_validator.validate_image_type(image_type):
            logger.warning(f"Invalid image type: {image_type} from {get_remote_address(request)}")
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        # Step 2: Validate path security
        is_path_safe, path_error = security_validator.validate_path_security(image_path)
        if not is_path_safe:
            logger.warning(f"Path security violation: {image_path} - {path_error}")
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Step 3: Handle placeholder requests
        if image_type == 'placeholder':
            placeholder_path = image_mapping_service.get_placeholder_path(image_path, 'generic')
            if not os.path.exists(placeholder_path):
                # Create a minimal placeholder if it doesn't exist
                await create_default_placeholder(placeholder_path)
            
            return await serve_file_with_optimizations(
                request, placeholder_path, "image/png"
            )
        
        # Step 4: Resolve image mapping
        mapping = image_mapping_service.resolve_image_path(db, image_path, image_type)
        if not mapping or not mapping.exists:
            logger.info(f"Image not found: {image_path} (type: {image_type})")
            
            # Attempt to determine subject for fallback
            subject = extract_subject_from_path(image_path)
            fallback_path = image_mapping_service.get_placeholder_path(subject, image_type)
            
            if not os.path.exists(fallback_path):
                await create_default_placeholder(fallback_path)
            
            return await serve_file_with_optimizations(
                request, fallback_path, "image/png"
            )
        
        # Step 5: Validate file integrity
        is_file_valid, file_error = security_validator.validate_file_integrity(mapping.physical_path)
        if not is_file_valid:
            logger.warning(f"File validation failed: {mapping.physical_path} - {file_error}")
            raise HTTPException(status_code=400, detail="Invalid file")
        
        # Step 6: Determine MIME type
        mime_type, _ = mimetypes.guess_type(mapping.physical_path)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # Safe default
        
        # Step 7: Serve file with optimizations
        return await serve_file_with_optimizations(
            request, mapping.physical_path, mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {image_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def serve_file_with_optimizations(
    request: Request,
    file_path: str,
    mime_type: str
) -> Response:
    """Serve file with all optimizations applied"""
    try:
        path = Path(file_path)
        stat_info = path.stat()
        last_modified = datetime.fromtimestamp(stat_info.st_mtime)
        
        # Generate ETag
        etag = cache_manager.generate_etag(file_path)
        
        # Check if client has cached version
        if not cache_manager.check_if_modified(request, etag, last_modified):
            return Response(
                status_code=304,
                headers=cache_manager.get_cache_headers(etag, last_modified)
            )
        
        # Get cache headers
        headers = cache_manager.get_cache_headers(etag, last_modified)
        headers['Content-Type'] = mime_type
        
        # Check if compression is needed
        accept_encoding = request.headers.get('accept-encoding', '')
        should_compress = compression_handler.should_compress(
            file_path, stat_info.st_size, accept_encoding
        )
        
        if should_compress:
            # Compress and serve
            compressed_content = await compression_handler.compress_file(file_path)
            headers['Content-Encoding'] = 'gzip'
            headers['Content-Length'] = str(len(compressed_content))
            
            return Response(
                content=compressed_content,
                headers=headers,
                media_type=mime_type
            )
        else:
            # Serve directly
            return FileResponse(
                file_path,
                media_type=mime_type,
                headers=headers
            )
            
    except Exception as e:
        logger.error(f"Error optimizing file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="File serving error")

async def create_default_placeholder(placeholder_path: str) -> None:
    """Create a default placeholder image if it doesn't exist"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple placeholder image
        img = Image.new('RGB', (300, 200), color='#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        text = "Imagen no disponible"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (300 - text_width) // 2
        y = (200 - text_height) // 2
        
        draw.text((x, y), text, fill='#666666', font=font)
        
        # Ensure directory exists
        Path(placeholder_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save placeholder
        img.save(placeholder_path, 'PNG', optimize=True)
        logger.info(f"Created placeholder at {placeholder_path}")
        
    except Exception as e:
        logger.error(f"Failed to create placeholder {placeholder_path}: {e}")

def extract_subject_from_path(image_path: str) -> str:
    """Extract subject from image path for fallback placeholder selection"""
    path_lower = image_path.lower()
    
    subject_keywords = {
        'matematicas': ['mat', 'algebra', 'calculo', 'geometria', 'aritmetica'],
        'ciencias_naturales': ['ciencias', 'quimica', 'fisica', 'biologia'],
        'ciencias_sociales': ['sociales', 'historia', 'geografia'],
        'lectura_critica': ['lectura', 'comprension', 'texto'],
        'ingles': ['english', 'ingles', 'idioma']
    }
    
    for subject, keywords in subject_keywords.items():
        if any(keyword in path_lower for keyword in keywords):
            return subject
    
    return 'general'

@router.get("/images/{image_type}/{image_path:path}/info")
async def get_image_info(
    image_type: str,
    image_path: str,
    db: Session = Depends(get_db)
):
    """Get information about an image without serving the file"""
    try:
        # Validate inputs
        if not security_validator.validate_image_type(image_type):
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        is_path_safe, path_error = security_validator.validate_path_security(image_path)
        if not is_path_safe:
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Get mapping
        mapping = image_mapping_service.resolve_image_path(db, image_path, image_type)
        if not mapping:
            raise HTTPException(status_code=404, detail="Image mapping not found")
        
        # Build response
        info = {
            'csv_path': mapping.csv_path,
            'image_type': mapping.image_type,
            'subject': mapping.subject,
            'exists': mapping.exists,
            'physical_path': mapping.physical_path if mapping.exists else None,
            'file_size': mapping.file_size,
            'last_modified': mapping.last_modified.isoformat() if mapping.last_modified else None
        }
        
        if mapping.exists and mapping.physical_path:
            # Add additional file info
            mime_type, _ = mimetypes.guess_type(mapping.physical_path)
            info['mime_type'] = mime_type
            info['etag'] = cache_manager.generate_etag(mapping.physical_path)
            
            # Get image dimensions if possible
            try:
                from PIL import Image
                with Image.open(mapping.physical_path) as img:
                    info['dimensions'] = {
                        'width': img.size[0],
                        'height': img.size[1],
                        'format': img.format,
                        'mode': img.mode
                    }
            except Exception:
                pass
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving image information")

@router.get("/metrics")
async def get_comprehensive_media_metrics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive media cache metrics and analytics
    
    Args:
        days: Number of days to include in metrics (default: 7)
    
    Returns:
        Comprehensive metrics including cache performance, bandwidth analysis,
        top requested images, error analysis, and active alerts
    """
    try:
        from ..services.media_metrics_service import media_metrics_service
        from ..services.media_cache_service import media_cache_service
        
        # Get comprehensive metrics
        metrics = await media_metrics_service.get_comprehensive_metrics(days)
        
        # Add cache health check
        cache_health = await media_cache_service.health_check()
        metrics['cache_health'] = cache_health
        
        # Add service configuration
        metrics['service_config'] = {
            'cache_ttl_seconds': settings.MEDIA_CACHE_TTL,
            'cache_prefix': settings.MEDIA_CACHE_PREFIX,
            'compression_enabled': settings.MEDIA_CACHE_COMPRESSION,
            'resize_enabled': settings.MEDIA_RESIZE_ENABLED,
            'lazy_loading_enabled': settings.MEDIA_LAZY_LOADING,
            'prefetch_enabled': settings.MEDIA_PREFETCH_ENABLED,
            'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
            'allowed_image_types': list(ALLOWED_IMAGE_TYPES)
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting comprehensive media metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")

@router.get("/metrics/alerts")
async def get_active_alerts():
    """Get active alerts for media cache system"""
    try:
        from ..services.media_metrics_service import media_metrics_service
        alerts = await media_metrics_service._get_active_alerts()
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving alerts")

@router.post("/metrics/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an active alert"""
    try:
        from ..services.media_metrics_service import media_metrics_service
        success = await media_metrics_service.resolve_alert(alert_id)
        if success:
            return {"message": "Alert resolved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Error resolving alert")

@router.get("/cache/invalidate")
async def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching pattern"""
    try:
        from ..services.media_cache_service import media_cache_service
        count = await media_cache_service.invalidate_cache(pattern)
        return {
            "message": f"Invalidated {count} cache entries",
            "pattern": pattern,
            "count": count
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Error invalidating cache")

@router.get("/cache/health")
async def cache_health_check():
    """Check cache system health"""
    try:
        from ..services.media_cache_service import media_cache_service
        health = await media_cache_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        raise HTTPException(status_code=500, detail="Cache health check failed")

@router.get("/optimization/recommendations/{image_type}/{image_path:path}")
async def get_optimization_recommendations(
    image_type: str,
    image_path: str,
    db: Session = Depends(get_db)
):
    """Get optimization recommendations for an image"""
    try:
        from ..services.media_optimization_service import media_optimization_service
        from ..services.image_mapping_service import image_mapping_service
        
        # Validate inputs
        if not security_validator.validate_image_type(image_type):
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        is_path_safe, path_error = security_validator.validate_path_security(image_path)
        if not is_path_safe:
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Get image mapping
        mapping = image_mapping_service.resolve_image_path(db, image_path, image_type)
        if not mapping or not mapping.exists:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Read image data
        with open(mapping.physical_path, 'rb') as f:
            image_data = f.read()
        
        # Get recommendations
        recommendations = await media_optimization_service.get_optimization_recommendations(
            image_data, image_type
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error getting recommendations")

@router.get("/stats")
async def get_media_stats(db: Session = Depends(get_db)):
    """Get basic statistics about the media service (legacy endpoint)"""
    try:
        stats = image_mapping_service.get_mapping_stats(db)
        
        # Add service-specific stats
        stats['service_info'] = {
            'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
            'allowed_image_types': list(ALLOWED_IMAGE_TYPES),
            'cache_max_age_seconds': CACHE_MAX_AGE,
            'compression_threshold_bytes': COMPRESSION_THRESHOLD
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error generating media stats: {e}")
        raise HTTPException(status_code=500, detail="Error generating statistics")

# Rate limit error handler
@router.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = Response(
        content=f"Rate limit exceeded: {exc.detail}",
        status_code=429
    )
    response.headers["X-RateLimit-Limit"] = str(exc.detail)
    response.headers["X-RateLimit-Reset"] = str(exc.detail)
    return response