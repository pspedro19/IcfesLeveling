"""
Motor principal de recomendaciones ICFES
WHY: Integra los 337 temas con análisis IRT y genera rutas adaptativas
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
from datetime import datetime, timedelta
import logging
import math

from ...models.icfes.study_topics_catalog import StudyTopicsCatalog
from ...models.question import Question
from ...models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ...services.cache_service import cache_service

logger = logging.getLogger(__name__)

class ICFESRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        
    def generate_personalized_study_path(
        self,
        user_id: str,
        target_date: datetime,
        target_score: int = 350
    ) -> Dict[str, Any]:
        """
        Genera ruta de estudio personalizada usando los 337 temas
        
        WHY: Cada estudiante necesita un camino único basado en:
        - Sus debilidades específicas detectadas
        - El tiempo disponible hasta el examen
        - Los prerequisitos entre temas
        - Su velocidad de aprendizaje histórica
        """
        
        # Cache key única para este usuario
        cache_key = f"icfes_path:{user_id}:{target_date.isoformat()}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached
        
        # 1. ANÁLISIS DIAGNÓSTICO
        diagnostic_analysis = self._analyze_diagnostic_results(user_id)
        
        # 2. IDENTIFICAR TEMAS CRÍTICOS
        critical_topics = self._identify_critical_topics(
            diagnostic_analysis,
            target_score
        )
        
        # 3. CONSTRUIR GRAFO DE DEPENDENCIAS
        dependency_graph = self._build_dependency_graph(critical_topics)
        
        # 4. ORDENAMIENTO TOPOLÓGICO (respetando prerequisitos)
        ordered_topics = self._topological_sort(dependency_graph)
        
        # 5. CALCULAR TIEMPO POR TEMA
        time_allocation = self._allocate_study_time(
            ordered_topics,
            target_date,
            diagnostic_analysis['learning_speed']
        )
        
        # 6. SELECCIONAR RECURSOS ÓPTIMOS
        resources = self._select_optimal_resources(
            ordered_topics,
            diagnostic_analysis['learning_style']
        )
        
        # 7. CREAR PLAN DETALLADO
        study_path = {
            "user_id": user_id,
            "target_date": target_date.isoformat(),
            "target_score": target_score,
            "current_estimated_score": diagnostic_analysis['current_score'],
            "total_topics": len(ordered_topics),
            "total_study_hours": sum(time_allocation.values()),
            "topics_sequence": ordered_topics,
            "time_per_topic": time_allocation,
            "resources_per_topic": resources,
            "milestones": self._generate_milestones(ordered_topics, target_date),
            "success_probability": self._calculate_success_probability(
                diagnostic_analysis,
                target_score,
                sum(time_allocation.values())
            )
        }
        
        # Cache por 24 horas
        cache_service.set(cache_key, study_path, expire=86400)
        
        return study_path
    
    def _analyze_diagnostic_results(self, user_id: str) -> Dict[str, Any]:
        """
        Analiza resultados diagnósticos con enfoque en competencias ICFES
        """
        # Obtener último test diagnóstico
        latest_test = self.db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == user_id,
            DiagnosticTest.status == 'completed'
        ).order_by(DiagnosticTest.completed_at.desc()).first()
        
        if not latest_test:
            return self._get_default_analysis()
        
        # Analizar respuestas por competencia
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.test_id == latest_test.id
        ).all()
        
        competency_scores = {}
        topic_scores = {}
        
        for answer in answers:
            question = answer.question
            if question:
                # Análisis por competencia
                if question.competencia:
                    if question.competencia not in competency_scores:
                        competency_scores[question.competencia] = {
                            'correct': 0, 'total': 0
                        }
                    competency_scores[question.competencia]['total'] += 1
                    if answer.is_correct:
                        competency_scores[question.competencia]['correct'] += 1
                
                # Análisis por tema
                if question.codigo_tema:
                    if question.codigo_tema not in topic_scores:
                        topic_scores[question.codigo_tema] = {
                            'correct': 0, 'total': 0, 'avg_time': []
                        }
                    topic_scores[question.codigo_tema]['total'] += 1
                    if answer.is_correct:
                        topic_scores[question.codigo_tema]['correct'] += 1
                    if answer.response_time_ms:
                        topic_scores[question.codigo_tema]['avg_time'].append(
                            answer.response_time_ms
                        )
        
        # Calcular scores finales
        for comp in competency_scores:
            data = competency_scores[comp]
            competency_scores[comp]['score'] = (
                data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
            )
        
        for topic in topic_scores:
            data = topic_scores[topic]
            topic_scores[topic]['score'] = (
                data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
            )
            topic_scores[topic]['avg_response_time'] = (
                np.mean(data['avg_time']) if data['avg_time'] else 0
            )
        
        # Estimar score ICFES actual
        current_score = self._estimate_icfes_score(competency_scores)
        
        # Detectar estilo de aprendizaje
        learning_style = self._detect_learning_style(answers)
        
        # Calcular velocidad de aprendizaje
        learning_speed = self._calculate_learning_speed(user_id)
        
        return {
            'current_score': current_score,
            'competency_scores': competency_scores,
            'topic_scores': topic_scores,
            'learning_style': learning_style,
            'learning_speed': learning_speed,
            'weakest_competencies': self._get_weakest_competencies(competency_scores),
            'weakest_topics': self._get_weakest_topics(topic_scores)
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Retorna análisis por defecto para usuarios nuevos"""
        return {
            'current_score': 200,  # Score base
            'competency_scores': {},
            'topic_scores': {},
            'learning_style': 'visual',
            'learning_speed': 1.0,
            'weakest_competencies': [],
            'weakest_topics': []
        }
    
    def _identify_critical_topics(
        self,
        analysis: Dict[str, Any],
        target_score: int
    ) -> List[str]:
        """
        Identifica temas críticos basados en debilidades y objetivo
        """
        critical_topics = []
        
        # Obtener todos los temas del catálogo
        all_topics = self.db.query(StudyTopicsCatalog).filter(
            StudyTopicsCatalog.estado == 'activo'
        ).all()
        
        # Calcular gap para alcanzar objetivo
        score_gap = target_score - analysis['current_score']
        
        # Priorizar temas según:
        # 1. Debilidades actuales
        # 2. Importancia ICFES
        # 3. Frecuencia en el examen
        
        for topic in all_topics:
            topic_score = analysis['topic_scores'].get(
                topic.codigo_tema, {'score': 0}
            )['score']
            
            # Calcular prioridad
            priority = 0
            
            # Factor 1: Debilidad (más débil = más prioritario)
            if topic_score < 40:
                priority += 5
            elif topic_score < 60:
                priority += 3
            elif topic_score < 80:
                priority += 1
            
            # Factor 2: Importancia ICFES
            priority += topic.importancia_icfes or 0
            
            # Factor 3: Frecuencia de evaluación
            priority += (topic.frecuencia_evaluacion or 0) / 10
            
            # Factor 4: Gap específico para alcanzar objetivo
            if score_gap > 100 and topic.nivel_dificultad <= 3:
                priority += 2  # Enfocarse en temas básicos/intermedios
            elif score_gap > 50 and topic.nivel_dificultad <= 4:
                priority += 1
            
            if priority >= 3:  # Umbral de inclusión
                critical_topics.append({
                    'codigo': topic.codigo_tema,
                    'priority': priority,
                    'current_score': topic_score,
                    'importance': topic.importancia_icfes,
                    'difficulty': topic.nivel_dificultad
                })
        
        # Ordenar por prioridad y tomar los más importantes
        critical_topics.sort(key=lambda x: x['priority'], reverse=True)
        
        # Limitar según tiempo disponible (máximo 100 temas)
        return [t['codigo'] for t in critical_topics[:100]]
    
    def _build_dependency_graph(self, topics: List[str]) -> Dict[str, List[str]]:
        """
        Construye grafo de dependencias entre temas
        """
        graph = {topic: [] for topic in topics}
        
        for topic_code in topics:
            topic = self.db.query(StudyTopicsCatalog).filter(
                StudyTopicsCatalog.codigo_tema == topic_code
            ).first()
            
            if topic and topic.prerequisitos:
                for prereq in topic.prerequisitos:
                    if prereq in topics:
                        # El prerequisito debe venir antes
                        graph[prereq].append(topic_code)
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Ordenamiento topológico para respetar prerequisitos
        Algoritmo de Kahn
        """
        from collections import deque
        
        # Calcular grado de entrada
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        # Cola con nodos sin dependencias
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        sorted_topics = []
        
        while queue:
            node = queue.popleft()
            sorted_topics.append(node)
            
            # Reducir grado de entrada de vecinos
            for neighbor in graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # Verificar ciclos
        if len(sorted_topics) != len(graph):
            logger.warning("Ciclo detectado en dependencias, usando orden parcial")
            # Agregar nodos faltantes al final
            for node in graph:
                if node not in sorted_topics:
                    sorted_topics.append(node)
        
        return sorted_topics
    
    def _allocate_study_time(
        self,
        topics: List[str],
        target_date: datetime,
        learning_speed: float
    ) -> Dict[str, int]:
        """
        Asigna tiempo de estudio por tema según dificultad y velocidad
        """
        days_available = (target_date - datetime.now()).days
        hours_available = days_available * 4  # 4 horas promedio por día
        
        time_allocation = {}
        total_weight = 0
        
        # Calcular peso de cada tema
        topic_weights = {}
        for topic_code in topics:
            topic = self.db.query(StudyTopicsCatalog).filter(
                StudyTopicsCatalog.codigo_tema == topic_code
            ).first()
            
            if topic:
                # Base: horas recomendadas del catálogo
                base_hours = topic.calculate_study_hours()
                
                # Ajustar por velocidad de aprendizaje
                adjusted_hours = base_hours / learning_speed
                
                # Ajustar por dificultad
                difficulty_factor = 1 + (topic.nivel_dificultad - 3) * 0.2
                final_hours = adjusted_hours * difficulty_factor
                
                topic_weights[topic_code] = max(1, int(final_hours))
                total_weight += topic_weights[topic_code]
        
        # Distribuir tiempo proporcionalmente
        if total_weight > hours_available:
            # Comprimir tiempos proporcionalmente
            compression_ratio = hours_available / total_weight
            for topic_code, weight in topic_weights.items():
                time_allocation[topic_code] = max(1, int(weight * compression_ratio))
        else:
            time_allocation = topic_weights
        
        return time_allocation
    
    def _select_optimal_resources(
        self,
        topics: List[str],
        learning_style: str
    ) -> Dict[str, List[Dict]]:
        """
        Selecciona recursos óptimos por tema según estilo de aprendizaje
        """
        resources_per_topic = {}
        
        for topic_code in topics:
            # Obtener tema del catálogo
            topic = self.db.query(StudyTopicsCatalog).filter(
                StudyTopicsCatalog.codigo_tema == topic_code
            ).first()
            
            if not topic:
                continue
            
            resources = []
            
            # Recursos del catálogo
            if topic.recursos_teoria:
                resources.extend([
                    {'type': 'teoria', 'url': r, 'priority': 1}
                    for r in topic.recursos_teoria[:2]
                ])
            
            if topic.recursos_practica:
                resources.extend([
                    {'type': 'practica', 'url': r, 'priority': 2}
                    for r in topic.recursos_practica[:3]
                ])
            
            # Buscar recursos adicionales en la tabla learning_resources
            # (implementar cuando se cree la tabla)
            
            resources_per_topic[topic_code] = resources
        
        return resources_per_topic
    
    def _generate_milestones(
        self,
        topics: List[str],
        target_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Genera hitos de evaluación durante el plan
        """
        milestones = []
        total_topics = len(topics)
        days_available = (target_date - datetime.now()).days
        
        # Crear hitos cada 20% de progreso
        milestone_points = [0.2, 0.4, 0.6, 0.8, 1.0]
        
        for point in milestone_points:
            milestone_date = datetime.now() + timedelta(
                days=int(days_available * point)
            )
            topics_to_complete = int(total_topics * point)
            
            milestones.append({
                'date': milestone_date.isoformat(),
                'progress_target': point * 100,
                'topics_to_complete': topics_to_complete,
                'evaluation_type': 'simulacro' if point >= 0.6 else 'quiz',
                'description': f"Completar {topics_to_complete} temas"
            })
        
        return milestones
    
    def _calculate_success_probability(
        self,
        analysis: Dict,
        target_score: int,
        study_hours: int
    ) -> float:
        """
        Calcula probabilidad de éxito usando modelo predictivo
        """
        current_score = analysis['current_score']
        score_gap = target_score - current_score
        learning_speed = analysis['learning_speed']
        
        # Modelo simplificado (en producción usar ML)
        # Factores:
        # 1. Gap de puntaje
        # 2. Horas de estudio disponibles
        # 3. Velocidad de aprendizaje histórica
        
        # Factor 1: Dificultad del gap
        if score_gap <= 50:
            gap_factor = 0.9
        elif score_gap <= 100:
            gap_factor = 0.7
        elif score_gap <= 150:
            gap_factor = 0.5
        else:
            gap_factor = 0.3
        
        # Factor 2: Tiempo de estudio
        hours_per_point = study_hours / max(score_gap, 1)
        if hours_per_point >= 2:
            time_factor = 0.9
        elif hours_per_point >= 1:
            time_factor = 0.7
        elif hours_per_point >= 0.5:
            time_factor = 0.5
        else:
            time_factor = 0.3
        
        # Factor 3: Velocidad de aprendizaje
        speed_factor = min(1.0, learning_speed)
        
        # Probabilidad final
        probability = gap_factor * time_factor * speed_factor
        
        return min(0.95, max(0.05, probability))
    
    def _estimate_icfes_score(self, competency_scores: Dict) -> int:
        """Estima score ICFES basado en competencias"""
        if not competency_scores:
            return 200  # Score base
        
        total_score = 0
        total_weight = 0
        
        for comp, data in competency_scores.items():
            weight = self._get_competency_weight(comp)
            total_score += data['score'] * weight
            total_weight += weight
        
        if total_weight == 0:
            return 200
        
        estimated_score = total_score / total_weight
        return int(estimated_score * 5)  # Escalar a 500 puntos
    
    def _get_competency_weight(self, competency: str) -> float:
        """Retorna peso de competencia en el examen ICFES"""
        weights = {
            'Identificar y entender los contenidos locales': 0.35,
            'Comprender cómo se articulan las partes de un texto': 0.35,
            'Reflexionar a partir de un texto': 0.30,
            'Formulación y ejecución': 0.43,
            'Interpretación y representación': 0.34,
            'Indagación': 0.40,
            'Explicación de fenómenos': 0.30,
            'Uso comprensivo del conocimiento científico': 0.30,
            'Pensamiento social': 0.40,
            'Interpretación y análisis de perspectivas': 0.30,
            'Pensamiento reflexivo y sistémico': 0.30,
            'Lingüística': 0.40,
            'Pragmática': 0.30,
            'Sociolingüística': 0.30
        }
        return weights.get(competency, 0.25)
    
    def _detect_learning_style(self, answers: List[DiagnosticTestAnswer]) -> str:
        """Detecta estilo de aprendizaje basado en respuestas"""
        # Implementar lógica de detección
        return 'visual'  # Por defecto
    
    def _calculate_learning_speed(self, user_id: str) -> float:
        """Calcula velocidad de aprendizaje del usuario"""
        # Implementar cálculo basado en progreso histórico
        return 1.0  # Factor base
    
    def _get_weakest_competencies(self, competency_scores: Dict) -> List[str]:
        """Retorna las competencias más débiles"""
        if not competency_scores:
            return []
        
        sorted_competencies = sorted(
            competency_scores.items(),
            key=lambda x: x[1]['score']
        )
        return [comp for comp, _ in sorted_competencies[:3]]
    
    def _get_weakest_topics(self, topic_scores: Dict) -> List[str]:
        """Retorna los temas más débiles"""
        if not topic_scores:
            return []
        
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: x[1]['score']
        )
        return [topic for topic, _ in sorted_topics[:5]]
