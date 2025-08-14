import csv
import os
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class ICFESCatalogService:
    """Servicio para manejar el catálogo completo de temas ICFES"""
    
    def __init__(self, db: Session):
        self.db = db
        self.catalog_data = self._load_catalog()
        self.areas = {
            'MAT': 'Matemáticas',
            'CN': 'Ciencias Naturales', 
            'SOC': 'Sociales y Ciudadanas',
            'ING': 'Inglés',
            'LC': 'Lectura Crítica',
            'EXTRA': 'Ciencias Extras'
        }
    
    def _load_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """Cargar catálogo desde CSV"""
        try:
            catalog_path = os.getenv("ICFES_CATALOG_CSV_PATH", "01_icfes_topics_catalog.csv")
            if not os.path.exists(catalog_path):
                logger.warning(f"Catálogo ICFES no encontrado en: {catalog_path}")
                return self._get_default_catalog()
            
            catalog = {}
            with open(catalog_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    area_code = row['codigo_tema'][:3]  # MAT, CN, SOC, ING, LC, EXTRA
                    if area_code not in catalog:
                        catalog[area_code] = []
                    
                    topic_data = {
                        'code': row['codigo_tema'],
                        'area': row['area_evaluada'],
                        'main_topic': row['tema_principal'],
                        'suggested_channel': row['canal_sugerido'],
                        'youtube_url': row['youtube_url'],
                        'youtube_video_id': row['youtube_video_id'],
                        'difficulty': self._calculate_difficulty(row['codigo_tema']),
                        'icfes_weight': self._calculate_icfes_weight(row['codigo_tema']),
                        'estimated_time': self._calculate_estimated_time(row['codigo_tema'])
                    }
                    catalog[area_code].append(topic_data)
            
            logger.info(f"✅ Catálogo ICFES cargado: {sum(len(topics) for topics in catalog.values())} temas")
            return catalog
            
        except Exception as e:
            logger.error(f"Error cargando catálogo ICFES: {e}")
            return self._get_default_catalog()
    
    def _get_default_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """Catálogo por defecto si no se puede cargar el CSV"""
        return {
            'MAT': [
                {
                    'code': 'MAT001',
                    'area': 'Matemáticas',
                    'main_topic': 'Números reales - Operaciones básicas',
                    'suggested_channel': '@julioprofe',
                    'youtube_url': 'https://www.youtube.com/watch?v=5JgHN5v0PFc',
                    'youtube_video_id': '5JgHN5v0PFc',
                    'difficulty': 1,
                    'icfes_weight': 0.25,
                    'estimated_time': 30
                }
            ],
            'CN': [
                {
                    'code': 'CN001',
                    'area': 'Ciencias Naturales',
                    'main_topic': 'Estructura celular',
                    'suggested_channel': '@educatina',
                    'youtube_url': 'https://www.youtube.com/watch?v=EBjcb2C6RW0',
                    'youtube_video_id': 'EBjcb2C6RW0',
                    'difficulty': 1,
                    'icfes_weight': 0.20,
                    'estimated_time': 25
                }
            ]
        }
    
    def _calculate_difficulty(self, code: str) -> int:
        """Calcular dificultad basada en el código del tema"""
        try:
            number = int(code[3:])
            if number <= 20:
                return 1  # Básico
            elif number <= 40:
                return 2  # Intermedio
            else:
                return 3  # Avanzado
        except:
            return 2  # Por defecto intermedio
    
    def _calculate_icfes_weight(self, code: str) -> float:
        """Calcular peso en el ICFES basado en el código del tema"""
        try:
            number = int(code[3:])
            if number <= 15:
                return 0.35  # Temas fundamentales
            elif number <= 30:
                return 0.30  # Temas intermedios
            else:
                return 0.25  # Temas avanzados
        except:
            return 0.30
    
    def _calculate_estimated_time(self, code: str) -> int:
        """Calcular tiempo estimado de estudio en minutos"""
        try:
            number = int(code[3:])
            if number <= 20:
                return 25  # Temas básicos
            elif number <= 40:
                return 35  # Temas intermedios
            else:
                return 45  # Temas avanzados
        except:
            return 30
    
    def get_all_areas(self) -> List[Dict[str, Any]]:
        """Obtener todas las áreas disponibles"""
        return [
            {
                'code': code,
                'name': name,
                'topic_count': len(topics),
                'total_weight': sum(t['icfes_weight'] for t in topics),
                'estimated_total_time': sum(t['estimated_time'] for t in topics)
            }
            for code, name in self.areas.items()
            if code in self.catalog_data
        ]
    
    def get_topics_by_area(self, area_code: str) -> List[Dict[str, Any]]:
        """Obtener todos los temas de un área específica"""
        return self.catalog_data.get(area_code, [])
    
    def get_topic_by_code(self, topic_code: str) -> Optional[Dict[str, Any]]:
        """Obtener un tema específico por código"""
        area_code = topic_code[:3]
        if area_code in self.catalog_data:
            for topic in self.catalog_data[area_code]:
                if topic['code'] == topic_code:
                    return topic
        return None
    
    def get_topics_by_difficulty(self, area_code: str, difficulty: int) -> List[Dict[str, Any]]:
        """Obtener temas de una dificultad específica en un área"""
        if area_code not in self.catalog_data:
            return []
        
        return [
            topic for topic in self.catalog_data[area_code]
            if topic['difficulty'] == difficulty
        ]
    
    def get_recommended_topics(self, user_level: int, max_topics: int = 10) -> List[Dict[str, Any]]:
        """Obtener temas recomendados basados en el nivel del usuario"""
        recommended = []
        
        # Mapear nivel del usuario a dificultad
        if user_level <= 3:
            target_difficulty = 1  # Básico
        elif user_level <= 6:
            target_difficulty = 2  # Intermedio
        else:
            target_difficulty = 3  # Avanzado
        
        # Obtener temas de todas las áreas con la dificultad objetivo
        for area_code in self.catalog_data:
            topics = self.get_topics_by_difficulty(area_code, target_difficulty)
            recommended.extend(topics[:max_topics // len(self.catalog_data)])
        
        # Ordenar por peso ICFES (más importante primero)
        recommended.sort(key=lambda x: x['icfes_weight'], reverse=True)
        
        return recommended[:max_topics]
    
    def generate_study_units_from_catalog(self, area_code: str, user_level: int) -> List[Dict[str, Any]]:
        """Generar unidades de estudio basadas en el catálogo"""
        if area_code not in self.catalog_data:
            return []
        
        topics = self.catalog_data[area_code]
        
        # Agrupar temas por dificultad
        basic_topics = [t for t in topics if t['difficulty'] == 1]
        intermediate_topics = [t for t in topics if t['difficulty'] == 2]
        advanced_topics = [t for t in topics if t['difficulty'] == 3]
        
        units = []
        
        # Unidad 1: Fundamentos (temas básicos)
        if basic_topics:
            units.append({
                'unit_number': 1,
                'name': f'Fundamentos de {self.areas.get(area_code, area_code)}',
                'description': 'Conceptos básicos y fundamentales del área',
                'topics': basic_topics[:8],  # Máximo 8 temas por unidad
                'difficulty_level': 1,
                'icfes_weight': sum(t['icfes_weight'] for t in basic_topics[:8]),
                'estimated_completion_time': sum(t['estimated_time'] for t in basic_topics[:8]) // 60,  # Convertir a horas
                'unlocked': True,
                'ai_recommended': user_level <= 3
            })
        
        # Unidad 2: Desarrollo (temas intermedios)
        if intermediate_topics:
            units.append({
                'unit_number': 2,
                'name': f'Desarrollo en {self.areas.get(area_code, area_code)}',
                'description': 'Conceptos intermedios y aplicaciones',
                'topics': intermediate_topics[:10],
                'difficulty_level': 2,
                'icfes_weight': sum(t['icfes_weight'] for t in intermediate_topics[:10]),
                'estimated_completion_time': sum(t['estimated_time'] for t in intermediate_topics[:10]) // 60,
                'unlocked': user_level >= 2,
                'ai_recommended': user_level <= 5
            })
        
        # Unidad 3: Avanzado (temas avanzados)
        if advanced_topics:
            units.append({
                'unit_number': 3,
                'name': f'Avanzado en {self.areas.get(area_code, area_code)}',
                'description': 'Conceptos avanzados y preparación ICFES',
                'topics': advanced_topics[:12],
                'difficulty_level': 3,
                'icfes_weight': sum(t['icfes_weight'] for t in advanced_topics[:12]),
                'estimated_completion_time': sum(t['estimated_time'] for t in advanced_topics[:12]) // 60,
                'unlocked': user_level >= 4,
                'ai_recommended': user_level >= 6
            })
        
        return units
    
    def get_youtube_videos_by_area(self, area_code: str) -> List[Dict[str, str]]:
        """Obtener todos los videos YouTube de un área específica"""
        if area_code not in self.catalog_data:
            return []
        
        videos = []
        for topic in self.catalog_data[area_code]:
            if topic['youtube_url'] and topic['youtube_url'] != 'Pending':
                videos.append({
                    'topic_code': topic['code'],
                    'topic_name': topic['main_topic'],
                    'youtube_url': topic['youtube_url'],
                    'video_id': topic['youtube_video_id'],
                    'channel': topic['suggested_channel']
                })
        
        return videos
    
    def get_catalog_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del catálogo"""
        total_topics = sum(len(topics) for topics in self.catalog_data.values())
        total_videos = sum(
            len([t for t in topics if t['youtube_url'] and t['youtube_url'] != 'Pending'])
            for topics in self.catalog_data.values()
        )
        
        return {
            'total_areas': len(self.catalog_data),
            'total_topics': total_topics,
            'total_videos': total_videos,
            'areas_breakdown': {
                area: {
                    'topic_count': len(topics),
                    'video_count': len([t for t in topics if t['youtube_url'] and t['youtube_url'] != 'Pending']),
                    'total_weight': sum(t['icfes_weight'] for t in topics),
                    'estimated_time': sum(t['estimated_time'] for t in topics)
                }
                for area, topics in self.catalog_data.items()
            }
        }
