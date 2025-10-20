# Sistema de Catálogo YouTube y Embeddings

**FASE 2 SEMANA 1 - PASO 8-9: Sistema completo de carga de catálogo YouTube y generación de embeddings**

Este sistema implementa una solución completa para:
- Carga masiva de catálogo YouTube desde CSV
- Generación de embeddings vectoriales usando OpenAI
- Búsqueda semántica con pgvector
- Mapeo inteligente pregunta-video
- Scoring multi-criterio para recomendaciones

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **Modelos de Datos**
   - `YoutubeCatalog`: Catálogo completo de videos con metadatos
   - `ContentEmbeddings`: Embeddings vectoriales con soporte pgvector

2. **Servicios**
   - `EmbeddingService`: Generación de embeddings con OpenAI
   - `IntelligentVideoMapper`: Mapeo pregunta-video inteligente
   - `VectorSearchService`: Búsqueda vectorial optimizada

3. **Scripts de Procesamiento**
   - `load_youtube_catalog.py`: Carga masiva desde CSV
   - `process_embeddings_batch.py`: Procesamiento en lotes
   - `run_youtube_embeddings_pipeline.py`: Pipeline maestro

4. **Testing y Validación**
   - `test_youtube_embeddings_system.py`: Suite de tests completa

### Base de Datos

```sql
-- Tabla principal de catálogo
youtube_catalog (
    id, uuid, youtube_id, url, title, description,
    codigo_tema, area_evaluada, tema_principal,
    subject_id, topic_id, competencias, componentes,
    quality_score, has_embeddings, processing_status
)

-- Tabla de embeddings vectoriales
content_embeddings (
    id, uuid, content_type, content_id,
    embedding_type, embedding_vector[3072],
    source_text, subject_area, topic,
    confidence_score, is_active
)
```

## 🚀 Instalación y Configuración

### 1. Requisitos del Sistema

```bash
# Dependencias Python requeridas
pip install sqlalchemy asyncio numpy openai

# Dependencias opcionales (recomendadas)
pip install pgvector chardet
```

### 2. Configuración de Base de Datos

```bash
# 1. Habilitar extensión pgvector en PostgreSQL
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Aplicar migración
psql -d your_database -f database/migrations/031-youtube-catalog-embeddings.sql
```

### 3. Configuración de OpenAI

```bash
# Editar archivo .env
OPENAI_API_KEY=tu_clave_openai_aqui
```

### 4. Preparar Datos

```bash
# Verificar que existe el CSV del catálogo
ls database/seed_data/youtube_catalog_extendido_enriquecido.csv
```

## 📊 Uso del Sistema

### Opción 1: Pipeline Automático (Recomendado)

```bash
# Ejecutar pipeline completo
python run_youtube_embeddings_pipeline.py

# Con opciones personalizadas
python run_youtube_embeddings_pipeline.py \
    --batch-size 15 \
    --max-concurrent 5 \
    --max-videos 50
```

### Opción 2: Ejecución Manual por Pasos

#### Paso 1: Cargar Catálogo YouTube

```bash
cd apps/backend
python -m app.scripts.load_youtube_catalog \
    --csv-file ../../database/seed_data/youtube_catalog_extendido_enriquecido.csv \
    --batch-size 50 \
    --create-tables
```

#### Paso 2: Procesar Embeddings

```bash
cd apps/backend
python -m app.scripts.process_embeddings_batch \
    --batch-size 10 \
    --max-concurrent 3 \
    --max-videos 100
```

#### Paso 3: Validar Sistema

```bash
python test_youtube_embeddings_system.py
```

### Opción 3: Uso Programático

```python
from app.services.intelligent_video_mapper import IntelligentVideoMapper
from app.core.database import SessionLocal

# Inicializar servicios
mapper = IntelligentVideoMapper()
db = SessionLocal()

# Buscar videos para una pregunta
recommendations = await mapper.find_recommended_videos(
    db=db,
    question_text="¿Cómo funciona la fotosíntesis en las plantas?",
    subject_id=1,  # Ciencias Naturales
    limit=5
)

for video in recommendations:
    print(f"Video: {video['title']}")
    print(f"Relevancia: {video['relevance_score']:.2f}")
    print(f"URL: {video['url']}")
    print()
```

## 🔧 Configuración Avanzada

### Parámetros del Embedding Service

```python
# En app/services/embedding_service.py
model_name = "text-embedding-3-large"  # Modelo OpenAI
vector_dimensions = 3072               # Dimensiones del vector
max_tokens = 8191                     # Límite de tokens
requests_per_minute = 3000            # Rate limit
```

### Weights de Scoring Multi-criterio

```python
# En app/services/intelligent_video_mapper.py
scoring_weights = {
    'exact_match': 0.4,      # Coincidencia exacta subject/topic
    'semantic_similarity': 0.3,  # Similaridad semántica
    'content_quality': 0.2,      # Calidad del video
    'engagement': 0.1           # Métricas de engagement
}

embedding_weights = {
    'title': 0.3,        # Peso del título
    'description': 0.2,   # Peso de la descripción
    'transcript': 0.4,    # Peso de la transcripción
    'combined': 0.1      # Peso del embedding combinado
}
```

### Configuración de Índices pgvector

```sql
-- Índice HNSW (recomendado para consultas rápidas)
CREATE INDEX idx_embeddings_hnsw 
ON content_embeddings 
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índice IVFFlat (alternativo para datasets grandes)
CREATE INDEX idx_embeddings_ivfflat 
ON content_embeddings 
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);
```

## 📈 Monitoreo y Performance

### Métricas Clave

```python
# Estadísticas del sistema
from app.services.vector_search_service import VectorSearchService

search_service = VectorSearchService()
stats = search_service.get_search_stats()

print(f"pgvector disponible: {stats['pgvector_available']}")
print(f"Búsquedas totales: {stats['search_stats']['total_searches']}")
print(f"Tiempo promedio: {stats['search_stats']['avg_search_time_ms']}ms")
```

### Consultas de Monitoreo

```sql
-- Estado de procesamiento de videos
SELECT processing_status, COUNT(*) 
FROM youtube_catalog 
GROUP BY processing_status;

-- Embeddings por tipo
SELECT embedding_type, COUNT(*) 
FROM content_embeddings 
WHERE is_active = 'true'
GROUP BY embedding_type;

-- Calidad promedio de embeddings
SELECT AVG(confidence_score) as avg_confidence,
       AVG(processing_time_ms) as avg_processing_time
FROM content_embeddings;
```

## 🧪 Testing

### Suite de Tests Completa

```bash
# Ejecutar todos los tests
python test_youtube_embeddings_system.py

# Tests específicos
python -m unittest TestYouTubeEmbeddingsSystem.test_youtube_catalog_model
python -m unittest TestYouTubeEmbeddingsSystem.test_embedding_service
```

### Tests de Performance

```bash
# Test de carga con videos limitados
python run_youtube_embeddings_pipeline.py --max-videos 10 --no-openai-check

# Test de procesamiento en lotes pequeños
python apps/backend/app/scripts/process_embeddings_batch.py --batch-size 5 --status-only
```

## 🛠️ Troubleshooting

### Problemas Comunes

#### 1. Error de OpenAI API Key

```
Error: OpenAI API key no configurada correctamente
Solución: Configurar OPENAI_API_KEY en .env
```

#### 2. Error de pgvector

```
Error: pgvector extension not found
Solución: pip install pgvector y CREATE EXTENSION vector;
```

#### 3. Rate Limit de OpenAI

```
Error: Rate limit exceeded
Solución: Reducir batch_size o max_concurrent
```

#### 4. Memoria insuficiente

```
Error: Out of memory processing embeddings
Solución: Reducir batch_size y processing concurrency
```

### Logs y Debugging

```bash
# Ver logs del pipeline
tail -f youtube_pipeline_*.log

# Logs de carga de catálogo
tail -f youtube_catalog_load.log

# Logs de procesamiento de embeddings
tail -f embeddings_batch_processing.log
```

### Comandos de Limpieza

```sql
-- Limpiar embeddings inactivos
DELETE FROM content_embeddings WHERE is_active = 'false';

-- Reset de estado de procesamiento
UPDATE youtube_catalog 
SET processing_status = 'pending', has_embeddings = false 
WHERE processing_status = 'error';
```

## 📚 API Reference

### EmbeddingService

```python
service = EmbeddingService(api_key="your_key")

# Generar embedding individual
embedding = await service.generate_embedding("texto de ejemplo")

# Procesar video completo
embeddings = await service.process_youtube_video_embeddings(db, video)

# Procesamiento en lotes
stats = await service.batch_process_videos(db, batch_size=10)
```

### IntelligentVideoMapper

```python
mapper = IntelligentVideoMapper()

# Encontrar videos recomendados
videos = await mapper.find_recommended_videos(
    db=db,
    question_text="pregunta del estudiante",
    subject_id=1,
    topic_id=5,
    difficulty_level="basic",
    limit=10
)
```

### VectorSearchService

```python
search = VectorSearchService()

# Búsqueda vectorial básica
results = await search.vector_similarity_search(
    db=db,
    query_embedding=embedding,
    similarity_threshold=0.3,
    limit=20
)

# Búsqueda híbrida con re-ranking
results = await search.hybrid_search_with_reranking(
    db=db,
    query_embedding=embedding,
    query_text="texto de búsqueda",
    final_limit=10
)
```

## 🚀 Roadmap y Mejoras Futuras

### Próximas Características

1. **Integración con YouTube API**
   - Obtener metadatos reales de videos
   - Actualización automática de estadísticas
   - Validación de URLs activas

2. **Mejoras de Performance**
   - Cache distribuido con Redis
   - Índices especializados adicionales
   - Optimización de queries vectoriales

3. **Machine Learning Avanzado**
   - Fine-tuning de embeddings específicos
   - Modelos de ranking personalizados
   - A/B testing de algoritmos

4. **Dashboard de Administración**
   - Interface web para monitoreo
   - Gestión de catálogo
   - Métricas en tiempo real

### Contribuciones

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear branch de feature
3. Implementar tests
4. Documentar cambios
5. Crear pull request

## 📄 Licencia y Créditos

- Sistema desarrollado para ICFES Leveling Platform
- Utiliza OpenAI API para embeddings
- Integración con pgvector para búsqueda vectorial
- Arquitectura basada en SQLAlchemy y FastAPI

---

Para soporte técnico o preguntas sobre el sistema, consultar la documentación técnica o contactar al equipo de desarrollo.