#!/usr/bin/env python3
"""
Multi-dimensional Topic-based Filtering System for ICFES Video Matching
=====================================================================

An advanced filtering system that uses multiple dimensions to match 
educational content with student needs based on ICFES competency 
framework, subject hierarchies, and cognitive load theory.

Features:
- ICFES competency mapping and alignment
- Subject-topic-subtopic hierarchical filtering
- Cognitive load assessment and matching
- Prerequisite knowledge tracking
- Learning objective alignment
- Content difficulty progression
- Personalized filtering based on student profile

Author: Claude Code Assistant (Video Matching Specialist)  
Date: 2025-09-11
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ICFESCompetency(Enum):
    """ICFES Competency Framework"""
    # Mathematics
    COMUNICACION_MATE = "comunicacion_matematica"
    RAZONAMIENTO_MATE = "razonamiento_matematico" 
    RESOLUCION_PROBLEMAS_MATE = "resolucion_problemas_matematicos"
    
    # Natural Sciences
    USO_CONOCIMIENTO_CIENTIFICO = "uso_comprensivo_conocimiento_cientifico"
    EXPLICACION_FENOMENOS = "explicacion_fenomenos"
    INDAGACION = "indagacion"
    
    # Social Sciences & Citizenship
    PENSAMIENTO_SOCIAL = "pensamiento_social"
    INTERPRETACION_ANALISIS = "interpretacion_y_analisis_perspectivas"
    PENSAMIENTO_SISTEMICO = "pensamiento_sistemico_reflexivo"
    
    # Critical Reading
    COMPRENSION_TEXTUAL = "comprension_textual"
    INTERPRETACION_TEXTUAL = "interpretacion_textual"
    REFLEXION_VALORACION = "reflexion_y_valoracion_textual"
    
    # English
    LEXICAL = "lexical"
    PRAGMATIC = "pragmatic"
    FUNCTIONAL = "functional"

class CognitiveLevel(Enum):
    """Bloom's Taxonomy Levels adapted for ICFES"""
    REMEMBER = "recordar"
    UNDERSTAND = "comprender"
    APPLY = "aplicar"
    ANALYZE = "analizar"
    EVALUATE = "evaluar"
    CREATE = "crear"
    
    # ICFES specific additions
    INTERPRET = "interpretar"
    ARGUE = "argumentar"
    PROPOSE = "proponer"

class ContentType(Enum):
    """Types of educational content"""
    VIDEO_LECTURE = "video_clase"
    VIDEO_EXERCISE = "video_ejercicio"
    VIDEO_CONCEPT = "video_concepto"
    VIDEO_EXAMPLE = "video_ejemplo"
    VIDEO_REVIEW = "video_repaso"
    INTERACTIVE = "interactivo"
    SIMULATION = "simulacion"
    PRACTICE_SET = "conjunto_practica"

@dataclass
class ICFESTopicHierarchy:
    """ICFES topic hierarchy representation"""
    subject_code: str
    subject_name: str
    area_code: str
    area_name: str
    competency: ICFESCompetency
    component: str
    topic: str
    subtopics: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    cognitive_levels: List[CognitiveLevel] = field(default_factory=list)
    difficulty_range: Tuple[int, int] = (1, 10)
    estimated_hours: float = 1.0

@dataclass
class StudentProfile:
    """Student profile for personalized filtering"""
    student_id: str
    current_theta: Dict[str, float]  # Subject -> theta value
    mastered_topics: Set[str]
    weak_topics: Set[str]
    learning_preferences: Dict[str, Any]
    available_study_time: int  # minutes per session
    preferred_content_types: List[ContentType]
    language_preference: str = "es"
    accessibility_needs: List[str] = field(default_factory=list)

@dataclass
class ContentMetadata:
    """Enhanced content metadata for filtering"""
    content_id: Union[int, str]
    title: str
    description: str
    content_type: ContentType
    
    # ICFES mapping
    icfes_competency: ICFESCompetency
    cognitive_level: CognitiveLevel
    subject_hierarchy: ICFESTopicHierarchy
    
    # Content characteristics
    duration_minutes: int
    difficulty_score: float
    prerequisite_topics: List[str]
    covered_objectives: List[str]
    
    # Quality and engagement metrics
    quality_score: float
    engagement_score: float
    completion_rate: float
    effectiveness_score: float
    
    # Additional metadata
    language: str
    has_subtitles: bool
    has_transcript: bool
    accessibility_features: List[str]
    created_date: datetime
    last_updated: datetime

@dataclass
class FilterCriteria:
    """Multi-dimensional filter criteria"""
    # ICFES specific
    competencies: List[ICFESCompetency] = field(default_factory=list)
    cognitive_levels: List[CognitiveLevel] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    
    # Content characteristics
    content_types: List[ContentType] = field(default_factory=list)
    difficulty_range: Tuple[float, float] = (0.0, 10.0)
    duration_range: Tuple[int, int] = (0, 9999)  # minutes
    
    # Quality thresholds
    min_quality_score: float = 0.0
    min_engagement_score: float = 0.0
    min_completion_rate: float = 0.0
    
    # Prerequisites and objectives
    required_prerequisites: List[str] = field(default_factory=list)
    target_objectives: List[str] = field(default_factory=list)
    
    # Personalization
    student_profile: Optional[StudentProfile] = None
    exclude_mastered: bool = True
    prioritize_weak_areas: bool = True
    
    # Technical requirements
    language: str = "es"
    require_subtitles: bool = False
    accessibility_requirements: List[str] = field(default_factory=list)

@dataclass
class FilterResult:
    """Result of applying multi-dimensional filtering"""
    content_metadata: ContentMetadata
    relevance_score: float
    dimension_scores: Dict[str, float]
    match_reasons: List[str]
    priority_level: int  # 1-5, 5 being highest priority
    estimated_learning_impact: float
    
class ICFESCompetencyMapper:
    """Maps content to ICFES competency framework"""
    
    def __init__(self):
        self.competency_keywords = self._initialize_competency_keywords()
        self.subject_competency_mapping = self._initialize_subject_competency_mapping()
        
    def _initialize_competency_keywords(self) -> Dict[ICFESCompetency, List[str]]:
        """Initialize keyword mapping for competencies"""
        return {
            # Mathematics
            ICFESCompetency.COMUNICACION_MATE: [
                "comunicar", "expresar", "representar", "simbolizar", "graficar",
                "lenguaje matemático", "notación", "terminología", "vocabulario"
            ],
            ICFESCompetency.RAZONAMIENTO_MATE: [
                "demostrar", "justificar", "argumentar", "deducir", "inferir",
                "lógica", "prueba", "razonamiento", "validar", "verificar"
            ],
            ICFESCompetency.RESOLUCION_PROBLEMAS_MATE: [
                "resolver", "solucionar", "aplicar", "modelar", "estrategia",
                "problema", "situación", "contexto", "algoritmo", "procedimiento"
            ],
            
            # Natural Sciences
            ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO: [
                "aplicar", "usar", "utilizar", "implementar", "emplear",
                "conocimiento científico", "teoría", "ley", "principio", "concepto"
            ],
            ICFESCompetency.EXPLICACION_FENOMENOS: [
                "explicar", "describir", "justificar", "interpretar", "analizar",
                "fenómeno", "proceso", "mecanismo", "causa", "efecto"
            ],
            ICFESCompetency.INDAGACION: [
                "investigar", "indagar", "experimentar", "observar", "hipótesis",
                "método científico", "evidencia", "dato", "conclusión", "variable"
            ],
            
            # Social Sciences
            ICFESCompetency.PENSAMIENTO_SOCIAL: [
                "sociedad", "cultura", "historia", "geografía", "política",
                "economía", "social", "humano", "comunidad", "civilización"
            ],
            ICFESCompetency.INTERPRETACION_ANALISIS: [
                "interpretar", "analizar", "perspectiva", "punto de vista",
                "enfoque", "análisis", "crítico", "reflexión", "posición"
            ],
            ICFESCompetency.PENSAMIENTO_SISTEMICO: [
                "sistema", "sistémico", "relación", "interacción", "estructura",
                "organización", "complejo", "holístico", "integral", "conexión"
            ],
            
            # Critical Reading
            ICFESCompetency.COMPRENSION_TEXTUAL: [
                "comprender", "entender", "texto", "lectura", "información",
                "contenido", "mensaje", "idea", "significado", "sentido"
            ],
            ICFESCompetency.INTERPRETACION_TEXTUAL: [
                "interpretar", "inferir", "deducir", "implicar", "sugerir",
                "implícito", "explícito", "subtexto", "intención", "propósito"
            ],
            ICFESCompetency.REFLEXION_VALORACION: [
                "reflexionar", "valorar", "evaluar", "criticar", "juzgar",
                "opinión", "juicio", "criterio", "postura", "argumento"
            ],
            
            # English
            ICFESCompetency.LEXICAL: [
                "vocabulary", "words", "lexicon", "terms", "meaning",
                "vocabulario", "palabras", "léxico", "términos", "significado"
            ],
            ICFESCompetency.PRAGMATIC: [
                "context", "situation", "purpose", "intention", "communication",
                "contexto", "situación", "propósito", "intención", "comunicación"
            ],
            ICFESCompetency.FUNCTIONAL: [
                "function", "use", "application", "purpose", "role",
                "función", "uso", "aplicación", "propósito", "papel"
            ]
        }
    
    def _initialize_subject_competency_mapping(self) -> Dict[str, List[ICFESCompetency]]:
        """Map subjects to their relevant competencies"""
        return {
            "Matemáticas": [
                ICFESCompetency.COMUNICACION_MATE,
                ICFESCompetency.RAZONAMIENTO_MATE,
                ICFESCompetency.RESOLUCION_PROBLEMAS_MATE
            ],
            "Física": [
                ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO,
                ICFESCompetency.EXPLICACION_FENOMENOS,
                ICFESCompetency.INDAGACION
            ],
            "Química": [
                ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO,
                ICFESCompetency.EXPLICACION_FENOMENOS,
                ICFESCompetency.INDAGACION
            ],
            "Biología": [
                ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO,
                ICFESCompetency.EXPLICACION_FENOMENOS,
                ICFESCompetency.INDAGACION
            ],
            "Ciencias Sociales": [
                ICFESCompetency.PENSAMIENTO_SOCIAL,
                ICFESCompetency.INTERPRETACION_ANALISIS,
                ICFESCompetency.PENSAMIENTO_SISTEMICO
            ],
            "Historia": [
                ICFESCompetency.PENSAMIENTO_SOCIAL,
                ICFESCompetency.INTERPRETACION_ANALISIS
            ],
            "Geografía": [
                ICFESCompetency.PENSAMIENTO_SOCIAL,
                ICFESCompetency.PENSAMIENTO_SISTEMICO
            ],
            "Lenguaje": [
                ICFESCompetency.COMPRENSION_TEXTUAL,
                ICFESCompetency.INTERPRETACION_TEXTUAL,
                ICFESCompetency.REFLEXION_VALORACION
            ],
            "Literatura": [
                ICFESCompetency.COMPRENSION_TEXTUAL,
                ICFESCompetency.INTERPRETACION_TEXTUAL,
                ICFESCompetency.REFLEXION_VALORACION
            ],
            "Inglés": [
                ICFESCompetency.LEXICAL,
                ICFESCompetency.PRAGMATIC,
                ICFESCompetency.FUNCTIONAL
            ]
        }
    
    def identify_competencies(self, content: str, subject: str) -> List[ICFESCompetency]:
        """Identify ICFES competencies from content and subject"""
        competencies = []
        content_lower = content.lower()
        
        # First, get competencies based on subject
        subject_competencies = self.subject_competency_mapping.get(subject, [])
        
        # Then, refine based on content keywords
        for competency, keywords in self.competency_keywords.items():
            if competency in subject_competencies:
                keyword_matches = sum(1 for keyword in keywords if keyword in content_lower)
                if keyword_matches > 0:
                    competencies.append(competency)
        
        # If no specific competencies found, return default for subject
        if not competencies and subject_competencies:
            competencies = subject_competencies[:1]  # Return primary competency
        
        return competencies
    
    def get_competency_weight(self, competency: ICFESCompetency, content: str) -> float:
        """Calculate weight/relevance of competency for content"""
        keywords = self.competency_keywords.get(competency, [])
        content_lower = content.lower()
        
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        weight = min(matches / len(keywords) if keywords else 0, 1.0)
        
        return weight

class TopicHierarchyManager:
    """Manages ICFES topic hierarchies and relationships"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.hierarchy_cache = {}
        self.prerequisite_graph = {}
        
    def get_topic_hierarchy(self, subject_id: int, topic_id: int) -> Optional[ICFESTopicHierarchy]:
        """Get complete topic hierarchy information"""
        cache_key = f"{subject_id}_{topic_id}"
        
        if cache_key in self.hierarchy_cache:
            return self.hierarchy_cache[cache_key]
        
        try:
            # Query database for topic hierarchy
            query = text("""
                SELECT 
                    s.id as subject_id,
                    s.name as subject_name,
                    s.code as subject_code,
                    t.id as topic_id,
                    t.name as topic_name,
                    t.component,
                    t.competence,
                    t.cognitive_level,
                    t.prerequisites,
                    t.learning_objectives,
                    t.difficulty_min,
                    t.difficulty_max,
                    t.estimated_hours
                FROM subjects s
                JOIN topics t ON s.id = t.subject_id
                WHERE s.id = :subject_id AND t.id = :topic_id
            """)
            
            result = self.db.execute(query, {
                "subject_id": subject_id,
                "topic_id": topic_id
            }).fetchone()
            
            if not result:
                return None
            
            # Map to ICFESTopicHierarchy
            hierarchy = ICFESTopicHierarchy(
                subject_code=result.subject_code or f"SUB{subject_id}",
                subject_name=result.subject_name,
                area_code=result.subject_code[:2] if result.subject_code else "GE",
                area_name=result.subject_name,
                competency=self._map_competency_string(result.competence),
                component=result.component or "",
                topic=result.topic_name,
                subtopics=self._get_subtopics(topic_id),
                prerequisites=self._parse_json_field(result.prerequisites),
                learning_objectives=self._parse_json_field(result.learning_objectives),
                cognitive_levels=self._map_cognitive_levels(result.cognitive_level),
                difficulty_range=(result.difficulty_min or 1, result.difficulty_max or 10),
                estimated_hours=result.estimated_hours or 1.0
            )
            
            self.hierarchy_cache[cache_key] = hierarchy
            return hierarchy
            
        except Exception as e:
            logger.error(f"Error getting topic hierarchy: {e}")
            return None
    
    def _map_competency_string(self, competency_str: str) -> ICFESCompetency:
        """Map string to ICFESCompetency enum"""
        if not competency_str:
            return ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO  # Default
        
        competency_map = {
            "comunicacion": ICFESCompetency.COMUNICACION_MATE,
            "razonamiento": ICFESCompetency.RAZONAMIENTO_MATE,
            "resolucion": ICFESCompetency.RESOLUCION_PROBLEMAS_MATE,
            "uso comprensivo": ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO,
            "explicacion": ICFESCompetency.EXPLICACION_FENOMENOS,
            "indagacion": ICFESCompetency.INDAGACION,
            "pensamiento social": ICFESCompetency.PENSAMIENTO_SOCIAL,
            "interpretacion": ICFESCompetency.INTERPRETACION_ANALISIS,
            "sistemico": ICFESCompetency.PENSAMIENTO_SISTEMICO,
            "comprension": ICFESCompetency.COMPRENSION_TEXTUAL,
            "reflexion": ICFESCompetency.REFLEXION_VALORACION,
            "lexical": ICFESCompetency.LEXICAL,
            "pragmatic": ICFESCompetency.PRAGMATIC,
            "functional": ICFESCompetency.FUNCTIONAL
        }
        
        competency_lower = competency_str.lower()
        for key, value in competency_map.items():
            if key in competency_lower:
                return value
        
        return ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO
    
    def _map_cognitive_levels(self, cognitive_level_str: str) -> List[CognitiveLevel]:
        """Map string to CognitiveLevel enums"""
        if not cognitive_level_str:
            return [CognitiveLevel.UNDERSTAND]
        
        level_map = {
            "recordar": CognitiveLevel.REMEMBER,
            "remember": CognitiveLevel.REMEMBER,
            "comprender": CognitiveLevel.UNDERSTAND,
            "understand": CognitiveLevel.UNDERSTAND,
            "aplicar": CognitiveLevel.APPLY,
            "apply": CognitiveLevel.APPLY,
            "analizar": CognitiveLevel.ANALYZE,
            "analyze": CognitiveLevel.ANALYZE,
            "evaluar": CognitiveLevel.EVALUATE,
            "evaluate": CognitiveLevel.EVALUATE,
            "crear": CognitiveLevel.CREATE,
            "create": CognitiveLevel.CREATE,
            "interpretar": CognitiveLevel.INTERPRET,
            "argumentar": CognitiveLevel.ARGUE,
            "proponer": CognitiveLevel.PROPOSE
        }
        
        levels = []
        level_lower = cognitive_level_str.lower()
        for key, value in level_map.items():
            if key in level_lower:
                levels.append(value)
        
        return levels if levels else [CognitiveLevel.UNDERSTAND]
    
    def _get_subtopics(self, topic_id: int) -> List[str]:
        """Get subtopics for a topic"""
        try:
            query = text("""
                SELECT name FROM topics 
                WHERE parent_topic_id = :topic_id
                ORDER BY name
            """)
            
            results = self.db.execute(query, {"topic_id": topic_id}).fetchall()
            return [row.name for row in results]
            
        except Exception as e:
            logger.debug(f"No subtopics found for topic {topic_id}: {e}")
            return []
    
    def _parse_json_field(self, json_str: str) -> List[str]:
        """Parse JSON field to list of strings"""
        if not json_str:
            return []
        
        try:
            if isinstance(json_str, str):
                return json.loads(json_str)
            elif isinstance(json_str, list):
                return json_str
            else:
                return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def check_prerequisites(self, target_topic_id: int, mastered_topics: Set[str]) -> bool:
        """Check if prerequisites are met for target topic"""
        hierarchy = self.get_topic_hierarchy(0, target_topic_id)  # Subject ID not needed for prerequisites
        
        if not hierarchy or not hierarchy.prerequisites:
            return True  # No prerequisites
        
        # Check if all prerequisites are in mastered topics
        return all(prereq in mastered_topics for prereq in hierarchy.prerequisites)
    
    def get_learning_path(self, start_topic: str, target_topic: str) -> List[str]:
        """Generate learning path from start to target topic"""
        # This would implement a graph traversal algorithm
        # For now, return a simple path
        return [start_topic, target_topic]

class MultidimensionalTopicFilter:
    """Main multi-dimensional filtering system"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.competency_mapper = ICFESCompetencyMapper()
        self.hierarchy_manager = TopicHierarchyManager(db_session)
        
        # Scoring weights for different dimensions
        self.dimension_weights = {
            'competency_match': 0.25,
            'topic_relevance': 0.20,
            'difficulty_match': 0.15,
            'cognitive_level_match': 0.15,
            'quality_score': 0.10,
            'prerequisite_alignment': 0.10,
            'personalization': 0.05
        }
    
    def apply_filter(
        self, 
        content_items: List[ContentMetadata],
        filter_criteria: FilterCriteria
    ) -> List[FilterResult]:
        """Apply multi-dimensional filtering to content items"""
        
        logger.info(f"Applying multi-dimensional filter to {len(content_items)} items")
        results = []
        
        for content in content_items:
            # Apply each filter dimension
            if self._passes_basic_filters(content, filter_criteria):
                result = self._score_content_item(content, filter_criteria)
                if result.relevance_score >= 0.3:  # Minimum relevance threshold
                    results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Apply final ranking adjustments
        self._apply_ranking_adjustments(results, filter_criteria)
        
        logger.info(f"Filter produced {len(results)} relevant items")
        return results
    
    def _passes_basic_filters(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> bool:
        """Check if content passes basic filter criteria"""
        
        # Content type filter
        if criteria.content_types and content.content_type not in criteria.content_types:
            return False
        
        # Difficulty range filter
        if not (criteria.difficulty_range[0] <= content.difficulty_score <= criteria.difficulty_range[1]):
            return False
        
        # Duration filter
        if not (criteria.duration_range[0] <= content.duration_minutes <= criteria.duration_range[1]):
            return False
        
        # Quality thresholds
        if content.quality_score < criteria.min_quality_score:
            return False
        
        if content.engagement_score < criteria.min_engagement_score:
            return False
        
        if content.completion_rate < criteria.min_completion_rate:
            return False
        
        # Language filter
        if criteria.language and content.language != criteria.language:
            return False
        
        # Subtitles requirement
        if criteria.require_subtitles and not content.has_subtitles:
            return False
        
        # Accessibility requirements
        if criteria.accessibility_requirements:
            if not all(req in content.accessibility_features 
                      for req in criteria.accessibility_requirements):
                return False
        
        return True
    
    def _score_content_item(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> FilterResult:
        """Score content item across all dimensions"""
        
        dimension_scores = {}
        match_reasons = []
        
        # 1. Competency matching
        competency_score = self._score_competency_match(content, criteria)
        dimension_scores['competency_match'] = competency_score
        if competency_score > 0.7:
            match_reasons.append(f"Alta coincidencia de competencia ({competency_score:.2f})")
        
        # 2. Topic relevance
        topic_score = self._score_topic_relevance(content, criteria)
        dimension_scores['topic_relevance'] = topic_score
        if topic_score > 0.8:
            match_reasons.append("Tema altamente relevante")
        
        # 3. Difficulty matching
        difficulty_score = self._score_difficulty_match(content, criteria)
        dimension_scores['difficulty_match'] = difficulty_score
        
        # 4. Cognitive level matching
        cognitive_score = self._score_cognitive_level_match(content, criteria)
        dimension_scores['cognitive_level_match'] = cognitive_score
        
        # 5. Quality score (already normalized)
        dimension_scores['quality_score'] = content.quality_score / 10.0  # Assuming 0-10 scale
        
        # 6. Prerequisite alignment
        prerequisite_score = self._score_prerequisite_alignment(content, criteria)
        dimension_scores['prerequisite_alignment'] = prerequisite_score
        if prerequisite_score == 1.0:
            match_reasons.append("Todos los prerrequisitos cumplidos")
        
        # 7. Personalization score
        personalization_score = self._score_personalization(content, criteria)
        dimension_scores['personalization'] = personalization_score
        
        # Calculate weighted final score
        relevance_score = sum(
            score * self.dimension_weights.get(dimension, 0)
            for dimension, score in dimension_scores.items()
        )
        
        # Determine priority level
        priority_level = self._determine_priority_level(relevance_score, dimension_scores, criteria)
        
        # Estimate learning impact
        learning_impact = self._estimate_learning_impact(content, criteria, dimension_scores)
        
        return FilterResult(
            content_metadata=content,
            relevance_score=relevance_score,
            dimension_scores=dimension_scores,
            match_reasons=match_reasons,
            priority_level=priority_level,
            estimated_learning_impact=learning_impact
        )
    
    def _score_competency_match(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> float:
        """Score competency matching"""
        if not criteria.competencies:
            return 0.5  # Neutral score if no specific competencies required
        
        # Direct competency match
        if content.icfes_competency in criteria.competencies:
            return 1.0
        
        # Check for related competencies within same domain
        content_domain = self._get_competency_domain(content.icfes_competency)
        criteria_domains = [self._get_competency_domain(comp) for comp in criteria.competencies]
        
        if content_domain in criteria_domains:
            return 0.7
        
        return 0.2
    
    def _score_topic_relevance(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> float:
        """Score topic relevance"""
        score = 0.0
        
        # Subject match
        if criteria.subjects:
            if content.subject_hierarchy.subject_name in criteria.subjects:
                score += 0.4
            elif any(subj in content.subject_hierarchy.subject_name for subj in criteria.subjects):
                score += 0.2
        
        # Topic match  
        if criteria.topics:
            if content.subject_hierarchy.topic in criteria.topics:
                score += 0.4
            elif any(topic in content.subject_hierarchy.topic for topic in criteria.topics):
                score += 0.2
        
        # Subtopic match
        if criteria.topics and content.subject_hierarchy.subtopics:
            matching_subtopics = sum(1 for subtopic in content.subject_hierarchy.subtopics
                                   if any(topic in subtopic for topic in criteria.topics))
            if matching_subtopics > 0:
                score += 0.2 * (matching_subtopics / len(content.subject_hierarchy.subtopics))
        
        return min(1.0, score)
    
    def _score_difficulty_match(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> float:
        """Score difficulty matching"""
        target_min, target_max = criteria.difficulty_range
        content_difficulty = content.difficulty_score
        
        # Perfect match if within range
        if target_min <= content_difficulty <= target_max:
            # Bonus for being in the center of the range
            range_center = (target_min + target_max) / 2
            distance_from_center = abs(content_difficulty - range_center)
            range_width = (target_max - target_min) / 2
            
            if range_width > 0:
                center_score = 1.0 - (distance_from_center / range_width)
                return max(0.8, center_score)  # At least 0.8 for being in range
            else:
                return 1.0
        
        # Penalty for being outside range
        if content_difficulty < target_min:
            distance = target_min - content_difficulty
        else:
            distance = content_difficulty - target_max
        
        # Exponential decay for distance penalty
        penalty = np.exp(-distance / 2.0)  # Adjust decay rate as needed
        return max(0.1, penalty)
    
    def _score_cognitive_level_match(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> float:
        """Score cognitive level matching"""
        if not criteria.cognitive_levels:
            return 0.5
        
        content_level = content.cognitive_level
        target_levels = criteria.cognitive_levels
        
        # Direct match
        if content_level in target_levels:
            return 1.0
        
        # Check for compatible levels (e.g., APPLY can help with UNDERSTAND)
        compatibility_map = {
            CognitiveLevel.REMEMBER: [CognitiveLevel.UNDERSTAND],
            CognitiveLevel.UNDERSTAND: [CognitiveLevel.APPLY, CognitiveLevel.REMEMBER],
            CognitiveLevel.APPLY: [CognitiveLevel.ANALYZE, CognitiveLevel.UNDERSTAND],
            CognitiveLevel.ANALYZE: [CognitiveLevel.EVALUATE, CognitiveLevel.APPLY],
            CognitiveLevel.EVALUATE: [CognitiveLevel.CREATE, CognitiveLevel.ANALYZE],
            CognitiveLevel.CREATE: [CognitiveLevel.EVALUATE],
            CognitiveLevel.INTERPRET: [CognitiveLevel.UNDERSTAND, CognitiveLevel.ANALYZE],
            CognitiveLevel.ARGUE: [CognitiveLevel.EVALUATE, CognitiveLevel.ANALYZE],
            CognitiveLevel.PROPOSE: [CognitiveLevel.CREATE, CognitiveLevel.EVALUATE]
        }
        
        compatible_levels = compatibility_map.get(content_level, [])
        if any(level in target_levels for level in compatible_levels):
            return 0.7
        
        return 0.3
    
    def _score_prerequisite_alignment(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> float:
        """Score prerequisite alignment"""
        if not criteria.student_profile:
            return 1.0  # No student profile, assume prerequisites are met
        
        mastered_topics = criteria.student_profile.mastered_topics
        required_prerequisites = set(content.prerequisite_topics)
        
        if not required_prerequisites:
            return 1.0  # No prerequisites required
        
        met_prerequisites = required_prerequisites.intersection(mastered_topics)
        prerequisite_ratio = len(met_prerequisites) / len(required_prerequisites)
        
        return prerequisite_ratio
    
    def _score_personalization(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria
    ) -> float:
        """Score personalization fit"""
        if not criteria.student_profile:
            return 0.5
        
        profile = criteria.student_profile
        score = 0.0
        
        # Content type preference
        if content.content_type in profile.preferred_content_types:
            score += 0.3
        
        # Duration fit with available study time
        if content.duration_minutes <= profile.available_study_time:
            score += 0.2
        elif content.duration_minutes <= profile.available_study_time * 1.2:  # 20% tolerance
            score += 0.1
        
        # Language preference
        if content.language == profile.language_preference:
            score += 0.2
        
        # Accessibility needs
        if profile.accessibility_needs:
            met_needs = sum(1 for need in profile.accessibility_needs 
                          if need in content.accessibility_features)
            score += 0.3 * (met_needs / len(profile.accessibility_needs))
        else:
            score += 0.3  # No special needs
        
        return min(1.0, score)
    
    def _get_competency_domain(self, competency: ICFESCompetency) -> str:
        """Get the domain (subject area) of a competency"""
        domain_map = {
            ICFESCompetency.COMUNICACION_MATE: "matematicas",
            ICFESCompetency.RAZONAMIENTO_MATE: "matematicas", 
            ICFESCompetency.RESOLUCION_PROBLEMAS_MATE: "matematicas",
            ICFESCompetency.USO_CONOCIMIENTO_CIENTIFICO: "ciencias",
            ICFESCompetency.EXPLICACION_FENOMENOS: "ciencias",
            ICFESCompetency.INDAGACION: "ciencias",
            ICFESCompetency.PENSAMIENTO_SOCIAL: "sociales",
            ICFESCompetency.INTERPRETACION_ANALISIS: "sociales",
            ICFESCompetency.PENSAMIENTO_SISTEMICO: "sociales",
            ICFESCompetency.COMPRENSION_TEXTUAL: "lenguaje",
            ICFESCompetency.INTERPRETACION_TEXTUAL: "lenguaje",
            ICFESCompetency.REFLEXION_VALORACION: "lenguaje",
            ICFESCompetency.LEXICAL: "ingles",
            ICFESCompetency.PRAGMATIC: "ingles",
            ICFESCompetency.FUNCTIONAL: "ingles"
        }
        
        return domain_map.get(competency, "general")
    
    def _determine_priority_level(
        self, 
        relevance_score: float, 
        dimension_scores: Dict[str, float],
        criteria: FilterCriteria
    ) -> int:
        """Determine priority level (1-5, 5 being highest)"""
        
        # Base priority from relevance score
        if relevance_score >= 0.9:
            base_priority = 5
        elif relevance_score >= 0.8:
            base_priority = 4
        elif relevance_score >= 0.7:
            base_priority = 3
        elif relevance_score >= 0.5:
            base_priority = 2
        else:
            base_priority = 1
        
        # Adjust based on specific criteria
        adjustments = 0
        
        # High competency match boosts priority
        if dimension_scores.get('competency_match', 0) >= 0.9:
            adjustments += 1
        
        # Perfect prerequisite alignment boosts priority
        if dimension_scores.get('prerequisite_alignment', 0) == 1.0:
            adjustments += 1
        
        # Student's weak areas get priority boost
        if (criteria.student_profile and criteria.prioritize_weak_areas and
            criteria.student_profile.weak_topics):
            # This would need more logic to check if content addresses weak topics
            adjustments += 1
        
        final_priority = min(5, max(1, base_priority + adjustments))
        return final_priority
    
    def _estimate_learning_impact(
        self, 
        content: ContentMetadata, 
        criteria: FilterCriteria,
        dimension_scores: Dict[str, float]
    ) -> float:
        """Estimate potential learning impact (0-1 scale)"""
        
        # Base impact from content quality and engagement
        base_impact = (content.quality_score / 10.0 + content.engagement_score) / 2
        
        # Adjust based on match quality
        match_multiplier = (
            dimension_scores.get('competency_match', 0.5) * 0.4 +
            dimension_scores.get('topic_relevance', 0.5) * 0.3 +
            dimension_scores.get('difficulty_match', 0.5) * 0.2 +
            dimension_scores.get('prerequisite_alignment', 0.5) * 0.1
        )
        
        # Effectiveness factor
        effectiveness_factor = content.effectiveness_score
        
        # Calculate final impact
        learning_impact = base_impact * match_multiplier * effectiveness_factor
        
        return min(1.0, max(0.0, learning_impact))
    
    def _apply_ranking_adjustments(
        self, 
        results: List[FilterResult], 
        criteria: FilterCriteria
    ) -> None:
        """Apply final ranking adjustments"""
        
        if not criteria.student_profile:
            return
        
        profile = criteria.student_profile
        
        # Boost content addressing weak topics
        if criteria.prioritize_weak_areas and profile.weak_topics:
            for result in results:
                content_topics = set([result.content_metadata.subject_hierarchy.topic])
                if content_topics.intersection(profile.weak_topics):
                    result.relevance_score = min(1.0, result.relevance_score + 0.1)
        
        # Penalize content for mastered topics if configured
        if criteria.exclude_mastered and profile.mastered_topics:
            for result in results:
                content_topics = set([result.content_metadata.subject_hierarchy.topic])
                if content_topics.intersection(profile.mastered_topics):
                    result.relevance_score *= 0.8  # 20% penalty
        
        # Re-sort after adjustments
        results.sort(key=lambda x: x.relevance_score, reverse=True)

# Utility functions
def create_filter_from_failed_question(
    question_data: Dict[str, Any],
    student_profile: Optional[StudentProfile] = None
) -> FilterCriteria:
    """Create filter criteria from a failed question"""
    
    # Extract information from question
    subject = question_data.get('subject', '')
    topic = question_data.get('topic', '')
    competency_str = question_data.get('competency', '')
    difficulty = question_data.get('difficulty', 5.0)
    
    # Map to ICFES competency
    competency_mapper = ICFESCompetencyMapper()
    competencies = competency_mapper.identify_competencies(
        question_data.get('text', ''), subject
    )
    
    # Create filter criteria
    criteria = FilterCriteria(
        competencies=competencies,
        subjects=[subject],
        topics=[topic],
        difficulty_range=(max(1, difficulty - 1), min(10, difficulty + 1)),
        duration_range=(5, 30),  # 5-30 minutes for remedial content
        min_quality_score=3.0,
        min_engagement_score=0.6,
        student_profile=student_profile,
        exclude_mastered=True,
        prioritize_weak_areas=True
    )
    
    return criteria

if __name__ == "__main__":
    # Example usage and testing
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # This would be replaced with actual database connection
    # engine = create_engine("postgresql://user:pass@localhost/db")
    # SessionLocal = sessionmaker(bind=engine)
    # db = SessionLocal()
    
    # For testing purposes, create a mock setup
    class MockSession:
        def execute(self, query, params=None):
            # Mock database response
            class MockResult:
                def fetchone(self):
                    return None
                def fetchall(self):
                    return []
            return MockResult()
    
    db = MockSession()
    
    # Initialize filter
    topic_filter = MultidimensionalTopicFilter(db)
    
    logger.info("Multi-dimensional Topic Filter initialized successfully!")
    logger.debug(f"Available competencies: {len(ICFESCompetency)}")
    logger.debug(f"Available cognitive levels: {len(CognitiveLevel)}")
    logger.debug(f"Dimension weights: {topic_filter.dimension_weights}")