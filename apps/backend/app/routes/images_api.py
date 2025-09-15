"""
API endpoint for serving question images
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
import os
import mimetypes

router = APIRouter(prefix="/api/images", tags=["images"])

# Base path for images
IMAGES_BASE_PATH = Path("/app/allquestions")

@router.get("/list")
async def list_available_images():
    """
    List all available image directories for debugging
    """
    try:
        directories = []
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}
        
        for subject_dir in IMAGES_BASE_PATH.iterdir():
            if subject_dir.is_dir() and subject_dir.name not in ['placeholders', 'scripts']:
                image_count = 0
                for ext in image_extensions:
                    image_count += len(list(subject_dir.rglob(f'*{ext}')))
                
                directories.append({
                    'subject': subject_dir.name,
                    'image_count': image_count,
                    'path': str(subject_dir.relative_to(IMAGES_BASE_PATH))
                })
        
        return {
            'status': 'success',
            'base_path': str(IMAGES_BASE_PATH),
            'directories': directories,
            'total_images': sum(d['image_count'] for d in directories)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing images: {str(e)}"
        )

@router.get("/{file_path:path}")
async def serve_image(file_path: str):
    """
    Serve image files from the allquestions directory
    
    Args:
        file_path: Path to the image file (e.g., "Matematicas/Imagenes_Matematicas/001.png")
    
    Returns:
        FileResponse with the image
    """
    try:
        # Construct full file path
        full_path = IMAGES_BASE_PATH / file_path
        
        # Security check: ensure the path is within the allowed directory
        if not str(full_path.resolve()).startswith(str(IMAGES_BASE_PATH.resolve())):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Path outside allowed directory"
            )
        
        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {file_path}"
            )
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Return file response
        return FileResponse(
            path=str(full_path),
            media_type=mime_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                "Access-Control-Allow-Origin": "*"  # Allow CORS for images
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving image: {str(e)}"
        )