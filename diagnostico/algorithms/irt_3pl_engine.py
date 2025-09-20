#!/usr/bin/env python3
"""
IRT 3PL Engine - ICFES Leveling System

Implementación completa del modelo IRT 3-Parameter Logistic para:
1. Estimación de habilidad (theta) usando Maximum Likelihood Estimation
2. Selección adaptativa de ítems con máxima información Fisher
3. Criterios de parada basados en error estándar
4. Blueprint balanceado por dificultad y competencias

Author: Claude Code Assistant  
Date: 2024
"""

import numpy as np
import pandas as pd
import logging
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from scipy.optimize import minimize_scalar, brentq
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IRTItem:
    """Representa un ítem IRT con parámetros 3PL"""
    id: int
    statement: str
    subject_id: int
    topic_id: int
    competence: str
    difficulty_level: str
    
    # Parámetros IRT 3PL
    a: float  # Discriminación (0.5 - 2.0)
    b: float  # Dificultad (-3.0 a +3.0)  
    c: float  # Adivinanza (0.10 - 0.25)
    
    # Metadatos
    exposure_count: int = 0
    last_used: Optional[str] = None
    image_url: Optional[str] = None
    
    def probability(self, theta: float) -> float:
        """Calcula P(theta) usando modelo 3PL"""
        try:
            exp_term = np.exp(self.a * (theta - self.b))
            return self.c + (1 - self.c) * (exp_term / (1 + exp_term))
        except (OverflowError, RuntimeWarning):
            # Manejar overflow numérico
            if self.a * (theta - self.b) > 700:
                return 1.0 - 1e-10
            else:
                return self.c + 1e-10
    
    def information(self, theta: float) -> float:
        """Calcula información Fisher I(theta)"""
        p = self.probability(theta)
        q = 1 - p
        
        if p <= self.c + 1e-10 or q <= 1e-10:
            return 1e-10
            
        try:
            numerator = self.a**2 * (p - self.c)**2 * q
            denominator = p * (1 - self.c)**2
            return numerator / denominator
        except (ZeroDivisionError, OverflowError):
            return 1e-10


@dataclass  
class AdaptiveSession:
    """Sesión de evaluación adaptativa"""
    student_id: str
    subject_id: int
    subject_name: str
    started_at: str
    
    # Parámetros de la sesión
    max_items: int = 45
    min_items: int = 15
    target_se: float = 0.3
    theta_bounds: Tuple[float, float] = (-4.0, 4.0)
    
    # Estado actual
    current_theta: float = 0.0
    current_se: float = 10.0
    administered_items: List[IRTItem] = None
    responses: List[bool] = None
    response_times: List[float] = None
    theta_history: List[float] = None
    se_history: List[float] = None
    
    def __post_init__(self):
        if self.administered_items is None:
            self.administered_items = []
        if self.responses is None:
            self.responses = []
        if self.response_times is None:
            self.response_times = []
        if self.theta_history is None:
            self.theta_history = [0.0]
        if self.se_history is None:
            self.se_history = [10.0]
    
    @property
    def n_items(self) -> int:
        return len(self.administered_items)
    
    @property 
    def n_correct(self) -> int:
        return sum(self.responses) if self.responses else 0
    
    @property
    def accuracy(self) -> float:
        return self.n_correct / max(self.n_items, 1)
    
    def can_stop(self) -> bool:
        """Verifica si se puede terminar la sesión"""
        return (
            (self.n_items >= self.min_items and self.current_se <= self.target_se) or
            self.n_items >= self.max_items
        )
    
    def add_response(self, item: IRTItem, correct: bool, time_sec: float = 0.0):
        """Agrega respuesta y actualiza estimación theta"""
        self.administered_items.append(item)
        self.responses.append(correct)
        self.response_times.append(time_sec)
        
        # Actualizar theta y SE
        self.current_theta, self.current_se = self._estimate_theta()
        self.theta_history.append(self.current_theta)
        self.se_history.append(self.current_se)
        
    def _estimate_theta(self) -> Tuple[float, float]:
        """Estima theta usando Maximum Likelihood con log-sum-exp"""
        if not self.responses:
            return 0.0, 10.0
        
        # Grid search con estabilización numérica
        theta_grid = np.linspace(*self.theta_bounds, 81)  # Paso 0.1
        log_likelihoods = []
        
        for theta in theta_grid:
            log_lik = 0.0
            for item, response in zip(self.administered_items, self.responses):
                p = item.probability(theta)
                # Evitar log(0) 
                p = np.clip(p, 1e-10, 1 - 1e-10)
                
                if response:
                    log_lik += np.log(p)
                else:
                    log_lik += np.log(1 - p)
            
            log_likelihoods.append(log_lik)
        
        log_likelihoods = np.array(log_likelihoods)
        
        # Encontrar máximo usando log-sum-exp para estabilidad
        max_idx = np.argmax(log_likelihoods)
        theta_mle = theta_grid[max_idx]
        
        # Calcular SE usando información Fisher
        total_info = sum(item.information(theta_mle) for item in self.administered_items)
        se = 1 / np.sqrt(max(total_info, 1e-10))
        
        return theta_mle, se


class IRT3PLEngine:
    """Motor IRT 3PL para evaluación adaptativa"""
    
    def __init__(self, items_pool: List[Dict[str, Any]]):
        """
        Inicializar motor IRT
        
        Args:
            items_pool: Lista de diccionarios con información de ítems
        """
        self.items_pool = self._load_items(items_pool)
        self.subject_pools = self._organize_by_subject()
        
        # Blueprint de dificultad (percentajes)
        self.difficulty_blueprint = {
            'low': (0.25, 0.35),    # 25-35% fáciles (b < -0.5)
            'mid': (0.40, 0.50),    # 40-50% medias (-0.5 ≤ b ≤ 0.5) 
            'high': (0.15, 0.25)    # 15-25% difíciles (b > 0.5)
        }
        
        # Límites de exposición
        self.max_exposure_rate = 0.3  # Máximo 30% de estudiantes ven el mismo ítem
        
        logger.info(f"Motor IRT inicializado con {len(self.items_pool)} ítems")
        logger.info(f"Materias disponibles: {list(self.subject_pools.keys())}")
    
    def _load_items(self, items_data: List[Dict[str, Any]]) -> List[IRTItem]:
        """Carga ítems desde datos"""
        items = []
        for item_data in items_data:
            try:
                item = IRTItem(
                    id=item_data['id'],
                    statement=item_data['statement'],
                    subject_id=item_data['subject_id'], 
                    topic_id=item_data.get('topic_id', 0),
                    competence=item_data.get('competence', ''),
                    difficulty_level=item_data.get('difficulty', 'mid'),
                    a=float(item_data.get('irt_a', 1.0)),
                    b=float(item_data.get('irt_b', 0.0)),
                    c=float(item_data.get('irt_c', 0.25)),
                    image_url=item_data.get('image_url', '')
                )
                items.append(item)
            except (KeyError, ValueError) as e:
                logger.warning(f"Error cargando ítem {item_data.get('id', 'unknown')}: {e}")
                
        return items
    
    def _organize_by_subject(self) -> Dict[int, List[IRTItem]]:
        """Organiza ítems por materia"""
        pools = {}
        for item in self.items_pool:
            if item.subject_id not in pools:
                pools[item.subject_id] = []
            pools[item.subject_id].append(item)
        return pools
    
    def start_adaptive_session(self, student_id: str, subject_id: int, subject_name: str) -> AdaptiveSession:
        """Inicia nueva sesión adaptativa"""
        if subject_id not in self.subject_pools:
            raise ValueError(f"No hay ítems disponibles para materia {subject_id}")
            
        session = AdaptiveSession(
            student_id=student_id,
            subject_id=subject_id, 
            subject_name=subject_name,
            started_at=pd.Timestamp.now().isoformat()
        )
        
        logger.info(f"Sesión iniciada: {student_id} - {subject_name}")
        return session
    
    def select_next_item(self, session: AdaptiveSession) -> Optional[IRTItem]:
        """Selecciona próximo ítem usando máxima información Fisher con restricciones"""
        available_items = [
            item for item in self.subject_pools[session.subject_id]
            if item not in session.administered_items
        ]
        
        if not available_items:
            logger.warning(f"No hay más ítems disponibles para la sesión {session.student_id}")
            return None
        
        # Primera pregunta: dificultad media
        if session.n_items == 0:
            mid_items = [item for item in available_items if -0.2 <= item.b <= 0.2]
            if mid_items:
                return min(mid_items, key=lambda x: x.exposure_count)
        
        # Verificar blueprint de dificultad
        available_items = self._apply_blueprint_constraints(session, available_items)
        
        # Aplicar límites de exposición 
        available_items = self._apply_exposure_constraints(available_items)
        
        if not available_items:
            # Fallback: seleccionar cualquier ítem no usado
            fallback_items = [
                item for item in self.subject_pools[session.subject_id]
                if item not in session.administered_items
            ]
            if fallback_items:
                return fallback_items[0]
            return None
        
        # Seleccionar ítem con máxima información Fisher
        theta_current = session.current_theta
        
        item_scores = []
        for item in available_items:
            information = item.information(theta_current)
            # Penalizar por exposición alta
            exposure_penalty = item.exposure_count * 0.1
            score = information - exposure_penalty
            item_scores.append((item, score))
        
        # Seleccionar el mejor
        best_item = max(item_scores, key=lambda x: x[1])[0]
        best_item.exposure_count += 1
        
        return best_item
    
    def _apply_blueprint_constraints(self, session: AdaptiveSession, items: List[IRTItem]) -> List[IRTItem]:
        """Aplica restricciones de blueprint de dificultad"""
        current_counts = {'low': 0, 'mid': 0, 'high': 0}
        
        # Contar dificultades actuales
        for item in session.administered_items:
            if item.b < -0.5:
                current_counts['low'] += 1
            elif item.b > 0.5:
                current_counts['high'] += 1
            else:
                current_counts['mid'] += 1
        
        # Determinar qué tipo de dificultad necesitamos
        n_total = session.n_items + 1  # +1 para el próximo ítem
        target_ranges = {
            level: (
                int(self.difficulty_blueprint[level][0] * session.max_items),
                int(self.difficulty_blueprint[level][1] * session.max_items)
            )
            for level in ['low', 'mid', 'high']
        }
        
        # Filtrar ítems según necesidades del blueprint
        allowed_difficulties = []
        for level, (min_count, max_count) in target_ranges.items():
            if current_counts[level] < max_count:
                allowed_difficulties.append(level)
        
        if not allowed_difficulties:
            return items  # No hay restricciones activas
        
        # Filtrar ítems por dificultad permitida
        filtered_items = []
        for item in items:
            item_difficulty = 'low' if item.b < -0.5 else ('high' if item.b > 0.5 else 'mid')
            if item_difficulty in allowed_difficulties:
                filtered_items.append(item)
        
        return filtered_items or items  # Fallback a todos si no queda ninguno
    
    def _apply_exposure_constraints(self, items: List[IRTItem]) -> List[IRTItem]:
        """Aplica límites de exposición de ítems"""
        # En implementación real, esto dependería del número total de estudiantes
        # Por ahora, usar un límite absoluto
        max_exposure = 100  # Máximo número de veces que se puede usar un ítem
        
        return [item for item in items if item.exposure_count < max_exposure]
    
    def process_response(self, session: AdaptiveSession, item: IRTItem, 
                        correct: bool, response_time: float = 0.0) -> Dict[str, Any]:
        """Procesa respuesta del estudiante y actualiza sesión"""
        # Agregar respuesta
        session.add_response(item, correct, response_time)
        
        # Generar reporte del estado
        report = {
            'item_id': item.id,
            'correct': correct,
            'response_time': response_time,
            'theta_estimate': session.current_theta,
            'se_estimate': session.current_se,
            'n_items': session.n_items,
            'accuracy': session.accuracy,
            'can_stop': session.can_stop(),
            'theta_ci_95': self._calculate_confidence_interval(session.current_theta, session.current_se)
        }
        
        logger.info(f"Respuesta procesada - Theta: {session.current_theta:.3f} (±{session.current_se:.3f})")
        return report
    
    def _calculate_confidence_interval(self, theta: float, se: float, confidence: float = 0.95) -> Tuple[float, float]:
        """Calcula intervalo de confianza para theta"""
        z_score = norm.ppf((1 + confidence) / 2)
        margin = z_score * se
        return (theta - margin, theta + margin)
    
    def finalize_session(self, session: AdaptiveSession) -> Dict[str, Any]:
        """Finaliza sesión y genera reporte completo"""
        # Calcular métricas finales
        theta_ci = self._calculate_confidence_interval(session.current_theta, session.current_se)
        
        # Clasificar nivel de habilidad  
        ability_level = self._classify_ability_level(session.current_theta)
        
        # Identificar fortalezas y debilidades por tema
        topic_analysis = self._analyze_topics(session)
        
        # Generar reporte final
        final_report = {
            'session_id': f"{session.student_id}_{session.subject_id}_{session.started_at}",
            'student_id': session.student_id,
            'subject_id': session.subject_id,
            'subject_name': session.subject_name,
            'started_at': session.started_at,
            'finished_at': pd.Timestamp.now().isoformat(),
            
            # Resultados IRT
            'theta_final': session.current_theta,
            'se_final': session.current_se,
            'theta_ci_95': theta_ci,
            'ability_level': ability_level,
            
            # Estadísticas básicas
            'total_items': session.n_items,
            'correct_items': session.n_correct,
            'accuracy': session.accuracy,
            'avg_response_time': np.mean(session.response_times) if session.response_times else 0,
            
            # Análisis por temas
            'topic_analysis': topic_analysis,
            
            # Trayectoria de estimación
            'theta_trajectory': session.theta_history,
            'se_trajectory': session.se_history,
            
            # Items administrados (para logging)
            'items_used': [
                {
                    'id': item.id,
                    'difficulty_b': item.b, 
                    'discrimination_a': item.a,
                    'guessing_c': item.c,
                    'correct': response,
                    'time': time_sec
                }
                for item, response, time_sec in zip(
                    session.administered_items, 
                    session.responses, 
                    session.response_times
                )
            ]
        }
        
        logger.info(f"Sesión finalizada - {session.student_id}: θ={session.current_theta:.3f} ({ability_level})")
        return final_report
    
    def _classify_ability_level(self, theta: float) -> str:
        """Clasifica nivel de habilidad basado en theta"""
        if theta < -1.5:
            return "Insuficiente"
        elif theta < -0.5:
            return "Mínimo" 
        elif theta < 0.5:
            return "Satisfactorio"
        elif theta < 1.5:
            return "Avanzado"
        else:
            return "Superior"
    
    def _analyze_topics(self, session: AdaptiveSession) -> Dict[str, Any]:
        """Analiza desempeño por tema/competencia"""
        topic_stats = {}
        
        for item, correct, time_sec in zip(session.administered_items, session.responses, session.response_times):
            topic_key = f"{item.topic_id}_{item.competence}" if item.competence else str(item.topic_id)
            
            if topic_key not in topic_stats:
                topic_stats[topic_key] = {
                    'topic_id': item.topic_id,
                    'competence': item.competence,
                    'n_items': 0,
                    'n_correct': 0,
                    'avg_difficulty': 0,
                    'avg_time': 0,
                    'strengths': [],
                    'weaknesses': []
                }
            
            stats = topic_stats[topic_key]
            stats['n_items'] += 1
            stats['n_correct'] += int(correct)
            stats['avg_difficulty'] = (stats['avg_difficulty'] * (stats['n_items'] - 1) + item.b) / stats['n_items']
            stats['avg_time'] = (stats['avg_time'] * (stats['n_items'] - 1) + time_sec) / stats['n_items']
            
            # Clasificar fortalezas/debilidades
            if correct and item.b > 0.5:  # Respondió correctamente una pregunta difícil
                stats['strengths'].append(item.id)
            elif not correct and item.b < -0.5:  # Falló una pregunta fácil
                stats['weaknesses'].append(item.id)
        
        # Calcular accuracy por tema
        for stats in topic_stats.values():
            stats['accuracy'] = stats['n_correct'] / stats['n_items'] if stats['n_items'] > 0 else 0
            
        return topic_stats


def main():
    """Función principal para testing del motor IRT"""
    # Datos de ejemplo para testing
    sample_items = [
        {
            'id': 1, 'statement': 'Pregunta fácil matemáticas', 'subject_id': 1,
            'topic_id': 1, 'competence': 'Razonamiento', 'difficulty': 'low',
            'irt_a': 1.2, 'irt_b': -1.0, 'irt_c': 0.2
        },
        {
            'id': 2, 'statement': 'Pregunta media matemáticas', 'subject_id': 1, 
            'topic_id': 1, 'competence': 'Resolución', 'difficulty': 'mid',
            'irt_a': 1.5, 'irt_b': 0.0, 'irt_c': 0.25
        },
        {
            'id': 3, 'statement': 'Pregunta difícil matemáticas', 'subject_id': 1,
            'topic_id': 2, 'competence': 'Comunicación', 'difficulty': 'high', 
            'irt_a': 1.8, 'irt_b': 1.2, 'irt_c': 0.15
        }
    ]
    
    # Inicializar motor
    engine = IRT3PLEngine(sample_items)
    
    # Simular sesión adaptativa
    session = engine.start_adaptive_session("student_001", 1, "Matemáticas")
    
    # Simular algunas respuestas
    for i in range(3):
        item = engine.select_next_item(session)
        if item:
            # Simular respuesta (50% probabilidad de acierto)
            correct = np.random.random() > 0.5
            response_time = np.random.uniform(10, 60)
            
            report = engine.process_response(session, item, correct, response_time)
            print(f"Item {item.id}: Correct={correct}, Theta={report['theta_estimate']:.3f}")
        
        if session.can_stop():
            break
    
    # Finalizar sesión
    final_report = engine.finalize_session(session)
    print(f"\nSesión finalizada:")
    print(f"Theta final: {final_report['theta_final']:.3f}")
    print(f"Nivel: {final_report['ability_level']}")
    print(f"Precisión: {final_report['accuracy']:.1%}")


if __name__ == "__main__":
    main()