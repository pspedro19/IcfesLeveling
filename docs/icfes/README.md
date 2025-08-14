# Sistema de Recomendaciones ICFES

## 🎯 Visión General

Sistema completo de preparación para el examen ICFES Saber 11 con:
- **337 temas** categorizados y estructurados
- **Motor de recomendaciones** basado en IRT (Item Response Theory)
- **Rutas de aprendizaje adaptativas** con prerequisitos
- **Análisis psicométrico** de fortalezas y debilidades

## 🏗️ Arquitectura

### Base de Datos
- `study_topics_catalog`: 337 temas ICFES con metadata completa
- `questions`: Extendida con parámetros IRT y competencias ICFES
- `topic_performance_analytics`: Tracking granular por tema
- `learning_resources`: Biblioteca de recursos por tema

### Backend
- **ICFESRecommendationService**: Motor principal de recomendaciones
- **Análisis IRT**: Cálculo de probabilidades usando modelo 3PL
- **Grafo de dependencias**: Respeta prerequisitos entre temas
- **Predicción de rendimiento**: ML para estimar probabilidad de éxito

### Frontend
- **StudyPathView**: Visualización interactiva del plan
- **Progreso por competencias**: Dashboard ICFES específico
- **Recursos adaptativos**: Selección según estilo de aprendizaje

## 📊 Distribución de Temas

| Área | Temas | Competencias | Peso ICFES |
|------|-------|--------------|------------|
| Lectura Crítica | 41 | 3 competencias | 20% |
| Matemáticas | 87 | 3 competencias | 20% |
| Ciencias Naturales | 73 | 3 competencias | 20% |
| Ciencias Sociales | 68 | 3 competencias | 20% |
| Inglés | 52 | 3 competencias | 20% |
| **TOTAL** | **337** | | **100%** |

## 🔄 Flujo de Uso

1. **Diagnóstico Inicial**: Test adaptativo que evalúa competencias
2. **Análisis de Debilidades**: Identificación de temas críticos
3. **Generación de Ruta**: Plan personalizado respetando prerequisitos
4. **Estudio Adaptativo**: Recursos ajustados por progreso
5. **Evaluaciones Periódicas**: Hitos y simulacros
6. **Ajuste Dinámico**: Replanificación según avance

## 🧮 Algoritmos Clave

### Modelo IRT 3PL
```python
P(θ) = c + (1-c)/(1+e^(-a(θ-b)))
```
- `a`: Discriminación del ítem
- `b`: Dificultad del ítem
- `c`: Pseudo-adivinanza
- `θ`: Habilidad del estudiante

### Ordenamiento Topológico
Algoritmo de Kahn para respetar prerequisitos:
1. Identificar nodos sin dependencias
2. Procesar en orden BFS
3. Verificar ciclos

## 📈 Métricas de Éxito

- **Precisión de predicción**: MAE < 5 puntos
- **Mejora promedio**: >15% en 30 días
- **Completitud de planes**: >80%
- **Satisfacción**: >4.5/5

## 🚀 Instalación

### 1. Preparar Base de Datos
```bash
# Aplicar migración
psql -U postgres -d icfes_db -f database/migrations/002_icfes_complete_system.sql

# Cargar catálogo de temas
python scripts/load_icfes_catalog.py
```

### 2. Verificar Instalación
```bash
# Ejecutar tests
python -m pytest tests/icfes/ -v

# Verificar tablas
psql -U postgres -d icfes_db -c "SELECT COUNT(*) FROM study_topics_catalog;"
```

### 3. Configurar Variables de Entorno
```bash
# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=icfes_db
DB_USER=postgres
DB_PASSWORD=your_password
```

## 🔧 Uso del Sistema

### Generar Plan de Estudio
```python
from app.services.icfes.icfes_recommendation_service import ICFESRecommendationService

service = ICFESRecommendationService(db)
study_path = service.generate_personalized_study_path(
    user_id="user_123",
    target_date=datetime.now() + timedelta(days=90),
    target_score=350
)
```

### Obtener Catálogo de Temas
```python
from app.models.icfes.study_topics_catalog import StudyTopicsCatalog

# Todos los temas
topics = db.query(StudyTopicsCatalog).filter(
    StudyTopicsCatalog.estado == 'activo'
).all()

# Filtrar por área
math_topics = db.query(StudyTopicsCatalog).filter(
    StudyTopicsCatalog.area_evaluada == 'Matemáticas'
).all()
```

## 📚 API Endpoints

### Generar Plan de Estudio
```http
POST /icfes/generate-study-path
{
    "target_date": "2024-12-01T00:00:00Z",
    "target_score": 350
}
```

### Catálogo de Temas
```http
GET /icfes/topics-catalog?area=Matemáticas&limit=20
```

### Detalle de Tema
```http
GET /icfes/topics/LC001
```

### Resumen de Áreas
```http
GET /icfes/areas
```

### Búsqueda de Temas
```http
GET /icfes/search?q=ecuaciones&area=Matemáticas
```

## 🧪 Testing

### Ejecutar Tests Unitarios
```bash
# Todos los tests
python -m pytest tests/icfes/ -v

# Test específico
python -m pytest tests/icfes/test_recommendation_service.py::TestICFESRecommendationService::test_generate_study_path_basic -v
```

### Tests de Integración
```bash
# Tests con base de datos real
python -m pytest tests/icfes/ --db=real -v
```

## 📊 Monitoreo

### Métricas Clave
- **Tiempo de respuesta**: <2 segundos para generar plan
- **Precisión de predicción**: <5 puntos de error
- **Uso de recursos**: <80% CPU, <70% memoria

### Logs
```bash
# Ver logs del sistema
tail -f logs/icfes_system.log

# Logs de recomendaciones
grep "ICFESRecommendationService" logs/app.log
```

## 🔒 Seguridad

### Autenticación
- JWT tokens para usuarios autenticados
- Rate limiting: 100 requests/min por usuario
- Validación de entrada en todos los endpoints

### Validación de Datos
- Sanitización de parámetros de búsqueda
- Validación de fechas y scores
- Escape de caracteres especiales

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: "Tabla study_topics_catalog no existe"
```bash
# Aplicar migración manualmente
psql -U postgres -d icfes_db -f database/migrations/002_icfes_complete_system.sql
```

#### Error: "Solo X/337 temas cargados"
```bash
# Verificar archivo CSV
python scripts/load_icfes_catalog.py --verify-only

# Recargar datos
python scripts/load_icfes_catalog.py --force-reload
```

#### Error: "Timeout generando plan"
```bash
# Verificar índices de base de datos
psql -U postgres -d icfes_db -c "REINDEX DATABASE icfes_db;"

# Verificar cache
python -c "from app.services.cache_service import cache_service; cache_service.clear()"
```

## 📝 Contribución

### Estructura de Archivos
```
apps/backend/
├── app/
│   ├── models/icfes/
│   │   ├── __init__.py
│   │   └── study_topics_catalog.py
│   ├── services/icfes/
│   │   ├── __init__.py
│   │   └── icfes_recommendation_service.py
│   ├── routes/icfes/
│   │   ├── __init__.py
│   │   └── recommendations.py
│   └── schemas/icfes/
├── database/
│   ├── migrations/
│   │   └── 002_icfes_complete_system.sql
│   └── seeds/
├── tests/icfes/
│   └── test_recommendation_service.py
└── scripts/
    └── load_icfes_catalog.py
```

### Convenciones de Código
- **Python**: PEP 8, type hints, docstrings
- **SQL**: UPPERCASE para keywords, snake_case para identificadores
- **API**: RESTful, JSON responses, HTTP status codes apropiados

### Flujo de Desarrollo
1. Crear feature branch desde `develop`
2. Implementar funcionalidad con tests
3. Ejecutar tests y linting
4. Crear Pull Request
5. Code review y merge

## 📞 Soporte

### Contacto
- **Desarrollador**: Equipo ICFES
- **Email**: icfes@example.com
- **Documentación**: `/docs/icfes/`

### Recursos Adicionales
- [Especificación ICFES](https://www.icfes.gov.co/)
- [Teoría IRT](https://en.wikipedia.org/wiki/Item_response_theory)
- [Algoritmos de Grafos](https://en.wikipedia.org/wiki/Topological_sorting)

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2024  
**Estado**: En desarrollo activo
