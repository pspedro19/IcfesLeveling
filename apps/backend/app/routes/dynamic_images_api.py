"""
Dynamic Images API
=================
Serves images with dynamic URL generation based on environment.
No hardcoded URLs - fully portable across any server environment.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
import os
import mimetypes
import logging
from urllib.parse import unquote
from pathlib import Path

from ..core.database import get_db
from ..models.question import Question
from ..models.subject import Subject
from ..core.dynamic_config import get_server_config, get_dynamic_image_url

router = APIRouter(prefix="/dynamic-images", tags=["dynamic-images"])
logger = logging.getLogger(__name__)

class DynamicImageServer:
    """Dynamic image serving with environment-based URL generation"""
    
    def __init__(self):
        # Image base paths (in order of preference)
        self.base_paths = [
            "/app/images",  # Docker container path
            "/app/allquestions",  # Backend container path
            "/root/IcfesLeveling/database/allquestions",  # Direct host path
            "./database/allquestions",  # Relative path
        ]
        
        # Find the correct base path
        self.base_path = self._find_base_path()
        logger.info(f"Using image base path: {self.base_path}")
    
    def _find_base_path(self) -> str:
        """Find the correct base path for images"""
        for path in self.base_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        
        # If no path exists, create a fallback
        fallback_path = "/app/images"
        logger.warning(f"No image directory found, using fallback: {fallback_path}")
        return fallback_path
    
    def get_image_file_path(self, relative_path: str) -> Optional[str]:
        """Get full file path for relative image path"""
        if not relative_path:
            return None
        
        # Clean the relative path
        relative_path = relative_path.strip().lstrip('/')
        full_path = os.path.join(self.base_path, relative_path)
        
        # Security check - ensure path is within base directory
        resolved_base = os.path.abspath(self.base_path)
        resolved_full = os.path.abspath(full_path)
        
        if not resolved_full.startswith(resolved_base):
            logger.warning(f"Security: Path outside base directory: {relative_path}")
            return None
        
        return full_path if os.path.exists(full_path) else None
    
    def serve_image(self, relative_path: str) -> Dict[str, Any]:
        """Serve image file with proper headers"""
        file_path = self.get_image_file_path(relative_path)
        
        if not file_path:
            return {
                "error": "Image not found",
                "path": relative_path,
                "status": 404
            }
        
        try:
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "mime_type": mime_type,
                "file_size": file_size,
                "status": 200
            }
            
        except Exception as e:
            logger.error(f"Error serving image {relative_path}: {e}")
            return {
                "error": f"Error reading image: {str(e)}",
                "path": relative_path,
                "status": 500
            }

# Global image server instance
image_server = DynamicImageServer()

@router.get("/serve/{path:path}")
async def serve_image(path: str, request: Request):
    """Serve image file with dynamic configuration"""
    try:
        # URL decode the path
        decoded_path = unquote(path)
        
        # Get server configuration
        config = get_server_config()
        
        # Serve the image
        result = image_server.serve_image(decoded_path)
        
        if result["status"] != 200:
            raise HTTPException(
                status_code=result["status"], 
                detail=result.get("error", "Image not found")
            )
        
        # Read and return the file
        with open(result["file_path"], 'rb') as f:
            file_content = f.read()
        
        from fastapi import Response
        return Response(
            content=file_content,
            media_type=result["mime_type"],
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type",
                "X-Image-Server": "dynamic",
                "X-Environment": config.host
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/questions/{subject_id}")
async def get_questions_with_dynamic_urls(
    subject_id: str,
    limit: int = 20,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Get questions with dynamically generated image URLs"""
    try:
        # Get server configuration
        config = get_server_config()
        
        # Get subject
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Get questions with images (stored as relative paths)
        questions = db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                or_(
                    Question.pregunta_imagen.isnot(None),
                    Question.opcion_a_imagen.isnot(None),
                    Question.opcion_b_imagen.isnot(None),
                    Question.opcion_c_imagen.isnot(None),
                    Question.opcion_d_imagen.isnot(None)
                )
            )
        ).limit(limit).all()
        
        # Convert questions to response format with dynamic URLs
        questions_data = []
        for q in questions:
            question_data = {
                "id": str(q.id),
                "pregunta_texto": q.pregunta_texto,
                "opcion_a": q.opcion_a,
                "opcion_b": q.opcion_b,
                "opcion_c": q.opcion_c,
                "opcion_d": q.opcion_d,
                "respuesta_correcta": q.respuesta_correcta,
                "dificultad": q.dificultad or 1,
                "tiempo_estimado": q.tiempo_estimado or 60,
                "puntos_xp": q.puntos_xp or 10,
                
                # Generate dynamic URLs for images
                "pregunta_imagen": _generate_dynamic_url(q.pregunta_imagen, config),
                "opcion_a_imagen": _generate_dynamic_url(q.opcion_a_imagen, config),
                "opcion_b_imagen": _generate_dynamic_url(q.opcion_b_imagen, config),
                "opcion_c_imagen": _generate_dynamic_url(q.opcion_c_imagen, config),
                "opcion_d_imagen": _generate_dynamic_url(q.opcion_d_imagen, config),
                
                # Metadata
                "subject_name": subject.name,
                "has_images": any([q.pregunta_imagen, q.opcion_a_imagen, q.opcion_b_imagen, q.opcion_c_imagen, q.opcion_d_imagen])
            }
            questions_data.append(question_data)
        
        return {
            "subject": {
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description
            },
            "questions": questions_data,
            "total_questions": len(questions_data),
            "server_config": {
                "host": config.host,
                "backend_url": config.backend_url,
                "image_base_url": config.api_images_url,
                "environment": "dynamic"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questions for subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")

@router.get("/subjects")
async def get_subjects_with_image_counts(request: Request = None, db: Session = Depends(get_db)):
    """Get subjects with image question counts and dynamic URLs"""
    try:
        # Get server configuration
        config = get_server_config()
        
        # Query subjects with image question counts
        subjects_query = db.query(
            Subject.id,
            Subject.name,
            Subject.description,
            Subject.color,
            func.count(Question.id).label('total_questions'),
            func.count(
                func.case(
                    (or_(
                        Question.pregunta_imagen.isnot(None),
                        Question.opcion_a_imagen.isnot(None),
                        Question.opcion_b_imagen.isnot(None),
                        Question.opcion_c_imagen.isnot(None),
                        Question.opcion_d_imagen.isnot(None)
                    ), 1)
                )
            ).label('image_questions')
        ).outerjoin(Question, Subject.id == Question.subject_id)\
         .group_by(Subject.id, Subject.name, Subject.description, Subject.color)\
         .order_by(Subject.name).all()
        
        subjects_data = []
        for result in subjects_query:
            subjects_data.append({
                "id": str(result.id),
                "name": result.name,
                "description": result.description,
                "color": result.color,
                "total_questions": result.total_questions or 0,
                "image_questions": result.image_questions or 0,
                "has_images": (result.image_questions or 0) > 0,
                "image_api_url": f"{config.backend_url}/dynamic-images/questions/{result.id}"
            })
        
        return {
            "subjects": subjects_data,
            "server_config": {
                "host": config.host,
                "backend_url": config.backend_url,
                "image_base_url": config.api_images_url,
                "environment": "dynamic"
            },
            "total_subjects": len(subjects_data),
            "subjects_with_images": len([s for s in subjects_data if s["has_images"]])
        }
        
    except Exception as e:
        logger.error(f"Error getting subjects: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting subjects: {str(e)}")

@router.get("/config")
async def get_dynamic_config(request: Request = None):
    """Get current dynamic configuration"""
    try:
        config = get_server_config()
        
        return {
            "server_config": {
                "host": config.host,
                "frontend_url": config.frontend_url,
                "backend_url": config.backend_url,
                "image_server_url": config.image_server_url,
                "api_images_url": config.api_images_url,
                "protocol": config.protocol
            },
            "image_server": {
                "base_path": image_server.base_path,
                "base_paths_checked": image_server.base_paths
            },
            "environment": {
                "docker_env": os.getenv('DOCKER_ENV', 'false'),
                "node_env": os.getenv('NODE_ENV', 'development'),
                "host_ip": os.getenv('HOST_IP', 'auto-detected'),
                "public_url": os.getenv('PUBLIC_URL', 'none')
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")

def _generate_dynamic_url(relative_path: Optional[str], config) -> Optional[str]:
    """Generate dynamic URL for image based on server config"""
    if not relative_path or relative_path.strip() == "" or relative_path == "No Aplica":
        return None
    
    # Clean the relative path
    clean_path = relative_path.strip().lstrip('/')
    
    # Generate dynamic URL
    return f"{config.backend_url}/dynamic-images/serve/{clean_path}"