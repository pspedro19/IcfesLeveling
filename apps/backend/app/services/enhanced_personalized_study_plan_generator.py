"""
Enhanced Personalized Study Plan Generator
Versión mejorada que integra videos reales usando OptimizedVideoRecommendationEngine
"""

import yaml
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from dataclasses import dataclass, asdict

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question_video_recommendations import QuestionVideoRecommendations
from ..models.youtube_catalog import YoutubeCatalog
from ..models.study_plan import StudyPlan, PlanProgress
from ..core.database import get_db
from .optimized_video_recommendation_engine import OptimizedVideoRecommendationEngine

logger = logging.getLogger(__name__)

@dataclass
class PersonalizedUnit:
    """Represents a personalized learning unit with real videos"""
    unit_number: int
    title: str
    description: str
    focus_area: str
    difficulty_level: int
    estimated_hours: float
    videos: List[Dict[str, Any]]
    practice_questions: List[str]
    learning_objectives: List[str]
    weak_concepts: List[str]
    priority_score: float

@dataclass
class StudyPlanMetadata:
    """Enhanced metadata for the study plan"""
    student_id: str
    subject_id: str
    diagnostic_test_id: str
    weakness_areas: List[str]
    strength_areas: List[str]
    overall_score: float
    target_improvement: float
    plan_duration_weeks: int
    reassessment_date: str
    created_at: str
    version: str
    video_recommendation_engine: str = "OptimizedEngine_v2.0"
    total_real_videos: int = 0
    fallback_videos: int = 0

class EnhancedPersonalizedStudyPlanGenerator:
    """
    Enhanced generator that uses real YouTube videos from the catalog
    Integrates OptimizedVideoRecommendationEngine for better video matching
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_path = Path("/root/IcfesLeveling/storage/study_plans")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize the optimized video recommendation engine
        self.video_engine = OptimizedVideoRecommendationEngine(db)
        
        # Subject mapping for better video matching
        self.subject_mapping = {
            '550e8400-e29b-41d4-a716-446655440001': 'Matemáticas',
            '550e8400-e29b-41d4-a716-446655440002': 'Lenguaje',
            '550e8400-e29b-41d4-a716-446655440003': 'Ciencias Naturales',
            '550e8400-e29b-41d4-a716-446655440004': 'Ciencias Sociales',
            '550e8400-e29b-41d4-a716-446655440005': 'Inglés'
        }
        
    async def generate_personalized_plan(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str,
        target_weeks: int = 8
    ) -> Dict[str, Any]:
        """
        Generate enhanced personalized study plan with real videos
        """
        try:
            logger.info(f"🎯 Generating ENHANCED personalized plan for user {user_id}, subject {subject_id}")
            
            # 1. Analyze diagnostic test results
            diagnostic_analysis = await self._analyze_diagnostic_results(
                user_id, subject_id, diagnostic_test_id
            )
            
            if not diagnostic_analysis['success']:
                return diagnostic_analysis
            
            # 2. Extract weakness patterns and create targeted learning units
            learning_units = await self._create_targeted_learning_units(
                diagnostic_analysis['weakness_data'],
                subject_id,
                target_weeks
            )
            
            # 3. Get REAL video recommendations using optimized engine
            video_recommendations = await self._get_enhanced_video_recommendations(
                diagnostic_analysis['failed_questions'],
                diagnostic_analysis['weakness_areas'],
                subject_id
            )
            
            # 4. Enrich units with matched REAL videos
            enriched_units = await self._enrich_units_with_real_videos(
                learning_units,
                video_recommendations,
                subject_id
            )
            
            # 5. Calculate video statistics
            video_stats = self._calculate_video_statistics(enriched_units)
            
            # 6. Create enhanced YAML structure
            study_plan_yaml = await self._create_enhanced_study_plan_yaml(
                user_id,
                subject_id,
                diagnostic_test_id,
                enriched_units,
                diagnostic_analysis,
                video_stats
            )
            
            # 7. Save to both database and file system
            plan_id = await self._save_enhanced_study_plan(
                user_id,
                subject_id,
                study_plan_yaml,
                enriched_units,
                diagnostic_analysis,
                video_stats
            )
            
            # 8. Schedule reassessment reminder
            await self._schedule_monthly_reassessment(user_id, subject_id, plan_id)
            
            return {
                'success': True,
                'plan_id': plan_id,
                'file_path': f"{self.storage_path}/{user_id}_{subject_id}_{plan_id}.yaml",
                'units': len(enriched_units),
                'total_videos': video_stats['total_videos'],
                'real_videos': video_stats['real_videos'],
                'fallback_videos': video_stats['fallback_videos'],
                'video_quality_score': video_stats['average_quality'],
                'estimated_duration_weeks': target_weeks,
                'weakness_areas': diagnostic_analysis['weakness_areas'],
                'enhancement_level': 'OPTIMIZED_REAL_VIDEOS',
                'message': f'Enhanced personalized study plan generated with {video_stats["real_videos"]} real videos'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced personalized plan: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate enhanced personalized study plan'
            }

    async def _analyze_diagnostic_results(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str
    ) -> Dict[str, Any]:
        """
        Enhanced analysis of diagnostic test to identify specific weaknesses
        """
        try:
            # Get diagnostic test with answers
            query = text("""
                SELECT 
                    dt.id,
                    dt.score_percentage,
                    dt.strengths,
                    dt.weaknesses,
                    dt.score_by_topic,
                    json_agg(
                        json_build_object(
                            'question_id', dta.question_id,
                            'user_answer', dta.user_answer,
                            'is_correct', dta.is_correct,
                            'topic_id', dta.topic_id,
                            'response_time', dta.response_time_ms,
                            'question_text', q.question_text,
                            'correct_answer', q.correct_answer,
                            'difficulty_theta', q.difficulty_theta,
                            'topic_name', t.name,
                            'codigo_tema', t.codigo_tema
                        )
                    ) as answers
                FROM diagnostic_tests dt
                LEFT JOIN diagnostic_test_answers dta ON dt.id = dta.diagnostic_test_id
                LEFT JOIN questions q ON dta.question_id = q.id
                LEFT JOIN topics t ON dta.topic_id = t.id
                WHERE dt.id = :diagnostic_test_id 
                AND dt.user_id = :user_id 
                AND dt.subject_id = :subject_id
                GROUP BY dt.id
            """)
            
            result = self.db.execute(query, {
                'diagnostic_test_id': diagnostic_test_id,
                'user_id': user_id,
                'subject_id': subject_id
            }).first()
            
            if not result:
                return {
                    'success': False,
                    'error': 'Diagnostic test not found'
                }
            
            answers = json.loads(result[5]) if result[5] else []
            failed_questions = [ans for ans in answers if not ans['is_correct']]
            correct_questions = [ans for ans in answers if ans['is_correct']]
            
            # Enhanced weakness analysis with topic codes
            weakness_analysis = self._enhanced_weakness_analysis(failed_questions)
            strength_analysis = self._analyze_strength_patterns(correct_questions)
            
            return {
                'success': True,
                'overall_score': result[1],
                'strengths': json.loads(result[2]) if result[2] else [],
                'weaknesses': json.loads(result[3]) if result[3] else [],
                'score_by_topic': json.loads(result[4]) if result[4] else {},
                'failed_questions': failed_questions,
                'correct_questions': correct_questions,
                'weakness_data': weakness_analysis,
                'strength_data': strength_analysis,
                'weakness_areas': list(weakness_analysis.keys()),
                'total_questions': len(answers),
                'accuracy_rate': len(correct_questions) / len(answers) if answers else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing diagnostic results: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _enhanced_weakness_analysis(self, failed_questions: List[Dict]) -> Dict[str, Dict]:
        """
        Enhanced analysis with topic codes for better video matching
        """
        weakness_data = {}
        
        for question in failed_questions:
            topic_name = question.get('topic_name', 'General')
            topic_code = question.get('codigo_tema', 'GEN001')
            difficulty = question.get('difficulty_theta', 0)
            response_time = question.get('response_time', 0)
            
            if topic_name not in weakness_data:
                weakness_data[topic_name] = {
                    'failed_count': 0,
                    'average_difficulty': 0,
                    'average_response_time': 0,
                    'question_ids': [],
                    'topic_codes': [],
                    'difficulty_levels': [],
                    'response_times': [],
                    'priority_score': 0
                }
            
            weakness_data[topic_name]['failed_count'] += 1
            weakness_data[topic_name]['question_ids'].append(question['question_id'])
            weakness_data[topic_name]['topic_codes'].append(topic_code)
            weakness_data[topic_name]['difficulty_levels'].append(difficulty)
            weakness_data[topic_name]['response_times'].append(response_time)
        
        # Calculate aggregated metrics
        for topic, data in weakness_data.items():
            data['average_difficulty'] = sum(data['difficulty_levels']) / len(data['difficulty_levels'])
            data['average_response_time'] = sum(data['response_times']) / len(data['response_times'])
            # Priority score: combines frequency and difficulty
            data['priority_score'] = data['failed_count'] * (1 + data['average_difficulty'])
            # Get unique topic codes
            data['topic_codes'] = list(set(data['topic_codes']))
        
        return weakness_data

    async def _get_enhanced_video_recommendations(
        self,
        failed_questions: List[Dict],
        weakness_areas: List[str],
        subject_id: str
    ) -> Dict[str, List[Dict]]:
        """
        Get REAL video recommendations using the optimized engine
        """
        video_recommendations = {}
        
        try:
            logger.info(f"🎥 Getting enhanced video recommendations for {len(weakness_areas)} weakness areas")
            
            # Group failed questions by topic
            questions_by_topic = {}
            for question in failed_questions:
                topic_name = question.get('topic_name', 'General')
                topic_code = question.get('codigo_tema', 'GEN001')
                
                if topic_name not in questions_by_topic:
                    questions_by_topic[topic_name] = {
                        'questions': [],
                        'topic_code': topic_code
                    }
                questions_by_topic[topic_name]['questions'].append(question)
            
            # Get video recommendations for each topic using optimized engine
            for topic_name, topic_data in questions_by_topic.items():
                topic_code = topic_data['topic_code']
                
                logger.info(f"🔍 Getting videos for topic: {topic_name} (code: {topic_code})")
                
                # Use the optimized engine for real video recommendations
                videos = self.video_engine.get_intelligent_recommendations(
                    topic_code=topic_code,
                    topic_name=topic_name,
                    subject_id=subject_id,
                    difficulty_level=0.5,
                    max_videos=5  # Get more videos per topic
                )
                
                if videos:
                    video_recommendations[topic_name] = videos
                    logger.info(f"✅ Found {len(videos)} videos for {topic_name}")
                else:
                    logger.warning(f"⚠️ No videos found for {topic_name}")
                    # Try fallback with general topic search
                    fallback_videos = await self._get_fallback_videos(topic_name, subject_id)
                    video_recommendations[topic_name] = fallback_videos
            
            # If still no videos found, try general subject videos
            for topic_name in weakness_areas:
                if topic_name not in video_recommendations or not video_recommendations[topic_name]:
                    general_videos = await self._get_general_subject_videos(subject_id, topic_name)
                    if general_videos:
                        video_recommendations[topic_name] = general_videos
                        
        except Exception as e:
            logger.error(f"Error getting enhanced video recommendations: {e}")
            # Provide fallback recommendations
            for topic_name in weakness_areas:
                if topic_name not in video_recommendations:
                    video_recommendations[topic_name] = await self._get_fallback_videos(topic_name, subject_id)
        
        return video_recommendations

    async def _get_fallback_videos(self, topic_name: str, subject_id: str) -> List[Dict[str, Any]]:
        """
        Get fallback videos when optimized engine doesn't find matches
        """
        try:
            subject_name = self.subject_mapping.get(subject_id, 'Matemáticas')
            
            query = text("""
                SELECT 
                    youtube_id, title, url, duration_seconds, channel_name,
                    tema_principal, quality_score, area_evaluada
                FROM youtube_catalog
                WHERE area_evaluada = :subject_name
                AND (
                    LOWER(tema_principal) LIKE LOWER(:topic_pattern) OR
                    LOWER(title) LIKE LOWER(:topic_pattern)
                )
                AND processing_status = 'completed'
                AND youtube_id IS NOT NULL
                ORDER BY quality_score DESC, duration_seconds ASC
                LIMIT 3
            """)
            
            result = self.db.execute(query, {
                'subject_name': subject_name,
                'topic_pattern': f'%{topic_name}%'
            }).fetchall()
            
            videos = []
            for row in result:
                video_data = {
                    'video_id': row[0],
                    'youtube_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'duration_seconds': row[3] or 600,
                    'duration_minutes': (row[3] or 600) // 60,
                    'channel': row[4] or 'Canal Educativo',
                    'topic': row[5] or topic_name,
                    'relevance_score': 0.4,
                    'recommendation_type': 'fallback_search',
                    'quality_score': float(row[6] or 0.5),
                    'is_fallback': True,
                    'recommendation_reason': f'Video de {subject_name} relacionado con {topic_name}',
                    'embed_url': f"https://www.youtube.com/embed/{row[0]}" if row[0] else '',
                    'watch_url': row[2] or f"https://www.youtube.com/watch?v={row[0]}"
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting fallback videos: {e}")
            return []

    async def _get_general_subject_videos(self, subject_id: str, topic_name: str) -> List[Dict[str, Any]]:
        """
        Get general videos for the subject when topic-specific search fails
        """
        try:
            subject_name = self.subject_mapping.get(subject_id, 'Matemáticas')
            
            query = text("""
                SELECT 
                    youtube_id, title, url, duration_seconds, channel_name,
                    tema_principal, quality_score
                FROM youtube_catalog
                WHERE area_evaluada = :subject_name
                AND processing_status = 'completed'
                AND youtube_id IS NOT NULL
                AND quality_score > 0.3
                ORDER BY quality_score DESC, view_count DESC
                LIMIT 2
            """)
            
            result = self.db.execute(query, {
                'subject_name': subject_name
            }).fetchall()
            
            videos = []
            for row in result:
                video_data = {
                    'video_id': row[0],
                    'youtube_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'duration_seconds': row[3] or 600,
                    'duration_minutes': (row[3] or 600) // 60,
                    'channel': row[4] or 'Canal Educativo',
                    'topic': row[5] or topic_name,
                    'relevance_score': 0.3,
                    'recommendation_type': 'general_subject',
                    'quality_score': float(row[6] or 0.3),
                    'is_fallback': True,
                    'recommendation_reason': f'Contenido general de {subject_name}',
                    'embed_url': f"https://www.youtube.com/embed/{row[0]}" if row[0] else '',
                    'watch_url': row[2] or f"https://www.youtube.com/watch?v={row[0]}"
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting general subject videos: {e}")
            return []

    async def _create_targeted_learning_units(
        self,
        weakness_data: Dict[str, Dict],
        subject_id: str,
        target_weeks: int
    ) -> List[PersonalizedUnit]:
        """
        Create enhanced learning units specifically targeting identified weaknesses
        """
        units = []
        
        # Sort weaknesses by priority score
        sorted_weaknesses = sorted(
            weakness_data.items(),
            key=lambda x: x[1]['priority_score'],
            reverse=True
        )
        
        for i, (topic, weakness_info) in enumerate(sorted_weaknesses):
            unit_number = i + 1
            
            # Determine difficulty level based on failed questions
            avg_difficulty = weakness_info['average_difficulty']
            if avg_difficulty < -1:
                difficulty_level = 1  # Basic
            elif avg_difficulty < 0:
                difficulty_level = 2  # Intermediate
            else:
                difficulty_level = 3  # Advanced
            
            # Calculate estimated hours based on weakness severity
            base_hours = 4
            severity_multiplier = min(2.0, weakness_info['failed_count'] / 3)
            estimated_hours = base_hours * severity_multiplier
            
            unit = PersonalizedUnit(
                unit_number=unit_number,
                title=f"Unidad {unit_number}: Dominio de {topic}",
                description=f"Fortalece tus conocimientos en {topic} con videos educativos personalizados",
                focus_area=topic,
                difficulty_level=difficulty_level,
                estimated_hours=estimated_hours,
                videos=[],  # Will be populated with REAL videos
                practice_questions=weakness_info['question_ids'],
                learning_objectives=self._generate_enhanced_learning_objectives(topic, weakness_info),
                weak_concepts=self._extract_weak_concepts(topic, weakness_info),
                priority_score=weakness_info['priority_score']
            )
            
            units.append(unit)
        
        return units

    def _generate_enhanced_learning_objectives(self, topic: str, weakness_info: Dict) -> List[str]:
        """
        Generate enhanced learning objectives with video integration
        """
        objectives = [
            f"Comprender los conceptos fundamentales de {topic} a través de videos educativos",
            f"Resolver problemas de {topic} con 85% de precisión",
            f"Aplicar conocimientos de {topic} en situaciones complejas",
            f"Analizar videos educativos para reforzar el aprendizaje de {topic}"
        ]
        
        # Add specific objectives based on difficulty level
        avg_difficulty = weakness_info['average_difficulty']
        if avg_difficulty < -1:
            objectives.extend([
                f"Identificar terminología básica de {topic}",
                f"Reconocer patrones fundamentales en {topic}"
            ])
        elif avg_difficulty > 0:
            objectives.extend([
                f"Analizar problemas avanzados de {topic}",
                f"Sintetizar conceptos de {topic} con otras disciplinas"
            ])
        
        return objectives

    async def _enrich_units_with_real_videos(
        self,
        learning_units: List[PersonalizedUnit],
        video_recommendations: Dict[str, List[Dict]],
        subject_id: str
    ) -> List[PersonalizedUnit]:
        """
        Enrich learning units with REAL video recommendations
        """
        enriched_units = []
        
        for unit in learning_units:
            topic = unit.focus_area
            enhanced_unit = unit
            
            if topic in video_recommendations and video_recommendations[topic]:
                # Use the optimized video recommendations
                videos = video_recommendations[topic]
                
                # Sort videos by relevance score and quality
                videos.sort(key=lambda x: (
                    x.get('relevance_score', 0),
                    x.get('quality_score', 0)
                ), reverse=True)
                
                # Take top 4 videos per unit
                enhanced_unit.videos = videos[:4]
                logger.info(f"✅ Unit '{topic}' enriched with {len(enhanced_unit.videos)} real videos")
            else:
                # Last resort: try to find any videos for this topic
                fallback_videos = await self._get_fallback_videos(topic, subject_id)
                enhanced_unit.videos = fallback_videos[:2]
                logger.warning(f"⚠️ Unit '{topic}' using {len(enhanced_unit.videos)} fallback videos")
            
            # Ensure each unit has at least some content
            if not enhanced_unit.videos:
                logger.error(f"❌ No videos found for unit '{topic}' - adding educational placeholder")
                enhanced_unit.videos = [{
                    'video_id': f'educational_{topic.lower().replace(" ", "_")}',
                    'title': f'Estudio de {topic}',
                    'description': f'Contenido educativo sobre {topic}',
                    'duration_minutes': 15,
                    'relevance_score': 0.1,
                    'is_fallback': True,
                    'recommendation_type': 'educational_placeholder',
                    'embed_url': 'about:blank',
                    'watch_url': 'about:blank'
                }]
            
            enriched_units.append(enhanced_unit)
        
        return enriched_units

    def _calculate_video_statistics(self, enriched_units: List[PersonalizedUnit]) -> Dict[str, Any]:
        """
        Calculate statistics about the videos in the plan
        """
        total_videos = 0
        real_videos = 0
        fallback_videos = 0
        quality_scores = []
        
        for unit in enriched_units:
            for video in unit.videos:
                total_videos += 1
                
                if video.get('is_fallback', False):
                    fallback_videos += 1
                else:
                    real_videos += 1
                
                quality_score = video.get('quality_score', 0.0)
                if quality_score > 0:
                    quality_scores.append(quality_score)
        
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            'total_videos': total_videos,
            'real_videos': real_videos,
            'fallback_videos': fallback_videos,
            'average_quality': round(average_quality, 3),
            'quality_distribution': {
                'high': len([q for q in quality_scores if q >= 0.7]),
                'medium': len([q for q in quality_scores if 0.4 <= q < 0.7]),
                'low': len([q for q in quality_scores if q < 0.4])
            }
        }

    def _extract_weak_concepts(self, topic: str, weakness_info: Dict) -> List[str]:
        """
        Extract specific weak concepts within a topic
        """
        # Enhanced concept mapping
        concept_map = {
            'Algebra': ['Ecuaciones lineales', 'Funciones cuadráticas', 'Factorización', 'Sistemas de ecuaciones'],
            'Geometría': ['Cálculo de áreas', 'Relaciones angulares', 'Triángulos semejantes', 'Teorema de Pitágoras'],
            'Probabilidad': ['Probabilidad básica', 'Probabilidad condicional', 'Combinaciones y permutaciones'],
            'Comprensión Lectora': ['Identificación de idea principal', 'Habilidades de inferencia', 'Vocabulario contextual'],
            'Gramática': ['Tiempos verbales', 'Concordancia sujeto-verbo', 'Puntuación y ortografía'],
            'Química': ['Enlaces químicos', 'Estequiometría', 'Tabla periódica', 'Reacciones químicas'],
            'Física': ['Ecuaciones de movimiento', 'Cálculo de fuerzas', 'Conservación de energía', 'Ondas y sonido'],
            'Biología': ['Genética básica', 'Ecosistemas', 'Anatomía humana', 'Evolución'],
            'Historia': ['Procesos históricos', 'Causas y consecuencias', 'Cronología', 'Fuentes históricas'],
            'Geografía': ['Cartografía', 'Relieve y clima', 'Población y demografía', 'Recursos naturales']
        }
        
        return concept_map.get(topic, [f"Conceptos básicos de {topic}", f"Aplicación práctica de {topic}"])

    async def _create_enhanced_study_plan_yaml(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str,
        units: List[PersonalizedUnit],
        diagnostic_analysis: Dict,
        video_stats: Dict
    ) -> str:
        """
        Create enhanced YAML structure with video statistics
        """
        plan_metadata = StudyPlanMetadata(
            student_id=user_id,
            subject_id=subject_id,
            diagnostic_test_id=diagnostic_test_id,
            weakness_areas=diagnostic_analysis['weakness_areas'],
            strength_areas=list(diagnostic_analysis['strength_data'].keys()),
            overall_score=diagnostic_analysis['overall_score'],
            target_improvement=min(95.0, diagnostic_analysis['overall_score'] + 25.0),
            plan_duration_weeks=len(units),
            reassessment_date=(datetime.now() + timedelta(weeks=4)).isoformat(),
            created_at=datetime.now().isoformat(),
            version="2.1_Enhanced_Real_Videos",
            video_recommendation_engine="OptimizedEngine_v2.0",
            total_real_videos=video_stats['real_videos'],
            fallback_videos=video_stats['fallback_videos']
        )
        
        yaml_structure = {
            'enhanced_personalized_study_plan': {
                'metadata': asdict(plan_metadata),
                'video_quality_report': {
                    'total_videos': video_stats['total_videos'],
                    'real_videos_count': video_stats['real_videos'],
                    'fallback_videos_count': video_stats['fallback_videos'],
                    'average_quality_score': video_stats['average_quality'],
                    'quality_distribution': video_stats['quality_distribution'],
                    'enhancement_status': 'OPTIMIZED_WITH_REAL_VIDEOS'
                },
                'diagnostic_summary': {
                    'total_questions': diagnostic_analysis['total_questions'],
                    'accuracy_rate': round(diagnostic_analysis['accuracy_rate'], 3),
                    'primary_weaknesses': diagnostic_analysis['weakness_areas'][:3],
                    'main_strengths': list(diagnostic_analysis['strength_data'].keys())[:3]
                },
                'learning_path': {
                    'total_units': len(units),
                    'estimated_total_hours': sum(unit.estimated_hours for unit in units),
                    'units': [
                        {
                            'unit_number': unit.unit_number,
                            'title': unit.title,
                            'description': unit.description,
                            'focus_area': unit.focus_area,
                            'difficulty_level': unit.difficulty_level,
                            'estimated_hours': unit.estimated_hours,
                            'priority_score': unit.priority_score,
                            'learning_objectives': unit.learning_objectives,
                            'weak_concepts': unit.weak_concepts,
                            'recommended_videos': [
                                {
                                    'video_id': video.get('video_id', video.get('youtube_id', '')),
                                    'youtube_id': video.get('youtube_id', video.get('video_id', '')),
                                    'title': video['title'],
                                    'url': video.get('url', video.get('watch_url', '')),
                                    'embed_url': video.get('embed_url', ''),
                                    'duration_minutes': video.get('duration_minutes', 0),
                                    'channel': video.get('channel', video.get('channel_name', '')),
                                    'relevance_score': video.get('relevance_score', 0.0),
                                    'quality_score': video.get('quality_score', 0.0),
                                    'recommendation_type': video.get('recommendation_type', 'optimized'),
                                    'is_real_video': not video.get('is_fallback', False),
                                    'recommendation_reason': video.get('recommendation_reason', ''),
                                    'quality_indicator': video.get('quality_indicator', 'Standard')
                                }
                                for video in unit.videos
                            ],
                            'practice_questions': unit.practice_questions,
                            'completion_criteria': {
                                'videos_watched': len(unit.videos),
                                'practice_accuracy': 0.85,  # Higher target with better videos
                                'min_time_spent_hours': unit.estimated_hours * 0.75
                            }
                        }
                        for unit in units
                    ]
                },
                'reassessment_plan': {
                    'schedule_date': (datetime.now() + timedelta(weeks=4)).isoformat(),
                    'focus_areas': diagnostic_analysis['weakness_areas'],
                    'success_metrics': {
                        'target_overall_score': plan_metadata.target_improvement,
                        'weakness_improvement_threshold': 0.7,  # Higher with better content
                        'video_engagement_target': 0.8,
                        'consistency_target': 0.8
                    }
                }
            }
        }
        
        return yaml.dump(yaml_structure, default_flow_style=False, allow_unicode=True, sort_keys=False)

    async def _save_enhanced_study_plan(
        self,
        user_id: str,
        subject_id: str,
        yaml_content: str,
        units: List[PersonalizedUnit],
        diagnostic_analysis: Dict,
        video_stats: Dict
    ) -> str:
        """
        Save enhanced study plan with video statistics
        """
        plan_id = str(uuid.uuid4())
        
        try:
            # 1. Save to file system
            file_path = self.storage_path / f"{user_id}_{subject_id}_{plan_id}_enhanced.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # 2. Save to database with enhanced metadata
            study_plan_data = {
                'metadata': {
                    'total_units': len(units),
                    'total_videos': video_stats['total_videos'],
                    'real_videos': video_stats['real_videos'],
                    'fallback_videos': video_stats['fallback_videos'],
                    'average_video_quality': video_stats['average_quality'],
                    'weakness_areas': diagnostic_analysis['weakness_areas'],
                    'file_path': str(file_path),
                    'enhancement_level': 'OPTIMIZED_REAL_VIDEOS',
                    'video_engine': 'OptimizedEngine_v2.0'
                },
                'units': [asdict(unit) for unit in units],
                'video_statistics': video_stats
            }
            
            query = text("""
                INSERT INTO study_plans (
                    id, user_id, subject_id, plan_name, plan_data, 
                    total_units, completed_units, progress_percentage, is_active
                ) VALUES (
                    :id, :user_id, :subject_id, :plan_name, :plan_data,
                    :total_units, 0, 0.0, true
                )
            """)
            
            self.db.execute(query, {
                'id': plan_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'plan_name': f"Enhanced Plan with Real Videos - {datetime.now().strftime('%Y-%m-%d')}",
                'plan_data': json.dumps(study_plan_data),
                'total_units': len(units)
            })
            
            self.db.commit()
            logger.info(f"✅ Enhanced personalized study plan saved: {plan_id}")
            logger.info(f"📊 Video stats: {video_stats['real_videos']} real videos, {video_stats['fallback_videos']} fallbacks")
            
        except Exception as e:
            logger.error(f"Error saving enhanced study plan: {e}")
            self.db.rollback()
            raise
        
        return plan_id

    # Keep existing methods for compatibility
    def _analyze_strength_patterns(self, correct_questions: List[Dict]) -> Dict[str, Dict]:
        """Analyze areas where student performed well"""
        strength_data = {}
        
        for question in correct_questions:
            topic_name = question.get('topic_name', 'General')
            difficulty = question.get('difficulty_theta', 0)
            
            if topic_name not in strength_data:
                strength_data[topic_name] = {
                    'correct_count': 0,
                    'average_difficulty': 0,
                    'question_ids': [],
                    'mastery_level': 0
                }
            
            strength_data[topic_name]['correct_count'] += 1
            strength_data[topic_name]['question_ids'].append(question['question_id'])
            strength_data[topic_name]['average_difficulty'] += difficulty
        
        # Calculate mastery levels
        for topic, data in strength_data.items():
            if data['correct_count'] > 0:
                data['average_difficulty'] = data['average_difficulty'] / data['correct_count']
                data['mastery_level'] = min(1.0, data['correct_count'] * 0.2 + data['average_difficulty'] * 0.3)
        
        return strength_data

    async def _schedule_monthly_reassessment(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str
    ) -> None:
        """Schedule monthly reassessment reminder"""
        try:
            reassessment_date = datetime.now() + timedelta(days=30)
            
            query = text("""
                INSERT INTO notifications (
                    id, user_id, title, message, type, scheduled_for, 
                    metadata, is_active
                ) VALUES (
                    :id, :user_id, :title, :message, 'reassessment_reminder',
                    :scheduled_for, :metadata, true
                )
            """)
            
            metadata = json.dumps({
                'plan_id': plan_id,
                'subject_id': subject_id,
                'reassessment_type': 'monthly_progress_enhanced',
                'plan_type': 'enhanced_with_real_videos'
            })
            
            self.db.execute(query, {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'title': 'Evaluación Mensual del Plan de Estudio Mejorado',
                'message': '¡Es hora de evaluar tu progreso con el plan de estudio con videos reales!',
                'scheduled_for': reassessment_date,
                'metadata': metadata
            })
            
            self.db.commit()
            logger.info(f"📅 Enhanced reassessment scheduled for {reassessment_date}")
            
        except Exception as e:
            logger.error(f"Error scheduling enhanced reassessment: {e}")

    async def get_student_plan(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Retrieve the current active enhanced study plan for a student"""
        try:
            query = text("""
                SELECT id, plan_name, plan_data, total_units, completed_units, 
                       progress_percentage, created_at, updated_at
                FROM study_plans
                WHERE user_id = :user_id AND subject_id = :subject_id AND is_active = true
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'subject_id': subject_id
            }).first()
            
            if not result:
                return {
                    'success': False,
                    'message': 'No active enhanced study plan found'
                }
            
            plan_data = json.loads(result[2])
            
            return {
                'success': True,
                'plan_id': result[0],
                'plan_name': result[1],
                'plan_data': plan_data,
                'total_units': result[3],
                'completed_units': result[4],
                'progress_percentage': float(result[5]),
                'enhancement_level': plan_data.get('metadata', {}).get('enhancement_level', 'STANDARD'),
                'video_statistics': plan_data.get('video_statistics', {}),
                'created_at': result[6].isoformat() if result[6] else None,
                'updated_at': result[7].isoformat() if result[7] else None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving enhanced student plan: {e}")
            return {
                'success': False,
                'error': str(e)
            }