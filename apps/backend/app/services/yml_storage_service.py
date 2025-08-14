import os
import yaml
import json
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import boto3
from botocore.exceptions import ClientError
import redis
import logging

from ..models.yml_storage import UserYMLPlan
from ..core.config import settings

logger = logging.getLogger(__name__)

class YMLStorageService:
    """
    Servicio completo de almacenamiento YML con sistema de 3 capas:
    1. PostgreSQL: Metadata y referencias
    2. S3/Spaces: Archivos YML comprimidos
    3. Redis: Cache para usuarios activos
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = self._setup_redis()
        self.storage_client = self._setup_storage()
        self.environment = os.getenv('ENVIRONMENT', 'local')
        
    def _setup_redis(self) -> redis.Redis:
        """Configura cliente Redis para cache"""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=False
            )
        except Exception as e:
            logger.warning(f"Redis no disponible, usando cache en memoria: {e}")
            return None
    
    def _setup_storage(self):
        """Configura cliente de almacenamiento (S3/Spaces)"""
        try:
            if self.environment == 'digitalocean':
                # DigitalOcean Spaces (S3-compatible)
                return boto3.client(
                    's3',
                    endpoint_url=os.getenv('SPACES_ENDPOINT'),
                    aws_access_key_id=os.getenv('SPACES_KEY'),
                    aws_secret_access_key=os.getenv('SPACES_SECRET'),
                    region_name=os.getenv('SPACES_REGION', 'nyc3')
                )
            elif self.environment == 'aws':
                # AWS S3
                return boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
            else:
                # Local storage
                return None
        except Exception as e:
            logger.warning(f"Storage externo no disponible: {e}")
            return None
    
    def _get_storage_path(self, user_id: str, subject: str, version: int = 1) -> str:
        """Genera ruta de almacenamiento según el entorno"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.environment == 'local':
            return f"/app/storage/ymls/{user_id}/{subject}/v{version}_{timestamp}.yml"
        elif self.environment == 'digitalocean':
            bucket = os.getenv('SPACES_BUCKET', 'icfes-ymls')
            return f"{bucket}/{user_id}/{subject}/v{version}_{timestamp}.yml"
        elif self.environment == 'aws':
            bucket = os.getenv('S3_BUCKET', 'icfes-yml-prod')
            return f"{bucket}/{user_id}/{subject}/v{version}_{timestamp}.yml"
        else:
            return f"local/{user_id}/{subject}/v{version}_{timestamp}.yml"
    
    def _compress_yml(self, yml_content: str) -> bytes:
        """Comprime contenido YML para reducir tamaño de almacenamiento"""
        try:
            return gzip.compress(yml_content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error comprimiendo YML: {e}")
            return yml_content.encode('utf-8')
    
    def _decompress_yml(self, compressed_content: bytes) -> str:
        """Descomprime contenido YML"""
        try:
            return gzip.decompress(compressed_content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error descomprimiendo YML: {e}")
            return compressed_content.decode('utf-8')
    
    def _calculate_file_hash(self, content: str) -> str:
        """Calcula hash MD5 del contenido para validación de cache"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def store_yml(
        self, 
        user_id: str, 
        subject: str, 
        yml_content: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Almacena YML en el sistema de 3 capas
        """
        try:
            # 1. Comprimir contenido
            compressed_content = self._compress_yml(yml_content)
            file_size = len(compressed_content)
            file_hash = self._calculate_file_hash(yml_content)
            
            # 2. Generar ruta de almacenamiento
            storage_path = self._get_storage_path(user_id, subject)
            
            # 3. Almacenar en S3/Spaces o local
            storage_url = await self._store_file(storage_path, compressed_content)
            
            # 4. Guardar metadata en PostgreSQL
            yml_record = UserYMLPlan(
                user_id=user_id,
                subject=subject,
                storage_type=self.environment,
                storage_path=storage_path,
                storage_url=storage_url,
                file_size_bytes=file_size,
                file_hash=file_hash,
                version=1,
                generation_time_ms=metadata.get('generation_time_ms', 0),
                algorithm_version=metadata.get('algorithm_version', '1.0'),
                cache_key=f"yml:{user_id}:{subject}",
                cache_ttl=3600,
                is_active=True
            )
            
            self.db.add(yml_record)
            self.db.commit()
            self.db.refresh(yml_record)
            
            # 5. Cachear en Redis
            await self._cache_yml(user_id, subject, yml_content)
            
            logger.info(f"✅ YML almacenado exitosamente para usuario {user_id}, materia {subject}")
            
            return {
                'storage_id': str(yml_record.id),
                'storage_path': storage_path,
                'storage_url': storage_url,
                'file_size_bytes': file_size,
                'file_hash': file_hash,
                'cache_key': yml_record.cache_key
            }
            
        except Exception as e:
            logger.error(f"❌ Error almacenando YML: {e}")
            self.db.rollback()
            raise
    
    async def _store_file(self, storage_path: str, content: bytes) -> str:
        """Almacena archivo en S3/Spaces o sistema local"""
        try:
            if self.storage_client:
                # S3/Spaces
                if self.environment == 'digitalocean':
                    bucket = os.getenv('SPACES_BUCKET', 'icfes-ymls')
                    key = storage_path.replace(f"{bucket}/", "")
                    self.storage_client.put_object(
                        Bucket=bucket,
                        Key=key,
                        Body=content,
                        ContentType='application/x-yaml',
                        ContentEncoding='gzip'
                    )
                    return f"https://{bucket}.{os.getenv('SPACES_ENDPOINT', 'nyc3.digitaloceanspaces.com')}/{key}"
                
                elif self.environment == 'aws':
                    bucket = os.getenv('S3_BUCKET', 'icfes-yml-prod')
                    key = storage_path.replace(f"{bucket}/", "")
                    self.storage_client.put_object(
                        Bucket=bucket,
                        Key=key,
                        Body=content,
                        ContentType='application/x-yaml',
                        ContentEncoding='gzip'
                    )
                    return f"https://{bucket}.s3.amazonaws.com/{key}"
            
            else:
                # Almacenamiento local
                local_path = f"./storage/ymls/{storage_path.split('/')[-1]}"
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(content)
                return f"file://{local_path}"
                
        except Exception as e:
            logger.error(f"Error almacenando archivo: {e}")
            raise
    
    async def retrieve_yml(self, user_id: str, subject: str) -> Optional[str]:
        """
        Recupera YML usando el sistema de 3 capas (cache -> DB -> storage)
        """
        try:
            # 1. Verificar cache Redis (1ms)
            cached_content = await self._get_cached_yml(user_id, subject)
            if cached_content:
                logger.info(f"✅ YML recuperado desde cache para usuario {user_id}")
                return cached_content
            
            # 2. Verificar base de datos (5ms)
            yml_record = self.db.query(UserYMLPlan).filter(
                and_(
                    UserYMLPlan.user_id == user_id,
                    UserYMLPlan.subject == subject,
                    UserYMLPlan.is_active == True
                )
            ).order_by(desc(UserYMLPlan.version)).first()
            
            if not yml_record:
                logger.warning(f"❌ No se encontró YML para usuario {user_id}, materia {subject}")
                return None
            
            # 3. Recuperar desde storage (50ms)
            yml_content = await self._retrieve_file(yml_record.storage_path)
            if not yml_content:
                logger.error(f"❌ Error recuperando archivo desde storage: {yml_record.storage_path}")
                return None
            
            # 4. Cachear para futuras consultas
            await self._cache_yml(user_id, subject, yml_content)
            
            # 5. Actualizar estadísticas de acceso
            yml_record.last_accessed = datetime.utcnow()
            yml_record.access_count += 1
            self.db.commit()
            
            logger.info(f"✅ YML recuperado desde storage para usuario {user_id}")
            return yml_content
            
        except Exception as e:
            logger.error(f"❌ Error recuperando YML: {e}")
            return None
    
    async def _retrieve_file(self, storage_path: str) -> Optional[str]:
        """Recupera archivo desde S3/Spaces o sistema local"""
        try:
            if self.storage_client:
                # S3/Spaces
                if self.environment == 'digitalocean':
                    bucket = os.getenv('SPACES_BUCKET', 'icfes-ymls')
                    key = storage_path.replace(f"{bucket}/", "")
                    response = self.storage_client.get_object(Bucket=bucket, Key=key)
                    compressed_content = response['Body'].read()
                
                elif self.environment == 'aws':
                    bucket = os.getenv('S3_BUCKET', 'icfes-yml-prod')
                    key = storage_path.replace(f"{bucket}/", "")
                    response = self.storage_client.get_object(Bucket=bucket, Key=key)
                    compressed_content = response['Body'].read()
            
            else:
                # Almacenamiento local
                local_path = f"./storage/ymls/{storage_path.split('/')[-1]}"
                with open(local_path, 'rb') as f:
                    compressed_content = f.read()
            
            # Descomprimir contenido
            return self._decompress_yml(compressed_content)
            
        except Exception as e:
            logger.error(f"Error recuperando archivo: {e}")
            return None
    
    async def _cache_yml(self, user_id: str, subject: str, content: str):
        """Cachea YML en Redis para acceso rápido"""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"yml:{user_id}:{subject}"
            # Cache por 1 hora
            self.redis_client.setex(cache_key, 3600, content)
            logger.debug(f"YML cacheado en Redis: {cache_key}")
        except Exception as e:
            logger.warning(f"Error cacheando en Redis: {e}")
    
    async def _get_cached_yml(self, user_id: str, subject: str) -> Optional[str]:
        """Recupera YML desde cache Redis"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"yml:{user_id}:{subject}"
            cached = self.redis_client.get(cache_key)
            if cached:
                return cached.decode('utf-8')
        except Exception as e:
            logger.warning(f"Error recuperando desde Redis: {e}")
        
        return None
    
    def get_user_yml_metadata(self, user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """Obtiene metadata del YML sin recuperar el contenido completo"""
        try:
            yml_record = self.db.query(UserYMLPlan).filter(
                and_(
                    UserYMLPlan.user_id == user_id,
                    UserYMLPlan.subject == subject,
                    UserYMLPlan.is_active == True
                )
            ).order_by(desc(UserYMLPlan.version)).first()
            
            if not yml_record:
                return None
            
            return {
                'id': str(yml_record.id),
                'user_id': yml_record.user_id,
                'subject': yml_record.subject,
                'version': yml_record.version,
                'file_size_bytes': yml_record.file_size_bytes,
                'file_hash': yml_record.file_hash,
                'generated_at': yml_record.generated_at.isoformat(),
                'generation_time_ms': yml_record.generation_time_ms,
                'algorithm_version': yml_record.algorithm_version,
                'last_accessed': yml_record.last_accessed.isoformat() if yml_record.last_accessed else None,
                'access_count': yml_record.access_count,
                'storage_type': yml_record.storage_type,
                'storage_url': yml_record.storage_url
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo metadata: {e}")
            return None
    
    def list_user_ymls(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista todos los YMLs de un usuario"""
        try:
            yml_records = self.db.query(UserYMLPlan).filter(
                and_(
                    UserYMLPlan.user_id == user_id,
                    UserYMLPlan.is_active == True
                )
            ).order_by(desc(UserYMLPlan.generated_at)).all()
            
            return [
                {
                    'id': str(record.id),
                    'subject': record.subject,
                    'version': record.version,
                    'generated_at': record.generated_at.isoformat(),
                    'file_size_bytes': record.file_size_bytes,
                    'last_accessed': record.last_accessed.isoformat() if record.last_accessed else None,
                    'access_count': record.access_count
                }
                for record in yml_records
            ]
            
        except Exception as e:
            logger.error(f"Error listando YMLs: {e}")
            return []
    
    async def invalidate_cache(self, user_id: str, subject: str = None):
        """Invalida cache de YML"""
        if not self.redis_client:
            return
        
        try:
            if subject:
                # Invalidar YML específico
                cache_key = f"yml:{user_id}:{subject}"
                self.redis_client.delete(cache_key)
            else:
                # Invalidar todos los YMLs del usuario
                pattern = f"yml:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            logger.info(f"Cache invalidado para usuario {user_id}")
        except Exception as e:
            logger.warning(f"Error invalidando cache: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de almacenamiento"""
        try:
            total_ymls = self.db.query(UserYMLPlan).filter(UserYMLPlan.is_active == True).count()
            total_size = self.db.query(UserYMLPlan).filter(UserYMLPlan.is_active == True).with_entities(
                func.sum(UserYMLPlan.file_size_bytes)
            ).scalar() or 0
            
            # Estadísticas de cache Redis
            cache_stats = {}
            if self.redis_client:
                try:
                    cache_stats = {
                        'total_keys': self.redis_client.dbsize(),
                        'memory_usage': self.redis_client.info('memory').get('used_memory_human', 'N/A')
                    }
                except:
                    cache_stats = {'error': 'No disponible'}
            
            return {
                'total_ymls': total_ymls,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'environment': self.environment,
                'cache_stats': cache_stats
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
