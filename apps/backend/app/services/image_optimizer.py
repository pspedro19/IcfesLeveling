#!/usr/bin/env python3
"""
Advanced Image Optimization Service
Optimizes images for web delivery with caching, compression, and CDN support
"""

import os
import hashlib
import logging
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageOpt
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class ImageOptimizationSettings:
    """Image optimization configuration"""
    jpeg_quality: int = 85
    png_optimize: bool = True
    webp_quality: int = 85
    max_width: int = 1920
    max_height: int = 1080
    thumbnail_sizes: List[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.thumbnail_sizes is None:
            self.thumbnail_sizes = [(150, 150), (300, 300), (600, 400)]

@dataclass
class OptimizationResult:
    """Result of image optimization process"""
    original_size: int
    optimized_size: int
    compression_ratio: float
    format_original: str
    format_optimized: str
    width: int
    height: int
    processing_time: float
    thumbnails_created: int

class ImageOptimizer:
    """Advanced image optimization service with CDN support"""
    
    def __init__(self, 
                 cache_dir: str = "/tmp/image_cache",
                 settings: Optional[ImageOptimizationSettings] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.settings = settings or ImageOptimizationSettings()
        self.optimization_stats = {
            'total_images_processed': 0,
            'total_bytes_saved': 0,
            'avg_compression_ratio': 0.0,
            'formats_converted': {'to_webp': 0, 'to_jpeg': 0, 'to_png': 0}
        }
    
    def generate_image_hash(self, image_data: bytes) -> str:
        """Generate hash for image content"""
        return hashlib.md5(image_data).hexdigest()
    
    def get_optimized_filename(self, original_name: str, optimization_type: str, size: Optional[Tuple[int, int]] = None) -> str:
        """Generate filename for optimized image"""
        name_parts = original_name.split('.')
        base_name = '.'.join(name_parts[:-1])
        
        size_suffix = f"_{size[0]}x{size[1]}" if size else ""
        return f"{base_name}_{optimization_type}{size_suffix}.webp"
    
    def is_image_cached(self, image_hash: str, optimization_type: str, size: Optional[Tuple[int, int]] = None) -> bool:
        """Check if optimized image exists in cache"""
        cache_filename = self.get_cache_filename(image_hash, optimization_type, size)
        return (self.cache_dir / cache_filename).exists()
    
    def get_cache_filename(self, image_hash: str, optimization_type: str, size: Optional[Tuple[int, int]] = None) -> str:
        """Generate cache filename for optimized image"""
        size_suffix = f"_{size[0]}x{size[1]}" if size else ""
        return f"{image_hash}_{optimization_type}{size_suffix}.webp"
    
    def optimize_image(self, image_data: bytes, filename: str, 
                      target_format: str = 'webp') -> OptimizationResult:
        """Optimize a single image with specified format and quality"""
        import time
        start_time = time.time()
        
        try:
            # Open image with PIL
            with Image.open(BytesIO(image_data)) as img:
                original_size = len(image_data)
                original_format = img.format.lower() if img.format else 'unknown'
                
                # Convert RGBA to RGB if saving as JPEG
                if target_format.lower() == 'jpeg' and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Resize if image is too large
                original_width, original_height = img.size
                if (original_width > self.settings.max_width or 
                    original_height > self.settings.max_height):
                    
                    img.thumbnail((self.settings.max_width, self.settings.max_height), 
                                Image.Resampling.LANCZOS)
                
                # Optimize and save to memory
                output_buffer = BytesIO()
                
                if target_format.lower() == 'webp':
                    img.save(output_buffer, 'WEBP', 
                            quality=self.settings.webp_quality, 
                            optimize=True)
                elif target_format.lower() == 'jpeg':
                    img.save(output_buffer, 'JPEG', 
                            quality=self.settings.jpeg_quality, 
                            optimize=True)
                elif target_format.lower() == 'png':
                    img.save(output_buffer, 'PNG', 
                            optimize=self.settings.png_optimize)
                
                optimized_data = output_buffer.getvalue()
                optimized_size = len(optimized_data)
                compression_ratio = (1 - optimized_size / original_size) * 100
                
                processing_time = time.time() - start_time
                
                # Update stats
                self.optimization_stats['total_images_processed'] += 1
                self.optimization_stats['total_bytes_saved'] += (original_size - optimized_size)
                self.optimization_stats[f'formats_converted'][f'to_{target_format}'] += 1
                
                return OptimizationResult(
                    original_size=original_size,
                    optimized_size=optimized_size,
                    compression_ratio=compression_ratio,
                    format_original=original_format,
                    format_optimized=target_format,
                    width=img.width,
                    height=img.height,
                    processing_time=processing_time,
                    thumbnails_created=0  # Will be set by create_thumbnails
                )
        
        except Exception as e:
            logger.error(f"Error optimizing image {filename}: {e}")
            raise
    
    def create_thumbnails(self, image_data: bytes, filename: str) -> List[Tuple[Tuple[int, int], bytes]]:
        """Create thumbnail versions of an image"""
        thumbnails = []
        
        try:
            with Image.open(BytesIO(image_data)) as img:
                for size in self.settings.thumbnail_sizes:
                    # Create thumbnail
                    thumb_img = img.copy()
                    thumb_img.thumbnail(size, Image.Resampling.LANCZOS)
                    
                    # Save thumbnail
                    output_buffer = BytesIO()
                    thumb_img.save(output_buffer, 'WEBP', 
                                  quality=self.settings.webp_quality, 
                                  optimize=True)
                    
                    thumbnails.append((size, output_buffer.getvalue()))
            
            return thumbnails
        
        except Exception as e:
            logger.error(f"Error creating thumbnails for {filename}: {e}")
            return []
    
    async def process_image_complete(self, image_data: bytes, filename: str, 
                                   create_thumbs: bool = True) -> Dict[str, Any]:
        """Complete image processing: optimization + thumbnails + caching"""
        image_hash = self.generate_image_hash(image_data)
        
        results = {
            'hash': image_hash,
            'original_filename': filename,
            'optimized': None,
            'thumbnails': [],
            'cached': False
        }
        
        # Check if already cached
        if self.is_image_cached(image_hash, 'optimized'):
            results['cached'] = True
            cache_file = self.cache_dir / self.get_cache_filename(image_hash, 'optimized')
            with open(cache_file, 'rb') as f:
                optimized_data = f.read()
            
            results['optimized'] = {
                'data': optimized_data,
                'size': len(optimized_data),
                'format': 'webp',
                'from_cache': True
            }
        else:
            # Optimize image
            optimization_result = self.optimize_image(image_data, filename, 'webp')
            
            # Cache optimized image
            cache_filename = self.get_cache_filename(image_hash, 'optimized')
            cache_path = self.cache_dir / cache_filename
            
            with Image.open(BytesIO(image_data)) as img:
                img.save(cache_path, 'WEBP', quality=self.settings.webp_quality, optimize=True)
            
            with open(cache_path, 'rb') as f:
                optimized_data = f.read()
            
            results['optimized'] = {
                'data': optimized_data,
                'size': optimization_result.optimized_size,
                'format': 'webp',
                'compression_ratio': optimization_result.compression_ratio,
                'processing_time': optimization_result.processing_time,
                'from_cache': False
            }
        
        # Create thumbnails if requested
        if create_thumbs:
            thumbnails = self.create_thumbnails(image_data, filename)
            
            for size, thumb_data in thumbnails:
                thumb_cache_filename = self.get_cache_filename(image_hash, 'thumbnail', size)
                thumb_cache_path = self.cache_dir / thumb_cache_filename
                
                # Cache thumbnail
                if not thumb_cache_path.exists():
                    with open(thumb_cache_path, 'wb') as f:
                        f.write(thumb_data)
                
                results['thumbnails'].append({
                    'size': size,
                    'data': thumb_data,
                    'file_size': len(thumb_data),
                    'cache_filename': thumb_cache_filename
                })
        
        return results
    
    def get_cached_image(self, image_hash: str, optimization_type: str = 'optimized', 
                        size: Optional[Tuple[int, int]] = None) -> Optional[bytes]:
        """Retrieve cached optimized image"""
        cache_filename = self.get_cache_filename(image_hash, optimization_type, size)
        cache_path = self.cache_dir / cache_filename
        
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                return f.read()
        
        return None
    
    def batch_optimize_directory(self, directory: str, 
                               supported_formats: List[str] = None) -> Dict[str, Any]:
        """Batch optimize all images in a directory"""
        if supported_formats is None:
            supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']
        
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        results = {
            'total_images': 0,
            'processed': 0,
            'errors': 0,
            'total_size_before': 0,
            'total_size_after': 0,
            'processing_time': 0,
            'processed_files': []
        }
        
        import time
        start_time = time.time()
        
        # Find all image files
        image_files = []
        for ext in supported_formats:
            image_files.extend(directory_path.rglob(f"*{ext}"))
            image_files.extend(directory_path.rglob(f"*{ext.upper()}"))
        
        results['total_images'] = len(image_files)
        
        for image_file in image_files:
            try:
                with open(image_file, 'rb') as f:
                    image_data = f.read()
                
                results['total_size_before'] += len(image_data)
                
                # Process image
                processed = asyncio.run(self.process_image_complete(
                    image_data, 
                    image_file.name,
                    create_thumbs=False
                ))
                
                results['total_size_after'] += processed['optimized']['size']
                results['processed'] += 1
                results['processed_files'].append({
                    'filename': image_file.name,
                    'original_size': len(image_data),
                    'optimized_size': processed['optimized']['size'],
                    'compression_ratio': ((len(image_data) - processed['optimized']['size']) / len(image_data)) * 100,
                    'hash': processed['hash']
                })
                
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
                results['errors'] += 1
        
        results['processing_time'] = time.time() - start_time
        results['total_compression_ratio'] = ((results['total_size_before'] - results['total_size_after']) / 
                                            max(results['total_size_before'], 1)) * 100
        
        return results
    
    def cleanup_cache(self, max_age_days: int = 30) -> Dict[str, int]:
        """Clean up old cached images"""
        import time
        from datetime import timedelta
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        cleaned_files = 0
        total_size_freed = 0
        
        for cache_file in self.cache_dir.iterdir():
            if cache_file.is_file():
                file_age = current_time - cache_file.stat().st_mtime
                
                if file_age > max_age_seconds:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    cleaned_files += 1
                    total_size_freed += file_size
        
        return {
            'cleaned_files': cleaned_files,
            'size_freed_mb': total_size_freed / (1024 * 1024),
            'max_age_days': max_age_days
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get image optimization statistics"""
        cache_stats = self.get_cache_stats()
        
        return {
            'processing_stats': self.optimization_stats,
            'cache_stats': cache_stats,
            'settings': {
                'jpeg_quality': self.settings.jpeg_quality,
                'png_optimize': self.settings.png_optimize,
                'webp_quality': self.settings.webp_quality,
                'max_dimensions': f"{self.settings.max_width}x{self.settings.max_height}",
                'thumbnail_sizes': self.settings.thumbnail_sizes
            }
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache directory statistics"""
        total_files = 0
        total_size = 0
        file_types = {'optimized': 0, 'thumbnail': 0}
        
        for cache_file in self.cache_dir.iterdir():
            if cache_file.is_file():
                total_files += 1
                total_size += cache_file.stat().st_size
                
                if 'thumbnail' in cache_file.name:
                    file_types['thumbnail'] += 1
                else:
                    file_types['optimized'] += 1
        
        return {
            'total_cached_files': total_files,
            'total_cache_size_mb': total_size / (1024 * 1024),
            'file_types': file_types,
            'cache_directory': str(self.cache_dir)
        }
    
    def generate_responsive_image_urls(self, image_hash: str, base_url: str) -> Dict[str, str]:
        """Generate responsive image URLs for different screen sizes"""
        urls = {
            'original': f"{base_url}/images/{image_hash}/optimized",
            'thumbnails': {}
        }
        
        for size in self.settings.thumbnail_sizes:
            size_key = f"{size[0]}x{size[1]}"
            urls['thumbnails'][size_key] = f"{base_url}/images/{image_hash}/thumbnail/{size[0]}x{size[1]}"
        
        return urls
    
    def get_image_metadata(self, image_data: bytes) -> Dict[str, Any]:
        """Extract metadata from image"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                metadata = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    'file_size': len(image_data)
                }
                
                # Add EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    metadata['exif'] = {k: v for k, v in exif.items() if isinstance(v, (int, str, float))}
                
                return metadata
        
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            return {}

# Global image optimizer instance
image_optimizer = ImageOptimizer()

# Utility functions for image optimization
async def optimize_math_images(math_images_dir: str = "/root/IcfesLeveling/mathimg") -> Dict[str, Any]:
    """Optimize math images specifically for the ICFES system"""
    if not os.path.exists(math_images_dir):
        return {'error': 'Math images directory not found'}
    
    # Custom settings for math images (higher quality for readability)
    math_settings = ImageOptimizationSettings(
        jpeg_quality=95,
        webp_quality=95,
        max_width=1200,
        max_height=800,
        thumbnail_sizes=[(150, 150), (300, 200), (600, 400)]
    )
    
    math_optimizer = ImageOptimizer(
        cache_dir="/tmp/math_image_cache",
        settings=math_settings
    )
    
    return math_optimizer.batch_optimize_directory(math_images_dir)

def create_image_cdn_headers(image_hash: str, format: str = 'webp') -> Dict[str, str]:
    """Generate appropriate headers for CDN caching"""
    return {
        'Content-Type': f'image/{format}',
        'Cache-Control': 'public, max-age=31536000, immutable',  # 1 year cache
        'ETag': f'"{image_hash}"',
        'Vary': 'Accept',
        'X-Optimized': 'true'
    }

def should_serve_webp(accept_header: str) -> bool:
    """Determine if client supports WebP format"""
    return 'image/webp' in accept_header.lower() if accept_header else False