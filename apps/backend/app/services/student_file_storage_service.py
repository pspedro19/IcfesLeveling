import os
import json
import gzip
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, BinaryIO, Union
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import boto3
from botocore.exceptions import ClientError
from minio import Minio
from minio.error import S3Error
import redis
import logging

from ..models.yml_storage import UserYMLPlan
from ..core.config import settings

logger = logging.getLogger(__name__)

class StudentFileStorageService:
    """
    Comprehensive Student File Storage Service
    
    Features:
    - Multi-tier storage (MinIO/S3, Local, Cache)
    - Student-specific directory organization
    - Versioning and backup support
    - Access control and security
    - Automated cleanup and archiving
    - File serving API with secure access
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = self._setup_redis()
        self.minio_client = self._setup_minio()
        self.s3_client = self._setup_s3()
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.storage_type = os.getenv('STORAGE_TYPE', 'local')  # local, minio, s3
        
        # Storage buckets/directories
        self.buckets = {
            'study_plans': 'study-plans',
            'student_data': 'student-data', 
            'educational_content': 'educational-content',
            'backups': 'backups',
            'archives': 'archives'
        }
        
        # Initialize storage
        self._ensure_storage_structure()
    
    def _setup_redis(self) -> Optional[redis.Redis]:
        """Setup Redis for caching"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            return redis.from_url(redis_url, decode_responses=False)
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            return None
    
    def _setup_minio(self) -> Optional[Minio]:
        """Setup MinIO client"""
        try:
            if self.storage_type == 'minio':
                endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9001')
                access_key = os.getenv('MINIO_ACCESS_KEY', 'icfes_admin')
                secret_key = os.getenv('MINIO_SECRET_KEY', 'icfes_secure_password_2024')
                secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
                
                return Minio(
                    endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=secure
                )
        except Exception as e:
            logger.warning(f"MinIO not available: {e}")
        return None
    
    def _setup_s3(self) -> Optional[boto3.client]:
        """Setup S3 client for production"""
        try:
            if self.storage_type == 's3':
                return boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
        except Exception as e:
            logger.warning(f"S3 not available: {e}")
        return None
    
    def _ensure_storage_structure(self):
        """Ensure storage buckets/directories exist"""
        if self.storage_type == 'minio' and self.minio_client:
            try:
                for bucket_name in self.buckets.values():
                    if not self.minio_client.bucket_exists(bucket_name):
                        self.minio_client.make_bucket(bucket_name)
                        logger.info(f"Created MinIO bucket: {bucket_name}")
            except Exception as e:
                logger.error(f"Error creating MinIO buckets: {e}")
        
        elif self.storage_type == 'local':
            try:
                base_path = Path("./storage/student-files")
                for bucket_name in self.buckets.values():
                    bucket_path = base_path / bucket_name
                    bucket_path.mkdir(parents=True, exist_ok=True)
                logger.info("Created local storage directories")
            except Exception as e:
                logger.error(f"Error creating local directories: {e}")
    
    def _get_student_directory_structure(self, user_id: str, content_type: str) -> Dict[str, str]:
        """Generate standardized student directory structure"""
        timestamp = datetime.now()
        year_month = timestamp.strftime('%Y/%m')
        
        # Student-specific paths
        paths = {
            'study_plans': f"{user_id}/study-plans/{year_month}",
            'progress_data': f"{user_id}/progress/{year_month}",
            'assessments': f"{user_id}/assessments/{year_month}",
            'certificates': f"{user_id}/certificates",
            'multimedia': f"{user_id}/multimedia/{year_month}",
            'backups': f"backups/{user_id}/{year_month}",
            'archives': f"archives/{user_id}/{timestamp.year}"
        }
        
        return paths.get(content_type, f"{user_id}/misc/{year_month}")
    
    def store_student_file(
        self,
        user_id: str,
        file_content: Union[bytes, str],
        filename: str,
        content_type: str = 'study_plans',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store student file with proper organization and versioning
        
        Args:
            user_id: Student's unique ID
            file_content: File content (bytes or string)
            filename: Original filename
            content_type: Type of content (study_plans, progress_data, etc.)
            metadata: Additional metadata
        
        Returns:
            Storage information and access details
        """
        try:
            # Prepare file content
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            
            # Generate file info
            file_hash = hashlib.md5(file_content).hexdigest()
            file_size = len(file_content)
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # Get student directory structure
            student_path = self._get_student_directory_structure(user_id, content_type)
            
            # Generate versioned filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name, ext = os.path.splitext(filename)
            versioned_filename = f"{base_name}_{timestamp}_{file_hash[:8]}{ext}"
            
            # Determine bucket and full path
            bucket = self.buckets.get(content_type, self.buckets['student_data'])
            full_path = f"{student_path}/{versioned_filename}"
            
            # Store file based on storage type
            storage_info = self._store_file_by_type(bucket, full_path, file_content, mime_type)
            
            # Create database record
            yml_record = UserYMLPlan(
                user_id=user_id,
                subject=content_type,
                storage_type=self.storage_type,
                storage_path=full_path,
                storage_url=storage_info.get('url'),
                file_size_bytes=file_size,
                file_hash=file_hash,
                version=self._get_next_version(user_id, content_type),
                generation_time_ms=metadata.get('generation_time_ms', 0) if metadata else 0,
                algorithm_version=metadata.get('algorithm_version', '1.0') if metadata else '1.0',
                cache_key=f"file:{user_id}:{content_type}:{file_hash[:8]}",
                cache_ttl=3600,
                is_active=True
            )
            
            self.db.add(yml_record)
            self.db.commit()
            self.db.refresh(yml_record)
            
            # Cache file metadata
            self._cache_file_metadata(yml_record)
            
            logger.info(f"✅ File stored successfully: {full_path}")
            
            return {
                'file_id': str(yml_record.id),
                'storage_path': full_path,
                'storage_url': storage_info.get('url'),
                'file_size_bytes': file_size,
                'file_hash': file_hash,
                'version': yml_record.version,
                'bucket': bucket,
                'access_url': self._generate_access_url(yml_record.id)
            }
            
        except Exception as e:
            logger.error(f"❌ Error storing student file: {e}")
            self.db.rollback()
            raise
    
    def _store_file_by_type(self, bucket: str, path: str, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Store file based on configured storage type"""
        if self.storage_type == 'minio' and self.minio_client:
            return self._store_file_minio(bucket, path, content, mime_type)
        elif self.storage_type == 's3' and self.s3_client:
            return self._store_file_s3(bucket, path, content, mime_type)
        else:
            return self._store_file_local(bucket, path, content)
    
    def _store_file_minio(self, bucket: str, path: str, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Store file in MinIO"""
        try:
            from io import BytesIO
            self.minio_client.put_object(
                bucket,
                path,
                BytesIO(content),
                length=len(content),
                content_type=mime_type
            )
            
            # Generate presigned URL for access
            url = self.minio_client.presigned_get_object(bucket, path, expires=timedelta(hours=1))
            
            return {
                'url': url,
                'type': 'minio',
                'bucket': bucket,
                'path': path
            }
        except Exception as e:
            logger.error(f"MinIO storage error: {e}")
            raise
    
    def _store_file_s3(self, bucket: str, path: str, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Store file in S3"""
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=path,
                Body=content,
                ContentType=mime_type
            )
            
            url = f"https://{bucket}.s3.amazonaws.com/{path}"
            
            return {
                'url': url,
                'type': 's3',
                'bucket': bucket,
                'path': path
            }
        except Exception as e:
            logger.error(f"S3 storage error: {e}")
            raise
    
    def _store_file_local(self, bucket: str, path: str, content: bytes) -> Dict[str, Any]:
        """Store file locally"""
        try:
            full_path = Path(f"./storage/student-files/{bucket}/{path}")
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(content)
            
            return {
                'url': f"file://{full_path.absolute()}",
                'type': 'local',
                'bucket': bucket,
                'path': str(full_path)
            }
        except Exception as e:
            logger.error(f"Local storage error: {e}")
            raise
    
    def retrieve_student_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve student file by ID"""
        try:
            # Get file record
            file_record = self.db.query(UserYMLPlan).filter(
                UserYMLPlan.id == file_id,
                UserYMLPlan.is_active == True
            ).first()
            
            if not file_record:
                return None
            
            # Check cache first
            cached_content = self._get_cached_file(file_record.cache_key)
            if cached_content:
                return {
                    'content': cached_content,
                    'metadata': self._file_record_to_dict(file_record),
                    'source': 'cache'
                }
            
            # Retrieve from storage
            content = self._retrieve_file_by_type(file_record)
            if content:
                # Update access statistics
                file_record.last_accessed = datetime.utcnow()
                file_record.access_count += 1
                self.db.commit()
                
                # Cache for future access
                self._cache_file_content(file_record.cache_key, content)
                
                return {
                    'content': content,
                    'metadata': self._file_record_to_dict(file_record),
                    'source': 'storage'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {e}")
            return None
    
    def _retrieve_file_by_type(self, file_record: UserYMLPlan) -> Optional[bytes]:
        """Retrieve file based on storage type"""
        try:
            if file_record.storage_type == 'minio' and self.minio_client:
                return self._retrieve_file_minio(file_record)
            elif file_record.storage_type == 's3' and self.s3_client:
                return self._retrieve_file_s3(file_record)
            else:
                return self._retrieve_file_local(file_record)
        except Exception as e:
            logger.error(f"Error retrieving file from {file_record.storage_type}: {e}")
            return None
    
    def _retrieve_file_minio(self, file_record: UserYMLPlan) -> Optional[bytes]:
        """Retrieve file from MinIO"""
        try:
            # Parse storage path to get bucket and object name
            path_parts = file_record.storage_path.split('/', 1)
            if len(path_parts) == 2:
                bucket, object_name = path_parts
            else:
                # Assume default bucket
                bucket = self.buckets['student_data']
                object_name = file_record.storage_path
            
            response = self.minio_client.get_object(bucket, object_name)
            return response.read()
        except Exception as e:
            logger.error(f"MinIO retrieval error: {e}")
            return None
    
    def _retrieve_file_s3(self, file_record: UserYMLPlan) -> Optional[bytes]:
        """Retrieve file from S3"""
        try:
            path_parts = file_record.storage_path.split('/', 1)
            if len(path_parts) == 2:
                bucket, key = path_parts
            else:
                bucket = self.buckets['student_data']
                key = file_record.storage_path
            
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"S3 retrieval error: {e}")
            return None
    
    def _retrieve_file_local(self, file_record: UserYMLPlan) -> Optional[bytes]:
        """Retrieve file from local storage"""
        try:
            file_path = Path(f"./storage/student-files/{file_record.storage_path}")
            if file_path.exists():
                return file_path.read_bytes()
            return None
        except Exception as e:
            logger.error(f"Local retrieval error: {e}")
            return None
    
    def list_student_files(
        self, 
        user_id: str, 
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all files for a student"""
        try:
            query = self.db.query(UserYMLPlan).filter(
                UserYMLPlan.user_id == user_id,
                UserYMLPlan.is_active == True
            )
            
            if content_type:
                query = query.filter(UserYMLPlan.subject == content_type)
            
            files = query.order_by(desc(UserYMLPlan.created_at)).offset(offset).limit(limit).all()
            
            return [self._file_record_to_dict(file_record) for file_record in files]
            
        except Exception as e:
            logger.error(f"Error listing files for user {user_id}: {e}")
            return []
    
    def create_backup(self, user_id: str) -> Dict[str, Any]:
        """Create a complete backup of student's files"""
        try:
            # Get all active files for user
            files = self.list_student_files(user_id)
            
            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{user_id}_{backup_timestamp}"
            
            # Create backup metadata
            backup_metadata = {
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'file_count': len(files),
                'files': files
            }
            
            # Store backup metadata
            backup_content = json.dumps(backup_metadata, indent=2).encode('utf-8')
            backup_filename = f"{backup_name}_metadata.json"
            
            backup_info = self.store_student_file(
                user_id=user_id,
                file_content=backup_content,
                filename=backup_filename,
                content_type='backups',
                metadata={'backup_type': 'full', 'file_count': len(files)}
            )
            
            logger.info(f"✅ Backup created for user {user_id}: {backup_name}")
            
            return {
                'backup_id': backup_info['file_id'],
                'backup_name': backup_name,
                'file_count': len(files),
                'backup_size': backup_info['file_size_bytes'],
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating backup for user {user_id}: {e}")
            raise
    
    def archive_old_files(self, days_old: int = 90) -> Dict[str, Any]:
        """Archive files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Find old files
            old_files = self.db.query(UserYMLPlan).filter(
                UserYMLPlan.created_at < cutoff_date,
                UserYMLPlan.is_active == True,
                UserYMLPlan.subject != 'backups'  # Don't archive backups
            ).all()
            
            archived_count = 0
            total_size = 0
            
            for file_record in old_files:
                try:
                    # Move to archive
                    archive_path = f"archives/{file_record.user_id}/{file_record.created_at.year}/{file_record.storage_path}"
                    
                    # Update record
                    file_record.storage_path = archive_path
                    file_record.subject = 'archives'
                    file_record.is_active = False
                    
                    archived_count += 1
                    total_size += file_record.file_size_bytes
                    
                except Exception as e:
                    logger.error(f"Error archiving file {file_record.id}: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"✅ Archived {archived_count} files totaling {total_size} bytes")
            
            return {
                'archived_count': archived_count,
                'total_size_bytes': total_size,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error during archival process: {e}")
            self.db.rollback()
            raise
    
    def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries"""
        if not self.redis_client:
            return {'status': 'Redis not available'}
        
        try:
            # Get all file cache keys
            cache_keys = self.redis_client.keys("file:*")
            expired_count = 0
            
            for key in cache_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    self.redis_client.expire(key, 3600)  # Set 1 hour expiration
                elif ttl == -2:  # Key doesn't exist
                    expired_count += 1
            
            logger.info(f"✅ Cache cleanup completed. Found {expired_count} expired keys")
            
            return {
                'total_keys': len(cache_keys),
                'expired_keys': expired_count,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"❌ Error during cache cleanup: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        try:
            # Database statistics
            total_files = self.db.query(UserYMLPlan).filter(UserYMLPlan.is_active == True).count()
            total_size = self.db.query(func.sum(UserYMLPlan.file_size_bytes)).filter(
                UserYMLPlan.is_active == True
            ).scalar() or 0
            
            # Files by type
            files_by_type = self.db.query(
                UserYMLPlan.subject,
                func.count(UserYMLPlan.id).label('count'),
                func.sum(UserYMLPlan.file_size_bytes).label('size')
            ).filter(UserYMLPlan.is_active == True).group_by(UserYMLPlan.subject).all()
            
            # Recent activity
            recent_files = self.db.query(UserYMLPlan).filter(
                UserYMLPlan.created_at >= datetime.now() - timedelta(days=7),
                UserYMLPlan.is_active == True
            ).count()
            
            # Cache statistics
            cache_stats = {}
            if self.redis_client:
                try:
                    cache_info = self.redis_client.info('memory')
                    cache_stats = {
                        'total_keys': self.redis_client.dbsize(),
                        'memory_usage': cache_info.get('used_memory_human', 'N/A'),
                        'cache_hits': cache_info.get('keyspace_hits', 0),
                        'cache_misses': cache_info.get('keyspace_misses', 0)
                    }
                except Exception:
                    cache_stats = {'error': 'No disponible'}
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'recent_files_7_days': recent_files,
                'files_by_type': [
                    {
                        'type': row.subject,
                        'count': row.count,
                        'size_bytes': row.size or 0,
                        'size_mb': round((row.size or 0) / (1024 * 1024), 2)
                    }
                    for row in files_by_type
                ],
                'storage_type': self.storage_type,
                'environment': self.environment,
                'cache_stats': cache_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            return {'error': str(e)}
    
    # Helper methods
    def _get_next_version(self, user_id: str, content_type: str) -> int:
        """Get next version number for file"""
        latest = self.db.query(UserYMLPlan).filter(
            UserYMLPlan.user_id == user_id,
            UserYMLPlan.subject == content_type
        ).order_by(desc(UserYMLPlan.version)).first()
        
        return (latest.version + 1) if latest else 1
    
    def _cache_file_metadata(self, file_record: UserYMLPlan):
        """Cache file metadata in Redis"""
        if not self.redis_client:
            return
        
        try:
            metadata = self._file_record_to_dict(file_record)
            cache_key = f"metadata:{file_record.cache_key}"
            self.redis_client.setex(cache_key, 3600, json.dumps(metadata))
        except Exception as e:
            logger.warning(f"Error caching metadata: {e}")
    
    def _cache_file_content(self, cache_key: str, content: bytes):
        """Cache file content in Redis"""
        if not self.redis_client or len(content) > 1024 * 1024:  # Don't cache files > 1MB
            return
        
        try:
            self.redis_client.setex(cache_key, 1800, content)  # 30 min cache
        except Exception as e:
            logger.warning(f"Error caching content: {e}")
    
    def _get_cached_file(self, cache_key: str) -> Optional[bytes]:
        """Get cached file content"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(cache_key)
        except Exception as e:
            logger.warning(f"Error getting cached content: {e}")
            return None
    
    def _file_record_to_dict(self, file_record: UserYMLPlan) -> Dict[str, Any]:
        """Convert file record to dictionary"""
        return {
            'id': str(file_record.id),
            'user_id': file_record.user_id,
            'content_type': file_record.subject,
            'storage_path': file_record.storage_path,
            'storage_url': file_record.storage_url,
            'file_size_bytes': file_record.file_size_bytes,
            'file_size_mb': round(file_record.file_size_bytes / (1024 * 1024), 2),
            'file_hash': file_record.file_hash,
            'version': file_record.version,
            'created_at': file_record.created_at.isoformat(),
            'last_accessed': file_record.last_accessed.isoformat() if file_record.last_accessed else None,
            'access_count': file_record.access_count,
            'storage_type': file_record.storage_type,
            'is_active': file_record.is_active
        }
    
    def _generate_access_url(self, file_id: str) -> str:
        """Generate secure access URL for file"""
        return f"/api/storage/files/{file_id}/download"