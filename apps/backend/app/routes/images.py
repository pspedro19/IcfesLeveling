"""
Secure image serving endpoints for ICFES Leveling system
Provides secure, validated image serving with caching and CORS support
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
import logging

from ..core.database import get_db
from ..core.config import settings
from ..services.multimedia_service import multimedia_service

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)

# Allowed image extensions for security
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}

# Base paths for image serving - updated to match actual project structure
BASE_PATHS = {
    'allquestions': Path('database/allquestions'),
    'mathimg': Path('mathimg'),
    'uploads': Path('uploads'),
    'cache': Path('cache')
}

def get_base_project_path():
    """Get the base project path (IcfesLeveling directory)"""
    # This will be the IcfesLeveling project root
    current_file = Path(__file__)
    project_root = current_file.parents[4]  # Go up from app/routes/images.py to project root
    return project_root

def validate_image_path(image_path: str) -> Optional[Path]:
    """
    Validate and resolve image path securely
    Prevents directory traversal attacks and validates file existence
    """
    try:
        # Clean the path and prevent directory traversal
        clean_path = os.path.normpath(image_path).replace('\\', '/')
        
        # Check for directory traversal attempts
        if '..' in clean_path or clean_path.startswith('/') or '~' in clean_path:
            logger.warning(f"Directory traversal attempt detected: {image_path}")
            return None
        
        project_root = get_base_project_path()
        
        # Try different base paths
        for base_name, base_path in BASE_PATHS.items():
            full_base_path = project_root / base_path
            full_image_path = full_base_path / clean_path
            
            logger.debug(f"Checking path: {full_image_path}")
            
            # Check if file exists and is within allowed directory
            if full_image_path.exists() and full_image_path.is_file():
                # Ensure the resolved path is still within the base directory
                try:
                    full_image_path.resolve().relative_to(full_base_path.resolve())
                    
                    # Check file extension
                    if full_image_path.suffix.lower() in ALLOWED_EXTENSIONS:
                        logger.info(f"Valid image path found: {full_image_path}")
                        return full_image_path
                    else:
                        logger.warning(f"Invalid file extension: {full_image_path.suffix}")
                except ValueError:
                    # Path is outside the base directory
                    logger.warning(f"Path outside base directory: {full_image_path}")
                    continue
        
        # Try direct path from project root (for legacy compatibility)
        direct_path = project_root / clean_path
        if direct_path.exists() and direct_path.is_file():
            if direct_path.suffix.lower() in ALLOWED_EXTENSIONS:
                logger.info(f"Valid direct image path found: {direct_path}")
                return direct_path
        
        logger.warning(f"Image not found in any base path: {image_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error validating image path {image_path}: {e}")
        return None

@router.get("/{image_path:path}")
async def serve_image(
    request: Request,
    image_path: str,
    width: Optional[int] = Query(None, description="Resize width"),
    height: Optional[int] = Query(None, description="Resize height"),
    quality: Optional[int] = Query(85, description="JPEG quality (1-100)", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Serve images securely with optional resizing and caching
    
    Examples:
    - /api/v1/images/Matematicas/Imagenes_Matematicas/Cuadernillo Matematicas/001_CuadernilloMatematic.png
    - /api/v1/images/Ciencias Naturales/imagenes/contexto_Pregunta_21.png?width=400&height=300
    """
    try:
        # Validate and resolve the image path
        resolved_path = validate_image_path(image_path)
        if not resolved_path:
            logger.warning(f"Invalid or not found image path: {image_path}")
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(resolved_path))
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # Default fallback
        
        # Check if resizing is requested
        if width or height:
            try:
                # Generate cache key
                cache_key = f"{resolved_path.stem}_{width}x{height}_{quality}{resolved_path.suffix}"
                cache_path = get_base_project_path() / 'cache' / 'images' / cache_key
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if cached version exists
                if cache_path.exists():
                    logger.debug(f"Serving cached resized image: {cache_path}")
                    return FileResponse(
                        cache_path,
                        media_type=mime_type,
                        headers={
                            "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET",
                            "Access-Control-Allow-Headers": "Content-Type"
                        }
                    )
                
                # Resize image and cache it
                from PIL import Image
                with Image.open(resolved_path) as img:
                    # Calculate resize dimensions maintaining aspect ratio
                    original_width, original_height = img.size
                    
                    if width and height:
                        new_size = (width, height)
                    elif width:
                        aspect_ratio = original_height / original_width
                        new_size = (width, int(width * aspect_ratio))
                    elif height:
                        aspect_ratio = original_width / original_height
                        new_size = (int(height * aspect_ratio), height)
                    else:
                        new_size = (original_width, original_height)
                    
                    # Resize using high-quality resampling
                    resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary (for JPEG)
                    if resized_img.mode in ('RGBA', 'LA', 'P') and mime_type == 'image/jpeg':
                        rgb_img = Image.new('RGB', resized_img.size, (255, 255, 255))
                        if resized_img.mode == 'RGBA':
                            rgb_img.paste(resized_img, mask=resized_img.split()[-1])
                        else:
                            rgb_img.paste(resized_img)
                        resized_img = rgb_img
                    
                    # Save cached version
                    if mime_type == 'image/jpeg':
                        resized_img.save(cache_path, 'JPEG', quality=quality, optimize=True)
                    else:
                        resized_img.save(cache_path, optimize=True)
                    
                    logger.info(f"Created and cached resized image: {cache_path}")
                
                return FileResponse(
                    cache_path,
                    media_type=mime_type,
                    headers={
                        "Cache-Control": "public, max-age=86400",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET",
                        "Access-Control-Allow-Headers": "Content-Type"
                    }
                )
                
            except Exception as resize_error:
                logger.error(f"Error resizing image: {resize_error}")
                # Fall back to serving original image
        
        # Serve original image
        logger.info(f"Serving original image: {resolved_path}")
        return FileResponse(
            resolved_path,
            media_type=mime_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {image_path}: {e}")
        raise HTTPException(status_code=500, detail="Error serving image")

@router.get("/info/{image_path:path}")
async def get_image_info(
    image_path: str,
    db: Session = Depends(get_db)
):
    """
    Get information about an image without serving the actual file
    """
    try:
        resolved_path = validate_image_path(image_path)
        if not resolved_path:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get file stats
        stat_info = resolved_path.stat()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(resolved_path))
        
        # Try to get image dimensions
        dimensions = None
        try:
            from PIL import Image
            with Image.open(resolved_path) as img:
                dimensions = {
                    "width": img.size[0],
                    "height": img.size[1],
                    "mode": img.mode,
                    "format": img.format
                }
        except Exception as img_error:
            logger.warning(f"Could not get image dimensions for {image_path}: {img_error}")
        
        return {
            "path": image_path,
            "resolved_path": str(resolved_path),
            "filename": resolved_path.name,
            "size_bytes": stat_info.st_size,
            "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
            "mime_type": mime_type,
            "last_modified": stat_info.st_mtime,
            "dimensions": dimensions,
            "exists": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image info for {image_path}: {e}")
        raise HTTPException(status_code=500, detail="Error getting image information")

@router.get("/manifest")
async def get_images_manifest(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: Optional[int] = Query(100, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    Get a manifest of all available images
    """
    try:
        project_root = get_base_project_path()
        manifest = {
            "total_count": 0,
            "total_size_mb": 0,
            "categories": {}
        }
        
        for category_name, base_path in BASE_PATHS.items():
            if category and category != category_name:
                continue
                
            full_base_path = project_root / base_path
            if not full_base_path.exists():
                continue
            
            category_images = []
            category_size = 0
            
            # Recursively find all image files
            for ext in ALLOWED_EXTENSIONS:
                pattern = f"**/*{ext}"
                for image_path in full_base_path.rglob(pattern):
                    if image_path.is_file():
                        try:
                            stat_info = image_path.stat()
                            relative_path = image_path.relative_to(full_base_path)
                            
                            category_images.append({
                                "path": str(relative_path).replace('\\', '/'),
                                "filename": image_path.name,
                                "size_bytes": stat_info.st_size,
                                "last_modified": stat_info.st_mtime
                            })
                            category_size += stat_info.st_size
                            
                        except Exception as file_error:
                            logger.warning(f"Error processing file {image_path}: {file_error}")
            
            # Limit results per category
            if limit:
                category_images = category_images[:limit]
            
            manifest["categories"][category_name] = {
                "count": len(category_images),
                "size_mb": round(category_size / (1024 * 1024), 2),
                "images": category_images
            }
            
            manifest["total_count"] += len(category_images)
            manifest["total_size_mb"] += round(category_size / (1024 * 1024), 2)
        
        return manifest
        
    except Exception as e:
        logger.error(f"Error generating images manifest: {e}")
        raise HTTPException(status_code=500, detail="Error generating images manifest")

@router.post("/cache/clear")
async def clear_image_cache():
    """
    Clear the image cache directory
    """
    try:
        import shutil
        
        cache_path = get_base_project_path() / 'cache' / 'images'
        if cache_path.exists():
            shutil.rmtree(cache_path)
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.info("Image cache cleared successfully")
            return {"message": "Image cache cleared successfully"}
        else:
            return {"message": "Cache directory does not exist"}
            
    except Exception as e:
        logger.error(f"Error clearing image cache: {e}")
        raise HTTPException(status_code=500, detail="Error clearing image cache")