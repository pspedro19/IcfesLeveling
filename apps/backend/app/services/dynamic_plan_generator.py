"""
Dynamic Study Plan Generator with YouTube Integration
Genera planes de estudio personalizados basados en errores del diagnóstico
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import yaml
import json
import logging
from datetime import datetime, timedelta
from .smart_recommendation_engine import SmartRecommendationEngine

logger = logging.getLogger(__name__)

class DynamicPlanGenerator:
    """Generador dinámico de planes de estudio con videos de YouTube"""
    
    def __init__(self, db: Session):
        self.db = db
        self.recommendation_engine = SmartRecommendationEngine(db)
    
    def generate_plan_from_diagnostic(
        self, 
        user_id: str, 
        subject_id: str,
        diagnostic_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera un plan de estudio dinámico basado en los resultados del diagnóstico
        """
        try:
            logger.info(f"🚀 Generando plan dinámico para usuario {user_id}, materia {subject_id}")
            
            # 1. Analizar respuestas incorrectas
            incorrect_questions = diagnostic_results.get('incorrect_answers', [])
            if not incorrect_questions:
                # Crear datos de prueba si no hay errores específicos
                incorrect_questions = [
                    {'question_text': 'pregunta de prueba', 'subject_id': subject_id}
                ]
            
            logger.info(f"📊 Analizando {len(incorrect_questions)} respuestas incorrectas")
            
            # 2. Obtener videos personalizados usando el motor inteligente
            videos = self.recommendation_engine.get_personalized_videos(
                subject_id=subject_id,
                incorrect_questions=incorrect_questions,
                max_videos=15
            )
            logger.info(f"🎥 {len(videos)} videos personalizados encontrados")
            
            # 3. Organizar videos en unidades de aprendizaje
            # Extraer temas de los videos
            topics_found = list(set([v.get('topic', 'General') for v in videos]))
            units = self._organize_into_units(videos, topics_found)
            logger.info(f"📚 {len(units)} unidades creadas")
            
            # 4. Crear estructura YML del plan
            yml_content = self._create_yml_structure(
                user_id=user_id,
                subject_id=subject_id,
                units=units,
                diagnostic_results=diagnostic_results
            )
            
            # 5. Guardar plan en base de datos
            plan_id = self._save_plan_to_db(
                user_id=user_id,
                subject_id=subject_id,
                yml_content=yml_content,
                units=units
            )
            
            return {
                'success': True,
                'plan_id': plan_id,
                'units': units,
                'yml_content': yml_content,
                'total_videos': sum(len(u['videos']) for u in units),
                'estimated_weeks': len(units) // 3 + 1,
                'message': f'Plan personalizado creado con {len(units)} unidades'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando plan dinámico: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al generar el plan de estudio'
            }
    
    def _analyze_weak_areas(self, diagnostic_results: Dict) -> List[str]:
        """Analiza las áreas débiles basándose en respuestas incorrectas"""
        weak_topics = []
        
        # Si hay respuestas incorrectas específicas
        if 'incorrect_answers' in diagnostic_results:
            for answer in diagnostic_results['incorrect_answers']:
                topic = answer.get('topic', 'General')
                if topic not in weak_topics:
                    weak_topics.append(topic)
        
        # Si no hay datos específicos, usar temas generales por materia
        if not weak_topics:
            subject_name = diagnostic_results.get('subject_name', 'Matemáticas')
            
            default_topics = {
                'Matemáticas': ['Álgebra básica', 'Factorización', 'Funciones cuadráticas', 
                               'Geometría analítica', 'Trigonometría'],
                'Lenguaje': ['Comprensión lectora', 'Gramática', 'Ortografía'],
                'Ciencias Naturales': ['Física mecánica', 'Química general', 'Biología celular'],
                'Ciencias Sociales': ['Historia de Colombia', 'Geografía'],
                'Inglés': ['Grammar basics', 'Vocabulary']
            }
            
            weak_topics = default_topics.get(subject_name, ['Conceptos básicos'])[:3]
        
        return weak_topics
    
    def _get_videos_for_topics(self, subject_id: str, topics: List[str]) -> List[Dict]:
        """Obtiene videos de YouTube relacionados con los temas"""
        videos = []
        
        try:
            # Obtener nombre de la materia
            subject_query = text("""
                SELECT name FROM subjects WHERE id = :subject_id
            """)
            subject_result = self.db.execute(subject_query, {'subject_id': subject_id}).first()
            subject_name = subject_result[0] if subject_result else 'Matemáticas'
            
            # Buscar videos para cada tema
            for topic in topics:
                query = text("""
                    SELECT 
                        youtube_id,
                        video_title,
                        youtube_url,
                        duration_seconds,
                        nivel_dificultad,
                        puntos_xp,
                        canal_sugerido,
                        tema_principal
                    FROM youtube_links
                    WHERE area_evaluada = :area
                    AND (
                        LOWER(tema_principal) LIKE LOWER(:topic_pattern)
                        OR LOWER(video_title) LIKE LOWER(:topic_pattern)
                    )
                    AND estado = 'activo'
                    ORDER BY relevancia_score DESC, orden_recomendacion
                    LIMIT 3
                """)
                
                results = self.db.execute(query, {
                    'area': subject_name,
                    'topic_pattern': f'%{topic}%'
                }).fetchall()
                
                for row in results:
                    videos.append({
                        'id': row[0],
                        'title': row[1],
                        'url': row[2],
                        'duration': row[3],
                        'difficulty': row[4],
                        'xp': row[5],
                        'channel': row[6],
                        'topic': row[7]
                    })
            
            # Si no hay suficientes videos, agregar algunos generales
            if len(videos) < 5:
                general_query = text("""
                    SELECT 
                        youtube_id,
                        video_title,
                        youtube_url,
                        duration_seconds,
                        nivel_dificultad,
                        puntos_xp,
                        canal_sugerido,
                        tema_principal
                    FROM youtube_links
                    WHERE area_evaluada = :area
                    AND estado = 'activo'
                    ORDER BY relevancia_score DESC
                    LIMIT :limit
                """)
                
                additional_results = self.db.execute(general_query, {
                    'area': subject_name,
                    'limit': 5 - len(videos)
                }).fetchall()
                
                for row in additional_results:
                    videos.append({
                        'id': row[0],
                        'title': row[1],
                        'url': row[2],
                        'duration': row[3],
                        'difficulty': row[4],
                        'xp': row[5],
                        'channel': row[6],
                        'topic': row[7]
                    })
            
        except Exception as e:
            logger.error(f"Error obteniendo videos: {e}")
        
        return videos
    
    def _organize_into_units(self, videos: List[Dict], topics: List[str]) -> List[Dict]:
        """Organiza los videos en unidades de aprendizaje"""
        units = []
        
        # Agrupar videos por tema
        videos_by_topic = {}
        for video in videos:
            topic = video.get('topic', 'General')
            if topic not in videos_by_topic:
                videos_by_topic[topic] = []
            videos_by_topic[topic].append(video)
        
        # Crear unidades
        unit_number = 1
        for topic, topic_videos in videos_by_topic.items():
            if topic_videos:
                units.append({
                    'unit_number': unit_number,
                    'title': f'Unidad {unit_number}: {topic}',
                    'description': f'Domina los conceptos de {topic}',
                    'videos': topic_videos,
                    'total_duration': sum(v['duration'] for v in topic_videos),
                    'total_xp': sum(v['xp'] for v in topic_videos),
                    'exercises': self._generate_exercises_for_unit(topic)
                })
                unit_number += 1
        
        # Si no hay unidades, crear una por defecto
        if not units:
            units.append({
                'unit_number': 1,
                'title': 'Unidad 1: Fundamentos',
                'description': 'Conceptos básicos y fundamentales',
                'videos': [],
                'total_duration': 0,
                'total_xp': 0,
                'exercises': []
            })
        
        return units
    
    def _generate_exercises_for_unit(self, topic: str) -> List[Dict]:
        """Genera ejercicios para practicar después de los videos"""
        return [
            {
                'type': 'quiz',
                'title': f'Quiz: {topic}',
                'questions': 5,
                'xp': 50
            },
            {
                'type': 'practice',
                'title': f'Práctica: {topic}',
                'questions': 10,
                'xp': 100
            }
        ]
    
    def _create_yml_structure(
        self, 
        user_id: str,
        subject_id: str,
        units: List[Dict],
        diagnostic_results: Dict
    ) -> str:
        """Crea la estructura YML del plan de estudio"""
        
        yml_data = {
            'plan': {
                'metadata': {
                    'version': '2.0',
                    'generated_at': datetime.now().isoformat(),
                    'user_id': user_id,
                    'subject_id': subject_id,
                    'diagnostic_score': diagnostic_results.get('score', 0),
                    'total_units': len(units)
                },
                'units': []
            }
        }
        
        for unit in units:
            unit_data = {
                'unit_number': unit['unit_number'],
                'title': unit['title'],
                'description': unit['description'],
                'videos': [
                    {
                        'id': v['id'],
                        'title': v['title'],
                        'url': v['url'],
                        'duration_minutes': v['duration'] // 60,
                        'xp': v['xp']
                    }
                    for v in unit['videos']
                ],
                'exercises': unit['exercises'],
                'estimated_hours': unit['total_duration'] / 3600
            }
            yml_data['plan']['units'].append(unit_data)
        
        return yaml.dump(yml_data, default_flow_style=False, allow_unicode=True)
    
    def _save_plan_to_db(
        self, 
        user_id: str,
        subject_id: str,
        yml_content: str,
        units: List[Dict]
    ) -> str:
        """Guarda el plan en la base de datos"""
        plan_id = str(uuid.uuid4())
        
        try:
            # Guardar en tabla yml_storage
            query = text("""
                INSERT INTO yml_storage (
                    id, user_id, subject, yml_content, version, metadata
                ) VALUES (
                    :id, :user_id, :subject_id, :yml_content, '2.0', :metadata
                )
            """)
            
            metadata = json.dumps({
                'total_units': len(units),
                'total_videos': sum(len(u['videos']) for u in units),
                'generated_at': datetime.now().isoformat()
            })
            
            self.db.execute(query, {
                'id': plan_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'yml_content': yml_content,
                'metadata': metadata
            })
            
            self.db.commit()
            logger.info(f"✅ Plan guardado con ID: {plan_id}")
            
        except Exception as e:
            logger.error(f"Error guardando plan: {e}")
            self.db.rollback()
            
        return plan_id