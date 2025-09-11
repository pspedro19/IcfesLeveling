"""
PASO 10: Servicio de mapeo avanzado Preguntas-Videos
Implementa algoritmos de matching semántico y criterios multi-factoriales
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.sql import select

from app.models.question import Question
from app.models.youtube_catalog import YoutubeCatalog
from app.models.content_embeddings import ContentEmbeddings
from app.models.question_video_recommendations import QuestionVideoRecommendations, RecommendationMetrics
from app.models.icfes.study_topics_catalog import StudyTopicsCatalog
from app.models.user_answer import UserAnswer
from app.services.embedding_service import EmbeddingService
from app.core.database import get_db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionVideoMappingService:
    """
    Servicio principal para mapeo inteligente entre preguntas ICFES y videos de YouTube
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or EmbeddingService()
        
        # Configuración de criterios de matching
        self.scoring_weights = {
            'semantic_similarity': 0.50,    # 50% similitud semántica
            'difficulty_proximity': 0.20,   # 20% match de dificultad
            'exact_match': 0.15,            # 15% cobertura del error común
            'popularity': 0.15              # 15% popularidad/engagement
        }
        
        # Umbrales de calidad
        self.min_recommendation_threshold = 0.75
        self.high_confidence_threshold = 0.85
        self.semantic_similarity_threshold = 0.7
        
        # Parámetros de diversificación
        self.max_recommendations_per_question = 5
        self.max_same_topic_videos = 3
        
    async def generate_question_embeddings(
        self, 
        db: Session, 
        question: Question,
        force_regenerate: bool = False
    ) -> Dict[str, Optional[ContentEmbeddings]]:
        """
        Genera embeddings para una pregunta ICFES
        """
        logger.info(f"Generating embeddings for question {question.id}")
        
        embeddings = {}
        
        # Metadata de la pregunta
        metadata = {
            'content_uuid': question.id,
            'subject_area': getattr(question.subject, 'name', None) if hasattr(question, 'subject') else None,
            'topic': getattr(question.topic, 'name', None) if hasattr(question, 'topic') else None,
            'difficulty_level': self._categorize_difficulty(question.difficulty),
            'language': 'es'
        }
        
        # Texto principal de la pregunta
        question_text = self._extract_question_text(question)
        if question_text:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'icfes_question', question.id, 'question_text')
            
            embeddings['question_text'] = await self.embedding_service.create_content_embedding(
                db=db,
                content_type='icfes_question',
                content_id=question.id,
                embedding_type='question_text',
                source_text=question_text,
                **metadata
            )
        
        # Opciones de respuesta (para detectar errores comunes)
        options_text = self._extract_options_text(question)
        if options_text:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'icfes_question', question.id, 'options')
            
            embeddings['options'] = await self.embedding_service.create_content_embedding(
                db=db,
                content_type='icfes_question',
                content_id=question.id,
                embedding_type='options',
                source_text=options_text,
                **metadata
            )
        
        # Combined embedding (pregunta + contexto + opciones)
        combined_text = self._create_combined_question_text(question)
        if combined_text:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'icfes_question', question.id, 'combined')
            
            embeddings['combined'] = await self.embedding_service.create_content_embedding(
                db=db,
                content_type='icfes_question',
                content_id=question.id,
                embedding_type='combined',
                source_text=combined_text,
                **metadata
            )
        
        return embeddings
    
    def _extract_question_text(self, question: Question) -> str:
        """Extrae el texto principal de la pregunta"""
        parts = []
        
        if question.pregunta_texto:
            parts.append(question.pregunta_texto.strip())
        elif question.question_text:
            parts.append(question.question_text.strip())
        
        return " ".join(parts)
    
    def _extract_options_text(self, question: Question) -> str:
        """Extrae texto de todas las opciones para análisis de errores comunes"""
        options = []
        
        # Opciones individuales
        for option_letter in ['a', 'b', 'c', 'd']:
            option_text = getattr(question, f'opcion_{option_letter}_texto', None)
            if option_text:
                options.append(f"{option_letter.upper()}. {option_text.strip()}")
        
        # Fallback a JSON options
        if not options and question.options:
            if isinstance(question.options, dict):
                for key, value in question.options.items():
                    if isinstance(value, str):
                        options.append(f"{key.upper()}. {value.strip()}")
            elif isinstance(question.options, list):
                for i, option in enumerate(question.options):
                    letter = chr(65 + i)  # A, B, C, D
                    options.append(f"{letter}. {option.strip()}")
        
        return " | ".join(options)
    
    def _create_combined_question_text(self, question: Question) -> str:
        """Crea texto combinado de la pregunta para embedding comprehensivo"""
        parts = []
        
        # Texto principal con peso mayor
        question_text = self._extract_question_text(question)
        if question_text:
            parts.extend([question_text] * 3)  # Triple peso
        
        # Opciones con peso menor
        options_text = self._extract_options_text(question)
        if options_text:
            parts.append(options_text)
        
        # Contexto adicional si está disponible
        if hasattr(question, 'topic') and question.topic:
            parts.append(f"Tema: {question.topic.name}")
        
        if hasattr(question, 'subject') and question.subject:
            parts.append(f"Materia: {question.subject.name}")
        
        return " ".join(parts)
    
    def _categorize_difficulty(self, difficulty: int) -> str:
        """Categoriza la dificultad numérica en niveles"""
        if difficulty <= 2:
            return 'Básico'
        elif difficulty <= 4:
            return 'Intermedio'
        else:
            return 'Avanzado'
    
    def _deactivate_existing_embeddings(
        self, 
        db: Session, 
        content_type: str, 
        content_id: Any, 
        embedding_type: str
    ):
        """Desactiva embeddings existentes (soft delete)"""
        db.query(ContentEmbeddings).filter(
            and_(
                ContentEmbeddings.content_type == content_type,
                ContentEmbeddings.content_id == content_id,
                ContentEmbeddings.embedding_type == embedding_type
            )
        ).update({'is_active': 'false'})
        db.commit()
    
    async def calculate_semantic_similarity(
        self, 
        db: Session,
        question_embedding: ContentEmbeddings,
        video_embedding: ContentEmbeddings
    ) -> float:
        """
        Calcula la similaridad semántica entre pregunta y video usando embeddings
        """
        if not question_embedding or not video_embedding:
            return 0.0
        
        if not question_embedding.embedding_vector or not video_embedding.embedding_vector:
            return 0.0
        
        try:
            # Usar pgvector si está disponible
            if hasattr(ContentEmbeddings, '__table__') and 'embedding_vector' in ContentEmbeddings.__table__.columns:
                # Query optimizada con pgvector
                result = db.execute(
                    text("""
                        SELECT 1 - (q.embedding_vector <=> v.embedding_vector) as similarity
                        FROM content_embeddings q, content_embeddings v
                        WHERE q.id = :q_id AND v.id = :v_id
                    """),
                    {'q_id': question_embedding.id, 'v_id': video_embedding.id}
                ).fetchone()
                
                if result:
                    return float(result[0])
            
            # Fallback a cálculo manual
            return question_embedding.calculate_similarity(video_embedding.embedding_vector)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def calculate_exact_match_score(
        self, 
        db: Session,
        question: Question, 
        video: YoutubeCatalog
    ) -> float:
        """
        Calcula score de match exacto basado en subject_id y topic_id
        """
        score = 0.0
        
        # Match de materia/área
        if (hasattr(question, 'subject') and question.subject and 
            video.area_evaluada and 
            question.subject.name.lower() in video.area_evaluada.lower()):
            score += 0.6
        
        # Match de tema
        if (hasattr(question, 'topic') and question.topic and 
            video.tema_principal and 
            question.topic.name.lower() in video.tema_principal.lower()):
            score += 0.4
        
        # Bonus por match exacto de ambos
        if score >= 1.0:
            score = 1.0
        
        return score
    
    def calculate_difficulty_proximity_score(
        self, 
        question: Question, 
        video: YoutubeCatalog
    ) -> float:
        """
        Calcula proximidad de dificultad usando parámetros theta de IRT
        """
        try:
            # Obtener theta de la pregunta (dificultad IRT)
            question_theta = getattr(question, 'theta', None) or (question.difficulty / 5.0 - 1.0)
            
            # Estimar theta del video basado en su nivel
            video_theta = self._estimate_video_theta(video)
            
            if question_theta is None or video_theta is None:
                return 0.5  # Score neutral si no hay datos
            
            # Calcular proximidad (menor diferencia = mayor score)
            theta_diff = abs(question_theta - video_theta)
            
            # Función gaussiana para scoring: mejor score cuando están cerca
            proximity_score = np.exp(-0.5 * (theta_diff / 0.5) ** 2)
            
            return float(proximity_score)
            
        except Exception as e:
            logger.error(f"Error calculating difficulty proximity: {e}")
            return 0.5
    
    def _estimate_video_theta(self, video: YoutubeCatalog) -> Optional[float]:
        """Estima el parámetro theta del video basado en metadatos"""
        if not video.nivel:
            return None
        
        # Mapeo de nivel a theta aproximado
        nivel_mapping = {
            'Básico': -0.5,
            'Intermedio': 0.0, 
            'Avanzado': 0.5,
            'Fundamental': -0.8,
            'Medio': -0.2,
            'Superior': 0.8
        }
        
        return nivel_mapping.get(video.nivel, 0.0)
    
    def calculate_popularity_score(self, video: YoutubeCatalog) -> float:
        """
        Calcula score de popularidad basado en métricas de engagement
        """
        try:
            score = 0.0
            
            # Views (normalizado)
            if video.views:
                # Log scale para views (10K+ views = buen score)
                view_score = min(1.0, np.log10(max(1, video.views)) / 5.0)
                score += view_score * 0.4
            
            # Likes ratio
            if video.likes and video.views and video.views > 0:
                like_ratio = video.likes / video.views
                # Buenos videos tienen ~1-5% like ratio
                like_score = min(1.0, like_ratio * 100)
                score += like_score * 0.3
            
            # Duración apropiada (5-20 minutos ideal para contenido educativo)
            if video.duration_seconds:
                duration_minutes = video.duration_seconds / 60
                if 5 <= duration_minutes <= 20:
                    score += 0.3
                elif 3 <= duration_minutes <= 30:
                    score += 0.15
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating popularity score: {e}")
            return 0.5
    
    async def analyze_common_errors(
        self, 
        db: Session, 
        question: Question
    ) -> Dict[str, Any]:
        """
        Analiza patrones de errores comunes para la pregunta
        """
        try:
            # Query para obtener respuestas de estudiantes
            error_analysis = db.query(
                UserAnswer.selected_option,
                func.count(UserAnswer.id).label('count')
            ).filter(
                UserAnswer.question_id == question.id,
                UserAnswer.selected_option != question.respuesta_correcta
            ).group_by(UserAnswer.selected_option).all()
            
            total_wrong_answers = sum([r.count for r in error_analysis])
            
            if total_wrong_answers == 0:
                return {'dominant_distractor': None, 'error_rate': 0.0, 'patterns': {}}
            
            # Encontrar distractor dominante
            dominant_distractor = max(error_analysis, key=lambda x: x.count)
            
            # Calcular patrones
            patterns = {}
            for result in error_analysis:
                patterns[result.selected_option] = {
                    'count': result.count,
                    'percentage': (result.count / total_wrong_answers) * 100
                }
            
            return {
                'dominant_distractor': dominant_distractor.selected_option,
                'error_rate': total_wrong_answers,
                'patterns': patterns,
                'needs_remediation': total_wrong_answers > 10  # Umbral para intervención
            }
            
        except Exception as e:
            logger.error(f"Error analyzing common errors: {e}")
            return {'dominant_distractor': None, 'error_rate': 0.0, 'patterns': {}}
    
    async def generate_recommendations_for_question(
        self, 
        db: Session,
        question: Question,
        max_recommendations: int = 5,
        force_regenerate: bool = False
    ) -> List[QuestionVideoRecommendations]:
        """
        Genera recomendaciones completas para una pregunta específica
        """
        logger.info(f"Generating recommendations for question {question.id}")
        
        # 1. Generar embeddings de la pregunta si no existen
        question_embeddings = await self.generate_question_embeddings(db, question, force_regenerate)
        
        if not any(question_embeddings.values()):
            logger.warning(f"No embeddings generated for question {question.id}")
            return []
        
        # 2. Obtener videos candidatos
        candidate_videos = self._get_candidate_videos(db, question)
        
        if not candidate_videos:
            logger.warning(f"No candidate videos found for question {question.id}")
            return []
        
        # 3. Analizar errores comunes
        error_analysis = await self.analyze_common_errors(db, question)
        
        # 4. Calcular scores para cada video candidato
        recommendations = []
        
        for video in candidate_videos:
            try:
                recommendation = await self._create_recommendation(
                    db, question, video, question_embeddings, error_analysis
                )
                
                if recommendation and recommendation.should_recommend(self.min_recommendation_threshold):
                    recommendations.append(recommendation)
                    
            except Exception as e:
                logger.error(f"Error creating recommendation for video {video.id}: {e}")
                continue
        
        # 5. Ordenar por score y aplicar diversificación
        recommendations.sort(key=lambda x: x.total_score, reverse=True)
        diversified_recommendations = self._apply_diversification(recommendations, max_recommendations)
        
        # 6. Guardar en base de datos
        for rec in diversified_recommendations:
            try:
                db.add(rec)
                db.commit()
                db.refresh(rec)
            except Exception as e:
                db.rollback()
                logger.error(f"Error saving recommendation: {e}")
        
        logger.info(f"Generated {len(diversified_recommendations)} recommendations for question {question.id}")
        return diversified_recommendations
    
    def _get_candidate_videos(self, db: Session, question: Question) -> List[YoutubeCatalog]:
        """
        Obtiene videos candidatos basados en filtros básicos
        """
        query = db.query(YoutubeCatalog).filter(
            YoutubeCatalog.has_embeddings == True,
            YoutubeCatalog.status == 'active'
        )
        
        # Filtrar por área evaluada si está disponible
        if hasattr(question, 'subject') and question.subject:
            subject_name = question.subject.name
            query = query.filter(
                or_(
                    YoutubeCatalog.area_evaluada.ilike(f'%{subject_name}%'),
                    YoutubeCatalog.tema_principal.ilike(f'%{subject_name}%')
                )
            )
        
        # Limitar a videos de calidad mínima
        query = query.filter(
            or_(
                YoutubeCatalog.views >= 1000,
                YoutubeCatalog.likes >= 10
            )
        )
        
        return query.limit(100).all()  # Limitar candidatos para eficiencia
    
    async def _create_recommendation(
        self, 
        db: Session,
        question: Question, 
        video: YoutubeCatalog,
        question_embeddings: Dict[str, ContentEmbeddings],
        error_analysis: Dict[str, Any]
    ) -> Optional[QuestionVideoRecommendations]:
        """
        Crea una recomendación individual con todos los scores calculados
        """
        try:
            # 1. Obtener embedding del video
            video_embedding = db.query(ContentEmbeddings).filter(
                and_(
                    ContentEmbeddings.content_type == 'youtube_video',
                    ContentEmbeddings.content_id == video.id,
                    ContentEmbeddings.embedding_type == 'combined',
                    ContentEmbeddings.is_active == 'true'
                )
            ).first()
            
            if not video_embedding:
                return None
            
            # 2. Calcular scores individuales
            exact_match_score = self.calculate_exact_match_score(db, question, video)
            popularity_score = self.calculate_popularity_score(video)
            difficulty_score = self.calculate_difficulty_proximity_score(question, video)
            
            # 3. Calcular similaridad semántica
            semantic_score = 0.0
            if question_embeddings.get('combined'):
                semantic_score = await self.calculate_semantic_similarity(
                    db, question_embeddings['combined'], video_embedding
                )
            
            # 4. Determinar tipo de recomendación
            recommendation_type = self._determine_recommendation_type(
                exact_match_score, semantic_score, error_analysis
            )
            
            # 5. Crear objeto de recomendación
            recommendation = QuestionVideoRecommendations(
                question_id=question.id,
                video_id=video.id,
                exact_match_score=exact_match_score,
                semantic_similarity_score=semantic_score,
                difficulty_proximity_score=difficulty_score,
                popularity_score=popularity_score,
                recommendation_type=recommendation_type,
                embedding_similarity=semantic_score,
                topic_alignment=exact_match_score,
                difficulty_gap=abs(difficulty_score - 0.5) * 2,  # Convertir a gap
                targets_common_error=error_analysis.get('needs_remediation', False),
                error_pattern_addressed=self._get_error_pattern(video, error_analysis),
                distractor_focus=error_analysis.get('dominant_distractor'),
                algorithm_version='v1.0',
                processing_metadata={
                    'processing_timestamp': datetime.utcnow().isoformat(),
                    'question_embeddings_types': list(question_embeddings.keys()),
                    'video_embedding_type': video_embedding.embedding_type,
                    'error_analysis': error_analysis
                }
            )
            
            # 6. Calcular score total
            recommendation.update_score_components(
                exact_match_score, semantic_score, difficulty_score, popularity_score
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")
            return None
    
    def _determine_recommendation_type(
        self, 
        exact_match: float, 
        semantic_similarity: float, 
        error_analysis: Dict[str, Any]
    ) -> str:
        """Determina el tipo de recomendación basado en los scores"""
        if error_analysis.get('needs_remediation', False):
            return 'error_remediation'
        elif exact_match >= 0.8:
            return 'concept_review'
        elif semantic_similarity >= 0.7:
            return 'skill_building'
        else:
            return 'concept_review'
    
    def _get_error_pattern(self, video: YoutubeCatalog, error_analysis: Dict[str, Any]) -> Optional[str]:
        """Identifica si el video aborda patrones de error específicos"""
        # Lógica para determinar si el video aborda errores comunes
        # Esto requeriría análisis más avanzado del contenido del video
        
        if error_analysis.get('needs_remediation', False):
            # Categorías de errores comunes
            if 'procedural' in (video.description or '').lower():
                return 'procedural_error'
            elif 'conceptual' in (video.description or '').lower():
                return 'conceptual_error'
            else:
                return 'general_error'
        
        return None
    
    def _apply_diversification(
        self, 
        recommendations: List[QuestionVideoRecommendations], 
        max_count: int
    ) -> List[QuestionVideoRecommendations]:
        """
        Aplica diversificación para evitar over-recommendation del mismo tipo de contenido
        """
        if len(recommendations) <= max_count:
            return recommendations
        
        # Diversificar por tipo de recomendación y temas
        diversified = []
        type_counts = {}
        topic_counts = {}
        
        for rec in recommendations:
            # Limitar por tipo
            if type_counts.get(rec.recommendation_type, 0) >= 2:
                continue
            
            # Limitar por tema similar (requiere info del video)
            # Este es un placeholder - requeriría lógica más sofisticada
            
            diversified.append(rec)
            type_counts[rec.recommendation_type] = type_counts.get(rec.recommendation_type, 0) + 1
            
            if len(diversified) >= max_count:
                break
        
        return diversified
    
    async def batch_generate_recommendations(
        self, 
        db: Session,
        batch_size: int = 10,
        max_questions: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Genera recomendaciones en lotes para múltiples preguntas
        """
        logger.info(f"Starting batch recommendation generation")
        
        # Obtener preguntas que necesitan recomendaciones
        query = db.query(Question)
        
        if max_questions:
            query = query.limit(max_questions)
        
        questions = query.all()
        total_questions = len(questions)
        
        logger.info(f"Processing {total_questions} questions")
        
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_recommendations': 0
        }
        
        # Procesar en lotes
        for i in range(0, total_questions, batch_size):
            batch = questions[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_questions-1)//batch_size + 1}")
            
            for question in batch:
                try:
                    recommendations = await self.generate_recommendations_for_question(db, question)
                    
                    if recommendations:
                        stats['successful'] += 1
                        stats['total_recommendations'] += len(recommendations)
                        logger.info(f"✓ Generated {len(recommendations)} recommendations for question {question.id}")
                    else:
                        stats['failed'] += 1
                        logger.warning(f"✗ No recommendations generated for question {question.id}")
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"Error processing question {question.id}: {e}")
            
            # Pausa entre lotes
            if i + batch_size < total_questions:
                await asyncio.sleep(1)
        
        logger.info(f"Batch processing completed: {stats}")
        return stats