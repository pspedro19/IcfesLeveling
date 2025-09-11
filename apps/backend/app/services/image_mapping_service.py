"""
Image Mapping Service for ICFES Leveling System
Maps CSV image paths to physical file locations using the normalized correspondence system
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from dataclasses import dataclass
import json
from datetime import datetime

from ..core.database import get_db
from ..core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ImageMapping:
    """Represents a mapping between CSV path and physical path"""
    csv_path: str
    physical_path: str
    image_type: str  # question, option_a, option_b, option_c, option_d
    subject: str
    exists: bool
    file_size: Optional[int] = None
    last_modified: Optional[datetime] = None

class ImageMappingService:
    """Service for mapping CSV image references to physical file locations"""
    
    def __init__(self):
        # Base paths for the project
        self.project_root = Path("C:/Users/PEDRO_PEREZ/Documents/IcfesLeveling")
        self.backend_root = self.project_root / "apps" / "backend"
        self.allquestions_root = self.project_root / "database" / "allquestions"
        self.placeholders_root = self.allquestions_root / "placeholders"
        
        # Ensure placeholder directory exists
        self.placeholders_root.mkdir(parents=True, exist_ok=True)
        
        # Allowed image types and file extensions
        self.allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        
        # Subject mappings for placeholders
        self.subject_mappings = {
            'matematicas': 'Matematicas',
            'lectura_critica': 'Lectura Critica', 
            'ciencias_naturales': 'Ciencias Naturales',
            'ciencias_sociales': 'Ciencias Sociales',
            'ingles': 'Ingles'
        }
        
        # In-memory cache for mappings
        self._mapping_cache: Dict[str, ImageMapping] = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
        
        logger.info(f"ImageMappingService initialized with root: {self.allquestions_root}")
    
    def _get_cache_key(self, image_path: str, image_type: str) -> str:
        """Generate a cache key for the image mapping"""
        return f"{image_type}:{image_path}"
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        if self._cache_timestamp is None:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_ttl
    
    def _refresh_cache(self, db: Session) -> None:
        """Refresh the mapping cache from database"""
        try:
            logger.info("Refreshing image mapping cache...")
            self._mapping_cache.clear()
            
            # Query questions with image metadata
            query = text("""
                SELECT 
                    q.id as question_id,
                    q.pregunta_imagen,
                    q.opcion_a_imagen,
                    q.opcion_b_imagen,
                    q.opcion_c_imagen,
                    q.opcion_d_imagen,
                    s.name as subject_name,
                    qm.area_evaluada
                FROM questions q
                LEFT JOIN subjects s ON s.id = q.subject_id
                LEFT JOIN questions_icfes_metadata qm ON qm.question_id = q.id
                WHERE q.pregunta_imagen IS NOT NULL 
                   OR q.opcion_a_imagen IS NOT NULL
                   OR q.opcion_b_imagen IS NOT NULL
                   OR q.opcion_c_imagen IS NOT NULL
                   OR q.opcion_d_imagen IS NOT NULL
                LIMIT 1000
            """)
            
            result = db.execute(query)
            rows = result.fetchall()
            
            for row in rows:
                subject = self._normalize_subject_name(row.subject_name or row.area_evaluada or 'general')
                
                # Process each image type
                image_fields = {
                    'question': row.pregunta_imagen,
                    'option_a': row.opcion_a_imagen,
                    'option_b': row.opcion_b_imagen,
                    'option_c': row.opcion_c_imagen,
                    'option_d': row.opcion_d_imagen
                }
                
                for image_type, csv_path in image_fields.items():
                    if csv_path:
                        mapping = self._create_mapping(csv_path, image_type, subject)
                        if mapping:
                            cache_key = self._get_cache_key(csv_path, image_type)
                            self._mapping_cache[cache_key] = mapping
            
            self._cache_timestamp = datetime.now()
            logger.info(f"Cache refreshed with {len(self._mapping_cache)} mappings")
            
        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")
    
    def _normalize_subject_name(self, subject: str) -> str:
        """Normalize subject name for directory mapping"""
        if not subject:
            return 'general'
        
        subject_lower = subject.lower()
        
        # Direct mappings
        subject_map = {
            'matematicas': 'Matematicas',
            'matemáticas': 'Matematicas',
            'lectura critica': 'Lectura Critica',
            'lectura crítica': 'Lectura Critica',
            'ciencias naturales': 'Ciencias Naturales',
            'ciencias sociales': 'Ciencias Sociales',
            'inglés': 'Ingles',
            'ingles': 'Ingles',
            'english': 'Ingles'
        }
        
        return subject_map.get(subject_lower, subject)
    
    def _create_mapping(self, csv_path: str, image_type: str, subject: str) -> Optional[ImageMapping]:
        """Create an image mapping from CSV path to physical path"""
        if not csv_path or csv_path.strip() == '':
            return None
        
        # Clean the CSV path
        clean_path = csv_path.strip().replace('\\', '/')
        
        # Try different resolution strategies
        physical_path = None
        
        # Strategy 1: Direct path within subject directory
        subject_dir = self.allquestions_root / subject
        if subject_dir.exists():
            potential_path = subject_dir / clean_path
            if potential_path.exists() and potential_path.is_file():
                physical_path = potential_path
        
        # Strategy 2: Search in all subject directories
        if not physical_path:
            for subject_name in self.subject_mappings.values():
                subject_dir = self.allquestions_root / subject_name
                if subject_dir.exists():
                    potential_path = subject_dir / clean_path
                    if potential_path.exists() and potential_path.is_file():
                        physical_path = potential_path
                        break
        
        # Strategy 3: Recursive search by filename
        if not physical_path:
            filename = Path(clean_path).name
            for subject_name in self.subject_mappings.values():
                subject_dir = self.allquestions_root / subject_name
                if subject_dir.exists():
                    for file_path in subject_dir.rglob(filename):
                        if file_path.is_file():
                            physical_path = file_path
                            break
                    if physical_path:
                        break
        
        # Strategy 4: Search in root allquestions directory
        if not physical_path:
            potential_path = self.allquestions_root / clean_path
            if potential_path.exists() and potential_path.is_file():
                physical_path = potential_path
        
        # Create mapping
        if physical_path:
            try:
                stat_info = physical_path.stat()
                return ImageMapping(
                    csv_path=csv_path,
                    physical_path=str(physical_path),
                    image_type=image_type,
                    subject=subject,
                    exists=True,
                    file_size=stat_info.st_size,
                    last_modified=datetime.fromtimestamp(stat_info.st_mtime)
                )
            except Exception as e:
                logger.warning(f"Error getting file stats for {physical_path}: {e}")
        
        # Return mapping even if file doesn't exist (for placeholder handling)
        return ImageMapping(
            csv_path=csv_path,
            physical_path="",
            image_type=image_type,
            subject=subject,
            exists=False
        )
    
    def resolve_image_path(
        self, 
        db: Session, 
        image_path: str, 
        image_type: str = "question"
    ) -> Optional[ImageMapping]:
        """
        Resolve a CSV image path to a physical file location
        
        Args:
            db: Database session
            image_path: The image path from CSV
            image_type: Type of image (question, option_a, option_b, option_c, option_d)
            
        Returns:
            ImageMapping object or None if not found
        """
        # Validate inputs
        if not image_path or not image_type:
            return None
        
        # Sanitize path to prevent traversal
        clean_path = self._sanitize_path(image_path)
        if not clean_path:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(clean_path, image_type)
        if self._is_cache_valid() and cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]
        
        # Refresh cache if needed
        if not self._is_cache_valid():
            self._refresh_cache(db)
            if cache_key in self._mapping_cache:
                return self._mapping_cache[cache_key]
        
        # Direct resolution if not in cache
        mapping = self._create_mapping(clean_path, image_type, 'general')
        if mapping:
            self._mapping_cache[cache_key] = mapping
        
        return mapping
    
    def _sanitize_path(self, path: str) -> Optional[str]:
        """
        Sanitize path to prevent directory traversal attacks
        
        Args:
            path: Input path to sanitize
            
        Returns:
            Sanitized path or None if invalid
        """
        if not path:
            return None
        
        # Remove dangerous characters and patterns
        dangerous_patterns = ['../', '..\\', '~/', '~\\', '//', '\\\\']
        clean_path = path.strip()
        
        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if pattern in clean_path:
                logger.warning(f"Directory traversal attempt detected: {path}")
                return None
        
        # Remove leading slashes and backslashes
        clean_path = clean_path.lstrip('/\\')
        
        # Convert to forward slashes
        clean_path = clean_path.replace('\\', '/')
        
        # Additional validation
        if any(part in ['.', '..', '~'] for part in clean_path.split('/')):
            logger.warning(f"Invalid path component detected: {path}")
            return None
        
        return clean_path
    
    def get_placeholder_path(self, subject: str, image_type: str) -> str:
        """
        Get the path to a placeholder image for the given subject and type
        
        Args:
            subject: Subject name
            image_type: Type of image
            
        Returns:
            Path to placeholder image
        """
        normalized_subject = self._normalize_subject_name(subject)
        placeholder_name = f"{normalized_subject.lower().replace(' ', '_')}_{image_type}_placeholder.png"
        placeholder_path = self.placeholders_root / placeholder_name
        
        # If specific placeholder doesn't exist, use generic one
        if not placeholder_path.exists():
            generic_placeholder = self.placeholders_root / f"generic_{image_type}_placeholder.png"
            if generic_placeholder.exists():
                return str(generic_placeholder)
            else:
                # Return path where placeholder should be created
                return str(placeholder_path)
        
        return str(placeholder_path)
    
    def validate_image_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an image file for security and size
        
        Args:
            file_path: Path to the image file
            
        Returns:
            (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return False, "File does not exist"
            
            # Check file extension
            if path.suffix.lower() not in self.allowed_extensions:
                return False, f"File type not allowed: {path.suffix}"
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return False, f"File too large: {file_size} bytes (max: {self.max_file_size})"
            
            # Verify it's actually an image file (basic check)
            try:
                from PIL import Image
                with Image.open(path) as img:
                    img.verify()
            except Exception:
                return False, "File is not a valid image"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def generate_etag(self, file_path: str) -> str:
        """
        Generate an ETag for caching based on file content and modification time
        
        Args:
            file_path: Path to the file
            
        Returns:
            ETag string
        """
        try:
            path = Path(file_path)
            stat_info = path.stat()
            
            # Use file size and modification time for ETag
            etag_data = f"{stat_info.st_size}-{stat_info.st_mtime}"
            etag = hashlib.md5(etag_data.encode()).hexdigest()
            
            return f'"{etag}"'
            
        except Exception:
            # Fallback to current timestamp
            return f'"{hashlib.md5(str(datetime.now()).encode()).hexdigest()}"'
    
    def get_mapping_stats(self, db: Session) -> Dict:
        """
        Get statistics about image mappings
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with mapping statistics
        """
        try:
            # Refresh cache to get latest data
            self._refresh_cache(db)
            
            stats = {
                'total_mappings': len(self._mapping_cache),
                'existing_files': 0,
                'missing_files': 0,
                'by_subject': {},
                'by_type': {},
                'cache_age_seconds': 0
            }
            
            if self._cache_timestamp:
                stats['cache_age_seconds'] = (datetime.now() - self._cache_timestamp).seconds
            
            for mapping in self._mapping_cache.values():
                # Count existing vs missing
                if mapping.exists:
                    stats['existing_files'] += 1
                else:
                    stats['missing_files'] += 1
                
                # Count by subject
                if mapping.subject not in stats['by_subject']:
                    stats['by_subject'][mapping.subject] = {'total': 0, 'existing': 0, 'missing': 0}
                
                stats['by_subject'][mapping.subject]['total'] += 1
                if mapping.exists:
                    stats['by_subject'][mapping.subject]['existing'] += 1
                else:
                    stats['by_subject'][mapping.subject]['missing'] += 1
                
                # Count by type
                if mapping.image_type not in stats['by_type']:
                    stats['by_type'][mapping.image_type] = {'total': 0, 'existing': 0, 'missing': 0}
                
                stats['by_type'][mapping.image_type]['total'] += 1
                if mapping.exists:
                    stats['by_type'][mapping.image_type]['existing'] += 1
                else:
                    stats['by_type'][mapping.image_type]['missing'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating mapping stats: {e}")
            return {'error': str(e)}

# Global service instance
image_mapping_service = ImageMappingService()