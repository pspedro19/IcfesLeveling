"""Dynamic Subject Management Service - Production Ready"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import logging
import uuid

from ..models.subject import Subject
from ..models.subject_config import SubjectConfig, SubjectAlias, AssetConfiguration
from ..models.question import Topic
from ..core.database import get_db

logger = logging.getLogger(__name__)

class DynamicSubjectService:
    """Production-ready service for dynamic subject management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_subjects_with_config(self) -> List[Dict[str, Any]]:
        """Get all subjects with their dynamic configurations"""
        subjects = self.db.query(Subject).filter(
            Subject.config.has(SubjectConfig.is_active == True)
        ).all()
        
        result = []
        for subject in subjects:
            config = subject.config or self._create_default_config(subject.id)
            aliases = [alias.alias_name for alias in subject.aliases]
            
            result.append({
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "aliases": aliases,
                "config": {
                    "total_questions": config.total_questions,
                    "time_limit_minutes": config.time_limit_minutes,
                    "passing_score": config.passing_score,
                    "topics": config.topics or [],
                    "difficulty_levels": config.difficulty_levels or {},
                    "study_sequence": config.study_sequence or []
                },
                "display": {
                    "icon_url": config.icon_url or subject.icon_url,
                    "color_primary": config.color_primary or subject.color,
                    "color_secondary": config.color_secondary,
                    "description_short": config.description_short,
                    "description_long": config.description_long
                }
            })
        
        return result
    
    def find_subject_by_name_or_alias(self, name: str) -> Optional[Subject]:
        """Intelligently find subject by name or any of its aliases"""
        # Direct name match
        subject = self.db.query(Subject).filter(
            func.lower(Subject.name) == func.lower(name.strip())
        ).first()
        
        if subject:
            return subject
        
        # Check aliases
        alias = self.db.query(SubjectAlias).filter(
            func.lower(SubjectAlias.alias_name) == func.lower(name.strip())
        ).first()
        
        if alias:
            return alias.subject
        
        # Fuzzy matching for common variations
        fuzzy_patterns = [
            f"%{name.lower()}%",
            f"{name.lower()}%",
            f"%{name.lower()}"
        ]
        
        for pattern in fuzzy_patterns:
            subject = self.db.query(Subject).filter(
                or_(
                    func.lower(Subject.name).like(pattern),
                    Subject.aliases.any(func.lower(SubjectAlias.alias_name).like(pattern))
                )
            ).first()
            
            if subject:
                return subject
        
        return None
    
    def get_subject_config(self, subject_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Get dynamic configuration for a specific subject"""
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise ValueError(f"Subject with ID {subject_id} not found")
        
        config = subject.config or self._create_default_config(subject.id)
        
        return {
            "total_questions": config.total_questions,
            "time_limit_minutes": config.time_limit_minutes,
            "passing_score": config.passing_score,
            "topics": config.topics or self._get_dynamic_topics(subject_id),
            "difficulty_levels": config.difficulty_levels or self._get_default_difficulty_levels(),
            "study_sequence": config.study_sequence or []
        }
    
    def get_assets_for_entity(self, entity_type: str, entity_id: Union[str, uuid.UUID]) -> Dict[str, str]:
        """Get dynamic assets for any entity (subject, hero, achievement)"""
        assets = self.db.query(AssetConfiguration).filter(
            AssetConfiguration.entity_type == entity_type,
            AssetConfiguration.entity_id == entity_id
        ).all()
        
        asset_map = {}
        for asset in assets:
            if asset.is_default or asset.asset_type not in asset_map:
                asset_map[asset.asset_type] = asset.asset_url
        
        return asset_map
    
    def create_subject_with_config(self, 
                                 name: str,
                                 description: str = None,
                                 aliases: List[str] = None,
                                 config: Dict[str, Any] = None) -> Subject:
        """Create a new subject with dynamic configuration"""
        
        # Create subject
        subject = Subject(
            name=name,
            description=description
        )
        self.db.add(subject)
        self.db.flush()  # Get the ID
        
        # Create configuration
        subject_config = SubjectConfig(
            subject_id=subject.id,
            total_questions=config.get('total_questions', 45) if config else 45,
            time_limit_minutes=config.get('time_limit_minutes', 60) if config else 60,
            passing_score=config.get('passing_score', 75) if config else 75,
            topics=config.get('topics', []) if config else [],
            difficulty_levels=config.get('difficulty_levels', {}) if config else {},
            study_sequence=config.get('study_sequence', []) if config else []
        )
        self.db.add(subject_config)
        
        # Create aliases
        if aliases:
            for alias_name in aliases:
                alias = SubjectAlias(
                    subject_id=subject.id,
                    alias_name=alias_name.strip()
                )
                self.db.add(alias)
        
        self.db.commit()
        return subject
    
    def update_subject_config(self, subject_id: Union[str, uuid.UUID], config_updates: Dict[str, Any]) -> bool:
        """Update subject configuration dynamically"""
        config = self.db.query(SubjectConfig).filter(
            SubjectConfig.subject_id == subject_id
        ).first()
        
        if not config:
            config = self._create_default_config(subject_id)
        
        # Update configuration
        for key, value in config_updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.db.commit()
        return True
    
    def add_subject_alias(self, subject_id: Union[str, uuid.UUID], alias_name: str) -> bool:
        """Add a new alias to a subject"""
        # Check if alias already exists
        existing = self.db.query(SubjectAlias).filter(
            func.lower(SubjectAlias.alias_name) == func.lower(alias_name.strip())
        ).first()
        
        if existing:
            return False  # Alias already exists
        
        alias = SubjectAlias(
            subject_id=subject_id,
            alias_name=alias_name.strip()
        )
        self.db.add(alias)
        self.db.commit()
        return True
    
    def get_subject_mapping_for_import(self) -> Dict[str, str]:
        """Generate intelligent subject mapping for import scripts with fuzzy matching"""
        mapping = {}
        subjects = self.db.query(Subject).all()
        
        for subject in subjects:
            # Add primary name (exact match)
            mapping[subject.name] = str(subject.id)
            mapping[subject.name.lower()] = str(subject.id)
            
            # Add all configured aliases
            for alias in subject.aliases:
                mapping[alias.alias_name] = str(subject.id)
                mapping[alias.alias_name.lower()] = str(subject.id)
            
            # Add intelligent variations based on subject name
            subject_variations = self._generate_intelligent_variations(subject.name)
            for variation in subject_variations:
                if variation not in mapping:  # Don't override existing mappings
                    mapping[variation] = str(subject.id)
        
        return mapping
    
    def _generate_intelligent_variations(self, subject_name: str) -> List[str]:
        """Generate intelligent variations of subject names for better matching"""
        variations = []
        name_lower = subject_name.lower()
        
        # Common Spanish subject mappings
        intelligent_mappings = {
            'matemáticas': ['matematica', 'matematicas', 'math', 'mathematics', 'mates'],
            'lectura crítica': ['lectura critica', 'lenguaje', 'español', 'language', 'reading', 'lectura'],
            'ciencias naturales': ['ciencias', 'naturales', 'science', 'natural sciences', 'fisica', 'quimica', 'biologia'],
            'sociales y ciudadanas': ['sociales', 'ciudadanas', 'social', 'social sciences', 'historia', 'geografia'],
            'inglés': ['ingles', 'english', 'foreign language', 'segunda lengua', 'idioma extranjero'],
            'filosofía': ['filosofia', 'philosophy', 'etica'],
            'química': ['quimica', 'chemistry'],
            'física': ['fisica', 'physics'],
            'biología': ['biologia', 'biology'],
            'historia': ['history'],
            'geografía': ['geografia', 'geography']
        }
        
        # Find matching base subject and add its variations
        for base_subject, aliases in intelligent_mappings.items():
            if base_subject in name_lower or any(alias in name_lower for alias in aliases):
                variations.extend(aliases)
                # Add the base subject itself
                variations.append(base_subject)
                
        # Add common variations (with/without accents, plural/singular)
        variations.extend(self._generate_accent_variations(subject_name))
        variations.extend(self._generate_plural_variations(subject_name))
        
        # Remove duplicates and return lowercase versions
        unique_variations = list(set([v.lower() for v in variations if v]))
        return unique_variations
    
    def _generate_accent_variations(self, text: str) -> List[str]:
        """Generate variations with and without Spanish accents"""
        accent_map = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        
        variations = [text]
        
        # Version without accents
        no_accent = text
        for accented, plain in accent_map.items():
            no_accent = no_accent.replace(accented, plain)
        variations.append(no_accent)
        
        return variations
    
    def _generate_plural_variations(self, text: str) -> List[str]:
        """Generate singular/plural variations"""
        variations = [text]
        text_lower = text.lower()
        
        # If ends with 's', try singular
        if text_lower.endswith('s') and len(text_lower) > 2:
            singular = text_lower[:-1]
            variations.append(singular)
            # Special case for words ending in 'es'
            if text_lower.endswith('es') and len(text_lower) > 3:
                variations.append(text_lower[:-2])
        
        # If doesn't end with 's', try plural
        else:
            variations.append(text_lower + 's')
            # Special plurals
            if text_lower.endswith('a') or text_lower.endswith('e') or text_lower.endswith('o'):
                variations.append(text_lower + 's')
            else:
                variations.append(text_lower + 'es')
        
        return variations
    
    def _create_default_config(self, subject_id: Union[str, uuid.UUID]) -> SubjectConfig:
        """Create default configuration for a subject"""
        config = SubjectConfig(
            subject_id=subject_id,
            total_questions=45,
            time_limit_minutes=60,
            passing_score=75,
            topics=[],
            difficulty_levels=self._get_default_difficulty_levels(),
            study_sequence=[]
        )
        self.db.add(config)
        self.db.commit()
        return config
    
    def _get_dynamic_topics(self, subject_id: Union[str, uuid.UUID]) -> List[str]:
        """Get topics dynamically from database"""
        topics = self.db.query(Topic).filter(Topic.subject_id == subject_id).all()
        return [topic.name for topic in topics]
    
    def _get_default_difficulty_levels(self) -> Dict[str, int]:
        """Get default difficulty level mapping"""
        return {
            "fácil": 1,
            "facil": 1,
            "bajo": 1,
            "medio": 2,
            "intermedio": 2,
            "alto": 3,
            "difícil": 3,
            "dificil": 3,
            "muy alto": 4,
            "muy difícil": 4,
            "extremo": 5
        }

# Singleton service instance
def get_dynamic_subject_service() -> DynamicSubjectService:
    """Get the dynamic subject service instance"""
    db = next(get_db())
    return DynamicSubjectService(db)