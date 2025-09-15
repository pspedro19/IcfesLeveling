"""
Study Plan Storage System
Handles file-based and database storage for personalized study plans
"""

import os
import json
import yaml
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class StudyPlanStorageManager:
    """
    Manages storage and retrieval of personalized study plans
    Supports both file-based and database storage
    """
    
    def __init__(self, db: Session, storage_base_path: str = "/root/IcfesLeveling/storage"):
        self.db = db
        self.storage_base_path = Path(storage_base_path)
        self.study_plans_path = self.storage_base_path / "study_plans"
        self.backups_path = self.storage_base_path / "backups"
        self.templates_path = self.storage_base_path / "templates"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary storage directories"""
        for path in [self.study_plans_path, self.backups_path, self.templates_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Ensured directory exists: {path}")
    
    def save_study_plan(
        self,
        user_id: str,
        subject_id: str,
        plan_data: Dict[str, Any],
        yaml_content: str,
        plan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save study plan to both file system and database
        """
        try:
            if not plan_id:
                plan_id = str(uuid.uuid4())
            
            # 1. Generate file names
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            yaml_filename = f"{user_id}_{subject_id}_{plan_id}.yaml"
            json_filename = f"{user_id}_{subject_id}_{plan_id}.json"
            
            yaml_file_path = self.study_plans_path / yaml_filename
            json_file_path = self.study_plans_path / json_filename
            
            # 2. Save YAML file
            with open(yaml_file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # 3. Save JSON metadata file
            metadata = {
                'plan_id': plan_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'created_at': datetime.now().isoformat(),
                'yaml_file': yaml_filename,
                'json_file': json_filename,
                'version': '2.1',
                'storage_type': 'file_system',
                'plan_data': plan_data
            }
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. Save to database for quick access
            db_result = self._save_to_database(plan_id, user_id, subject_id, plan_data, yaml_content, metadata)
            
            # 5. Create backup
            backup_result = self._create_backup(plan_id, yaml_content, metadata)
            
            logger.info(f"✅ Study plan saved successfully: {plan_id}")
            
            return {
                'success': True,
                'plan_id': plan_id,
                'yaml_file_path': str(yaml_file_path),
                'json_file_path': str(json_file_path),
                'database_saved': db_result['success'],
                'backup_created': backup_result['success'],
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Error saving study plan: {e}")
            return {
                'success': False,
                'error': str(e),
                'plan_id': plan_id
            }
    
    def _save_to_database(
        self,
        plan_id: str,
        user_id: str,
        subject_id: str,
        plan_data: Dict[str, Any],
        yaml_content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save plan to database tables"""
        try:
            # Save to study_plans table
            query = text("""
                INSERT INTO study_plans (
                    id, user_id, subject_id, plan_name, plan_data,
                    total_units, completed_units, progress_percentage, is_active
                ) VALUES (
                    :id, :user_id, :subject_id, :plan_name, :plan_data,
                    :total_units, 0, 0.0, true
                ) ON CONFLICT (id) DO UPDATE SET
                    plan_data = EXCLUDED.plan_data,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            total_units = len(plan_data.get('learning_path', {}).get('units', []))
            
            self.db.execute(query, {
                'id': plan_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'plan_name': f"Personalized Plan - {datetime.now().strftime('%Y-%m-%d')}",
                'plan_data': json.dumps(plan_data),
                'total_units': total_units
            })
            
            # Save to yml_storage for compatibility
            yml_query = text("""
                INSERT INTO yml_storage (
                    id, user_id, subject, yml_content, version, metadata
                ) VALUES (
                    :id, :user_id, :subject_id, :yml_content, '2.1', :metadata
                ) ON CONFLICT (id) DO UPDATE SET
                    yml_content = EXCLUDED.yml_content,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            self.db.execute(yml_query, {
                'id': f"yml_{plan_id}",
                'user_id': user_id,
                'subject_id': subject_id,
                'yml_content': yaml_content,
                'metadata': json.dumps(metadata)
            })
            
            self.db.commit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _create_backup(self, plan_id: str, yaml_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create timestamped backup of the study plan"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{plan_id}_{timestamp}.yaml"
            backup_path = self.backups_path / backup_filename
            
            backup_data = {
                'backup_metadata': {
                    'original_plan_id': plan_id,
                    'backup_created_at': datetime.now().isoformat(),
                    'original_metadata': metadata
                },
                'yaml_content': yaml_content
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                yaml.dump(backup_data, f, default_flow_style=False, allow_unicode=True)
            
            return {'success': True, 'backup_path': str(backup_path)}
            
        except Exception as e:
            logger.error(f"Backup creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_study_plan(self, plan_id: str, source: str = 'auto') -> Dict[str, Any]:
        """
        Retrieve study plan from specified source
        source: 'auto', 'file', 'database'
        """
        try:
            if source == 'auto':
                # Try database first, then file
                db_result = self._get_from_database(plan_id)
                if db_result['success']:
                    return db_result
                return self._get_from_file(plan_id)
            elif source == 'database':
                return self._get_from_database(plan_id)
            elif source == 'file':
                return self._get_from_file(plan_id)
            else:
                return {'success': False, 'error': 'Invalid source specified'}
                
        except Exception as e:
            logger.error(f"Error retrieving study plan: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_from_database(self, plan_id: str) -> Dict[str, Any]:
        """Get study plan from database"""
        try:
            query = text("""
                SELECT sp.id, sp.user_id, sp.subject_id, sp.plan_name, sp.plan_data,
                       sp.total_units, sp.completed_units, sp.progress_percentage,
                       sp.created_at, sp.updated_at,
                       yml.yml_content
                FROM study_plans sp
                LEFT JOIN yml_storage yml ON yml.id = CONCAT('yml_', sp.id)
                WHERE sp.id = :plan_id AND sp.is_active = true
            """)
            
            result = self.db.execute(query, {'plan_id': plan_id}).first()
            
            if not result:
                return {'success': False, 'error': 'Plan not found in database'}
            
            plan_data = json.loads(result[4]) if result[4] else {}
            
            return {
                'success': True,
                'source': 'database',
                'plan_id': result[0],
                'user_id': result[1],
                'subject_id': result[2],
                'plan_name': result[3],
                'plan_data': plan_data,
                'total_units': result[5],
                'completed_units': result[6],
                'progress_percentage': float(result[7]),
                'created_at': result[8].isoformat() if result[8] else None,
                'updated_at': result[9].isoformat() if result[9] else None,
                'yaml_content': result[10]
            }
            
        except Exception as e:
            logger.error(f"Database retrieval error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_from_file(self, plan_id: str) -> Dict[str, Any]:
        """Get study plan from file system"""
        try:
            # Find files matching the plan_id pattern
            json_files = list(self.study_plans_path.glob(f"*_{plan_id}.json"))
            yaml_files = list(self.study_plans_path.glob(f"*_{plan_id}.yaml"))
            
            if not json_files:
                return {'success': False, 'error': 'Plan metadata file not found'}
            
            # Load metadata
            with open(json_files[0], 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            yaml_content = None
            if yaml_files:
                with open(yaml_files[0], 'r', encoding='utf-8') as f:
                    yaml_content = f.read()
            
            return {
                'success': True,
                'source': 'file',
                'metadata': metadata,
                'yaml_content': yaml_content,
                'json_file_path': str(json_files[0]),
                'yaml_file_path': str(yaml_files[0]) if yaml_files else None
            }
            
        except Exception as e:
            logger.error(f"File retrieval error: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_user_plans(self, user_id: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
        """List all study plans for a user"""
        try:
            query = text("""
                SELECT id, subject_id, plan_name, total_units, completed_units,
                       progress_percentage, created_at, updated_at, is_active
                FROM study_plans
                WHERE user_id = :user_id
                {} 
                ORDER BY created_at DESC
            """.format("AND subject_id = :subject_id" if subject_id else ""))
            
            params = {'user_id': user_id}
            if subject_id:
                params['subject_id'] = subject_id
            
            results = self.db.execute(query, params).fetchall()
            
            plans = []
            for result in results:
                plans.append({
                    'plan_id': result[0],
                    'subject_id': result[1],
                    'plan_name': result[2],
                    'total_units': result[3],
                    'completed_units': result[4],
                    'progress_percentage': float(result[5]),
                    'created_at': result[6].isoformat() if result[6] else None,
                    'updated_at': result[7].isoformat() if result[7] else None,
                    'is_active': result[8]
                })
            
            return {
                'success': True,
                'user_id': user_id,
                'subject_id': subject_id,
                'plans': plans,
                'total_plans': len(plans)
            }
            
        except Exception as e:
            logger.error(f"Error listing user plans: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_plan_progress(
        self,
        plan_id: str,
        completed_units: int,
        progress_percentage: float
    ) -> Dict[str, Any]:
        """Update study plan progress"""
        try:
            query = text("""
                UPDATE study_plans
                SET completed_units = :completed_units,
                    progress_percentage = :progress_percentage,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :plan_id
            """)
            
            self.db.execute(query, {
                'plan_id': plan_id,
                'completed_units': completed_units,
                'progress_percentage': progress_percentage
            })
            
            self.db.commit()
            
            return {
                'success': True,
                'plan_id': plan_id,
                'completed_units': completed_units,
                'progress_percentage': progress_percentage
            }
            
        except Exception as e:
            logger.error(f"Error updating plan progress: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def archive_plan(self, plan_id: str) -> Dict[str, Any]:
        """Archive a study plan (mark as inactive)"""
        try:
            query = text("""
                UPDATE study_plans
                SET is_active = false,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :plan_id
            """)
            
            self.db.execute(query, {'plan_id': plan_id})
            self.db.commit()
            
            # Create archive backup
            plan_data = self._get_from_database(plan_id)
            if plan_data['success']:
                archive_path = self.backups_path / f"archived_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(archive_path, 'w', encoding='utf-8') as f:
                    json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'plan_id': plan_id,
                'message': 'Plan archived successfully'
            }
            
        except Exception as e:
            logger.error(f"Error archiving plan: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_plan(self, plan_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """Delete a study plan (with optional backup)"""
        try:
            if create_backup:
                # Create backup before deletion
                plan_data = self._get_from_database(plan_id)
                if plan_data['success']:
                    backup_path = self.backups_path / f"deleted_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            # Delete from database
            queries = [
                "DELETE FROM study_plans WHERE id = :plan_id",
                "DELETE FROM yml_storage WHERE id = :yml_id"
            ]
            
            for query in queries:
                self.db.execute(text(query), {
                    'plan_id': plan_id,
                    'yml_id': f'yml_{plan_id}'
                })
            
            # Delete files
            json_files = list(self.study_plans_path.glob(f"*_{plan_id}.json"))
            yaml_files = list(self.study_plans_path.glob(f"*_{plan_id}.yaml"))
            
            for file_path in json_files + yaml_files:
                if file_path.exists():
                    file_path.unlink()
            
            self.db.commit()
            
            return {
                'success': True,
                'plan_id': plan_id,
                'message': 'Plan deleted successfully',
                'backup_created': create_backup
            }
            
        except Exception as e:
            logger.error(f"Error deleting plan: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage system statistics"""
        try:
            # File system stats
            plan_files = list(self.study_plans_path.glob("*.yaml"))
            backup_files = list(self.backups_path.glob("*.yaml"))
            
            # Database stats
            db_query = text("""
                SELECT 
                    COUNT(*) as total_plans,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_plans,
                    AVG(progress_percentage) as avg_progress
                FROM study_plans
            """)
            
            db_result = self.db.execute(db_query).first()
            
            return {
                'success': True,
                'file_system': {
                    'total_plan_files': len(plan_files),
                    'total_backup_files': len(backup_files),
                    'storage_path': str(self.study_plans_path),
                    'backup_path': str(self.backups_path)
                },
                'database': {
                    'total_plans': db_result[0] if db_result else 0,
                    'active_plans': db_result[1] if db_result else 0,
                    'average_progress': float(db_result[2]) if db_result and db_result[2] else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {'success': False, 'error': str(e)}


class MinioStorageManager:
    """
    Optional Minio-based storage for scalable cloud storage
    """
    
    def __init__(self, minio_client=None, bucket_name: str = "study-plans"):
        self.minio_client = minio_client
        self.bucket_name = bucket_name
        self.enabled = minio_client is not None
        
        if self.enabled:
            self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the Minio bucket exists"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"✅ Created Minio bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error creating Minio bucket: {e}")
    
    def save_plan_to_minio(
        self,
        plan_id: str,
        user_id: str,
        subject_id: str,
        yaml_content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save study plan to Minio storage"""
        if not self.enabled:
            return {'success': False, 'error': 'Minio not configured'}
        
        try:
            # Save YAML content
            yaml_object_name = f"plans/{user_id}/{subject_id}/{plan_id}.yaml"
            yaml_data = yaml_content.encode('utf-8')
            
            self.minio_client.put_object(
                self.bucket_name,
                yaml_object_name,
                data=yaml_data,
                length=len(yaml_data),
                content_type='application/x-yaml'
            )
            
            # Save metadata
            metadata_object_name = f"metadata/{user_id}/{subject_id}/{plan_id}.json"
            metadata_data = json.dumps(metadata, indent=2).encode('utf-8')
            
            self.minio_client.put_object(
                self.bucket_name,
                metadata_object_name,
                data=metadata_data,
                length=len(metadata_data),
                content_type='application/json'
            )
            
            return {
                'success': True,
                'yaml_object_name': yaml_object_name,
                'metadata_object_name': metadata_object_name,
                'bucket': self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"Error saving to Minio: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_plan_from_minio(self, plan_id: str, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Retrieve study plan from Minio storage"""
        if not self.enabled:
            return {'success': False, 'error': 'Minio not configured'}
        
        try:
            yaml_object_name = f"plans/{user_id}/{subject_id}/{plan_id}.yaml"
            metadata_object_name = f"metadata/{user_id}/{subject_id}/{plan_id}.json"
            
            # Get YAML content
            yaml_response = self.minio_client.get_object(self.bucket_name, yaml_object_name)
            yaml_content = yaml_response.read().decode('utf-8')
            
            # Get metadata
            metadata_response = self.minio_client.get_object(self.bucket_name, metadata_object_name)
            metadata = json.loads(metadata_response.read().decode('utf-8'))
            
            return {
                'success': True,
                'yaml_content': yaml_content,
                'metadata': metadata,
                'source': 'minio'
            }
            
        except Exception as e:
            logger.error(f"Error retrieving from Minio: {e}")
            return {'success': False, 'error': str(e)}