"""
Tests para el servicio de recomendaciones ICFES
WHY: Asegurar que el motor maneja correctamente los 337 temas
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.services.icfes.icfes_recommendation_service import ICFESRecommendationService
from app.models.icfes.study_topics_catalog import StudyTopicsCatalog

class TestICFESRecommendationService:
    
    @pytest.fixture
    def mock_db(self):
        """Mock de la sesión de base de datos"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Instancia del servicio con DB mockeada"""
        return ICFESRecommendationService(mock_db)
    
    @pytest.fixture
    def sample_topics(self):
        """Temas de ejemplo para testing"""
        return [
            StudyTopicsCatalog(
                codigo_tema="LC001",
                area_evaluada="Lectura Crítica",
                tema_principal="Comprensión literal",
                subtema="Información explícita",
                competencia_icfes="Identificar y entender los contenidos locales",
                nivel_dificultad=1,
                importancia_icfes=5,
                prerequisitos=[],
                temas_relacionados=["LC002", "LC003"],
                orden_secuencial=1,
                horas_teoria=3,
                horas_practica=5
            ),
            StudyTopicsCatalog(
                codigo_tema="LC002",
                area_evaluada="Lectura Crítica",
                tema_principal="Comprensión literal",
                subtema="Ideas principales",
                competencia_icfes="Identificar y entender los contenidos locales",
                nivel_dificultad=1,
                importancia_icfes=5,
                prerequisitos=["LC001"],
                temas_relacionados=["LC004", "LC005"],
                orden_secuencial=2,
                horas_teoria=4,
                horas_practica=6
            ),
            StudyTopicsCatalog(
                codigo_tema="MAT001",
                area_evaluada="Matemáticas",
                tema_principal="Números reales",
                subtema="Operaciones básicas",
                competencia_icfes="Formulación y ejecución",
                nivel_dificultad=1,
                importancia_icfes=5,
                prerequisitos=[],
                temas_relacionados=["MAT002", "MAT003"],
                orden_secuencial=1,
                horas_teoria=2,
                horas_practica=6
            )
        ]
    
    def test_service_initialization(self, mock_db):
        """Verifica que el servicio se inicializa correctamente"""
        service = ICFESRecommendationService(mock_db)
        assert service.db == mock_db
        assert hasattr(service, 'generate_personalized_study_path')
    
    def test_generate_study_path_basic(self, service, mock_db, sample_topics):
        """Verifica generación básica de plan de estudio"""
        # Mock de la base de datos
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        # Mock del análisis por defecto
        with patch.object(service, '_analyze_diagnostic_results') as mock_analyze:
            mock_analyze.return_value = {
                'current_score': 250,
                'competency_scores': {},
                'topic_scores': {},
                'learning_style': 'visual',
                'learning_speed': 1.0,
                'weakest_competencies': [],
                'weakest_topics': []
            }
        
        # Mock de identificación de temas críticos
        with patch.object(service, '_identify_critical_topics') as mock_identify:
            mock_identify.return_value = ["LC001", "LC002", "MAT001"]
        
        # Mock de construcción de grafo
        with patch.object(service, '_build_dependency_graph') as mock_graph:
            mock_graph.return_value = {
                "LC001": ["LC002"],
                "LC002": [],
                "MAT001": []
            }
        
        # Mock de ordenamiento topológico
        with patch.object(service, '_topological_sort') as mock_sort:
            mock_sort.return_value = ["LC001", "LC002", "MAT001"]
        
        # Mock de asignación de tiempo
        with patch.object(service, '_allocate_study_time') as mock_time:
            mock_time.return_value = {
                "LC001": 8,
                "LC002": 10,
                "MAT001": 8
            }
        
        # Mock de selección de recursos
        with patch.object(service, '_select_optimal_resources') as mock_resources:
            mock_resources.return_value = {
                "LC001": [],
                "LC002": [],
                "MAT001": []
            }
        
        # Mock de generación de hitos
        with patch.object(service, '_generate_milestones') as mock_milestones:
            mock_milestones.return_value = []
        
        # Mock de cálculo de probabilidad
        with patch.object(service, '_calculate_success_probability') as mock_prob:
            mock_prob.return_value = 0.75
        
        # Ejecutar método
        target_date = datetime.now() + timedelta(days=90)
        result = service.generate_personalized_study_path(
            user_id="test_user",
            target_date=target_date,
            target_score=350
        )
        
        # Verificaciones
        assert result is not None
        assert 'user_id' in result
        assert 'target_date' in result
        assert 'target_score' in result
        assert 'topics_sequence' in result
        assert 'time_per_topic' in result
        assert 'success_probability' in result
        
        assert result['user_id'] == "test_user"
        assert result['target_score'] == 350
        assert len(result['topics_sequence']) == 3
        assert result['success_probability'] == 0.75
    
    def test_identify_critical_topics(self, service, mock_db, sample_topics):
        """Verifica identificación de temas críticos"""
        # Mock de la consulta de temas
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = sample_topics
        mock_db.query.return_value = mock_query
        
        # Mock del análisis
        analysis = {
            'current_score': 250,
            'topic_scores': {
                'LC001': {'score': 30},  # Débil
                'LC002': {'score': 70},  # Medio
                'MAT001': {'score': 45}  # Débil
            }
        }
        
        target_score = 350
        
        # Ejecutar método
        critical_topics = service._identify_critical_topics(analysis, target_score)
        
        # Verificaciones
        assert isinstance(critical_topics, list)
        assert len(critical_topics) > 0
        
        # Los temas débiles deberían tener prioridad
        assert "LC001" in critical_topics
        assert "MAT001" in critical_topics
    
    def test_build_dependency_graph(self, service, mock_db, sample_topics):
        """Verifica construcción del grafo de dependencias"""
        # Mock de la consulta de temas
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = sample_topics
        mock_db.query.return_value = mock_query
        
        topics = ["LC001", "LC002", "MAT001"]
        
        # Ejecutar método
        graph = service._build_dependency_graph(topics)
        
        # Verificaciones
        assert isinstance(graph, dict)
        assert all(topic in graph for topic in topics)
        
        # Verificar dependencias
        assert "LC002" in graph["LC001"]  # LC001 es prerequisito de LC002
        assert "MAT001" not in graph["LC001"]  # No hay dependencia
    
    def test_topological_sort(self, service):
        """Verifica ordenamiento topológico"""
        # Grafo de dependencias simple
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": []
        }
        
        # Ejecutar método
        sorted_topics = service._topological_sort(graph)
        
        # Verificaciones
        assert isinstance(sorted_topics, list)
        assert len(sorted_topics) == 4
        
        # Verificar que D viene después de B y C
        d_index = sorted_topics.index("D")
        b_index = sorted_topics.index("B")
        c_index = sorted_topics.index("C")
        
        assert d_index > b_index
        assert d_index > c_index
    
    def test_allocate_study_time(self, service, mock_db, sample_topics):
        """Verifica asignación de tiempo de estudio"""
        # Mock de la consulta de temas
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = sample_topics
        mock_db.query.return_value = mock_query
        
        topics = ["LC001", "LC002", "MAT001"]
        target_date = datetime.now() + timedelta(days=30)
        learning_speed = 1.0
        
        # Ejecutar método
        time_allocation = service._allocate_study_time(topics, target_date, learning_speed)
        
        # Verificaciones
        assert isinstance(time_allocation, dict)
        assert all(topic in time_allocation for topic in topics)
        assert all(isinstance(hours, int) for hours in time_allocation.values())
        assert all(hours > 0 for hours in time_allocation.values())
        
        # Verificar que el tiempo total no excede lo disponible
        total_hours = sum(time_allocation.values())
        max_hours = 30 * 4  # 30 días * 4 horas/día
        assert total_hours <= max_hours
    
    def test_calculate_success_probability(self, service):
        """Verifica cálculo de probabilidad de éxito"""
        analysis = {
            'current_score': 250,
            'learning_speed': 1.0
        }
        target_score = 350
        study_hours = 120
        
        # Ejecutar método
        probability = service._calculate_success_probability(analysis, target_score, study_hours)
        
        # Verificaciones
        assert isinstance(probability, float)
        assert 0.05 <= probability <= 0.95
        
        # Verificar que probabilidad es menor para gaps mayores
        analysis_large_gap = {'current_score': 200, 'learning_speed': 1.0}
        probability_large_gap = service._calculate_success_probability(
            analysis_large_gap, target_score, study_hours
        )
        
        assert probability_large_gap <= probability
    
    def test_estimate_icfes_score(self, service):
        """Verifica estimación de score ICFES"""
        competency_scores = {
            'Comprensión literal': {'score': 80.0},
            'Análisis crítico': {'score': 60.0},
            'Matemáticas básicas': {'score': 70.0}
        }
        
        # Ejecutar método
        estimated_score = service._estimate_icfes_score(competency_scores)
        
        # Verificaciones
        assert isinstance(estimated_score, int)
        assert 200 <= estimated_score <= 500
        
        # Score vacío debería retornar valor por defecto
        empty_score = service._estimate_icfes_score({})
        assert empty_score == 200
    
    def test_get_competency_weight(self, service):
        """Verifica pesos de competencias"""
        # Verificar pesos conocidos
        assert service._get_competency_weight('Identificar y entender los contenidos locales') == 0.35
        assert service._get_competency_weight('Formulación y ejecución') == 0.43
        assert service._get_competency_weight('Indagación') == 0.40
        
        # Competencia desconocida debería retornar peso por defecto
        assert service._get_competency_weight('Competencia desconocida') == 0.25
    
    def test_error_handling(self, service, mock_db):
        """Verifica manejo de errores"""
        # Mock de error en base de datos
        mock_db.query.side_effect = Exception("Database error")
        
        # El método debería manejar el error graciosamente
        with pytest.raises(Exception):
            service._identify_critical_topics({}, 350)
    
    def test_empty_topics_list(self, service):
        """Verifica comportamiento con lista vacía de temas"""
        # Métodos deberían manejar listas vacías
        empty_graph = service._build_dependency_graph([])
        assert empty_graph == {}
        
        empty_sort = service._topological_sort({})
        assert empty_sort == []
        
        empty_time = service._allocate_study_time([], datetime.now() + timedelta(days=30), 1.0)
        assert empty_time == {}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
