from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import io
import mimetypes
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import get_current_user, verify_token
from ..services.student_file_storage_service import StudentFileStorageService
from ..models.user import User

router = APIRouter(prefix="/api/storage", tags=["Storage"])
security = HTTPBearer()

@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    content_type: str = Form("study_plans"),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file for the authenticated user
    
    - **file**: File to upload
    - **content_type**: Type of content (study_plans, progress_data, assessments, etc.)
    - **metadata**: Optional JSON metadata
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Validate content type
        allowed_types = ['study_plans', 'progress_data', 'assessments', 'certificates', 'multimedia']
        if content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid content type. Allowed: {allowed_types}")
        
        # Parse metadata if provided
        file_metadata = None
        if metadata:
            import json
            try:
                file_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Store file
        storage_service = StudentFileStorageService(db)
        result = storage_service.store_student_file(
            user_id=str(current_user.id),
            file_content=content,
            filename=file.filename,
            content_type=content_type,
            metadata=file_metadata
        )
        
        return {
            "message": "File uploaded successfully",
            "file_id": result["file_id"],
            "filename": file.filename,
            "size_bytes": result["file_size_bytes"],
            "content_type": content_type,
            "version": result["version"],
            "access_url": result["access_url"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a file by ID (only accessible to file owner)
    """
    try:
        storage_service = StudentFileStorageService(db)
        file_data = storage_service.retrieve_student_file(file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify user owns the file
        if file_data["metadata"]["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare file response
        content = file_data["content"]
        metadata = file_data["metadata"]
        
        # Determine MIME type
        filename = metadata["storage_path"].split('/')[-1]
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Create streaming response
        def generate():
            yield content
        
        return StreamingResponse(
            generate(),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/files/{file_id}/info", response_model=Dict[str, Any])
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get file information without downloading content
    """
    try:
        storage_service = StudentFileStorageService(db)
        file_data = storage_service.retrieve_student_file(file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify user owns the file
        if file_data["metadata"]["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "file_id": file_id,
            "metadata": file_data["metadata"],
            "source": file_data["source"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")

@router.get("/files", response_model=List[Dict[str, Any]])
async def list_user_files(
    content_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all files for the authenticated user
    
    - **content_type**: Filter by content type
    - **limit**: Number of files to return (max 100)
    - **offset**: Number of files to skip
    """
    try:
        storage_service = StudentFileStorageService(db)
        files = storage_service.list_student_files(
            user_id=str(current_user.id),
            content_type=content_type,
            limit=limit,
            offset=offset
        )
        
        return files
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a complete backup of user's files
    """
    try:
        storage_service = StudentFileStorageService(db)
        backup_info = storage_service.create_backup(str(current_user.id))
        
        return {
            "message": "Backup created successfully",
            **backup_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_user_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get storage statistics for the authenticated user
    """
    try:
        storage_service = StudentFileStorageService(db)
        
        # Get user-specific stats
        user_files = storage_service.list_student_files(str(current_user.id), limit=1000)
        
        # Calculate user stats
        total_files = len(user_files)
        total_size = sum(f['file_size_bytes'] for f in user_files)
        
        # Group by content type
        by_type = {}
        for file_info in user_files:
            content_type = file_info['content_type']
            if content_type not in by_type:
                by_type[content_type] = {'count': 0, 'size_bytes': 0}
            by_type[content_type]['count'] += 1
            by_type[content_type]['size_bytes'] += file_info['file_size_bytes']
        
        # Recent activity (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_files = [
            f for f in user_files 
            if datetime.fromisoformat(f['created_at'].replace('Z', '+00:00')) > recent_cutoff
        ]
        
        return {
            "user_id": str(current_user.id),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "recent_files_7_days": len(recent_files),
            "files_by_type": [
                {
                    "content_type": ct,
                    "count": stats["count"],
                    "size_bytes": stats["size_bytes"],
                    "size_mb": round(stats["size_bytes"] / (1024 * 1024), 2)
                }
                for ct, stats in by_type.items()
            ],
            "last_upload": max([f['created_at'] for f in user_files]) if user_files else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Admin-only endpoints
@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_system_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide storage statistics (admin only)
    """
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        storage_service = StudentFileStorageService(db)
        stats = storage_service.get_storage_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

@router.post("/admin/archive", response_model=Dict[str, Any])
async def archive_old_files(
    days_old: int = Query(90, ge=30, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Archive files older than specified days (admin only)
    """
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        storage_service = StudentFileStorageService(db)
        result = storage_service.archive_old_files(days_old)
        
        return {
            "message": "Archival completed",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Archival failed: {str(e)}")

@router.post("/admin/cleanup-cache", response_model=Dict[str, Any])
async def cleanup_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clean up expired cache entries (admin only)
    """
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        storage_service = StudentFileStorageService(db)
        result = storage_service.cleanup_expired_cache()
        
        return {
            "message": "Cache cleanup completed",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")

# Health check for storage system
@router.get("/health", response_model=Dict[str, Any])
async def storage_health_check(db: Session = Depends(get_db)):
    """
    Check health of storage system
    """
    try:
        storage_service = StudentFileStorageService(db)
        
        # Test database connection
        db.execute("SELECT 1")
        
        # Test storage backends
        health_status = {
            "database": "healthy",
            "storage_type": storage_service.storage_type,
            "minio": "unavailable",
            "s3": "unavailable",
            "redis": "unavailable",
            "timestamp": datetime.now().isoformat()
        }
        
        # Test MinIO
        if storage_service.minio_client:
            try:
                list(storage_service.minio_client.list_buckets())
                health_status["minio"] = "healthy"
            except:
                health_status["minio"] = "error"
        
        # Test S3
        if storage_service.s3_client:
            try:
                storage_service.s3_client.list_buckets()
                health_status["s3"] = "healthy"
            except:
                health_status["s3"] = "error"
        
        # Test Redis
        if storage_service.redis_client:
            try:
                storage_service.redis_client.ping()
                health_status["redis"] = "healthy"
            except:
                health_status["redis"] = "error"
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")