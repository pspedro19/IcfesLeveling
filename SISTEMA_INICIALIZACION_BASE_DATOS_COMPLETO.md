# ANÁLISIS EXHAUSTIVO: SISTEMA DE INICIALIZACIÓN DE BASE DE DATOS - ICFES LEVELING

**Fecha de análisis:** 2025-10-20
**Proyecto:** ICFES Leveling - Sistema de Gamificación Educativa
**Base de datos:** PostgreSQL 16
**Ubicación:** /root/IcfesLeveling

---

## ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura de Inicialización](#arquitectura-de-inicialización)
3. [Flujo de Inicialización Completo](#flujo-de-inicialización-completo)
4. [Scripts de Inicialización Docker](#scripts-de-inicialización-docker)
5. [Modelos SQLAlchemy - Tablas del Sistema](#modelos-sqlalchemy---tablas-del-sistema)
6. [Datos Seed - Carga Inicial](#datos-seed---carga-inicial)
7. [Inicialización en main.py](#inicialización-en-mainpy)
8. [Análisis de Problemas y Inconsistencias](#análisis-de-problemas-y-inconsistencias)
9. [Diagrama de Flujo](#diagrama-de-flujo)
10. [Recomendaciones](#recomendaciones)

---

## RESUMEN EJECUTIVO

### Sistema de Inicialización Híbrido

El proyecto ICFES Leveling utiliza un **sistema híbrido de inicialización** que combina:

1. **Scripts SQL en Docker** (31 archivos .sql + 1 .sh)
2. **Modelos SQLAlchemy** con `Base.metadata.create_all()`
3. **Carga automática de datos** en startup de FastAPI
4. **NO utiliza Alembic** para migraciones

### Orden de Ejecución

```
Docker Compose UP
    ↓
PostgreSQL Container Init
    ↓
Scripts SQL (01-*.sql hasta 99-*.sql) - ALFABÉTICO
    ↓
Container Backend Start
    ↓
FastAPI Lifespan Startup
    ↓
Base.metadata.create_all()
    ↓
Ensure Columns (ALTER TABLE)
    ↓
Auto-import Excel Data (si está configurado)
    ↓
Load ICFES Catalog
    ↓
Sistema Listo
```

### Estadísticas

- **Scripts SQL:** 31 archivos
- **Modelos SQLAlchemy:** 45+ modelos
- **Tablas en DB:** ~50 tablas
- **Datos Seed:** ~480 preguntas ICFES + usuarios de ejemplo
- **Campos en questions:** ~100 columnas (81 campos ICFES + originales)

---

## ARQUITECTURA DE INICIALIZACIÓN

### Componentes Principales

```
/root/IcfesLeveling/
├── database/
│   ├── init/                         # Scripts de inicialización Docker
│   │   ├── 01-init.sql              # Tablas base
│   │   ├── 02-seed-data.sql         # Datos iniciales
│   │   ├── 03-import-icfes-data.sql # 81 campos ICFES
│   │   ├── 99-load-icfes-data.sh    # Carga automática Excel
│   │   └── 99-final-setup.sql       # Verificación final
│   ├── allquestions/                 # Archivos Excel con preguntas
│   │   └── questions.xlsx           # ~480 preguntas
│   └── seed_data/                    # Datos CSV/YML
│       ├── topics_catalog.csv       # Catálogo de temas
│       └── youtube_catalog_*.csv    # Videos educativos
├── apps/backend/app/
│   ├── models/                       # Modelos SQLAlchemy (45+)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── question.py
│   │   ├── subject.py
│   │   ├── diagnostic_test.py
│   │   └── ...
│   ├── core/
│   │   └── database.py              # Configuración SQLAlchemy
│   └── main.py                       # Inicialización en startup
└── docker-compose.yml                # Orquestación
```

---

## FLUJO DE INICIALIZACIÓN COMPLETO

### FASE 1: Docker Container Startup (PostgreSQL)

**Ubicación:** `docker-compose.yml`

```yaml
postgres:
  image: postgres:16
  volumes:
    - ./database/init:/docker-entrypoint-initdb.d
    - ./database/allquestions:/data
```

**Comportamiento:**
- Docker ejecuta automáticamente todos los archivos en `/docker-entrypoint-initdb.d`
- Los archivos se ejecutan en **orden alfabético**
- Solo ocurre en la **primera inicialización** (volumen vacío)

### FASE 2: Scripts SQL - Orden de Ejecución

**Total:** 31 archivos SQL + 1 script bash

#### Grupo 01-03: Estructura Base
```
01-create-production-db.sql       # Creación de DB (si no existe)
01-init.sql                        # Tablas fundamentales (users, subjects, questions, etc.)
02-seed-data.sql                   # Datos iniciales (subjects, topics, hero_classes, etc.)
03-admin-user.sql                  # Usuario administrador
03-boss-tables.sql                 # Tablas de jefes (gamificación)
03-import-icfes-data.sql          # ⭐ CRÍTICO: 81 campos ICFES
03-load-csv-data.sql              # Carga de datos CSV
```

#### Grupo 04-09: Funcionalidades Extendidas
```
04-import-study-plan-templates.sql # Plantillas de planes de estudio
04-monthly-reassessment.sql        # Sistema de re-evaluación mensual
05-initialize-adaptive-templates.sql # Plantillas adaptativas
05-premium-system.sql              # Sistema premium
05-youtube-links.sql               # Enlaces de YouTube
06-enhanced-youtube-catalog*.sql   # Catálogo YouTube (3 versiones)
06-guild-system.sql                # Sistema de gremios
07-achievement-system.sql          # Logros
08-virtual-economy.sql             # Economía virtual
09-question-enhancements.sql       # Mejoras a preguntas
```

#### Grupo 10-30: Sistemas Avanzados
```
10-study-plans-icfes.sql          # Planes de estudio ICFES
11-diagnostic-analytics.sql       # Analytics diagnóstico
14-multimedia-questions.sql       # Preguntas multimedia
15-expanded-achievements.sql      # Logros expandidos
16-gamification-complete.sql      # Gamificación completa
17-error-recovery-system.sql      # Sistema de recuperación de errores
17-gamification-sample-data.sql   # Datos de ejemplo
30-icfes-migration.sql            # Migración ICFES
```

#### Grupo 99: Finalización
```
99-definitive-data-initialization.sql # Inicialización definitiva
99-final-setup.sql                     # Verificación final
99-load-icfes-data.sh                 # ⭐ CARGA AUTOMÁTICA EXCEL
```

### FASE 3: Script Bash - Carga de Excel

**Archivo:** `99-load-icfes-data.sh`

**Funcionalidad:**
1. Instala Python 3 + pip en el container PostgreSQL
2. Instala pandas, psycopg2, openpyxl
3. Espera a que PostgreSQL esté listo
4. Ejecuta script Python inline para cargar Excel
5. Mapea áreas a subject_id UUIDs
6. Inserta ~480 preguntas con 81 campos ICFES

**Archivo Excel esperado:**
```
/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx
```

**Mapeo de Subjects:**
```python
subject_map = {
    'ciencias naturales': '550e8400-e29b-41d4-a716-446655440003',
    'ciencias sociales': '550e8400-e29b-41d4-a716-446655440004',
    'matemáticas': '550e8400-e29b-41d4-a716-446655440001',
    'lectura crítica': '550e8400-e29b-41d4-a716-446655440002',
    'inglés': '550e8400-e29b-41d4-a716-446655440005'
}
```

### FASE 4: Backend Startup (FastAPI)

**Archivo:** `/root/IcfesLeveling/apps/backend/app/main.py`

**Orden de Ejecución en Lifespan:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Iniciar servicio de caché de medios
    await media_background_service.start_background_service()

    # 2. Crear tablas con SQLAlchemy
    Base.metadata.create_all(bind=engine)

    # 3. Configurar monitores del sistema
    setup_schema_guard(app, engine)
    setup_system_health_monitor(app, engine)

    # 4. Asegurar columnas necesarias
    _ensure_question_columns()
    _ensure_diagnostic_test_columns()
    _ensure_advanced_learning_tables()

    # 5. Importar preguntas desde Excel (si AUTO_IMPORT_QUESTIONS=true)
    if auto_import and excel_path and os.path.exists(excel_path):
        ICFESExcelImporter(db).import_excel(excel_path)

    # 6. Cargar catálogo de temas ICFES
    ICFESCatalogLoader().run(catalog_csv_path)

    # 7. Cargar YouTube links
    YouTubeLinksLoader().load_youtube_links()

    yield  # Aplicación corriendo

    # Shutdown
    await media_background_service.stop_background_service()
```

**Variables de Entorno Clave:**
```bash
AUTO_IMPORT_QUESTIONS=true
QUESTIONS_EXCEL_PATH=/seed_data/questions.xlsx
IMPORT_CLEAR_EXISTING=true
ICFES_CATALOG_CSV_PATH=/seed_data/topics_catalog.csv
```

---

## SCRIPTS DE INICIALIZACIÓN DOCKER

### 01-init.sql - Tablas Base

**Propósito:** Crear la estructura fundamental de la base de datos

**Tablas Creadas (27 tablas):**

1. **users** - Usuarios del sistema
2. **hero_classes** - Clases de héroes (gamificación)
3. **user_profiles** - Perfiles de usuario con personalización
4. **subjects** - Materias (Matemáticas, Lenguaje, etc.)
5. **topics** - Temas dentro de materias
6. **questions** - Preguntas (estructura base)
7. **battles** - Batallas (gamificación)
8. **battle_answers** - Respuestas en batallas
9. **items** - Ítems del juego
10. **user_items** - Inventario de usuarios
11. **quests** - Misiones/quests
12. **user_quests** - Progreso de quests por usuario
13. **leaderboard** - Tabla de clasificación
14. **ai_explanations** - Explicaciones generadas por IA
15. **personality_questions** - Preguntas de personalidad
16. **diagnostic_tests** - Tests diagnósticos
17. **diagnostic_test_answers** - Respuestas de tests diagnósticos
18. **study_plans** - Planes de estudio personalizados
19. **plan_progress** - Progreso en planes de estudio
20. **video_tracking** - Seguimiento de videos vistos
21. **user_yml_plans** - Almacenamiento de planes YML
22. **yml_usage_stats** - Estadísticas de uso de planes
23. **quizzes** - Cuestionarios
24. **quiz_answers** - Respuestas de cuestionarios

**Índices Creados:** 28 índices para optimización

**Funciones SQL:**
- `calculate_weighted_progress()` - Calcula progreso ponderado
- `update_updated_at_column()` - Trigger para updated_at

### 02-seed-data.sql - Datos Iniciales

**Datos Insertados:**

#### Subjects (5 materias con UUIDs fijos)
```sql
'550e8400-e29b-41d4-a716-446655440001' - Matemáticas
'550e8400-e29b-41d4-a716-446655440002' - Lenguaje
'550e8400-e29b-41d4-a716-446655440003' - Ciencias Naturales
'550e8400-e29b-41d4-a716-446655440004' - Ciencias Sociales
'550e8400-e29b-41d4-a716-446655440005' - Inglés
```

#### Topics (10 temas ejemplo)
- Álgebra Básica, Geometría Euclidiana, Cálculo Diferencial
- Comprensión Lectora, Gramática, Literatura
- Mecánica Clásica, Química Orgánica, Biología Celular

#### Hero Classes (5 clases)
- Mago Cuántico (Matemáticas)
- Guerrero del Conocimiento (Resistencia)
- Arquero de la Sabiduría (Velocidad)
- Sacerdote del Aprendizaje (Curación)
- Asesino de la Lógica (Precisión)

#### Personality Questions (5 preguntas)
- Motivación, Estilo de aprendizaje, Materia favorita, etc.

#### Sample Users (5 usuarios)
- shadow_hunter (Nivel 25, Rango B)
- math_master (Nivel 18, Rango C)
- science_wizard (Nivel 12, Rango D)
- language_knight (Nivel 8, Rango E)
- newbie_student (Nivel 1, Rango E)

#### Items (5 ítems de juego)
- Poción de Tiempo, Poción de Sabiduría, Espada de Conocimiento, etc.

#### Sample Questions (25 preguntas ICFES)
- Matemáticas: 12 preguntas
- Lenguaje: 4 preguntas
- Ciencias: 5 preguntas
- Sociales: 3 preguntas
- Inglés: 3 preguntas

**NOTA:** Las preguntas de ejemplo están comentadas porque se usa data real del ICFES

### 03-import-icfes-data.sql - 81 Campos ICFES

**Propósito:** Expandir la tabla `questions` con todos los campos del formato ICFES

**Campos Agregados (81 campos adicionales):**

#### Campos Básicos (5)
- `id_pregunta_original`
- `area_evaluada`
- `tema_especifico`
- `grado_escolar`
- `periodo_aplicacion`

#### Campos de Imágenes (7)
- `requiere_imagen`
- `imagen_pregunta_url`
- `imagen_opcion_a_url`
- `imagen_opcion_b_url`
- `imagen_opcion_c_url`
- `imagen_opcion_d_url`
- `imagen_contexto_comp`

#### Campos de Contexto (7)
- `pregunta_con_contexto`
- `pregunta_libro`
- `orden_en_contexto`
- `contexto_requerido`
- `texto_contexto_completo`
- `id_contexto_compartido`

#### Campos de Archivo (2)
- `ruta_absoluta_archivo`
- `nombre_del_archivo`

#### Campos de Categorización (5)
- `subtema`
- `estrategia_discursiva`
- `tipo_razonamiento`
- `complejidad_cognitiva`
- `contexto_aplicacion`

#### Campos de Análisis Textual (3)
- `tipo_texto`
- `genero_textual`
- `funcion_comunicativa`

#### Campos Matemáticos (6)
- `pensamiento_matematico`
- `tipo_problema`
- `estrategia_solucion`
- `tipo_representacion`
- `uso_herramientas`
- `nivel_abstraccion`

#### Campos Científicos (9)
- `disciplina_predominante`
- `concepto_cientifico`
- `proceso_cientifico`
- `nivel_representacion`
- `tipo_experimento`
- `control_variables`
- `tipo_observacion`
- `nivel_taxonomico`
- `sistema_biologico`

#### Campos Sociales (7)
- `periodo_historico`
- `ambito_analisis`
- `escala_espacial`
- `concepto_social`
- `tipo_fuente`
- `contexto_historico`
- `perspectiva_analisis`

#### Campos de Comunicación (16)
- `habilidad_comunicativa`
- `estructura_textual`
- `proposito_comunicativo`
- `audiencia_objetivo`
- `registro_linguistico`
- `tipo_discurso`
- `elemento_retorico`
- `figura_literaria`
- `tipo_narracion`
- `elemento_narrativo`
- `tipo_descripcion`
- `punto_vista`
- `tono_texto`
- `intencion_autor`
- `contexto_produccion`
- `tipo_intertextualidad`

#### Campos de Análisis (11)
- `tipo_grafico`
- `interpretacion_datos`
- `tipo_modelo`
- `variables_relacionadas`
- `escala_temporal`
- `tipo_cambio`
- `tipo_interaccion`
- `nivel_organizacion`
- `tipo_evidencia`
- `grado_incertidumbre`
- `tipo_relacion_causal`

#### Campos de Argumentación (5)
- `tipo_argumento`
- `nivel_inferencia`
- `tipo_conclusion`
- `validez_argumento`
- `tipo_falacia`

**Operación:** `ALTER TABLE questions ADD COLUMN IF NOT EXISTS ...`

**Total de columnas en questions:** ~100 columnas

### 99-load-icfes-data.sh - Carga Automática Excel

**Funcionalidad:**

```bash
#!/bin/bash
# 1. Instalar dependencias
apt-get install python3 python3-pip
pip install pandas psycopg2-binary openpyxl

# 2. Esperar PostgreSQL
pg_isready -h localhost -p 5432

# 3. Ejecutar script Python inline
python3 /tmp/load_data.py
```

**Script Python Embebido:**

```python
import pandas as pd
import psycopg2
import uuid

# Leer Excel
df = pd.read_excel('/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx')

# Mapear áreas a subject_id
subject_map = {...}

# Limpiar questions existentes
cur.execute("DELETE FROM questions")

# Insertar cada pregunta
for index, row in df.iterrows():
    question_data = {
        'id': str(uuid.uuid4()),
        'subject_id': subject_map.get(area),
        'question_text': str(row.get('pregunta')),
        'option_a': str(row.get('opcion_a')),
        'option_b': str(row.get('opcion_b')),
        'option_c': str(row.get('opcion_c')),
        'option_d': str(row.get('opcion_d')),
        'correct_answer': str(row.get('respuesta_correcta')),
        'area_evaluada': str(row.get('área_evaluada')),
        'competencia': str(row.get('competencia')),
        'componente': str(row.get('componente'))
    }
    # INSERT query...
```

**Resultado:** ~480 preguntas cargadas automáticamente

### 99-final-setup.sql - Verificación Final

**Funcionalidad:**
1. Crear tabla `system_initialization` para tracking
2. Verificar que todas las tablas críticas existan
3. Verificar columnas críticas de `diagnostic_tests`
4. Verificar que haya datos básicos (usuarios, materias, preguntas)
5. Crear índices de rendimiento
6. Marcar inicialización como exitosa

**Tablas Verificadas:**
```sql
'users', 'subjects', 'topics', 'questions', 'diagnostic_tests',
'diagnostic_test_answers', 'study_plans', 'plan_progress',
'video_tracking', 'quizzes', 'achievements', 'guilds',
'monthly_reassessment', 'analytics_events', 'user_progress'
```

---

## MODELOS SQLALCHEMY - TABLAS DEL SISTEMA

### Configuración Base

**Archivo:** `/root/IcfesLeveling/apps/backend/app/core/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Engine con connection pooling optimizado
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # 20 conexiones en pool
    max_overflow=30,           # +30 adicionales
    pool_pre_ping=True,        # Validar conexiones
    pool_recycle=3600,         # Reciclar cada hora
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Ejecución de create_all:**
```python
# En main.py lifespan
Base.metadata.create_all(bind=engine)
```

### Modelos Principales (45+ modelos)

#### 1. User - Usuarios del Sistema

**Tabla:** `users`

**Campos:**
```python
id: UUID (PK)
username: String(50) UNIQUE NOT NULL
email: String(255) UNIQUE NOT NULL
hashed_password: String(255) NOT NULL
display_name: String(100)
level: Integer (default=1)
experience: Integer (default=0)
rank: String(10) (default="E")  # E, D, C, B, A, S, SS, SSS
hp: Integer (default=100)
mp: Integer (default=50)
power: Integer (default=10)
wisdom: Integer (default=10)
speed: Integer (default=10)
orbs: Integer (default=1000)
crystals: Integer (default=0)
is_active: Boolean (default=True)
created_at: DateTime
updated_at: DateTime
```

**Relaciones:**
- battles (one-to-many)
- user_quests (one-to-many)
- diagnostic_tests (one-to-many)
- study_plans (one-to-many)
- user_achievements (one-to-many)

**Métodos:**
- `rank_info()` - Obtener información de rango
- `add_experience(exp_amount)` - Agregar experiencia y subir nivel
- `add_test_experience(xp)` - XP por preguntas correctas

#### 2. Subject - Materias

**Tabla:** `subjects`

**Campos:**
```python
id: UUID (PK)
name: String(100) NOT NULL
description: Text
icon_url: String(500)
color: String(7) (default="#3b0f6f")
created_at: DateTime
```

**UUIDs Fijos:**
```
550e8400-e29b-41d4-a716-446655440001 - Matemáticas
550e8400-e29b-41d4-a716-446655440002 - Lenguaje
550e8400-e29b-41d4-a716-446655440003 - Ciencias Naturales
550e8400-e29b-41d4-a716-446655440004 - Ciencias Sociales
550e8400-e29b-41d4-a716-446655440005 - Inglés
```

**Relaciones:**
- topics (one-to-many)
- questions (one-to-many)
- diagnostic_tests (one-to-many)
- study_plans (one-to-many)

#### 3. Topic - Temas

**Tabla:** `topics`

**Campos:**
```python
id: UUID (PK)
subject_id: UUID (FK -> subjects.id)
name: String(200) NOT NULL
description: Text
difficulty_level: Integer (default=1)
created_at: DateTime
```

**Relaciones:**
- subject (many-to-one)
- questions (one-to-many)

#### 4. Question - Preguntas

**Tabla:** `questions`

**Campos Base (~20):**
```python
id: UUID (PK)
topic_id: UUID (FK -> topics.id)
subject_id: UUID (FK -> subjects.id)
pregunta_texto: Text  # Contenido textual
pregunta_imagen: String(500)  # URL imagen pregunta
opcion_a_texto: Text
opcion_a_imagen: String(500)
opcion_b_texto: Text
opcion_b_imagen: String(500)
opcion_c_texto: Text
opcion_c_imagen: String(500)
opcion_d_texto: Text
opcion_d_imagen: String(500)
respuesta_correcta: String(1)  # a, b, c, d
question_text: Text  # Legacy
question_type: String(50) (default="multiple_choice")
difficulty: Integer (1-10)
options: JSON  # Legacy
correct_answer: String(10)  # Legacy
explanation: Text
hint: Text
tags: ARRAY(String)
power_stats: JSON
created_at: DateTime
```

**Campos IRT (3):**
```python
parametro_irt_a: Float (default=1.0)  # Discriminación
parametro_irt_b: Float (default=0.0)  # Dificultad
parametro_irt_c: Float (default=0.25) # Pseudo-adivinanza
```

**Campos ICFES (81 campos adicionales):**
- Todos los campos descritos en `03-import-icfes-data.sql`

**Total de columnas:** ~100

**Relaciones:**
- topic (many-to-one)
- subject (many-to-one)
- battle_answers (one-to-many)
- diagnostic_answers (one-to-many)

**Métodos:**
```python
validate_question() -> List[str]  # Validar datos
get_options_dict() -> Dict  # Obtener opciones en diccionario
get_irt_probability(theta) -> float  # Probabilidad IRT 3PL
get_irt_information(theta) -> float  # Información de Fisher
get_optimal_hint(error_type) -> str  # Pista óptima
get_progressive_hint(level) -> str  # Pista progresiva
```

#### 5. DiagnosticTest - Tests Diagnósticos

**Tabla:** `diagnostic_tests`

**Campos:**
```python
id: UUID (PK)
user_id: UUID (FK -> users.id)
subject_id: UUID (FK -> subjects.id)
test_type: String(50) (default="real_icfes")
reassessment_type: String(50)  # 'initial', 'monthly', 'adaptive'
original_test_id: UUID (FK -> diagnostic_tests.id)
questions_answered: Integer (default=0)
correct_answers: Integer (default=0)
time_spent_seconds: Integer (default=0)
score_percentage: Float (default=0.0)
strengths: JSON (default=[])
weaknesses: JSON (default=[])
score_by_topic: JSON (default={})
status: String(20) (default="in_progress")  # 'in_progress', 'completed'
started_at: DateTime
completed_at: DateTime
created_at: DateTime

# Monthly reassessment fields
is_monthly_reassessment: Boolean (default=False)
days_since_initial: Integer
comparison_with_initial: JSON
plan_regenerated: Boolean (default=False)
new_goals_generated: Boolean (default=False)
notification_sent: Boolean (default=False)
```

**Relaciones:**
- user (many-to-one)
- subject (many-to-one)
- original_test (self-referential)
- answers (one-to-many -> diagnostic_test_answers)

#### 6. DiagnosticTestAnswer - Respuestas Diagnóstico

**Tabla:** `diagnostic_test_answers`

**Campos:**
```python
id: UUID (PK)
diagnostic_test_id: UUID (FK -> diagnostic_tests.id)
question_id: UUID (FK -> questions.id)
user_answer: String(10) NOT NULL
is_correct: Boolean NOT NULL
response_time_ms: Integer (default=0)
topic_id: UUID (FK -> topics.id)
created_at: DateTime
```

#### 7. StudyPlan - Planes de Estudio

**Tabla:** `study_plans`

**Campos:**
```python
id: UUID (PK)
user_id: UUID (FK -> users.id)
subject_id: UUID (FK -> subjects.id)
plan_name: String(200) NOT NULL
plan_data: JSON NOT NULL  # Contiene estructura del plan YML
total_units: Integer (default=8)
completed_units: Integer (default=0)
progress_percentage: DECIMAL(5,2) (default=0.00)
is_active: Boolean (default=True)
generated_at: DateTime
updated_at: DateTime
```

**Estructura de plan_data:**
```json
{
  "subject": "Matemáticas",
  "title": "Plan personalizado",
  "units": [
    {
      "unit_number": 1,
      "name": "Álgebra Básica",
      "topics": [...],
      "recommendations": {...},
      "unlocked": true,
      "progress": 0
    }
  ]
}
```

#### 8. PlanProgress - Progreso en Planes

**Tabla:** `plan_progress`

**Campos:**
```python
id: UUID (PK)
plan_id: UUID (FK -> study_plans.id)
unit_number: Integer NOT NULL
unit_name: String(200) NOT NULL
unit_description: Text
unit_content: JSON  # Videos, ejercicios, recursos
is_completed: Boolean (default=False)
completion_date: DateTime
score: DECIMAL(5,2) (default=0.00)
weighted_progress: JSON
created_at: DateTime
```

**Estructura weighted_progress:**
```json
{
  "videos": {"completed": 0, "total": 0, "weight": 0.3},
  "exercises": {"completed": 0, "total": 0, "weight": 0.5},
  "readings": {"completed": 0, "total": 0, "weight": 0.2}
}
```

#### Otros Modelos Importantes

**9. Battle** - Batallas gamificadas
**10. BattleAnswer** - Respuestas en batallas
**11. Item** - Ítems del juego
**12. UserItem** - Inventario de usuarios
**13. Quest** - Misiones
**14. UserQuest** - Progreso de misiones
**15. Leaderboard** - Clasificación
**16. AIExplanation** - Explicaciones IA
**17. UserProfile** - Perfiles de usuario
**18. HeroClass** - Clases de héroe
**19. PersonalityQuestion** - Preguntas de personalidad
**20. VideoTracking** - Seguimiento de videos
**21. Quiz** - Cuestionarios
**22. QuizAnswer** - Respuestas de quiz
**23. Achievement** - Logros
**24. UserAchievement** - Logros de usuario
**25. Guild** - Gremios
**26. GuildMember** - Miembros de gremio
**27. Subscription** - Suscripciones premium
**28. Payment** - Pagos
**29. Certificate** - Certificados
**30. StoreTransaction** - Transacciones tienda
**31. Notification** - Notificaciones
**32. YoutubeVideo** - Videos educativos
**33. YouTubeLinks** - Enlaces YouTube
**34. UserYMLPlan** - Planes YML almacenados

---

## DATOS SEED - CARGA INICIAL

### Fuentes de Datos

1. **SQL Scripts** (`02-seed-data.sql`)
2. **Excel Files** (`/database/allquestions/questions.xlsx`)
3. **CSV Files** (`/database/seed_data/topics_catalog.csv`)
4. **YML Files** (`/database/seed_data/youtube_catalog_*.yml`)

### Datos Insertados por 02-seed-data.sql

#### Subjects (5 materias)
```sql
INSERT INTO subjects VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Matemáticas', ...),
('550e8400-e29b-41d4-a716-446655440002', 'Lenguaje', ...),
('550e8400-e29b-41d4-a716-446655440003', 'Ciencias Naturales', ...),
('550e8400-e29b-41d4-a716-446655440004', 'Ciencias Sociales', ...),
('550e8400-e29b-41d4-a716-446655440005', 'Inglés', ...)
```

#### Topics (10 temas ejemplo)
- Por materia: 2-3 temas básicos

#### Hero Classes (5 clases)
- Mago Cuántico (+Matemáticas)
- Guerrero del Conocimiento (+HP/Resistencia)
- Arquero de la Sabiduría (+Velocidad)
- Sacerdote del Aprendizaje (+Curación)
- Asesino de la Lógica (+Críticos)

#### Personality Questions (5 preguntas)
- Motivación, Estilo de aprendizaje, Materia favorita, Resolución de problemas, Preferencia social

#### Sample Users (5 usuarios)
```sql
'aa0e8400-e29b-41d4-a716-446655440001' - shadow_hunter (Nivel 25, Rango B)
'aa0e8400-e29b-41d4-a716-446655440002' - math_master (Nivel 18, Rango C)
'aa0e8400-e29b-41d4-a716-446655440003' - science_wizard (Nivel 12, Rango D)
'aa0e8400-e29b-41d4-a716-446655440004' - language_knight (Nivel 8, Rango E)
'aa0e8400-e29b-41d4-a716-446655440005' - newbie_student (Nivel 1, Rango E)
```

#### Items (5 ítems)
- Poción de Tiempo (consumible)
- Poción de Sabiduría (consumible)
- Espada de Conocimiento (cosmético)
- Corona del Sabio (cosmético)
- Mascota Dragón (mascota)

#### Sample Battles (4 batallas)
- Goblin Matemático
- Guardián de la Torre
- Esqueleto Científico
- Rival Fantasma

#### Sample Questions (25 preguntas ICFES - COMENTADAS)
**NOTA:** Las preguntas de ejemplo están comentadas porque se cargan desde Excel

### Datos Cargados por 99-load-icfes-data.sh

**Fuente:** `/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx`

**Proceso:**
1. Leer Excel con pandas
2. Limpiar nombres de columnas
3. Mapear área_evaluada a subject_id UUID
4. Limpiar tabla questions existente
5. Insertar cada fila como pregunta

**Datos Insertados:**
- **~480 preguntas** con 81 campos ICFES completos
- **Distribución:**
  - Ciencias Naturales: ~258 preguntas
  - Ciencias Sociales: ~153 preguntas
  - Matemáticas: ~1+ preguntas
  - Lectura Crítica: ~50+ preguntas
  - Inglés: ~20+ preguntas

### Datos Cargados en Backend Startup

#### 1. Importación de Excel (si AUTO_IMPORT_QUESTIONS=true)

**Archivo:** `/seed_data/questions.xlsx`

**Clase:** `ICFESExcelImporter`

**Proceso:**
```python
# 1. Leer Excel
df = pd.read_excel(excel_path)

# 2. Validar estructura
validate_excel_structure(df)

# 3. Mapear columnas a campos del modelo
for row in df.iterrows():
    question = Question(
        subject_id=map_area_to_subject(row['área_evaluada']),
        pregunta_texto=row['pregunta'],
        opcion_a_texto=row['opcion_a'],
        # ... todos los 81 campos ICFES
    )
    db.add(question)

# 4. Commit en lotes
db.commit()
```

**Configuración:**
```python
AUTO_IMPORT_QUESTIONS=true
QUESTIONS_EXCEL_PATH=/seed_data/questions.xlsx
IMPORT_CLEAR_EXISTING=true  # Limpiar preguntas existentes
```

#### 2. Catálogo de Temas ICFES

**Archivo:** `/seed_data/topics_catalog.csv`

**Clase:** `ICFESCatalogLoader`

**Proceso:**
```python
# 1. Leer CSV
df = pd.read_csv(catalog_csv_path)

# 2. Crear/actualizar topics
for row in df.iterrows():
    topic = Topic(
        subject_id=row['subject_id'],
        name=row['tema'],
        description=row['descripcion'],
        difficulty_level=row['dificultad']
    )
    db.merge(topic)
```

**Estructura CSV:**
```csv
subject_id,tema,descripcion,dificultad
550e8400-e29b-41d4-a716-446655440001,Álgebra,Ecuaciones y sistemas,2
...
```

#### 3. Enlaces de YouTube

**Archivo:** `/seed_data/youtube_catalog_extendido_enriquecido.csv`

**Clase:** `YouTubeLinksLoader`

**Proceso:**
```python
# 1. Leer CSV
df = pd.read_csv(youtube_catalog_path)

# 2. Insertar enlaces
for row in df.iterrows():
    link = YouTubeLinks(
        subject_id=row['subject_id'],
        topic=row['tema'],
        video_title=row['titulo'],
        video_url=row['url'],
        duration_seconds=row['duracion']
    )
    db.add(link)
```

---

## INICIALIZACIÓN EN MAIN.PY

### Función Lifespan

**Ubicación:** `/root/IcfesLeveling/apps/backend/app/main.py`

**Decorador:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ...
    yield
    # Shutdown
    ...
```

### Orden de Ejecución Detallado

#### PASO 1: Iniciar Servicios de Fondo

```python
from .services.media_background_service import media_background_service
await media_background_service.start_background_service()
```

**Propósito:** Sistema de caché de imágenes/videos

#### PASO 2: Crear Tablas SQLAlchemy

```python
Base.metadata.create_all(bind=engine)
logger.info("Database tables created/verified successfully")
```

**Comportamiento:**
- Ejecuta `CREATE TABLE IF NOT EXISTS` para todos los modelos
- **Idempotente:** No afecta tablas existentes
- **No modifica estructura** de tablas existentes
- **Complementa** los scripts SQL de Docker

#### PASO 3: Configurar Monitores

```python
from .monitoring.schema_guard import setup_schema_guard
from .monitoring.system_health import setup_system_health_monitor

schema_guard = setup_schema_guard(app, engine)
system_health_monitor = setup_system_health_monitor(app, engine)
```

**Propósito:** Monitoreo de salud del sistema

#### PASO 4: Asegurar Columnas Necesarias

**Función 1:** `_ensure_question_columns()`

```python
def _ensure_question_columns() -> None:
    ddl_statements = [
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS pregunta_texto TEXT",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS pregunta_imagen VARCHAR(500)",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_a_texto TEXT",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_a_imagen VARCHAR(500)",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_b_texto TEXT",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_b_imagen VARCHAR(500)",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_c_texto TEXT",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_c_imagen VARCHAR(500)",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_d_texto TEXT",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_d_imagen VARCHAR(500)",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS respuesta_correcta VARCHAR(1)",
        "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS puntos_xp INTEGER DEFAULT 10"
    ]
    with engine.begin() as conn:
        for ddl in ddl_statements:
            conn.execute(text(ddl))
```

**Función 2:** `_ensure_diagnostic_test_columns()`

```python
def _ensure_diagnostic_test_columns() -> None:
    ddl_statements = [
        "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS reassessment_type VARCHAR(50)",
        "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS original_test_id UUID",
        "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS is_monthly_reassessment BOOLEAN DEFAULT FALSE",
        "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS days_since_initial INTEGER",
        "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS comparison_with_initial JSONB",
        # ... 10 columnas más
    ]
    # Ejecutar...
```

**Función 3:** `_ensure_advanced_learning_tables()`

```python
def _ensure_advanced_learning_tables() -> None:
    # Verificar si existen tablas críticas
    table_checks = [
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'user_skills'",
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'question_responses'",
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_sessions'",
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'skill_prerequisites'"
    ]

    # Si faltan, ejecutar SQL
    if missing_tables:
        sql_file_path = 'database/init/15-advanced-learning-system.sql'
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        with engine.begin() as conn:
            conn.execute(text(sql_content))
```

#### PASO 5: Importar Preguntas desde Excel

```python
auto_import = os.getenv("AUTO_IMPORT_QUESTIONS", "false").lower() in ("1", "true", "yes")
excel_path = os.getenv("QUESTIONS_EXCEL_PATH")
clear_existing = os.getenv("IMPORT_CLEAR_EXISTING", "false").lower() in ("1", "true", "yes")

if auto_import and excel_path and os.path.exists(excel_path):
    from .import_icfes_excel import ICFESExcelImporter

    db = next(get_db())

    if clear_existing:
        logger.info("🧹 Clearing existing questions...")
        db.query(Question).delete()
        db.commit()

    importer = ICFESExcelImporter(db)
    result = importer.import_excel(excel_path, validate_only=False)
    logger.info(f"✅ Imported {result['imported_questions']} questions")
```

**Variables de Entorno:**
```bash
AUTO_IMPORT_QUESTIONS=true
QUESTIONS_EXCEL_PATH=/seed_data/questions.xlsx
IMPORT_CLEAR_EXISTING=true
```

**Proceso:**
1. Verificar si está habilitado
2. Verificar que el Excel exista
3. Obtener sesión de DB
4. Limpiar preguntas existentes (si clear_existing=true)
5. Inicializar importador
6. Leer Excel y mapear campos
7. Insertar preguntas
8. Commit y log de resultados

**Reintentos:** 3 intentos con backoff exponencial

#### PASO 6: Cargar Catálogo de Temas ICFES

```python
catalog_csv_path = os.getenv("ICFES_CATALOG_CSV_PATH", "/app/01_icfes_topics_catalog.csv")

if os.path.exists(catalog_csv_path):
    from .scripts.load_icfes_catalog import ICFESCatalogLoader

    db = next(get_db())
    loader = ICFESCatalogLoader({
        'host': 'postgres',
        'port': '5432',
        'database': 'gameplay_db',
        'user': 'gameplay',
        'password': 'gameplay123'
    })
    loader.run(catalog_csv_path)
    logger.info("✅ ICFES topics catalog loaded successfully")
```

**Reintentos:** 3 intentos con backoff exponencial

#### PASO 7: Cargar Enlaces de YouTube

```python
try:
    from .scripts.load_youtube_links import YouTubeLinksLoader
    youtube_loader = YouTubeLinksLoader()
    await youtube_loader.load_youtube_links()
    logger.info("✅ YouTube links catalog loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ YouTube links loading failed: {e}")
```

**Comportamiento:**
- No falla la inicialización si no se pueden cargar
- Solo logea warning

#### PASO 8: Sistema Listo

```python
logger.info("🎉 Configuración automática del sistema completada exitosamente")

yield  # Aplicación corriendo

# Shutdown
logger.info("Shutting down ICFES LEVELING API...")
await media_background_service.stop_background_service()
media_optimization_service.cleanup()
```

---

## ANÁLISIS DE PROBLEMAS Y INCONSISTENCIAS

### PROBLEMA 1: Doble Creación de Tablas

**Descripción:**
Las tablas se crean en DOS lugares diferentes:
1. Scripts SQL en Docker (`01-init.sql`)
2. SQLAlchemy `Base.metadata.create_all()` en startup

**Consecuencias:**
- **Potencial inconsistencia** entre definiciones SQL y modelos
- **Campos comentados** en modelos porque "no existen en la tabla"
- **Confusión** sobre la fuente de verdad

**Ejemplo:**
```python
# En question.py
# image_url = Column(String(500))  # Comentado: columna no existe en la tabla
# options_images = Column(JSON)    # Comentado: columna no existe en la tabla
# usage_count = Column(Integer, default=0)  # Comentado: columna no existe en la tabla
```

**Evidencia:**
- 30+ campos comentados en `question.py`
- 10+ campos comentados en `user.py`
- 5+ campos comentados en `topic.py`

**Causa Raíz:**
- Los scripts SQL definen la estructura inicial
- SQLAlchemy solo agrega tablas que no existen
- Los modelos tienen campos que **NO están en los scripts SQL**
- No se sincronizan las definiciones

### PROBLEMA 2: Triple Sistema de Carga de Preguntas

**Descripción:**
Las preguntas ICFES se pueden cargar desde TRES lugares:

1. **99-load-icfes-data.sh** (Docker init)
   - Archivo: `/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx`
   - Ejecución: Primera inicialización de container

2. **main.py startup** (FastAPI)
   - Archivo: `/seed_data/questions.xlsx`
   - Variable: `AUTO_IMPORT_QUESTIONS=true`
   - Ejecución: Cada vez que arranca el backend

3. **02-seed-data.sql** (Comentado)
   - Preguntas de ejemplo hardcodeadas en SQL
   - Actualmente comentadas

**Consecuencias:**
- **Confusión** sobre cuál fuente usar
- **Posible duplicación** si ambos se ejecutan
- **Diferentes rutas** para el mismo archivo Excel

**Evidencia:**
```bash
# Docker script busca:
/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx

# Backend busca:
/seed_data/questions.xlsx

# Docker-compose monta:
- ./database/allquestions:/data
- ./database/seed_data:/app/seed_data
```

### PROBLEMA 3: ALTER TABLE en Startup

**Descripción:**
Se ejecutan `ALTER TABLE ADD COLUMN IF NOT EXISTS` en **CADA startup** de la aplicación

**Ubicación:**
- `_ensure_question_columns()`
- `_ensure_diagnostic_test_columns()`

**Consecuencias:**
- **Lentitud** en startup (12 DDL statements por startup)
- **No es necesario** si las tablas ya existen
- **Anti-pattern** de hacer DDL en código de aplicación

**Mejor Práctica:**
- Usar migraciones (Alembic)
- O solo en scripts SQL de inicialización

### PROBLEMA 4: Ausencia de Migraciones

**Descripción:**
El proyecto **NO usa Alembic** ni ningún sistema de migraciones

**Consecuencias:**
- **Imposible rastrear** cambios en el esquema
- **Difícil coordinar** cambios entre desarrollo y producción
- **Rollback imposible** de cambios de esquema
- **Sincronización manual** entre SQL scripts y modelos SQLAlchemy

**Evidencia:**
```bash
$ find /root/IcfesLeveling -name "alembic.ini"
# No files found

$ find /root/IcfesLeveling -name "alembic" -type d
# No files found
```

### PROBLEMA 5: UUIDs Hardcodeados

**Descripción:**
Los IDs de subjects están **hardcodeados** en múltiples lugares

**Lugares:**
1. `02-seed-data.sql` - INSERT de subjects
2. `99-load-icfes-data.sh` - Mapeo de áreas
3. `main.py` startup - Importador de Excel
4. Frontend - Múltiples componentes
5. Scripts Python - Loaders y importers

**UUIDs:**
```
550e8400-e29b-41d4-a716-446655440001 - Matemáticas
550e8400-e29b-41d4-a716-446655440002 - Lenguaje
550e8400-e29b-41d4-a716-446655440003 - Ciencias Naturales
550e8400-e29b-41d4-a716-446655440004 - Ciencias Sociales
550e8400-e29b-41d4-a716-446655440005 - Inglés
```

**Consecuencias:**
- **Cambio difícil** si se necesitan nuevos subjects
- **Acoplamiento fuerte** entre componentes
- **Mantenimiento complicado**

**Mejor Práctica:**
- Usar enums o constantes compartidas
- O lookup dinámico por nombre

### PROBLEMA 6: Campos Multimedia Inconsistentes

**Descripción:**
Hay **DOS sistemas** de campos para opciones de preguntas:

**Sistema 1: Campos individuales (Nuevo)**
```sql
pregunta_texto, pregunta_imagen
opcion_a_texto, opcion_a_imagen
opcion_b_texto, opcion_b_imagen
opcion_c_texto, opcion_c_imagen
opcion_d_texto, opcion_d_imagen
```

**Sistema 2: Campos JSON (Legacy)**
```sql
question_text
options (JSON: {"a": "...", "b": "...", "c": "...", "d": "..."})
image_url (comentado)
options_images (comentado)
```

**Consecuencias:**
- **Confusión** sobre qué campos usar
- **Código de validación** debe manejar ambos sistemas
- **Duplicación** de datos en algunos casos

**Evidencia:**
```python
# En question.py validate_question()
def opcion_tiene_contenido(letra: str) -> bool:
    # Chequear campos nuevos
    texto = getattr(self, f'opcion_{letra}_texto')
    imagen = getattr(self, f'opcion_{letra}_imagen')

    # Chequear campos legacy
    legacy_text = self.options.get(letra.upper())

    return bool(texto or imagen or legacy_text)
```

### PROBLEMA 7: Comentarios "Columna no existe"

**Descripción:**
Múltiples campos en modelos están **comentados** con nota "columna no existe en la tabla"

**Ejemplos:**

```python
# user.py
# avatar_url = Column(String(500))  # No existe en la tabla
# streak_days = Column(Integer, default=0)  # No existe en la tabla
# is_premium = Column(Boolean, default=False)  # No existe en la tabla
# premium_expires_at = Column(DateTime)  # No existe en la tabla

# question.py
# image_url = Column(String(500))  # Columna no existe en la tabla
# options_images = Column(JSON)  # Columna no existe en la tabla
# is_validated = Column(String(20))  # Columna no existe en la tabla
# usage_count = Column(Integer)  # Columna no existe en la tabla

# topic.py
# codigo_tema = Column(String(50))  # Column doesn't exist
# order_index = Column(Integer)  # Column doesn't exist
```

**Causa:**
- Los modelos fueron diseñados con campos adicionales
- Los scripts SQL no los incluyeron
- En lugar de agregar al SQL, se comentaron en Python

**Consecuencia:**
- **Funcionalidad no disponible** (premium, validación, etc.)
- **Código muerto** en los modelos
- **Confusión** sobre qué está implementado

### PROBLEMA 8: Orden de Ejecución No Garantizado

**Descripción:**
Los scripts SQL se ejecutan en **orden alfabético**, pero hay dependencias

**Ejemplo:**
```
03-import-icfes-data.sql  # Agrega columnas a questions
10-study-plans-icfes.sql  # Podría depender de subjects/topics
30-icfes-migration.sql    # "Migración" pero se ejecuta en orden alfabético
```

**Consecuencias:**
- **Posibles errores** si el orden no es correcto
- **Nombres confusos** para forzar orden (99-*, 03-*, etc.)
- **Difícil mantener** dependencias

**Mejor Práctica:**
- Usar números de secuencia claros (001, 002, 003)
- O usar sistema de migraciones con dependencias explícitas

### PROBLEMA 9: Múltiples Versiones de Catálogo YouTube

**Descripción:**
Hay **3 versiones** del mismo script:

```
06-enhanced-youtube-catalog.sql
06-enhanced-youtube-catalog-corrected.sql
06-enhanced-youtube-catalog-fallback.sql
```

**Consecuencia:**
- **Confusión** sobre cuál se ejecuta
- **Duplicación** de lógica
- **Posibles conflictos** si todos se ejecutan

### PROBLEMA 10: Falta de Documentación en Scripts

**Descripción:**
Los scripts SQL tienen **poca documentación** sobre:
- Qué hacen
- Por qué existen
- Cuándo se ejecutan
- Qué dependencias tienen

**Ejemplo:**
```sql
-- 003_video_learning_system.sql
-- ¿Qué es este script?
-- ¿Por qué empieza con 003?
-- ¿Tiene dependencias?
```

---

## DIAGRAMA DE FLUJO

### Flujo Completo de Inicialización

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE UP                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL Container Starts                         │
│              - postgres:16                                       │
│              - Volumes mounted:                                  │
│                * ./database/init -> /docker-entrypoint-initdb.d  │
│                * ./database/allquestions -> /data                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         FASE 1: Ejecutar Scripts SQL (Orden Alfabético)         │
├─────────────────────────────────────────────────────────────────┤
│  01-create-production-db.sql   → Crear DB si no existe          │
│  01-init.sql                   → Tablas base (27 tablas)        │
│  02-seed-data.sql              → Datos iniciales (subjects, etc)│
│  03-admin-user.sql             → Usuario admin                   │
│  03-boss-tables.sql            → Tablas de jefes                │
│  03-import-icfes-data.sql      → ⭐ 81 campos ICFES             │
│  03-load-csv-data.sql          → Carga CSV                      │
│  04-import-study-plan-*.sql    → Plantillas                     │
│  04-monthly-reassessment.sql   → Re-evaluación                  │
│  05-*.sql                      → Premium, YouTube links          │
│  06-*.sql                      → YouTube catalog, Guilds         │
│  07-achievement-system.sql     → Logros                         │
│  08-virtual-economy.sql        → Economía                       │
│  09-question-enhancements.sql  → Mejoras preguntas              │
│  10-study-plans-icfes.sql      → Planes ICFES                   │
│  11-diagnostic-analytics.sql   → Analytics                      │
│  14-multimedia-questions.sql   → Multimedia                     │
│  15-expanded-achievements.sql  → Logros expandidos              │
│  16-gamification-complete.sql  → Gamificación                   │
│  17-error-recovery-system.sql  → Recuperación errores           │
│  17-gamification-sample-data.sql → Datos ejemplo                │
│  30-icfes-migration.sql        → Migración ICFES                │
│  99-definitive-data-init.sql   → Inicialización definitiva      │
│  99-final-setup.sql            → Verificación final             │
│  99-load-icfes-data.sh         → ⭐ CARGA EXCEL                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│     FASE 2: Script Bash - Carga Excel (99-load-icfes-data.sh)  │
├─────────────────────────────────────────────────────────────────┤
│  1. Instalar Python + pip                                        │
│  2. Instalar pandas, psycopg2, openpyxl                         │
│  3. Esperar PostgreSQL (pg_isready)                             │
│  4. Leer Excel: /data/ICFES_BASE_DATOS_COMPLETA_*.xlsx          │
│  5. Mapear área_evaluada → subject_id UUID                      │
│  6. DELETE FROM questions                                        │
│  7. INSERT ~480 preguntas con 81 campos                         │
│  8. Log resultados                                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PostgreSQL Ready                                 │
│        Tablas creadas + Datos seed + Preguntas ICFES            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend Container Starts (FastAPI)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         FASE 3: FastAPI Lifespan Startup (main.py)              │
├─────────────────────────────────────────────────────────────────┤
│  PASO 1: Start media background service                         │
│         └─> media_background_service.start_background_service() │
│                                                                  │
│  PASO 2: Create tables with SQLAlchemy                          │
│         └─> Base.metadata.create_all(bind=engine)               │
│             (Solo crea tablas que NO existen)                   │
│                                                                  │
│  PASO 3: Setup system monitors                                  │
│         ├─> setup_schema_guard(app, engine)                     │
│         └─> setup_system_health_monitor(app, engine)            │
│                                                                  │
│  PASO 4: Ensure columns (ALTER TABLE IF NOT EXISTS)             │
│         ├─> _ensure_question_columns()                          │
│         ├─> _ensure_diagnostic_test_columns()                   │
│         └─> _ensure_advanced_learning_tables()                  │
│                                                                  │
│  PASO 5: Auto-import Excel (if AUTO_IMPORT_QUESTIONS=true)      │
│         ├─> Check if enabled and file exists                    │
│         ├─> ICFESExcelImporter(db).import_excel()               │
│         ├─> Read /seed_data/questions.xlsx                      │
│         ├─> Validate and map fields                             │
│         ├─> DELETE FROM questions (if CLEAR_EXISTING=true)      │
│         └─> INSERT questions                                    │
│                                                                  │
│  PASO 6: Load ICFES topics catalog                              │
│         ├─> ICFESCatalogLoader().run(catalog_csv_path)          │
│         └─> Read /seed_data/topics_catalog.csv                  │
│                                                                  │
│  PASO 7: Load YouTube links                                     │
│         ├─> YouTubeLinksLoader().load_youtube_links()           │
│         └─> Read /seed_data/youtube_catalog_*.csv               │
│                                                                  │
│  PASO 8: Sistema listo                                          │
│         └─> logger.info("🎉 Sistema listo")                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              APLICACIÓN CORRIENDO                               │
│         - API endpoints disponibles                              │
│         - Base de datos completamente inicializada              │
│         - ~480 preguntas ICFES cargadas                         │
│         - Catálogo de temas cargado                             │
│         - Enlaces de YouTube cargados                           │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Carga de Preguntas (Detallado)

```
┌──────────────────────────────────────────────────────────────────┐
│         OPCIÓN A: Docker Init (99-load-icfes-data.sh)            │
├──────────────────────────────────────────────────────────────────┤
│  Cuándo: Primera inicialización del container PostgreSQL         │
│  Archivo: /data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx│
│  Proceso:                                                         │
│    1. Bash script instala Python en container                    │
│    2. Script Python inline lee Excel                             │
│    3. DELETE FROM questions                                      │
│    4. INSERT ~480 preguntas                                      │
│  Ventajas: Se ejecuta una sola vez, parte del init de DB         │
│  Desventajas: Solo en primera init, requiere rebuild para cambios│
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│         OPCIÓN B: Backend Startup (main.py lifespan)             │
├──────────────────────────────────────────────────────────────────┤
│  Cuándo: Cada vez que arranca el backend (si habilitado)         │
│  Archivo: /seed_data/questions.xlsx                              │
│  Variables:                                                       │
│    - AUTO_IMPORT_QUESTIONS=true                                  │
│    - QUESTIONS_EXCEL_PATH=/seed_data/questions.xlsx              │
│    - IMPORT_CLEAR_EXISTING=true                                  │
│  Proceso:                                                         │
│    1. Verificar archivo existe                                   │
│    2. ICFESExcelImporter lee Excel                               │
│    3. Validar estructura                                         │
│    4. DELETE FROM questions (si CLEAR_EXISTING)                  │
│    5. Mapear campos Excel → modelo Question                      │
│    6. INSERT en lotes                                            │
│  Ventajas: Flexible, se puede re-ejecutar, no requiere rebuild   │
│  Desventajas: Ejecuta cada startup, puede ser lento              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│         OPCIÓN C: SQL Script (02-seed-data.sql - COMENTADO)      │
├──────────────────────────────────────────────────────────────────┤
│  Cuándo: Primera init de container (si estuviera activo)         │
│  Preguntas: 25 preguntas de ejemplo hardcodeadas                 │
│  Estado: COMENTADO (se usa data real del ICFES)                  │
│  Notas: Útil para desarrollo/testing sin Excel                   │
└──────────────────────────────────────────────────────────────────┘

RECOMENDACIÓN:
===============
- Usar OPCIÓN A (Docker init) para producción
- Usar OPCIÓN B (Backend startup) para desarrollo
- Deshabilitar B si A está activo (evitar duplicación)
```

---

## RECOMENDACIONES

### RECOMENDACIÓN 1: Implementar Sistema de Migraciones (Alembic)

**Problema Actual:**
- No hay tracking de cambios de esquema
- Inconsistencias entre SQL scripts y modelos SQLAlchemy
- Difícil rollback de cambios

**Solución:**

```bash
# 1. Instalar Alembic
pip install alembic

# 2. Inicializar Alembic
cd /root/IcfesLeveling/apps/backend
alembic init alembic

# 3. Configurar alembic.ini
sqlalchemy.url = postgresql://gameplay:gameplay123@postgres:5432/gameplay_db

# 4. Configurar env.py
from app.models import Base
target_metadata = Base.metadata

# 5. Crear migración inicial desde estado actual
alembic revision --autogenerate -m "Initial migration from existing schema"

# 6. Para futuros cambios
alembic revision --autogenerate -m "Add campo_nuevo to questions"
alembic upgrade head
```

**Beneficios:**
- Tracking de todos los cambios de esquema
- Rollback fácil de cambios
- Sincronización automática entre modelos y DB
- Historial de versiones

### RECOMENDACIÓN 2: Unificar Creación de Tablas

**Problema Actual:**
- Tablas se crean en SQL scripts Y en SQLAlchemy
- Campos comentados en modelos

**Solución Opción A (SQL como fuente de verdad):**

```python
# Eliminar Base.metadata.create_all() de main.py
# Mantener solo scripts SQL
# Sincronizar modelos con scripts SQL manualmente
```

**Solución Opción B (SQLAlchemy como fuente de verdad):**

```bash
# 1. Eliminar scripts de creación de tablas (01-init.sql)
# 2. Mantener solo datos seed en SQL
# 3. Usar Alembic para generar migraciones
# 4. Aplicar migraciones en Docker init
```

**Recomendación:** Opción B (SQLAlchemy + Alembic)

**Estructura Recomendada:**
```
database/init/
├── 01-create-db.sql              # Solo CREATE DATABASE
├── 02-enable-extensions.sql      # CREATE EXTENSION uuid-ossp
├── 03-apply-migrations.sh        # alembic upgrade head
├── 10-seed-subjects.sql          # Datos: subjects con UUIDs fijos
├── 11-seed-hero-classes.sql      # Datos: hero classes
├── 12-seed-personality.sql       # Datos: personality questions
├── 20-load-questions.sh          # Carga Excel
├── 21-load-topics-catalog.sh     # Carga CSV temas
├── 22-load-youtube-links.sh      # Carga CSV videos
└── 99-verify-setup.sql           # Verificación final
```

### RECOMENDACIÓN 3: Unificar Carga de Preguntas

**Problema Actual:**
- Dos sistemas de carga (Docker + Backend)
- Diferentes rutas de archivo
- Posible duplicación

**Solución:**

```yaml
# docker-compose.yml
services:
  postgres:
    environment:
      - LOAD_ICFES_DATA=true
      - ICFES_EXCEL_PATH=/data/questions.xlsx
    volumes:
      - ./database/allquestions:/data

  backend:
    environment:
      - AUTO_IMPORT_QUESTIONS=false  # Deshabilitar en backend
```

**Script Mejorado:**

```bash
# database/init/20-load-questions.sh
#!/bin/bash

LOAD_DATA=${LOAD_ICFES_DATA:-true}
EXCEL_FILE=${ICFES_EXCEL_PATH:-/data/questions.xlsx}

if [ "$LOAD_DATA" != "true" ]; then
    echo "⏭️ Skipping ICFES data load (LOAD_ICFES_DATA=$LOAD_DATA)"
    exit 0
fi

if [ ! -f "$EXCEL_FILE" ]; then
    echo "⚠️ Excel file not found: $EXCEL_FILE"
    echo "⏭️ Skipping data load"
    exit 0
fi

echo "📊 Loading ICFES data from: $EXCEL_FILE"

# Instalar dependencias
apt-get update -qq
apt-get install -y python3 python3-pip > /dev/null 2>&1
pip3 install pandas psycopg2-binary openpyxl > /dev/null 2>&1

# Ejecutar loader
python3 /docker-entrypoint-initdb.d/load_questions.py

echo "✅ ICFES data loaded successfully"
```

### RECOMENDACIÓN 4: Centralizar Configuración de UUIDs

**Problema Actual:**
- UUIDs hardcodeados en múltiples lugares

**Solución:**

```python
# apps/backend/app/core/constants.py

from enum import Enum
from uuid import UUID

class SubjectUUID(str, Enum):
    MATEMATICAS = "550e8400-e29b-41d4-a716-446655440001"
    LENGUAJE = "550e8400-e29b-41d4-a716-446655440002"
    CIENCIAS_NATURALES = "550e8400-e29b-41d4-a716-446655440003"
    CIENCIAS_SOCIALES = "550e8400-e29b-41d4-a716-446655440004"
    INGLES = "550e8400-e29b-41d4-a716-446655440005"

# Mapeo de nombres a UUIDs
SUBJECT_NAME_TO_UUID = {
    "matemáticas": SubjectUUID.MATEMATICAS,
    "lenguaje": SubjectUUID.LENGUAJE,
    "lectura crítica": SubjectUUID.LENGUAJE,
    "ciencias naturales": SubjectUUID.CIENCIAS_NATURALES,
    "ciencias sociales": SubjectUUID.CIENCIAS_SOCIALES,
    "inglés": SubjectUUID.INGLES,
}

def get_subject_uuid(name: str) -> str:
    """Get subject UUID from name (case-insensitive)"""
    name_lower = name.lower().strip()
    return SUBJECT_NAME_TO_UUID.get(name_lower, SubjectUUID.MATEMATICAS)
```

**Uso:**

```python
# En importers
from app.core.constants import get_subject_uuid

subject_id = get_subject_uuid(row['área_evaluada'])
```

### RECOMENDACIÓN 5: Unificar Sistema Multimedia

**Problema Actual:**
- Dos sistemas de campos (individuales + JSON)

**Solución:**

```python
# Migración Alembic
"""migrate_to_individual_fields

Revision ID: 20250120_001
"""

def upgrade():
    # 1. Ya existen los campos individuales

    # 2. Migrar datos de JSON a campos individuales
    op.execute("""
        UPDATE questions
        SET
            pregunta_texto = COALESCE(pregunta_texto, question_text),
            opcion_a_texto = COALESCE(opcion_a_texto, options->>'a'),
            opcion_b_texto = COALESCE(opcion_b_texto, options->>'b'),
            opcion_c_texto = COALESCE(opcion_c_texto, options->>'c'),
            opcion_d_texto = COALESCE(opcion_d_texto, options->>'d'),
            respuesta_correcta = COALESCE(respuesta_correcta, LEFT(correct_answer, 1))
    """)

    # 3. Marcar campos legacy como deprecated (no eliminar aún)
    # question_text, options, correct_answer permanecen por compatibilidad

def downgrade():
    # Rollback: copiar de campos individuales a JSON
    pass
```

### RECOMENDACIÓN 6: Agregar Validación de Datos en Startup

**Solución:**

```python
# apps/backend/app/core/validators.py

class DatabaseValidator:
    def __init__(self, db: Session):
        self.db = db
        self.errors = []

    def validate_all(self) -> bool:
        """Run all validations"""
        self.validate_subjects()
        self.validate_questions()
        self.validate_topics()
        return len(self.errors) == 0

    def validate_subjects(self):
        """Ensure all 5 subjects exist with correct UUIDs"""
        from app.core.constants import SubjectUUID

        for uuid_value in SubjectUUID:
            subject = self.db.query(Subject).filter(
                Subject.id == uuid_value
            ).first()

            if not subject:
                self.errors.append(f"Missing subject with UUID: {uuid_value}")

    def validate_questions(self):
        """Validate question data integrity"""
        # Check for questions without subject
        count = self.db.query(Question).filter(
            Question.subject_id.is_(None)
        ).count()

        if count > 0:
            self.errors.append(f"{count} questions without subject_id")

        # Check for questions without answer
        count = self.db.query(Question).filter(
            Question.respuesta_correcta.is_(None),
            Question.correct_answer.is_(None)
        ).count()

        if count > 0:
            self.errors.append(f"{count} questions without answer")

# En main.py lifespan
validator = DatabaseValidator(db)
if not validator.validate_all():
    logger.error(f"❌ Database validation failed:")
    for error in validator.errors:
        logger.error(f"  - {error}")
    raise RuntimeError("Database validation failed")
```

### RECOMENDACIÓN 7: Documentar Scripts SQL

**Solución:**

Agregar headers consistentes a todos los scripts:

```sql
-- =====================================================
-- Script: 01-init.sql
-- Purpose: Create fundamental database tables
-- Dependencies: None (first script)
-- Tables Created: users, subjects, topics, questions, etc.
-- Order: 01 (runs first)
-- Author: ICFES Leveling Team
-- Date: 2025-01-20
-- =====================================================
-- DESCRIPTION:
-- This script creates all the core tables needed for the
-- ICFES Leveling platform, including user management,
-- subject/topic hierarchy, question storage, and
-- gamification features.
--
-- TABLES CREATED (27):
-- - users: User accounts and stats
-- - subjects: Academic subjects (5 fixed)
-- - topics: Topics within subjects
-- - questions: Question bank
-- - [... list all tables ...]
--
-- INDEXES CREATED (28):
-- - Performance indexes for common queries
--
-- FUNCTIONS CREATED:
-- - calculate_weighted_progress()
-- - update_updated_at_column()
-- =====================================================
```

### RECOMENDACIÓN 8: Monitoreo de Inicialización

**Solución:**

```python
# apps/backend/app/core/initialization_monitor.py

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class InitializationMonitor:
    def __init__(self):
        self.steps = []
        self.start_time = datetime.now()

    def log_step(self, step_name: str, status: str, duration_ms: int, details: Dict[str, Any] = None):
        """Log initialization step"""
        step = {
            "step": step_name,
            "status": status,  # 'started', 'completed', 'failed', 'skipped'
            "duration_ms": duration_ms,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.steps.append(step)

        if status == "completed":
            logger.info(f"✅ {step_name} completed in {duration_ms}ms")
        elif status == "failed":
            logger.error(f"❌ {step_name} failed after {duration_ms}ms")
        elif status == "skipped":
            logger.info(f"⏭️ {step_name} skipped")

    def generate_report(self) -> str:
        """Generate initialization report"""
        total_duration = (datetime.now() - self.start_time).total_seconds() * 1000

        completed = len([s for s in self.steps if s['status'] == 'completed'])
        failed = len([s for s in self.steps if s['status'] == 'failed'])
        skipped = len([s for s in self.steps if s['status'] == 'skipped'])

        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║              ICFES LEVELING - INITIALIZATION REPORT                ║
╠════════════════════════════════════════════════════════════════════╣
║ Total Duration: {total_duration:.2f}ms                             ║
║ Steps Completed: {completed}                                       ║
║ Steps Failed: {failed}                                             ║
║ Steps Skipped: {skipped}                                           ║
╠════════════════════════════════════════════════════════════════════╣
║ STEPS:                                                             ║
"""

        for step in self.steps:
            status_icon = {
                'completed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'started': '🔄'
            }.get(step['status'], '❓')

            report += f"║  {status_icon} {step['step']:<50} {step['duration_ms']:>6}ms ║\n"

        report += "╚════════════════════════════════════════════════════════════════════╝"

        return report

# Uso en main.py
monitor = InitializationMonitor()

# PASO 1
start = time.time()
await media_background_service.start_background_service()
monitor.log_step("Media Background Service", "completed", int((time.time() - start) * 1000))

# ... otros pasos ...

# Al final
logger.info(monitor.generate_report())
```

### RECOMENDACIÓN 9: Limpiar Scripts Duplicados

**Solución:**

```bash
# Eliminar scripts duplicados
rm database/init/06-enhanced-youtube-catalog-corrected.sql
rm database/init/06-enhanced-youtube-catalog-fallback.sql

# Mantener solo:
# - 06-enhanced-youtube-catalog.sql

# Renombrar para claridad:
mv database/init/003_video_learning_system.sql database/init/03-video-learning-system.sql
```

### RECOMENDACIÓN 10: Agregar Health Check de Inicialización

**Solución:**

```python
# apps/backend/app/routes/health.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Subject, Question

router = APIRouter()

@router.get("/health/initialization")
async def check_initialization(db: Session = Depends(get_db)):
    """
    Comprehensive health check for database initialization
    """
    checks = {
        "database_connection": False,
        "subjects_loaded": False,
        "questions_loaded": False,
        "topics_loaded": False,
        "icfes_fields_exist": False,
        "youtube_links_loaded": False,
    }

    try:
        # Check 1: Database connection
        db.execute("SELECT 1")
        checks["database_connection"] = True

        # Check 2: Subjects (must be exactly 5)
        subject_count = db.query(Subject).count()
        checks["subjects_loaded"] = (subject_count == 5)

        # Check 3: Questions (at least 100)
        question_count = db.query(Question).count()
        checks["questions_loaded"] = (question_count >= 100)

        # Check 4: Topics (at least 10)
        from app.models import Topic
        topic_count = db.query(Topic).count()
        checks["topics_loaded"] = (topic_count >= 10)

        # Check 5: ICFES fields exist
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        columns = [c['name'] for c in inspector.get_columns('questions')]
        icfes_fields = ['area_evaluada', 'competencia', 'componente', 'tema_especifico']
        checks["icfes_fields_exist"] = all(f in columns for f in icfes_fields)

        # Check 6: YouTube links
        from app.models import YouTubeLinks
        youtube_count = db.query(YouTubeLinks).count()
        checks["youtube_links_loaded"] = (youtube_count > 0)

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "checks": checks
        }

    all_passed = all(checks.values())

    return {
        "status": "healthy" if all_passed else "degraded",
        "checks": checks,
        "details": {
            "subjects": subject_count,
            "questions": question_count,
            "topics": topic_count,
            "youtube_links": youtube_count
        }
    }
```

---

## CONCLUSIONES

### Estado Actual

El sistema de inicialización de base de datos de ICFES Leveling es **funcional pero complejo**, con:

✅ **Fortalezas:**
- **Carga automática** de datos ICFES desde Excel
- **Sistema híbrido** flexible (SQL + SQLAlchemy)
- **81 campos ICFES** implementados correctamente
- **Datos seed** completos para demostración
- **Gamificación** bien estructurada
- **Verificación final** con 99-final-setup.sql

⚠️ **Debilidades:**
- **Falta de migraciones** (no usa Alembic)
- **Doble creación** de tablas (SQL + SQLAlchemy)
- **Campos comentados** en modelos
- **Múltiples sistemas** de carga de datos
- **UUIDs hardcodeados** en múltiples lugares
- **Documentación insuficiente** en scripts
- **Scripts duplicados** (3 versiones de YouTube catalog)

### Prioridades de Mejora

**ALTA PRIORIDAD:**
1. Implementar Alembic para migraciones
2. Unificar creación de tablas (elegir SQL O SQLAlchemy)
3. Sincronizar modelos con scripts SQL (eliminar campos comentados)
4. Unificar sistema de carga de preguntas

**MEDIA PRIORIDAD:**
5. Centralizar configuración de UUIDs
6. Documentar todos los scripts SQL
7. Limpiar scripts duplicados
8. Agregar validación de datos en startup

**BAJA PRIORIDAD:**
9. Implementar monitoreo de inicialización
10. Agregar health check de inicialización

### Recomendación Final

**MIGRAR A:**
1. **Alembic** como sistema único de migraciones
2. **SQLAlchemy** como fuente de verdad del esquema
3. **SQL scripts** solo para datos seed
4. **Backend startup** solo para carga de datos externos (Excel, CSV)

**Estructura Ideal:**
```
database/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_icfes_fields.py
│   │   └── 003_add_gamification.py
│   └── env.py
├── init/
│   ├── 01-create-db.sql
│   ├── 02-extensions.sql
│   ├── 03-apply-migrations.sh  # alembic upgrade head
│   ├── 10-seed-subjects.sql
│   ├── 11-seed-data.sql
│   ├── 20-load-questions.sh
│   └── 99-verify.sql
└── seed_data/
    ├── questions.xlsx
    ├── topics_catalog.csv
    └── youtube_links.csv
```

---

**FIN DEL REPORTE**

---

**Notas:**
- Este análisis fue realizado el 2025-10-20
- Basado en código en /root/IcfesLeveling
- Versión de PostgreSQL: 16
- Versión de SQLAlchemy: 2.x
- Total de scripts SQL analizados: 31
- Total de modelos SQLAlchemy analizados: 45+
