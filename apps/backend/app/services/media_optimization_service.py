"""
Media Optimization Service
Advanced image processing, lazy loading, and performance optimizations
"""

import asyncio
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from PIL import Image, ImageOps, ImageFilter
import numpy as np

from ..core.config import settings
from .media_cache_service import media_cache_service

logger = logging.getLogger(__name__)

class ImageFormat(Enum):
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"
    GIF = "GIF"

class OptimizationLevel(Enum):
    NONE = 0
    BASIC = 1
    AGGRESSIVE = 2
    MAXIMUM = 3

@dataclass
class OptimizationSettings:
    """Image optimization settings"""
    quality: int = 85
    format: ImageFormat = ImageFormat.JPEG
    progressive: bool = True
    optimize: bool = True
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    preserve_exif: bool = False
    apply_sharpening: bool = False
    compression_level: int = 6

@dataclass
class LazyLoadConfig:
    """Lazy loading configuration"""
    placeholder_quality: int = 20
    placeholder_blur: int = 2
    placeholder_size: Tuple[int, int] = (50, 50)
    progressive_steps: List[int] = None
    
    def __post_init__(self):
        if self.progressive_steps is None:
            self.progressive_steps = [20, 40, 70, 100]

@dataclass
class OptimizationResult:
    """Result of image optimization"""
    original_size: int
    optimized_size: int
    compression_ratio: float
    format_changed: bool
    dimensions_changed: bool
    processing_time_ms: float
    optimization_level: OptimizationLevel

class MediaOptimizationService:
    """Advanced media optimization service with lazy loading and performance features"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.optimization_cache = {}
        self.lazy_load_configs = {
            'question': LazyLoadConfig(placeholder_quality=15, placeholder_blur=3),
            'option_a': LazyLoadConfig(placeholder_quality=20, placeholder_blur=2),
            'option_b': LazyLoadConfig(placeholder_quality=20, placeholder_blur=2),
            'option_c': LazyLoadConfig(placeholder_quality=20, placeholder_blur=2),
            'option_d': LazyLoadConfig(placeholder_quality=20, placeholder_blur=2),
            'placeholder': LazyLoadConfig(placeholder_quality=30, placeholder_blur=1)
        }
        
        # Optimization presets
        self.optimization_presets = {
            OptimizationLevel.BASIC: OptimizationSettings(
                quality=80, 
                format=ImageFormat.JPEG,
                optimize=True
            ),
            OptimizationLevel.AGGRESSIVE: OptimizationSettings(
                quality=70, 
                format=ImageFormat.WEBP,
                optimize=True,
                apply_sharpening=True
            ),
            OptimizationLevel.MAXIMUM: OptimizationSettings(
                quality=60, 
                format=ImageFormat.WEBP,
                optimize=True,
                max_width=1920,
                max_height=1080,
                apply_sharpening=True,
                compression_level=9
            )
        }
    
    async def optimize_image(self, image_data: bytes, image_type: str, 
                           optimization_level: OptimizationLevel = OptimizationLevel.BASIC,
                           custom_settings: Optional[OptimizationSettings] = None) -> Tuple[bytes, OptimizationResult]:
        """Optimize image with specified level and settings"""
        start_time = datetime.utcnow()
        
        try:
            # Use custom settings or preset
            settings_to_use = custom_settings or self.optimization_presets[optimization_level]
            
            # Run optimization in thread pool
            loop = asyncio.get_event_loop()
            optimized_data, result = await loop.run_in_executor(
                self.thread_pool,
                self._optimize_image_sync,
                image_data,
                image_type,
                settings_to_use,
                optimization_level
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = processing_time
            
            return optimized_data, result
            
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            # Return original data on error
            result = OptimizationResult(
                original_size=len(image_data),
                optimized_size=len(image_data),
                compression_ratio=1.0,
                format_changed=False,
                dimensions_changed=False,
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                optimization_level=OptimizationLevel.NONE
            )
            return image_data, result
    
    def _optimize_image_sync(self, image_data: bytes, image_type: str,
                           settings_obj: OptimizationSettings,
                           optimization_level: OptimizationLevel) -> Tuple[bytes, OptimizationResult]:
        """Synchronous image optimization"""
        try:
            original_size = len(image_data)
            
            # Load image
            with Image.open(io.BytesIO(image_data)) as img:
                original_format = img.format
                original_dimensions = img.size
                
                # Convert to RGB if necessary for JPEG
                if settings_obj.format == ImageFormat.JPEG and img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                
                # Resize if needed
                if settings_obj.max_width or settings_obj.max_height:
                    img = self._resize_image(img, settings_obj.max_width, settings_obj.max_height)
                
                # Apply sharpening if requested
                if settings_obj.apply_sharpening:
                    img = self._apply_sharpening(img)
                
                # Optimize based on image type
                img = self._apply_type_specific_optimizations(img, image_type)
                
                # Save optimized image
                output = io.BytesIO()
                save_kwargs = {
                    'format': settings_obj.format.value,
                    'optimize': settings_obj.optimize,
                    'quality': settings_obj.quality
                }
                
                if settings_obj.format == ImageFormat.JPEG:
                    save_kwargs['progressive'] = settings_obj.progressive
                elif settings_obj.format == ImageFormat.PNG:
                    save_kwargs['compress_level'] = settings_obj.compression_level
                elif settings_obj.format == ImageFormat.WEBP:
                    save_kwargs['method'] = 6  # Best compression method
                
                img.save(output, **save_kwargs)
                optimized_data = output.getvalue()
                
                # Calculate results
                optimized_size = len(optimized_data)
                compression_ratio = optimized_size / original_size if original_size > 0 else 1.0
                format_changed = original_format != settings_obj.format.value
                dimensions_changed = original_dimensions != img.size
                
                result = OptimizationResult(
                    original_size=original_size,
                    optimized_size=optimized_size,
                    compression_ratio=compression_ratio,
                    format_changed=format_changed,
                    dimensions_changed=dimensions_changed,
                    processing_time_ms=0,  # Will be set by caller
                    optimization_level=optimization_level
                )
                
                return optimized_data, result
                
        except Exception as e:
            logger.error(f"Error in synchronous image optimization: {e}")
            raise
    
    def _resize_image(self, img: Image.Image, max_width: Optional[int], 
                     max_height: Optional[int]) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        original_width, original_height = img.size
        
        # Calculate new dimensions
        if max_width and max_height:
            ratio = min(max_width / original_width, max_height / original_height)
        elif max_width:
            ratio = max_width / original_width
        elif max_height:
            ratio = max_height / original_height
        else:
            return img
        
        if ratio >= 1:
            return img  # Don't upscale
        
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Use high-quality resampling
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _apply_sharpening(self, img: Image.Image) -> Image.Image:
        """Apply subtle sharpening to image"""
        try:
            # Apply unsharp mask filter
            return img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        except Exception:
            return img
    
    def _apply_type_specific_optimizations(self, img: Image.Image, image_type: str) -> Image.Image:
        """Apply optimizations specific to image type"""
        try:
            if image_type == 'question':
                # Questions might be text-heavy, prefer sharper images
                return img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            elif image_type in ['option_a', 'option_b', 'option_c', 'option_d']:
                # Options might be mathematical formulas, enhance text
                return img.filter(ImageFilter.EDGE_ENHANCE)
            elif image_type == 'placeholder':
                # Placeholders can be more compressed
                return img
            else:
                return img
        except Exception:
            return img
    
    async def generate_lazy_load_placeholder(self, image_data: bytes, 
                                           image_type: str) -> bytes:
        """Generate a low-quality placeholder for lazy loading"""
        try:
            config = self.lazy_load_configs.get(image_type, LazyLoadConfig())
            
            loop = asyncio.get_event_loop()
            placeholder_data = await loop.run_in_executor(
                self.thread_pool,
                self._generate_placeholder_sync,
                image_data,
                config
            )
            
            return placeholder_data
            
        except Exception as e:
            logger.error(f"Error generating lazy load placeholder: {e}")
            return image_data
    
    def _generate_placeholder_sync(self, image_data: bytes, 
                                  config: LazyLoadConfig) -> bytes:
        """Synchronously generate placeholder"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Resize to small size
                placeholder = img.resize(config.placeholder_size, Image.Resampling.LANCZOS)
                
                # Apply blur
                if config.placeholder_blur > 0:
                    placeholder = placeholder.filter(
                        ImageFilter.GaussianBlur(radius=config.placeholder_blur)
                    )
                
                # Convert to RGB for JPEG
                if placeholder.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', placeholder.size, (255, 255, 255))
                    if placeholder.mode == 'P':
                        placeholder = placeholder.convert('RGBA')
                    background.paste(
                        placeholder, 
                        mask=placeholder.split()[-1] if placeholder.mode in ('RGBA', 'LA') else None
                    )
                    placeholder = background
                
                # Save as low-quality JPEG
                output = io.BytesIO()
                placeholder.save(
                    output,
                    format='JPEG',
                    quality=config.placeholder_quality,
                    optimize=True
                )
                
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error in placeholder generation: {e}")
            return image_data
    
    async def generate_progressive_images(self, image_data: bytes, 
                                        image_type: str) -> Dict[int, bytes]:
        """Generate progressive quality images for lazy loading"""
        try:
            config = self.lazy_load_configs.get(image_type, LazyLoadConfig())
            
            loop = asyncio.get_event_loop()
            progressive_images = await loop.run_in_executor(
                self.thread_pool,
                self._generate_progressive_sync,
                image_data,
                config
            )
            
            return progressive_images
            
        except Exception as e:
            logger.error(f"Error generating progressive images: {e}")
            return {100: image_data}
    
    def _generate_progressive_sync(self, image_data: bytes, 
                                  config: LazyLoadConfig) -> Dict[int, bytes]:
        """Synchronously generate progressive quality images"""
        try:
            progressive_images = {}
            
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(
                        img, 
                        mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                    )
                    img = background
                
                for quality in config.progressive_steps:
                    output = io.BytesIO()
                    img.save(
                        output,
                        format='JPEG',
                        quality=quality,
                        optimize=True,
                        progressive=True
                    )
                    progressive_images[quality] = output.getvalue()
            
            return progressive_images
            
        except Exception as e:
            logger.error(f"Error in progressive image generation: {e}")
            return {100: image_data}
    
    async def auto_optimize_for_device(self, image_data: bytes, image_type: str,
                                     user_agent: str, connection_speed: str = 'unknown') -> Tuple[bytes, OptimizationResult]:
        """Automatically optimize image based on device and connection"""
        try:
            # Determine optimization level based on user agent and connection
            optimization_level = self._determine_optimization_level(user_agent, connection_speed)
            
            # Get device-specific settings
            custom_settings = self._get_device_settings(user_agent, image_type)
            
            return await self.optimize_image(
                image_data,
                image_type,
                optimization_level,
                custom_settings
            )
            
        except Exception as e:
            logger.error(f"Error in auto-optimization: {e}")
            result = OptimizationResult(
                original_size=len(image_data),
                optimized_size=len(image_data),
                compression_ratio=1.0,
                format_changed=False,
                dimensions_changed=False,
                processing_time_ms=0,
                optimization_level=OptimizationLevel.NONE
            )
            return image_data, result
    
    def _determine_optimization_level(self, user_agent: str, 
                                    connection_speed: str) -> OptimizationLevel:
        """Determine optimization level based on device and connection"""
        user_agent_lower = user_agent.lower()
        
        # Mobile devices - more aggressive compression
        if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone', 'ipad']):
            if connection_speed in ['slow', '2g', '3g']:
                return OptimizationLevel.MAXIMUM
            elif connection_speed in ['4g', 'fast']:
                return OptimizationLevel.AGGRESSIVE
            else:
                return OptimizationLevel.AGGRESSIVE
        
        # Desktop devices
        else:
            if connection_speed in ['slow', '2g']:
                return OptimizationLevel.AGGRESSIVE
            elif connection_speed in ['3g', '4g']:
                return OptimizationLevel.BASIC
            else:
                return OptimizationLevel.BASIC
    
    def _get_device_settings(self, user_agent: str, 
                           image_type: str) -> Optional[OptimizationSettings]:
        """Get device-specific optimization settings"""
        user_agent_lower = user_agent.lower()
        
        # Mobile devices
        if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone']):
            return OptimizationSettings(
                quality=70,
                format=ImageFormat.WEBP if 'chrome' in user_agent_lower or 'android' in user_agent_lower else ImageFormat.JPEG,
                max_width=800,
                max_height=600,
                optimize=True,
                progressive=True
            )
        
        # Tablet devices
        elif 'ipad' in user_agent_lower or 'tablet' in user_agent_lower:
            return OptimizationSettings(
                quality=75,
                format=ImageFormat.WEBP if 'chrome' in user_agent_lower else ImageFormat.JPEG,
                max_width=1200,
                max_height=900,
                optimize=True,
                progressive=True
            )
        
        # Desktop - less aggressive
        else:
            return OptimizationSettings(
                quality=85,
                format=ImageFormat.WEBP if 'chrome' in user_agent_lower else ImageFormat.JPEG,
                optimize=True,
                progressive=True
            )
    
    async def batch_optimize_images(self, image_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch optimize multiple images for efficiency"""
        try:
            # Process images in parallel
            tasks = []
            for request in image_requests:
                task = self.optimize_image(
                    request['image_data'],
                    request['image_type'],
                    request.get('optimization_level', OptimizationLevel.BASIC),
                    request.get('custom_settings')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch optimization {i}: {result}")
                    processed_results.append({
                        'success': False,
                        'error': str(result),
                        'original_request': image_requests[i]
                    })
                else:
                    optimized_data, optimization_result = result
                    processed_results.append({
                        'success': True,
                        'optimized_data': optimized_data,
                        'optimization_result': optimization_result,
                        'original_request': image_requests[i]
                    })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in batch optimization: {e}")
            return [{'success': False, 'error': str(e)} for _ in image_requests]
    
    async def get_optimization_recommendations(self, image_data: bytes, 
                                             image_type: str) -> Dict[str, Any]:
        """Get optimization recommendations for an image"""
        try:
            loop = asyncio.get_event_loop()
            recommendations = await loop.run_in_executor(
                self.thread_pool,
                self._analyze_image_sync,
                image_data,
                image_type
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return {'error': str(e)}
    
    def _analyze_image_sync(self, image_data: bytes, image_type: str) -> Dict[str, Any]:
        """Analyze image and provide optimization recommendations"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
                file_size = len(image_data)
                
                recommendations = {
                    'current_stats': {
                        'file_size': file_size,
                        'dimensions': f"{width}x{height}",
                        'format': format_name,
                        'mode': mode
                    },
                    'recommendations': []
                }
                
                # Size recommendations
                if file_size > 500 * 1024:  # > 500KB
                    recommendations['recommendations'].append({
                        'type': 'compression',
                        'message': 'Image is large, consider more aggressive compression',
                        'suggested_quality': 70
                    })
                
                # Dimension recommendations
                if width > 1920 or height > 1080:
                    recommendations['recommendations'].append({
                        'type': 'resize',
                        'message': 'Image dimensions are very large, consider resizing',
                        'suggested_max_width': 1920,
                        'suggested_max_height': 1080
                    })
                
                # Format recommendations
                if format_name == 'PNG' and mode == 'RGB':
                    recommendations['recommendations'].append({
                        'type': 'format',
                        'message': 'RGB PNG can be converted to JPEG for better compression',
                        'suggested_format': 'JPEG'
                    })
                
                # Type-specific recommendations
                if image_type in ['option_a', 'option_b', 'option_c', 'option_d']:
                    if file_size > 100 * 1024:  # > 100KB
                        recommendations['recommendations'].append({
                            'type': 'optimization',
                            'message': 'Option images should be optimized for fast loading',
                            'suggested_optimization': 'aggressive'
                        })
                
                return recommendations
                
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)

# Global instance
media_optimization_service = MediaOptimizationService()