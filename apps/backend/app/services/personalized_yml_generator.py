import yaml
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from sqlalchemy import and_

from ..models.user import User
from ..models.diagnostic_analytics import DiagnosticTestAnalytics
from ..models.battle import BattleAnswer
from ..models.question import Question
from ..models.subject import Subject
from ..services.yml_storage_service import YMLStorageService
from ..services.llm_service import LLMService
from .intelligent_video_recommendation_engine import IntelligentVideoRecommendationEngine

logger = logging.getLogger(__name__)

class PersonalizedYMLGenerator:
    """
    Generador de YML personalizado que crea planes únicos para cada usuario
    basado en su diagnóstico, perfil de aprendizaje y errores específicos
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.yml_storage = YMLStorageService(db)
        self.llm_service = LLMService()
        self.video_engine = IntelligentVideoRecommendationEngine(db)
        
    async def generate_user_yml(
        self, 
        user_id: str, 
        diagnostic_id: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Pipeline principal de generación de YML personalizado
        """
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Iniciando generación de YML para usuario {user_id}, materia {subject}")
            
            # Paso 1: Obtener resultados del diagnóstico
            diagnostic = await self._fetch_diagnostic_results(diagnostic_id, user_id)
            if not diagnostic:
                raise ValueError(f"No se encontraron resultados de diagnóstico para usuario {user_id}")
            
            # Paso 2: Analizar qué falló el usuario
            failed_questions = self._extract_failed_questions(diagnostic)
            logger.info(f"📊 Usuario falló {len(failed_questions)} preguntas")
            
            # Paso 3: Construir perfil del usuario
            user_profile = await self._build_user_profile(user_id, subject)
            logger.info(f"👤 Perfil de usuario construido: {user_profile['learning_style']}")
            
            # Paso 4: Mapear fallas a temas
            weak_topics = self._map_questions_to_topics(failed_questions)
            logger.info(f"🎯 Temas débiles identificados: {len(weak_topics)}")
            
            # Paso 5: Construir grafo de dependencias
            learning_graph = self._build_dependency_graph(weak_topics, subject)
            logger.info(f"🕸️ Grafo de dependencias construido con {len(learning_graph)} nodos")
            
            # Paso 6: Generar camino de aprendizaje óptimo
            learning_path = self._optimize_learning_path(learning_graph, user_profile)
            logger.info(f"🛤️ Camino de aprendizaje optimizado: {len(learning_path)} módulos")
            
            # Paso 7: Seleccionar mejores recursos para este usuario
            resources = await self._select_personalized_resources(learning_path, user_profile)
            logger.info(f"📚 Recursos personalizados seleccionados: {len(resources)}")
            
            # Paso 8: Generar estructura YML
            yml_content = self._create_yml_structure(
                user_id=user_id,
                subject=subject,
                learning_path=learning_path,
                resources=resources,
                failed_questions=failed_questions,
                user_profile=user_profile,
                diagnostic=diagnostic
            )
            
            # Paso 9: Almacenar YML
            generation_time = int((time.time() - start_time) * 1000)
            storage_info = await self.yml_storage.store_yml(
                user_id, 
                subject, 
                yml_content,
                metadata={
                    'generation_time_ms': generation_time,
                    'algorithm_version': '2.0',
                    'diagnostic_id': diagnostic_id,
                    'failed_questions_count': len(failed_questions),
                    'weak_topics_count': len(weak_topics)
                }
            )
            
            logger.info(f"✅ YML generado y almacenado exitosamente en {generation_time}ms")
            
            return {
                'yml_content': yml_content,
                'storage_info': storage_info,
                'generated_at': datetime.utcnow().isoformat(),
                'generation_time_ms': generation_time,
                'summary': {
                    'total_modules': len(learning_path),
                    'failed_questions': len(failed_questions),
                    'weak_topics': len(weak_topics),
                    'estimated_weeks': len(learning_path) // 3 + 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando YML: {e}")
            raise
    
    async def _fetch_diagnostic_results(self, diagnostic_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene resultados del test diagnóstico"""
        try:
            # Buscar en analytics de diagnóstico
            analytics = self.db.query(DiagnosticTestAnalytics).filter(
                DiagnosticTestAnalytics.user_id == user_id
            ).first()
            
            if analytics:
                return {
                    'analytics_id': str(analytics.id),
                    'overall_score': analytics.overall_score,
                    'subject_scores': analytics.subject_scores,
                    'weak_areas': analytics.weak_areas,
                    'strong_areas': analytics.strong_areas,
                    'test_date': analytics.test_date.isoformat() if analytics.test_date else None
                }
            
            # Fallback: buscar en respuestas de batalla
            battle_answers = self.db.query(BattleAnswer).filter(
                BattleAnswer.user_id == user_id
            ).all()
            
            if battle_answers:
                return self._analyze_battle_answers(battle_answers)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo resultados de diagnóstico: {e}")
            return None
    
    def _analyze_battle_answers(self, battle_answers: List[BattleAnswer]) -> Dict[str, Any]:
        """Analiza respuestas de batalla para crear perfil de diagnóstico"""
        total_questions = len(battle_answers)
        correct_answers = sum(1 for answer in battle_answers if answer.is_correct)
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Agrupar por tema
        topic_performance = {}
        for answer in battle_answers:
            if answer.question and answer.question.topic:
                topic = answer.question.topic
                if topic not in topic_performance:
                    topic_performance[topic] = {'correct': 0, 'total': 0}
                topic_performance[topic]['total'] += 1
                if answer.is_correct:
                    topic_performance[topic]['correct'] += 1
        
        # Identificar áreas débiles y fuertes
        weak_areas = []
        strong_areas = []
        for topic, stats in topic_performance.items():
            accuracy = (stats['correct'] / stats['total']) * 100
            if accuracy < 70:
                weak_areas.append({'topic': topic, 'accuracy': accuracy})
            elif accuracy > 85:
                strong_areas.append({'topic': topic, 'accuracy': accuracy})
        
        return {
            'overall_score': score,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'topic_performance': topic_performance,
            'weak_areas': weak_areas,
            'strong_areas': strong_areas
        }
    
    def _extract_failed_questions(self, diagnostic: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae preguntas fallidas del diagnóstico"""
        failed_questions = []
        
        # Buscar respuestas incorrectas en batallas
        user_id = diagnostic.get('user_id')
        if user_id:
            battle_answers = self.db.query(BattleAnswer).filter(
                and_(
                    BattleAnswer.user_id == user_id,
                    BattleAnswer.is_correct == False
                )
            ).limit(10).all()  # Top 10 errores más recientes
            
            for answer in battle_answers:
                if answer.question:
                    failed_questions.append({
                        'id': str(answer.question.id),
                        'topic': answer.question.topic or 'general',
                        'question_text': answer.question.question_text[:100] + '...',
                        'user_answer': answer.user_answer,
                        'correct_answer': answer.question.correct_answer,
                        'error_type': self._classify_error_type(answer),
                        'difficulty': answer.question.difficulty or 'medium',
                        'answered_at': answer.created_at.isoformat() if answer.created_at else None
                    })
        
        return failed_questions
    
    def _classify_error_type(self, answer: BattleAnswer) -> str:
        """Clasifica el tipo de error del usuario"""
        if not answer.question:
            return 'unknown'
        
        user_answer = answer.user_answer.lower()
        correct_answer = answer.question.correct_answer.lower()
        
        # Análisis simple del tipo de error
        if user_answer in ['', 'no sé', 'no se']:
            return 'no_answer'
        elif len(user_answer) < 3:
            return 'incomplete'
        elif user_answer in correct_answer or correct_answer in user_answer:
            return 'partial_correct'
        else:
            return 'conceptual'
    
    async def _build_user_profile(self, user_id: str, subject: str) -> Dict[str, Any]:
        """Construye perfil completo del usuario"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return self._get_default_user_profile()
            
            # Analizar patrones de aprendizaje
            learning_patterns = await self._analyze_learning_patterns(user_id, subject)
            
            # Determinar estilo de aprendizaje
            learning_style = self._determine_learning_style(learning_patterns)
            
            # Calcular nivel de confianza
            confidence_level = self._calculate_confidence_level(user_id, subject)
            
            return {
                'user_id': str(user.id),
                'username': user.username,
                'level': user.level or 1,
                'experience_points': user.experience_points or 0,
                'learning_style': learning_style,
                'pace': learning_patterns.get('pace', 'normal'),
                'confidence_level': confidence_level,
                'time_available': learning_patterns.get('avg_session_minutes', 30),
                'session_length': learning_patterns.get('preferred_session_length', 25),
                'preferred_time': learning_patterns.get('preferred_time', 'afternoon'),
                'streak_days': learning_patterns.get('streak_days', 0),
                'weak_subjects': learning_patterns.get('weak_subjects', []),
                'strong_subjects': learning_patterns.get('strong_subjects', [])
            }
            
        except Exception as e:
            logger.error(f"Error construyendo perfil de usuario: {e}")
            return self._get_default_user_profile()
    
    async def _analyze_learning_patterns(self, user_id: str, subject: str) -> Dict[str, Any]:
        """Analiza patrones de aprendizaje del usuario"""
        try:
            # Analizar sesiones de estudio
            battle_answers = self.db.query(BattleAnswer).filter(
                BattleAnswer.user_id == user_id
            ).order_by(BattleAnswer.created_at.desc()).limit(100).all()
            
            if not battle_answers:
                return self._get_default_learning_patterns()
            
            # Calcular métricas
            total_sessions = len(set(answer.session_id for answer in battle_answers if answer.session_id))
            avg_questions_per_session = len(battle_answers) / total_sessions if total_sessions > 0 else 0
            
            # Determinar ritmo de aprendizaje
            pace = 'normal'
            if avg_questions_per_session > 15:
                pace = 'fast'
            elif avg_questions_per_session < 8:
                pace = 'slow'
            
            # Duración preferida de sesión
            session_length = 25
            if pace == 'fast':
                session_length = 20
            elif pace == 'slow':
                session_length = 35
            
            return {
                'pace': pace,
                'avg_session_minutes': session_length,
                'preferred_session_length': session_length,
                'total_sessions': total_sessions,
                'avg_questions_per_session': avg_questions_per_session,
                'preferred_time': 'afternoon',  # Por defecto
                'streak_days': 0,  # Implementar lógica de racha
                'weak_subjects': [],
                'strong_subjects': []
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrones de aprendizaje: {e}")
            return self._get_default_learning_patterns()
    
    def _determine_learning_style(self, patterns: Dict[str, Any]) -> str:
        """Determina el estilo de aprendizaje del usuario"""
        # Lógica simple basada en patrones
        if patterns.get('pace') == 'fast':
            return 'kinesthetic'  # Aprende haciendo
        elif patterns.get('avg_questions_per_session', 0) > 12:
            return 'visual'  # Procesa mucha información
        else:
            return 'auditory'  # Prefiere explicaciones
    
    def _calculate_confidence_level(self, user_id: str, subject: str) -> float:
        """Calcula nivel de confianza del usuario en la materia"""
        try:
            # Calcular basado en respuestas correctas recientes
            recent_answers = self.db.query(BattleAnswer).filter(
                and_(
                    BattleAnswer.user_id == user_id,
                    BattleAnswer.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).limit(20).all()
            
            if not recent_answers:
                return 0.5  # Nivel medio por defecto
            
            correct_count = sum(1 for answer in recent_answers if answer.is_correct)
            confidence = correct_count / len(recent_answers)
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculando nivel de confianza: {e}")
            return 0.5
    
    def _map_questions_to_topics(self, failed_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mapea preguntas fallidas a temas específicos"""
        topic_mapping = {}
        
        for question in failed_questions:
            topic = question['topic']
            if topic not in topic_mapping:
                topic_mapping[topic] = {
                    'name': topic,
                    'code': topic,
                    'failed_questions': [],
                    'error_patterns': [],
                    'total_errors': 0
                }
            
            topic_mapping[topic]['failed_questions'].append(question)
            topic_mapping[topic]['error_patterns'].append(question['error_type'])
            topic_mapping[topic]['total_errors'] += 1
        
        # Convertir a lista y ordenar por número de errores
        topics = list(topic_mapping.values())
        topics.sort(key=lambda x: x['total_errors'], reverse=True)
        
        return topics
    
    def _build_dependency_graph(self, weak_topics: List[Dict[str, Any]], subject: str) -> Dict[str, Any]:
        """Construye grafo de dependencias entre temas"""
        # Mapeo de dependencias por materia
        dependencies = {
            'matematicas': {
                'algebra_basica': [],
                'ecuaciones_lineales': ['algebra_basica'],
                'ecuaciones_cuadraticas': ['ecuaciones_lineales', 'algebra_basica'],
                'funciones': ['ecuaciones_lineales'],
                'geometria': ['algebra_basica'],
                'trigonometria': ['geometria', 'algebra_basica'],
                'calculo': ['funciones', 'trigonometria']
            },
            'lenguaje': {
                'comprension_lectora': [],
                'analisis_textual': ['comprension_lectora'],
                'gramatica_basica': [],
                'sintaxis': ['gramatica_basica'],
                'literatura': ['comprension_lectora', 'analisis_textual']
            },
            'ciencias': {
                'biologia_celular': [],
                'genetica': ['biologia_celular'],
                'ecologia': ['biologia_celular'],
                'quimica_basica': [],
                'reacciones_quimicas': ['quimica_basica'],
                'fisica_mecanica': ['matematicas_basicas']
            }
        }
        
        # Construir grafo para la materia específica
        subject_deps = dependencies.get(subject, {})
        
        # Agregar temas débiles que no estén en dependencias
        for topic in weak_topics:
            topic_code = topic['code']
            if topic_code not in subject_deps:
                subject_deps[topic_code] = []
        
        return {
            'subject': subject,
            'topics': subject_deps,
            'weak_topics': [t['code'] for t in weak_topics]
        }
    
    def _optimize_learning_path(
        self, 
        learning_graph: Dict[str, Any], 
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Optimiza el camino de aprendizaje para el usuario específico"""
        topics = learning_graph['topics']
        weak_topics = learning_graph['weak_topics']
        
        # Ordenar temas por dependencias (orden topológico)
        ordered_topics = self._topological_sort(topics)
        
        # Filtrar solo temas débiles y sus dependencias
        relevant_topics = []
        for topic in ordered_topics:
            if topic in weak_topics or self._has_dependency_on_weak(topic, weak_topics, topics):
                relevant_topics.append(topic)
        
        # Limitar a máximo 8 módulos
        max_modules = 8
        if len(relevant_topics) > max_modules:
            # Priorizar temas con más errores
            relevant_topics = relevant_topics[:max_modules]
        
        # Construir módulos de aprendizaje
        modules = []
        for i, topic_code in enumerate(relevant_topics):
            module = {
                'id': f'MOD_{i+1:03d}',
                'week': (i // 3) + 1,  # 3 módulos por semana
                'topic_code': topic_code,
                'topic_name': self._get_topic_display_name(topic_code),
                'depends_on': topics.get(topic_code, []),
                'difficulty': self._calculate_topic_difficulty(topic_code, user_profile),
                'estimated_hours': self._estimate_topic_time(topic_code, user_profile),
                'priority': 'high' if topic_code in weak_topics else 'medium'
            }
            modules.append(module)
        
        return modules
    
    def _topological_sort(self, topics: Dict[str, List[str]]) -> List[str]:
        """Ordena temas por dependencias"""
        visited = set()
        temp_visited = set()
        order = []
        
        def dfs(topic):
            if topic in temp_visited:
                return  # Ciclo detectado
            if topic in visited:
                return
            
            temp_visited.add(topic)
            
            for dependency in topics.get(topic, []):
                dfs(dependency)
            
            temp_visited.remove(topic)
            visited.add(topic)
            order.append(topic)
        
        for topic in topics:
            if topic not in visited:
                dfs(topic)
        
        return order
    
    def _has_dependency_on_weak(self, topic: str, weak_topics: List[str], dependencies: Dict[str, List[str]]) -> bool:
        """Verifica si un tema depende de temas débiles"""
        for weak_topic in weak_topics:
            if weak_topic in dependencies.get(topic, []):
                return True
        return False
    
    def _get_topic_display_name(self, topic_code: str) -> str:
        """Obtiene nombre legible del tema"""
        display_names = {
            'algebra_basica': 'Álgebra Básica',
            'ecuaciones_lineales': 'Ecuaciones Lineales',
            'ecuaciones_cuadraticas': 'Ecuaciones Cuadráticas',
            'funciones': 'Funciones Matemáticas',
            'geometria': 'Geometría',
            'trigonometria': 'Trigonometría',
            'calculo': 'Cálculo Diferencial',
            'comprension_lectora': 'Comprensión Lectora',
            'analisis_textual': 'Análisis Textual',
            'gramatica_basica': 'Gramática Básica',
            'sintaxis': 'Sintaxis',
            'literatura': 'Literatura',
            'biologia_celular': 'Biología Celular',
            'genetica': 'Genética',
            'ecologia': 'Ecología',
            'quimica_basica': 'Química Básica',
            'reacciones_quimicas': 'Reacciones Químicas',
            'fisica_mecanica': 'Física Mecánica'
        }
        return display_names.get(topic_code, topic_code.title())
    
    def _calculate_topic_difficulty(self, topic_code: str, user_profile: Dict[str, Any]) -> str:
        """Calcula dificultad del tema para el usuario específico"""
        base_difficulty = {
            'algebra_basica': 'easy',
            'ecuaciones_lineales': 'medium',
            'ecuaciones_cuadraticas': 'hard',
            'funciones': 'medium',
            'geometria': 'medium',
            'trigonometria': 'hard',
            'calculo': 'expert'
        }
        
        difficulty = base_difficulty.get(topic_code, 'medium')
        
        # Ajustar según perfil del usuario
        if user_profile.get('confidence_level', 0.5) < 0.4:
            # Usuario con baja confianza, reducir dificultad
            if difficulty == 'hard':
                difficulty = 'medium'
            elif difficulty == 'expert':
                difficulty = 'hard'
        
        return difficulty
    
    def _estimate_topic_time(self, topic_code: str, user_profile: Dict[str, Any]) -> int:
        """Estima tiempo necesario para el tema"""
        base_time = {
            'easy': 2,
            'medium': 4,
            'hard': 6,
            'expert': 8
        }
        
        difficulty = self._calculate_topic_difficulty(topic_code, user_profile)
        base_hours = base_time.get(difficulty, 4)
        
        # Ajustar según ritmo del usuario
        pace = user_profile.get('pace', 'normal')
        if pace == 'slow':
            base_hours = int(base_hours * 1.5)
        elif pace == 'fast':
            base_hours = int(base_hours * 0.7)
        
        return base_hours
    
    async def _select_personalized_resources(
        self, 
        learning_path: List[Dict[str, Any]], 
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Selecciona recursos personalizados para el usuario"""
        resources = {}
        
        for module in learning_path:
            topic_code = module['topic_code']
            learning_style = user_profile.get('learning_style', 'visual')
            
            # Seleccionar videos según estilo de aprendizaje
            video_urls = self._select_videos_for_style(topic_code, learning_style)
            
            # Seleccionar ejercicios según nivel de confianza
            exercise_count = self._select_exercise_count(user_profile)
            
            # Seleccionar recursos adicionales
            additional_resources = self._select_additional_resources(topic_code, learning_style)
            
            resources[topic_code] = {
                'video_urls': video_urls,
                'exercise_count': exercise_count,
                'additional_resources': additional_resources,
                'style': learning_style,
                'estimated_duration': module['estimated_hours']
            }
        
        return resources
    
    def _select_videos_for_style(self, topic_code: str, learning_style: str) -> List[Dict[str, Any]]:
        """Selecciona videos del catálogo ICFES según el estilo de aprendizaje"""
        try:
            # Consultar videos del catálogo ICFES para este tema
            query = """
                SELECT 
                    video_id,
                    titulo,
                    descripcion,
                    duracion_segundos,
                    calidad,
                    codigo_tema,
                    area_evaluada,
                    dificultad,
                    estilo_aprendizaje,
                    url_video,
                    thumbnail_url
                FROM icfes_youtube_catalog 
                WHERE codigo_tema = :topic_code 
                  AND (estilo_aprendizaje = :learning_style OR estilo_aprendizaje = 'general')
                ORDER BY 
                    CASE WHEN estilo_aprendizaje = :learning_style THEN 1 ELSE 2 END,
                    dificultad ASC,
                    duracion_segundos ASC
                LIMIT 3
            """
            
            result = self.db.execute(query, {
                "topic_code": topic_code,
                "learning_style": learning_style
            })
            
            videos = []
            for row in result:
                video_data = {
                    'video_id': row.video_id,
                    'title': row.titulo,
                    'description': row.descripcion,
                    'duration_seconds': row.duracion_segundos,
                    'duration_minutes': round(row.duracion_segundos / 60, 1),
                    'quality': row.calidad,
                    'codigo_tema': row.codigo_tema,
                    'area_evaluada': row.area_evaluada,
                    'difficulty': row.dificultad,
                    'learning_style': row.estilo_aprendizaje,
                    'url': row.url_video,
                    'thumbnail': row.thumbnail_url,
                    'embed_url': f"https://www.youtube.com/embed/{row.video_id}",
                    'watch_url': f"https://www.youtube.com/watch?v={row.video_id}"
                }
                videos.append(video_data)
            
            # Si no hay videos específicos, buscar videos generales del tema
            if not videos:
                general_query = """
                    SELECT 
                        video_id, titulo, descripcion, duracion_segundos, 
                        calidad, codigo_tema, area_evaluada, dificultad,
                        estilo_aprendizaje, url_video, thumbnail_url
                    FROM icfes_youtube_catalog 
                    WHERE codigo_tema = :topic_code 
                    ORDER BY dificultad ASC, duracion_segundos ASC
                    LIMIT 2
                """
                
                general_result = self.db.execute(general_query, {"topic_code": topic_code})
                for row in general_result:
                    video_data = {
                        'video_id': row.video_id,
                        'title': row.titulo,
                        'description': row.descripcion,
                        'duration_seconds': row.duracion_segundos,
                        'duration_minutes': round(row.duracion_segundos / 60, 1),
                        'quality': row.calidad,
                        'codigo_tema': row.codigo_tema,
                        'area_evaluada': row.area_evaluada,
                        'difficulty': row.dificultad,
                        'learning_style': row.estilo_aprendizaje,
                        'url': row.url_video,
                        'thumbnail': row.thumbnail_url,
                        'embed_url': f"https://www.youtube.com/embed/{row.video_id}",
                        'watch_url': f"https://www.youtube.com/watch?v={row.video_id}"
                    }
                    videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error seleccionando videos para tema {topic_code}: {e}")
            # Fallback a videos por defecto
            return [{
                'video_id': 'dQw4w9WgXcQ',
                'title': f'Video de {topic_code}',
                'description': 'Video educativo recomendado',
                'duration_minutes': 15,
                'quality': 'HD',
                'codigo_tema': topic_code,
                'embed_url': f'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'watch_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }]
    
    def _select_exercise_count(self, user_profile: Dict[str, Any]) -> int:
        """Selecciona número de ejercicios según perfil del usuario"""
        confidence = user_profile.get('confidence_level', 0.5)
        pace = user_profile.get('pace', 'normal')
        
        base_count = 5
        if confidence < 0.4:
            base_count += 3  # Más práctica para usuarios con baja confianza
        elif confidence > 0.8:
            base_count -= 1  # Menos práctica para usuarios confiados
        
        if pace == 'slow':
            base_count += 2  # Más tiempo = más ejercicios
        elif pace == 'fast':
            base_count -= 1  # Menos tiempo = menos ejercicios
        
        return max(3, min(10, base_count))  # Entre 3 y 10 ejercicios
    
    def _select_additional_resources(self, topic_code: str, learning_style: str) -> List[Dict[str, str]]:
        """Selecciona recursos adicionales según tema y estilo"""
        resources = []
        
        if learning_style == 'visual':
            resources.extend([
                {'type': 'infographic', 'url': f'https://example.com/infographics/{topic_code}'},
                {'type': 'mind_map', 'url': f'https://example.com/mindmaps/{topic_code}'}
            ])
        elif learning_style == 'auditory':
            resources.extend([
                {'type': 'podcast', 'url': f'https://example.com/podcasts/{topic_code}'},
                {'type': 'audio_summary', 'url': f'https://example.com/audio/{topic_code}'}
            ])
        else:  # kinesthetic
            resources.extend([
                {'type': 'interactive_simulation', 'url': f'https://example.com/simulations/{topic_code}'},
                {'type': 'hands_on_activity', 'url': f'https://example.com/activities/{topic_code}'}
            ])
        
        return resources
    
    def _create_yml_structure(self, **kwargs) -> str:
        """Crea la estructura YML personalizada"""
        yml_dict = {
            'version': '2.0',
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': kwargs['user_id'],
            'subject': kwargs['subject'],
            
            # Personalización única para este usuario
            'personalization': {
                'learning_style': kwargs['user_profile']['learning_style'],
                'pace': kwargs['user_profile']['pace'],
                'confidence_level': kwargs['user_profile']['confidence_level'],
                'available_hours_per_week': kwargs['user_profile']['time_available'],
                'preferred_session_length': kwargs['user_profile']['session_length'],
                'user_level': kwargs['user_profile']['level'],
                'experience_points': kwargs['user_profile']['experience_points']
            },
            
            # Contexto del diagnóstico
            'diagnostic_context': {
                'total_questions': kwargs['diagnostic'].get('total_questions', 0),
                'failed_questions': len(kwargs['failed_questions']),
                'overall_score': kwargs['diagnostic'].get('overall_score', 0),
                'weak_areas': [q['topic'] for q in kwargs['failed_questions']],
                'specific_errors': [
                    {
                        'question_id': q['id'],
                        'topic': q['topic'],
                        'error_type': q['error_type'],
                        'your_answer': q['user_answer'],
                        'correct_answer': q['correct_answer'],
                        'difficulty': q['difficulty']
                    }
                    for q in kwargs['failed_questions']
                ]
            },
            
            # Módulos de aprendizaje personalizados
            'modules': self._generate_yml_modules(kwargs),
            
            # Reglas de adaptación específicas del usuario
            'adaptation_rules': {
                'speed_up_if_score_above': 0.9 if kwargs['user_profile']['pace'] == 'fast' else 0.95,
                'slow_down_if_score_below': 0.7 if kwargs['user_profile']['pace'] == 'slow' else 0.6,
                'max_daily_time_minutes': kwargs['user_profile']['session_length'],
                'reinforcement_frequency': 'high' if kwargs['user_profile']['confidence_level'] < 0.5 else 'normal',
                'review_schedule': [1, 3, 7, 14] if kwargs['user_profile']['confidence_level'] < 0.5 else [3, 7, 21]
            }
        }
        
        return yaml.dump(yml_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def _generate_yml_modules(self, kwargs) -> List[Dict[str, Any]]:
        """Genera módulos YML basados en el camino de aprendizaje"""
        modules = []
        
        for idx, module in enumerate(kwargs['learning_path'], 1):
            # Encontrar pregunta fallida para este tema
            failed_q = next(
                (q for q in kwargs['failed_questions'] if q['topic'] == module['topic_code']), 
                None
            )
            
            # Recursos para este tema
            topic_resources = kwargs['resources'].get(module['topic_code'], {})
            
            yml_module = {
                'id': module['id'],
                'week': module['week'],
                'topic_code': module['topic_code'],
                'topic_name': module['topic_name'],
                'difficulty': module['difficulty'],
                'estimated_hours': module['estimated_hours'],
                'priority': module['priority'],
                
                # Justificación de por qué existe este módulo
                'justification': self._generate_module_justification(module, failed_q),
                
                # Lecciones personalizadas
                'lessons': [
                    {
                        'id': f'LES_{idx:03d}_001',
                        'title': f"Dominando {module['topic_name']}",
                        
                        # Contexto del error del usuario
                        'your_mistake_context': self._generate_mistake_context(failed_q) if failed_q else None,
                        
                        # Recursos seleccionados para este usuario
                        'primary_resource': {
                            'videos': topic_resources.get('video_urls', []),  # Ahora contiene objetos completos de video
                            'duration_hours': topic_resources.get('estimated_duration', 2),
                            'style': topic_resources.get('style', 'visual'),
                            'difficulty': module['difficulty'],
                            'total_video_duration_minutes': sum(
                                [v.get('duration_minutes', 0) for v in topic_resources.get('video_urls', [])]
                            )
                        },
                        
                        # Explicaciones AI personalizadas
                        'ai_explanations': self._generate_ai_explanations(module, failed_q, kwargs['user_profile']),
                        
                        # Ejercicios adaptados
                        'exercises': {
                            'count': topic_resources.get('exercise_count', 5),
                            'difficulty': module['difficulty'],
                            'focus_areas': [failed_q['topic']] if failed_q else [],
                            'estimated_time_minutes': topic_resources.get('exercise_count', 5) * 3
                        },
                        
                        # Recursos adicionales
                        'additional_resources': topic_resources.get('additional_resources', []),
                        
                        # Horario de repaso personalizado
                        'review_schedule': kwargs['user_profile']['confidence_level'] < 0.5 and [1, 3, 7, 14] or [3, 7, 21]
                    }
                ]
            }
            
            modules.append(yml_module)
        
        return modules
    
    def _generate_module_justification(self, module: Dict[str, Any], failed_q: Optional[Dict[str, Any]]) -> str:
        """Genera justificación personalizada para el módulo"""
        if failed_q:
            return f"Este módulo existe porque tuviste dificultades con {module['topic_name']} en la pregunta {failed_q['id']}. El error tipo '{failed_q['error_type']}' sugiere que necesitas reforzar los conceptos fundamentales."
        else:
            return f"Este módulo es un prerrequisito para dominar {module['topic_name']}, basado en tu perfil de aprendizaje y el camino óptimo identificado."
    
    def _generate_mistake_context(self, failed_q: Dict[str, Any]) -> Dict[str, Any]:
        """Genera contexto del error del usuario"""
        return {
            'what_you_answered': failed_q['user_answer'],
            'why_it_was_wrong': self._explain_error_type(failed_q['error_type']),
            'correct_approach': f"La respuesta correcta es: {failed_q['correct_answer']}",
            'question_preview': failed_q['question_text'],
            'difficulty_level': failed_q['difficulty']
        }
    
    def _explain_error_type(self, error_type: str) -> str:
        """Explica por qué fue incorrecto según el tipo de error"""
        explanations = {
            'no_answer': 'No respondiste la pregunta. Es importante intentar siempre, incluso si no estás seguro.',
            'incomplete': 'Tu respuesta está incompleta. Asegúrate de considerar todos los aspectos de la pregunta.',
            'partial_correct': 'Estuviste cerca, pero hay un detalle importante que pasaste por alto.',
            'conceptual': 'El error sugiere una confusión en el concepto fundamental. Necesitamos revisar la base teórica.'
        }
        return explanations.get(error_type, 'Hay un error en tu razonamiento que necesitamos identificar y corregir.')
    
    def _generate_ai_explanations(
        self, 
        module: Dict[str, Any], 
        failed_q: Optional[Dict[str, Any]], 
        user_profile: Dict[str, Any]
    ) -> Dict[str, str]:
        """Genera explicaciones AI personalizadas"""
        learning_style = user_profile.get('learning_style', 'visual')
        
        explanations = {
            'before_video': f"Antes de ver el video sobre {module['topic_name']}, recuerda que este tema es fundamental para avanzar en tu preparación ICFES.",
            'key_moments': f"Durante el video, presta especial atención a los conceptos básicos de {module['topic_name']}. Estos serán la base para temas más avanzados.",
            'after_video': f"Después del video, practica con los ejercicios para consolidar tu comprensión de {module['topic_name']}."
        }
        
        if failed_q:
            explanations['before_video'] += f" Específicamente, este módulo te ayudará a corregir el error que tuviste en la pregunta {failed_q['id']}."
        
        # Personalizar según estilo de aprendizaje
        if learning_style == 'visual':
            explanations['key_moments'] += " Usa diagramas y esquemas para visualizar los conceptos."
        elif learning_style == 'auditory':
            explanations['key_moments'] += " Repite en voz alta los conceptos clave para memorizarlos mejor."
        else:  # kinesthetic
            explanations['key_moments'] += " Practica con ejemplos concretos y ejercicios prácticos."
        
        return explanations
    
    def _get_default_user_profile(self) -> Dict[str, Any]:
        """Perfil por defecto para usuarios nuevos"""
        return {
            'learning_style': 'visual',
            'pace': 'normal',
            'confidence_level': 0.5,
            'time_available': 30,
            'session_length': 25,
            'level': 1,
            'experience_points': 0
        }
    
    def _get_default_learning_patterns(self) -> Dict[str, Any]:
        """Patrones de aprendizaje por defecto"""
        return {
            'pace': 'normal',
            'avg_session_minutes': 25,
            'preferred_session_length': 25,
            'total_sessions': 0,
            'avg_questions_per_session': 0,
            'preferred_time': 'afternoon',
            'streak_days': 0,
            'weak_subjects': [],
            'strong_subjects': []
        }
