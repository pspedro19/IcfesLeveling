"""
Módulo de rutas ICFES
Contiene todos los endpoints relacionados con el sistema de preparación ICFES
"""

from .recommendations import router as recommendations_router

__all__ = [
    'recommendations_router'
]
