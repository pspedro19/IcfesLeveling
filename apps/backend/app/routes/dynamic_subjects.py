"""Dynamic Subject Management API - Production Ready"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from ..core.database import get_db
from ..services.dynamic_subject_service import DynamicSubjectService
from ..models.subject import Subject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subjects", tags=["dynamic-subjects"])

class SubjectConfigUpdate(BaseModel):
    total_questions: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    topics: Optional[List[str]] = None
    difficulty_levels: Optional[Dict[str, int]] = None
    study_sequence: Optional[List[str]] = None

class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

@router.get("/dynamic", response_model=List[Dict[str, Any]])
async def get_dynamic_subjects(db: Session = Depends(get_db)):
    """Get all subjects with their dynamic configurations"""
    try:
        service = DynamicSubjectService(db)
        subjects = service.get_all_subjects_with_config()
        return subjects
    except Exception as e:
        logger.error(f"Error getting dynamic subjects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{name}")
async def find_subject_by_name(name: str, db: Session = Depends(get_db)):
    """Intelligently find subject by name or alias"""
    try:
        service = DynamicSubjectService(db)
        subject = service.find_subject_by_name_or_alias(name)
        
        if not subject:
            raise HTTPException(status_code=404, detail=f"Subject '{name}' not found")
        
        return {
            "id": str(subject.id),
            "name": subject.name,
            "description": subject.description,
            "aliases": [alias.alias_name for alias in subject.aliases]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching for subject '{name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{subject_id}/config")
async def get_subject_config(subject_id: str, db: Session = Depends(get_db)):
    """Get dynamic configuration for a specific subject"""
    try:
        service = DynamicSubjectService(db)
        config = service.get_subject_config(subject_id)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting config for subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{subject_id}/assets")
async def get_subject_assets(subject_id: str, db: Session = Depends(get_db)):
    """Get dynamic assets for a subject"""
    try:
        service = DynamicSubjectService(db)
        assets = service.get_assets_for_entity("subject", subject_id)
        return assets
    except Exception as e:
        logger.error(f"Error getting assets for subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mapping/import")
async def get_import_mapping(db: Session = Depends(get_db)):
    """Get dynamic subject mapping for import scripts"""
    try:
        service = DynamicSubjectService(db)
        mapping = service.get_subject_mapping_for_import()
        return {
            "mapping": mapping,
            "total_subjects": len(set(mapping.values())),
            "total_aliases": len(mapping)
        }
    except Exception as e:
        logger.error(f"Error getting import mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_subject(subject_data: SubjectCreate, db: Session = Depends(get_db)):
    """Create a new subject with dynamic configuration"""
    try:
        service = DynamicSubjectService(db)
        
        # Check if subject already exists
        existing = service.find_subject_by_name_or_alias(subject_data.name)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Subject '{subject_data.name}' already exists"
            )
        
        subject = service.create_subject_with_config(
            name=subject_data.name,
            description=subject_data.description,
            aliases=subject_data.aliases,
            config=subject_data.config
        )
        
        return {
            "id": str(subject.id),
            "name": subject.name,
            "description": subject.description,
            "message": "Subject created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{subject_id}/config")
async def update_subject_config(
    subject_id: str, 
    config_updates: SubjectConfigUpdate, 
    db: Session = Depends(get_db)
):
    """Update subject configuration dynamically"""
    try:
        service = DynamicSubjectService(db)
        
        # Convert to dict, excluding None values
        updates = config_updates.dict(exclude_none=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = service.update_subject_config(subject_id, updates)
        
        if success:
            return {"message": "Configuration updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config for subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{subject_id}/aliases")
async def add_subject_alias(
    subject_id: str, 
    alias_name: str = Query(..., description="New alias name"), 
    db: Session = Depends(get_db)
):
    """Add a new alias to a subject"""
    try:
        service = DynamicSubjectService(db)
        success = service.add_subject_alias(subject_id, alias_name)
        
        if success:
            return {"message": f"Alias '{alias_name}' added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Alias already exists")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding alias to subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/check")
async def health_check():
    """Health check for dynamic subjects system"""
    return {
        "status": "healthy",
        "system": "dynamic-subjects",
        "version": "1.0.0",
        "features": [
            "dynamic_subject_loading",
            "intelligent_name_matching", 
            "alias_support",
            "configurable_tests",
            "asset_management"
        ]
    }