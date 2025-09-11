"""
Sistema Integrado de Recomendaciones Maestro
Orquesta todos los servicios de recomendaciones y análisis inteligente
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc

from app.services.embedding_service import EmbeddingService
from app.services.question_video_mapping_service import QuestionVideoMappingService
from app.services.weakness_analysis_service import WeaknessAnalysisService
from app.services.recommendation_scoring_service import RecommendationScoringService
from app.services.yaml_plan_generator_service import YamlPlanGeneratorService
from app.models.user import User
from app.models.question import Question
from app.models.youtube_catalog import YoutubeCatalog
from app.models.question_video_recommendations import QuestionVideoRecommendations
from app.core.database import get_db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationPipeline(Enum):
    """Pipeline de procesamiento de recomendaciones"""
    EMBEDDINGS_GENERATION = "embeddings_generation"
    WEAKNESS_ANALYSIS = "weakness_analysis"
    QUESTION_VIDEO_MAPPING = "question_video_mapping"
    SCORING_OPTIMIZATION = "scoring_optimization"
    YAML_PLAN_GENERATION = "yaml_plan_generation"
    SYSTEM_VALIDATION = "system_validation"

@dataclass
class PipelineStatus:
    """Estado del pipeline de procesamiento"""
    stage: RecommendationPipeline
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress_percentage: float
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class RecommendationSystemMetrics:
    """Métricas del sistema de recomendaciones"""
    total_students_processed: int
    total_videos_analyzed: int
    total_embeddings_generated: int
    total_recommendations_created: int
    total_yaml_plans_generated: int
    average_processing_time_seconds: float
    system_accuracy_score: float
    coverage_percentage: float
    last_processing_date: datetime

class MasterRecommendationService:
    """
    Servicio maestro que orquesta todo el sistema de recomendaciones
    """
    
    def __init__(self):
        # Inicializar servicios dependientes
        self.embedding_service = EmbeddingService()
        self.mapping_service = QuestionVideoMappingService(self.embedding_service)
        self.weakness_service = WeaknessAnalysisService()
        self.scoring_service = RecommendationScoringService()
        self.yaml_service = YamlPlanGeneratorService()
        
        # Configuración del sistema
        self.config = {
            'batch_size': 10,
            'max_concurrent_processes': 5,
            'recommendation_refresh_hours': 24,
            'weakness_analysis_refresh_hours': 1,
            'yaml_generation_schedule': 'weekly',
            'quality_threshold': 0.85
        }
        
        # Estado del sistema
        self.pipeline_status = {}
        self.system_metrics = None
        
    async def run_complete_recommendation_pipeline(
        self,
        db: Session,
        target_students: Optional[List[str]] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de recomendaciones
        """
        try:
            start_time = datetime.utcnow()
            logger.info("Starting complete recommendation pipeline")
            
            # Inicializar estado del pipeline
            pipeline_id = f"pipeline_{start_time.strftime('%Y%m%d_%H%M%S')}"
            self.pipeline_status[pipeline_id] = {}
            
            results = {
                'pipeline_id': pipeline_id,
                'start_time': start_time.isoformat(),
                'stages': {},
                'overall_status': 'running'
            }
            
            # ETAPA 1: Generación de embeddings
            stage_result = await self._run_embeddings_generation(
                db, pipeline_id, force_regenerate
            )
            results['stages']['embeddings_generation'] = stage_result
            
            if stage_result['status'] != 'completed':
                results['overall_status'] = 'failed'
                return results
            
            # ETAPA 2: Análisis de debilidades
            stage_result = await self._run_weakness_analysis(
                db, pipeline_id, target_students
            )
            results['stages']['weakness_analysis'] = stage_result
            
            # ETAPA 3: Mapeo pregunta-video
            stage_result = await self._run_question_video_mapping(
                db, pipeline_id, target_students, force_regenerate
            )
            results['stages']['question_video_mapping'] = stage_result
            
            # ETAPA 4: Optimización de scoring
            stage_result = await self._run_scoring_optimization(
                db, pipeline_id
            )
            results['stages']['scoring_optimization'] = stage_result
            
            # ETAPA 5: Generación de planes YAML
            stage_result = await self._run_yaml_plan_generation(
                db, pipeline_id, target_students, force_regenerate
            )
            results['stages']['yaml_plan_generation'] = stage_result
            
            # ETAPA 6: Validación del sistema
            stage_result = await self._run_system_validation(
                db, pipeline_id
            )
            results['stages']['system_validation'] = stage_result
            
            # Calcular métricas finales
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            results.update({
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'overall_status': 'completed',
                'final_metrics': await self._calculate_system_metrics(db)
            })
            
            logger.info(f"Complete recommendation pipeline completed in {duration:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error in complete recommendation pipeline: {e}")
            results['overall_status'] = 'failed'
            results['error'] = str(e)
            return results
    
    async def _run_embeddings_generation(
        self,
        db: Session,
        pipeline_id: str,
        force_regenerate: bool
    ) -> Dict[str, Any]:
        """Ejecuta la etapa de generación de embeddings"""
        try:
            logger.info("Running embeddings generation stage")
            stage_start = datetime.utcnow()
            
            self._update_pipeline_status(
                pipeline_id, 
                RecommendationPipeline.EMBEDDINGS_GENERATION,
                'running',
                0.0,
                stage_start
            )
            
            # Generar embeddings para videos
            video_stats = await self.embedding_service.batch_process_videos(
                db, 
                batch_size=self.config['batch_size'],
                filter_processed=not force_regenerate
            )
            
            # Generar embeddings para preguntas (muestreo)
            questions = db.query(Question).limit(100).all()  # Procesar 100 preguntas como prueba
            question_stats = {'processed': 0, 'successful': 0, 'failed': 0}
            
            for question in questions:
                try:
                    embeddings = await self.mapping_service.generate_question_embeddings(
                        db, question, force_regenerate
                    )
                    if any(embeddings.values()):
                        question_stats['successful'] += 1
                    else:
                        question_stats['failed'] += 1
                    question_stats['processed'] += 1
                except Exception as e:
                    question_stats['failed'] += 1
                    question_stats['processed'] += 1
                    logger.error(f"Error processing question {question.id}: {e}")
            
            stage_end = datetime.utcnow()
            duration = (stage_end - stage_start).total_seconds()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.EMBEDDINGS_GENERATION,
                'completed',
                100.0,
                stage_start,
                stage_end
            )
            
            return {
                'status': 'completed',
                'duration_seconds': duration,
                'video_stats': video_stats,
                'question_stats': question_stats,
                'total_embeddings': video_stats.get('successful', 0) + question_stats['successful']
            }
            
        except Exception as e:
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.EMBEDDINGS_GENERATION,
                'failed',
                0.0,
                None,
                None,
                str(e)
            )
            logger.error(f"Error in embeddings generation stage: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_weakness_analysis(
        self,
        db: Session,
        pipeline_id: str,
        target_students: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Ejecuta la etapa de análisis de debilidades"""
        try:
            logger.info("Running weakness analysis stage")
            stage_start = datetime.utcnow()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.WEAKNESS_ANALYSIS,
                'running',
                0.0,
                stage_start
            )
            
            # Refresh de análisis de debilidades
            refresh_result = await self.weakness_service.refresh_weakness_analysis(db)
            
            # Generar alertas automáticas
            alerts_generated = await self.weakness_service.generate_weakness_alerts(db)
            
            # Obtener resumen de debilidades críticas
            critical_summary = await self.weakness_service.get_critical_weaknesses_summary(db)
            
            stage_end = datetime.utcnow()
            duration = (stage_end - stage_start).total_seconds()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.WEAKNESS_ANALYSIS,
                'completed',
                100.0,
                stage_start,
                stage_end
            )
            
            return {
                'status': 'completed',
                'duration_seconds': duration,
                'refresh_stats': refresh_result.get('statistics', {}),
                'alerts_generated': alerts_generated,
                'critical_summary': critical_summary
            }
            
        except Exception as e:
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.WEAKNESS_ANALYSIS,
                'failed',
                0.0,
                None,
                None,
                str(e)
            )
            logger.error(f"Error in weakness analysis stage: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_question_video_mapping(
        self,
        db: Session,
        pipeline_id: str,
        target_students: Optional[List[str]],
        force_regenerate: bool
    ) -> Dict[str, Any]:
        """Ejecuta la etapa de mapeo pregunta-video"""
        try:
            logger.info("Running question-video mapping stage")
            stage_start = datetime.utcnow()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.QUESTION_VIDEO_MAPPING,
                'running',
                0.0,
                stage_start
            )
            
            # Generar recomendaciones para preguntas
            mapping_stats = await self.mapping_service.batch_generate_recommendations(
                db,
                batch_size=self.config['batch_size'],
                max_questions=200  # Procesar 200 preguntas como prueba
            )
            
            stage_end = datetime.utcnow()
            duration = (stage_end - stage_start).total_seconds()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.QUESTION_VIDEO_MAPPING,
                'completed',
                100.0,
                stage_start,
                stage_end
            )
            
            return {
                'status': 'completed',
                'duration_seconds': duration,
                'mapping_stats': mapping_stats
            }
            
        except Exception as e:
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.QUESTION_VIDEO_MAPPING,
                'failed',
                0.0,
                None,
                None,
                str(e)
            )
            logger.error(f"Error in question-video mapping stage: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_scoring_optimization(
        self,
        db: Session,
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Ejecuta la etapa de optimización de scoring"""
        try:
            logger.info("Running scoring optimization stage")
            stage_start = datetime.utcnow()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.SCORING_OPTIMIZATION,
                'running',
                0.0,
                stage_start
            )
            
            # Obtener recomendaciones existentes para análisis
            recommendations = db.query(QuestionVideoRecommendations).filter(
                QuestionVideoRecommendations.is_active == True
            ).limit(1000).all()
            
            # Calcular analytics del scoring
            scoring_analytics = self.scoring_service.get_scoring_analytics([
                # Convertir a objetos RecommendationScore para análisis
                # En implementación real se cargarían los scores completos
            ])
            
            # Identificar recomendaciones de baja calidad
            low_quality_count = len([r for r in recommendations if r.total_score < 0.6])
            
            # Estadísticas de optimización
            optimization_stats = {
                'total_recommendations_analyzed': len(recommendations),
                'low_quality_recommendations': low_quality_count,
                'average_score': sum(r.total_score for r in recommendations) / len(recommendations) if recommendations else 0,
                'score_distribution': self._calculate_score_distribution(recommendations)
            }
            
            stage_end = datetime.utcnow()
            duration = (stage_end - stage_start).total_seconds()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.SCORING_OPTIMIZATION,
                'completed',
                100.0,
                stage_start,
                stage_end
            )
            
            return {
                'status': 'completed',
                'duration_seconds': duration,
                'optimization_stats': optimization_stats,
                'scoring_analytics': scoring_analytics
            }
            
        except Exception as e:
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.SCORING_OPTIMIZATION,
                'failed',
                0.0,
                None,
                None,
                str(e)
            )
            logger.error(f"Error in scoring optimization stage: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_yaml_plan_generation(
        self,
        db: Session,
        pipeline_id: str,
        target_students: Optional[List[str]],
        force_regenerate: bool
    ) -> Dict[str, Any]:
        """Ejecuta la etapa de generación de planes YAML"""
        try:
            logger.info("Running YAML plan generation stage")
            stage_start = datetime.utcnow()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.YAML_PLAN_GENERATION,
                'running',
                0.0,
                stage_start
            )
            
            # Obtener estudiantes objetivo
            if target_students:
                students = db.query(User).filter(User.id.in_(target_students)).all()
            else:
                # Generar para estudiantes activos recientes
                students = db.query(User).join(
                    # Join con user_answers para encontrar estudiantes activos
                ).limit(20).all()  # Procesar 20 estudiantes como prueba
            
            generation_stats = {
                'total_students': len(students),
                'successful_generations': 0,
                'failed_generations': 0,
                'plans_created': []
            }
            
            # Generar planes para cada estudiante
            for student in students:
                try:
                    plan_result = await self.yaml_service.generate_monthly_plan(
                        db, str(student.id), force_regenerate=force_regenerate
                    )
                    
                    if plan_result['status'] == 'success':
                        generation_stats['successful_generations'] += 1
                        generation_stats['plans_created'].append({
                            'student_id': str(student.id),
                            'plan_path': plan_result['plan_file_path'],
                            'summary': plan_result['plan_summary']
                        })
                    else:
                        generation_stats['failed_generations'] += 1
                        
                except Exception as e:
                    generation_stats['failed_generations'] += 1
                    logger.error(f"Error generating plan for student {student.id}: {e}")
            
            stage_end = datetime.utcnow()
            duration = (stage_end - stage_start).total_seconds()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.YAML_PLAN_GENERATION,
                'completed',
                100.0,
                stage_start,
                stage_end
            )
            
            return {
                'status': 'completed',
                'duration_seconds': duration,
                'generation_stats': generation_stats
            }
            
        except Exception as e:
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.YAML_PLAN_GENERATION,
                'failed',
                0.0,
                None,
                None,
                str(e)
            )
            logger.error(f"Error in YAML plan generation stage: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_system_validation(
        self,
        db: Session,
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Ejecuta la etapa de validación del sistema"""
        try:
            logger.info("Running system validation stage")
            stage_start = datetime.utcnow()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.SYSTEM_VALIDATION,
                'running',
                0.0,
                stage_start
            )
            
            validation_results = {
                'embeddings_health': await self._validate_embeddings_health(db),
                'recommendations_quality': await self._validate_recommendations_quality(db),
                'weakness_analysis_coverage': await self._validate_weakness_analysis_coverage(db),
                'yaml_plans_integrity': await self._validate_yaml_plans_integrity(),
                'system_performance': await self._validate_system_performance(db)
            }
            
            # Calcular score de salud general del sistema
            health_scores = [result.get('score', 0) for result in validation_results.values()]
            overall_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
            
            validation_results['overall_health_score'] = overall_health_score
            validation_results['system_status'] = 'healthy' if overall_health_score >= 0.8 else 'needs_attention'
            
            stage_end = datetime.utcnow()
            duration = (stage_end - stage_start).total_seconds()
            
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.SYSTEM_VALIDATION,
                'completed',
                100.0,
                stage_start,
                stage_end
            )
            
            return {
                'status': 'completed',
                'duration_seconds': duration,
                'validation_results': validation_results
            }
            
        except Exception as e:
            self._update_pipeline_status(
                pipeline_id,
                RecommendationPipeline.SYSTEM_VALIDATION,
                'failed',
                0.0,
                None,
                None,
                str(e)
            )
            logger.error(f"Error in system validation stage: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _update_pipeline_status(
        self,
        pipeline_id: str,
        stage: RecommendationPipeline,
        status: str,
        progress: float,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Actualiza el estado del pipeline"""
        if pipeline_id not in self.pipeline_status:
            self.pipeline_status[pipeline_id] = {}
        
        self.pipeline_status[pipeline_id][stage.value] = PipelineStatus(
            stage=stage,
            status=status,
            progress_percentage=progress,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            metadata=metadata or {}
        )
    
    def _calculate_score_distribution(self, recommendations: List[QuestionVideoRecommendations]) -> Dict[str, int]:
        """Calcula distribución de scores"""
        distribution = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }
        
        for rec in recommendations:
            score = rec.total_score
            if score < 0.2:
                distribution['0.0-0.2'] += 1
            elif score < 0.4:
                distribution['0.2-0.4'] += 1
            elif score < 0.6:
                distribution['0.4-0.6'] += 1
            elif score < 0.8:
                distribution['0.6-0.8'] += 1
            else:
                distribution['0.8-1.0'] += 1
        
        return distribution
    
    async def _validate_embeddings_health(self, db: Session) -> Dict[str, Any]:
        """Valida la salud de los embeddings"""
        try:
            # Contar embeddings por tipo
            from app.models.content_embeddings import ContentEmbeddings
            
            total_embeddings = db.query(ContentEmbeddings).filter(
                ContentEmbeddings.is_active == 'true'
            ).count()
            
            video_embeddings = db.query(ContentEmbeddings).filter(
                and_(
                    ContentEmbeddings.content_type == 'youtube_video',
                    ContentEmbeddings.is_active == 'true'
                )
            ).count()
            
            question_embeddings = db.query(ContentEmbeddings).filter(
                and_(
                    ContentEmbeddings.content_type == 'icfes_question',
                    ContentEmbeddings.is_active == 'true'
                )
            ).count()
            
            # Calcular score de salud basado en cobertura
            total_videos = db.query(YoutubeCatalog).filter(
                YoutubeCatalog.status == 'active'
            ).count()
            
            video_coverage = (video_embeddings / total_videos) if total_videos > 0 else 0
            health_score = min(1.0, video_coverage)
            
            return {
                'score': health_score,
                'total_embeddings': total_embeddings,
                'video_embeddings': video_embeddings,
                'question_embeddings': question_embeddings,
                'video_coverage_percentage': round(video_coverage * 100, 2),
                'status': 'healthy' if health_score >= 0.8 else 'needs_improvement'
            }
            
        except Exception as e:
            logger.error(f"Error validating embeddings health: {e}")
            return {'score': 0.0, 'status': 'error', 'error': str(e)}
    
    async def _validate_recommendations_quality(self, db: Session) -> Dict[str, Any]:
        """Valida la calidad de las recomendaciones"""
        try:
            # Obtener estadísticas de recomendaciones
            total_recs = db.query(QuestionVideoRecommendations).filter(
                QuestionVideoRecommendations.is_active == True
            ).count()
            
            high_quality_recs = db.query(QuestionVideoRecommendations).filter(
                and_(
                    QuestionVideoRecommendations.is_active == True,
                    QuestionVideoRecommendations.total_score >= 0.75
                )
            ).count()
            
            quality_ratio = (high_quality_recs / total_recs) if total_recs > 0 else 0
            
            return {
                'score': quality_ratio,
                'total_recommendations': total_recs,
                'high_quality_recommendations': high_quality_recs,
                'quality_percentage': round(quality_ratio * 100, 2),
                'status': 'good' if quality_ratio >= 0.7 else 'needs_improvement'
            }
            
        except Exception as e:
            logger.error(f"Error validating recommendations quality: {e}")
            return {'score': 0.0, 'status': 'error', 'error': str(e)}
    
    async def _validate_weakness_analysis_coverage(self, db: Session) -> Dict[str, Any]:
        """Valida la cobertura del análisis de debilidades"""
        try:
            # Verificar que la vista materializada esté actualizada
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_weaknesses,
                    COUNT(DISTINCT student_id) as students_with_weaknesses,
                    MAX(analysis_timestamp) as last_analysis,
                    AVG(intervention_priority_score) as avg_priority_score
                FROM vw_student_weak_topics
            """)).fetchone()
            
            # Calcular freshness de los datos
            if result and result.last_analysis:
                time_since_analysis = datetime.utcnow() - result.last_analysis
                freshness_hours = time_since_analysis.total_seconds() / 3600
                freshness_score = max(0, 1 - (freshness_hours / 24))  # Penalizar datos > 24h
            else:
                freshness_score = 0
            
            return {
                'score': freshness_score,
                'total_weaknesses': result.total_weaknesses if result else 0,
                'students_covered': result.students_with_weaknesses if result else 0,
                'last_analysis': result.last_analysis.isoformat() if result and result.last_analysis else None,
                'avg_priority_score': float(result.avg_priority_score) if result and result.avg_priority_score else 0,
                'data_freshness_hours': round(time_since_analysis.total_seconds() / 3600, 2) if result and result.last_analysis else None,
                'status': 'current' if freshness_score >= 0.8 else 'stale'
            }
            
        except Exception as e:
            logger.error(f"Error validating weakness analysis coverage: {e}")
            return {'score': 0.0, 'status': 'error', 'error': str(e)}
    
    async def _validate_yaml_plans_integrity(self) -> Dict[str, Any]:
        """Valida la integridad de los planes YAML"""
        try:
            import yaml
            from pathlib import Path
            
            plans_path = Path("plans/generated")
            if not plans_path.exists():
                return {'score': 0.0, 'status': 'no_plans_directory'}
            
            total_plans = 0
            valid_plans = 0
            
            for plan_file in plans_path.glob("rec_plan_*.yml"):
                total_plans += 1
                try:
                    with open(plan_file, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f.read())
                    valid_plans += 1
                except:
                    pass
            
            validity_ratio = (valid_plans / total_plans) if total_plans > 0 else 1.0
            
            return {
                'score': validity_ratio,
                'total_plans': total_plans,
                'valid_plans': valid_plans,
                'validity_percentage': round(validity_ratio * 100, 2),
                'status': 'good' if validity_ratio >= 0.95 else 'has_issues'
            }
            
        except Exception as e:
            logger.error(f"Error validating YAML plans integrity: {e}")
            return {'score': 0.0, 'status': 'error', 'error': str(e)}
    
    async def _validate_system_performance(self, db: Session) -> Dict[str, Any]:
        """Valida el rendimiento general del sistema"""
        try:
            # Métricas de rendimiento básicas
            start_time = datetime.utcnow()
            
            # Test de consulta de embeddings
            db.execute(text("SELECT COUNT(*) FROM content_embeddings WHERE is_active = 'true'")).fetchone()
            
            # Test de consulta de recomendaciones
            db.execute(text("SELECT COUNT(*) FROM question_video_recommendations WHERE is_active = true")).fetchone()
            
            # Test de vista materializada
            db.execute(text("SELECT COUNT(*) FROM vw_student_weak_topics")).fetchone()
            
            query_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Calcular score de rendimiento
            performance_score = max(0, min(1.0, 1 - (query_time / 10)))  # Penalizar si toma >10s
            
            return {
                'score': performance_score,
                'query_response_time_seconds': round(query_time, 3),
                'performance_level': 'excellent' if performance_score >= 0.9 else 'good' if performance_score >= 0.7 else 'slow',
                'status': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Error validating system performance: {e}")
            return {'score': 0.0, 'status': 'error', 'error': str(e)}
    
    async def _calculate_system_metrics(self, db: Session) -> RecommendationSystemMetrics:
        """Calcula métricas generales del sistema"""
        try:
            # Contar elementos del sistema
            total_students = db.query(User).count()
            total_videos = db.query(YoutubeCatalog).count()
            
            from app.models.content_embeddings import ContentEmbeddings
            total_embeddings = db.query(ContentEmbeddings).filter(
                ContentEmbeddings.is_active == 'true'
            ).count()
            
            total_recommendations = db.query(QuestionVideoRecommendations).filter(
                QuestionVideoRecommendations.is_active == True
            ).count()
            
            # Calcular métricas de calidad
            if total_recommendations > 0:
                avg_score = db.query(func.avg(QuestionVideoRecommendations.total_score)).filter(
                    QuestionVideoRecommendations.is_active == True
                ).scalar() or 0
                
                high_quality_count = db.query(QuestionVideoRecommendations).filter(
                    and_(
                        QuestionVideoRecommendations.is_active == True,
                        QuestionVideoRecommendations.total_score >= 0.75
                    )
                ).count()
                
                coverage_percentage = (high_quality_count / total_recommendations) * 100
            else:
                avg_score = 0
                coverage_percentage = 0
            
            return RecommendationSystemMetrics(
                total_students_processed=total_students,
                total_videos_analyzed=total_videos,
                total_embeddings_generated=total_embeddings,
                total_recommendations_created=total_recommendations,
                total_yaml_plans_generated=0,  # Se actualizaría en implementación real
                average_processing_time_seconds=0,  # Se calcularía basado en logs
                system_accuracy_score=float(avg_score),
                coverage_percentage=coverage_percentage,
                last_processing_date=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating system metrics: {e}")
            return RecommendationSystemMetrics(
                total_students_processed=0,
                total_videos_analyzed=0,
                total_embeddings_generated=0,
                total_recommendations_created=0,
                total_yaml_plans_generated=0,
                average_processing_time_seconds=0,
                system_accuracy_score=0.0,
                coverage_percentage=0.0,
                last_processing_date=datetime.utcnow()
            )
    
    async def get_recommendation_for_student(
        self,
        db: Session,
        student_id: str,
        limit: int = 10,
        recommendation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene recomendaciones personalizadas para un estudiante específico
        """
        try:
            logger.info(f"Getting recommendations for student {student_id}")
            
            # 1. Obtener debilidades del estudiante
            weaknesses = await self.weakness_service.get_student_weaknesses(
                db, student_id, limit=5
            )
            
            if not weaknesses:
                return {
                    'student_id': student_id,
                    'recommendations': [],
                    'message': 'No weaknesses detected - student performing well!',
                    'status': 'no_recommendations_needed'
                }
            
            # 2. Obtener recomendaciones de videos para las debilidades
            all_recommendations = []
            
            for weakness in weaknesses:
                # Buscar recomendaciones existentes para esta debilidad
                recs = db.query(QuestionVideoRecommendations).join(
                    Question, QuestionVideoRecommendations.question_id == Question.id
                ).filter(
                    and_(
                        Question.subject_id == weakness.subject_id,
                        Question.topic_id == weakness.topic_id,
                        QuestionVideoRecommendations.total_score >= 0.75,
                        QuestionVideoRecommendations.is_active == True
                    )
                ).order_by(QuestionVideoRecommendations.total_score.desc()).limit(3).all()
                
                for rec in recs:
                    video = db.query(YoutubeCatalog).filter(
                        YoutubeCatalog.id == rec.video_id
                    ).first()
                    
                    if video:
                        recommendation = {
                            'video_id': video.id,
                            'title': video.title,
                            'channel': video.channel_title,
                            'duration_minutes': round((video.duration_seconds or 0) / 60, 1),
                            'youtube_url': f"https://www.youtube.com/watch?v={video.video_id}",
                            'recommendation_score': round(rec.total_score, 3),
                            'recommendation_type': rec.recommendation_type,
                            'confidence_level': rec.confidence_level,
                            'targets_weakness': {
                                'subject': weakness.subject_name,
                                'topic': weakness.topic_name,
                                'severity': weakness.weakness_severity.value,
                                'priority_score': weakness.intervention_priority_score
                            },
                            'scoring_details': {
                                'semantic_similarity': round(rec.semantic_similarity_score, 3),
                                'difficulty_proximity': round(rec.difficulty_proximity_score, 3),
                                'error_coverage': round(rec.error_coverage_score, 3),
                                'popularity': round(rec.popularity_score, 3)
                            }
                        }
                        all_recommendations.append(recommendation)
            
            # 3. Aplicar diversificación y filtros
            if recommendation_type:
                all_recommendations = [r for r in all_recommendations if r['recommendation_type'] == recommendation_type]
            
            # Ordenar por score y limitar
            all_recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            final_recommendations = all_recommendations[:limit]
            
            # 4. Generar resumen
            summary = {
                'total_weaknesses_analyzed': len(weaknesses),
                'critical_weaknesses': len([w for w in weaknesses if w.weakness_severity.value == 'critical']),
                'recommendations_generated': len(final_recommendations),
                'average_recommendation_score': round(
                    sum(r['recommendation_score'] for r in final_recommendations) / len(final_recommendations), 3
                ) if final_recommendations else 0,
                'coverage_by_type': {}
            }
            
            # Contar por tipo de recomendación
            for rec in final_recommendations:
                rec_type = rec['recommendation_type']
                summary['coverage_by_type'][rec_type] = summary['coverage_by_type'].get(rec_type, 0) + 1
            
            return {
                'student_id': student_id,
                'recommendations': final_recommendations,
                'weaknesses_summary': [
                    {
                        'subject': w.subject_name,
                        'topic': w.topic_name,
                        'severity': w.weakness_severity.value,
                        'priority_score': w.intervention_priority_score,
                        'needs_action': w.recommended_action
                    }
                    for w in weaknesses
                ],
                'summary': summary,
                'status': 'success',
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations for student {student_id}: {e}")
            return {
                'student_id': student_id,
                'status': 'error',
                'error': str(e),
                'recommendations': []
            }
    
    async def get_system_health_status(self, db: Session) -> Dict[str, Any]:
        """
        Obtiene el estado de salud general del sistema
        """
        try:
            health_status = {
                'overall_status': 'healthy',
                'components': {},
                'metrics': {},
                'last_check': datetime.utcnow().isoformat()
            }
            
            # Verificar componentes individuales
            health_status['components']['embeddings'] = await self._validate_embeddings_health(db)
            health_status['components']['recommendations'] = await self._validate_recommendations_quality(db)
            health_status['components']['weakness_analysis'] = await self._validate_weakness_analysis_coverage(db)
            health_status['components']['yaml_plans'] = await self._validate_yaml_plans_integrity()
            health_status['components']['performance'] = await self._validate_system_performance(db)
            
            # Calcular estado general
            component_scores = [comp.get('score', 0) for comp in health_status['components'].values()]
            overall_score = sum(component_scores) / len(component_scores) if component_scores else 0
            
            if overall_score >= 0.9:
                health_status['overall_status'] = 'excellent'
            elif overall_score >= 0.8:
                health_status['overall_status'] = 'good'
            elif overall_score >= 0.6:
                health_status['overall_status'] = 'fair'
            else:
                health_status['overall_status'] = 'needs_attention'
            
            # Agregar métricas del sistema
            health_status['metrics'] = await self._calculate_system_metrics(db)
            health_status['overall_score'] = round(overall_score, 3)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health status: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de un pipeline específico"""
        if pipeline_id not in self.pipeline_status:
            return None
        
        pipeline_data = self.pipeline_status[pipeline_id]
        
        return {
            'pipeline_id': pipeline_id,
            'stages': {
                stage_name: {
                    'status': status.status,
                    'progress_percentage': status.progress_percentage,
                    'start_time': status.start_time.isoformat() if status.start_time else None,
                    'end_time': status.end_time.isoformat() if status.end_time else None,
                    'error_message': status.error_message,
                    'metadata': status.metadata
                }
                for stage_name, status in pipeline_data.items()
            }
        }