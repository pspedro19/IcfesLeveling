# 🗄️ TABLAS DE BASE DE DATOS - SISTEMA DE RECOMENDACIONES

## 📋 **RESUMEN DE TABLAS**

El sistema de recomendaciones utiliza **12 tablas principales** interconectadas para gestionar diagnósticos, recomendaciones y análisis de aprendizaje.

---

## 🎯 **TABLAS PRINCIPALES**

### **1. `subjects` - Materias/Asignaturas**
```sql
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Materias ICFES (Matemáticas, Lenguaje, Ciencias, etc.)
**Relaciones**:
- `questions.subject_id` → `subjects.id`
- `youtube_catalog.subject_id` → `subjects.id`

### **2. `questions` - Banco de Preguntas**
```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id),
    pregunta_texto TEXT NOT NULL,
    opcion_a TEXT NOT NULL,
    opcion_b TEXT NOT NULL,
    opcion_c TEXT NOT NULL,
    opcion_d TEXT NOT NULL,
    respuesta_correcta CHAR(1) NOT NULL,
    explanation TEXT,

    -- Parámetros IRT 3PL
    parametro_irt_a DECIMAL(8,4) DEFAULT 1.0,    -- Discriminación
    parametro_irt_b DECIMAL(8,4) DEFAULT 0.0,    -- Dificultad
    parametro_irt_c DECIMAL(8,4) DEFAULT 0.25,   -- Adivinanza

    -- Metadatos educativos
    componente VARCHAR(255),
    competencia VARCHAR(255),
    afirmacion VARCHAR(255),
    evidencia VARCHAR(255),
    proceso_cognitivo VARCHAR(255),

    difficulty INTEGER DEFAULT 5,
    topic VARCHAR(255),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Banco de preguntas con parámetros IRT para evaluación adaptativa
**Relaciones**:
- `diagnostic_test_answers.question_id` → `questions.id`
- `question_video_recommendations.question_id` → `questions.id`

### **3. `diagnostic_tests` - Tests Diagnósticos**
```sql
CREATE TABLE diagnostic_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    subject_id UUID REFERENCES subjects(id),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',

    -- Resultados IRT
    final_theta_score DECIMAL(8,4),
    theta_standard_error DECIMAL(8,4),
    score_percentage DECIMAL(5,2),

    questions_answered INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    completed_at TIMESTAMP
);
```
**Propósito**: Registro de tests diagnósticos realizados por estudiantes
**Relaciones**:
- `diagnostic_test_answers.diagnostic_test_id` → `diagnostic_tests.id`

### **4. `diagnostic_test_answers` - Respuestas del Diagnóstico**
```sql
CREATE TABLE diagnostic_test_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostic_test_id UUID REFERENCES diagnostic_tests(id),
    question_id UUID REFERENCES questions(id),
    user_answer CHAR(1) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    theta_before DECIMAL(8,4),
    theta_after DECIMAL(8,4),
    information_gained DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Respuestas individuales con análisis IRT
**Uso en Recomendaciones**: Análisis de patrones de error para identificar debilidades

### **5. `youtube_catalog` - Catálogo de Videos Educativos**
```sql
CREATE TABLE youtube_catalog (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    description TEXT,
    subject_id UUID REFERENCES subjects(id),
    topic VARCHAR(255),
    duration_minutes INTEGER DEFAULT 15,
    xp_reward INTEGER DEFAULT 100,
    difficulty_level INTEGER DEFAULT 5,
    channel_name VARCHAR(255) DEFAULT 'ICFES Prep',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Catálogo de videos educativos para recomendaciones
**Relaciones**:
- `question_video_recommendations.video_id` → `youtube_catalog.id`
- `content_embeddings.content_id` → `youtube_catalog.id`

### **6. `content_embeddings` - Embeddings Vectoriales**
```sql
CREATE TABLE content_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(50) NOT NULL, -- 'question', 'video', 'topic'
    content_id VARCHAR(255) NOT NULL,
    embedding_vector FLOAT8[] NOT NULL, -- Array de 3072 dimensiones
    model_name VARCHAR(100) DEFAULT 'text-embedding-3-large',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Embeddings vectoriales para análisis semántico
**Uso**: Matching inteligente pregunta-video usando similitud coseno

### **7. `question_video_recommendations` - Recomendaciones Pregunta-Video**
```sql
CREATE TABLE question_video_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES questions(id),
    video_id INTEGER REFERENCES youtube_catalog(id),
    similarity_score DECIMAL(5,4) NOT NULL,
    recommendation_reason TEXT,
    algorithm_used VARCHAR(100),
    confidence_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Mapeo inteligente entre preguntas falladas y videos recomendados
**Algoritmos**: Embeddings semánticos + NLP keywords + scoring multidimensional

### **8. `ai_explanation` - Explicaciones Generadas por IA**
```sql
CREATE TABLE ai_explanation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    question_id UUID REFERENCES questions(id),
    explanation_text TEXT NOT NULL,
    explanation_type VARCHAR(50), -- 'step_by_step', 'conceptual', 'hint'
    student_level VARCHAR(50),
    generated_by VARCHAR(100) DEFAULT 'gpt-4',
    confidence_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Propósito**: Explicaciones personalizadas generadas por LLM
**Uso**: Análisis de patrones de error para mejorar recomendaciones

---

## 🔗 **RELACIONES Y FLUJOS DE DATOS**

### **FLUJO 1: DIAGNÓSTICO IRT**
```
subjects → diagnostic_tests → diagnostic_test_answers → questions
                ↓
        Análisis IRT (theta, información Fisher)
```

### **FLUJO 2: RECOMENDACIONES INTELIGENTES**
```
diagnostic_test_answers (errores) → content_embeddings → youtube_catalog
                ↓
        question_video_recommendations
```

### **FLUJO 3: EXPLICACIONES IA**
```
questions (falladas) → ai_explanation → content_embeddings
                ↓
        Análisis de patrones → Mejores recomendaciones
```

---

## 📊 **ÍNDICES PARA PERFORMANCE**

```sql
-- Índices para queries de recomendación
CREATE INDEX idx_diagnostic_answers_incorrect ON diagnostic_test_answers(diagnostic_test_id) WHERE is_correct = false;
CREATE INDEX idx_questions_subject_topic ON questions(subject_id, topic);
CREATE INDEX idx_youtube_catalog_subject_difficulty ON youtube_catalog(subject_id, difficulty_level);
CREATE INDEX idx_content_embeddings_type_id ON content_embeddings(content_type, content_id);
CREATE INDEX idx_question_video_recommendations_score ON question_video_recommendations(similarity_score DESC);

-- Índice vectorial para embeddings (requiere extensión vector)
CREATE INDEX ON content_embeddings USING ivfflat (embedding_vector vector_cosine_ops);
```

---

## 🎯 **DATOS CLAVE PARA ALGORITMOS**

### **IRT Parameters (en tabla `questions`)**
- **parametro_irt_a**: Discriminación (0.5-2.0) - Qué tan bien diferencia la pregunta
- **parametro_irt_b**: Dificultad (-3.0 a +3.0) - Nivel de habilidad requerido
- **parametro_irt_c**: Adivinanza (0.10-0.25) - Probabilidad de respuesta correcta por azar

### **Embeddings Vectoriales (en tabla `content_embeddings`)**
- **embedding_vector**: Array de 3072 dimensiones (OpenAI text-embedding-3-large)
- **Similitud Coseno**: `SELECT 1 - (embedding1 <=> embedding2) AS similarity`

### **Scoring de Recomendaciones (en tabla `question_video_recommendations`)**
- **similarity_score**: 0.0-1.0 (similitud semántica)
- **confidence_score**: 0.0-1.0 (confianza del algoritmo)

---

## 🔧 **QUERIES PRINCIPALES DEL SISTEMA**

### **1. Obtener debilidades del estudiante**
```sql
SELECT q.topic, q.componente, COUNT(*) as errors
FROM diagnostic_test_answers dta
JOIN questions q ON dta.question_id = q.id
WHERE dta.diagnostic_test_id = :test_id
  AND dta.is_correct = false
GROUP BY q.topic, q.componente
ORDER BY errors DESC;
```

### **2. Buscar videos por similitud semántica**
```sql
SELECT yc.*, qvr.similarity_score
FROM youtube_catalog yc
JOIN question_video_recommendations qvr ON yc.id = qvr.video_id
WHERE qvr.question_id = :question_id
ORDER BY qvr.similarity_score DESC
LIMIT 5;
```

### **3. Análisis IRT - Próxima pregunta**
```sql
SELECT q.*,
       ABS(q.parametro_irt_b - :current_theta) as difficulty_distance
FROM questions q
WHERE q.subject_id = :subject_id
  AND q.id NOT IN (SELECT question_id FROM diagnostic_test_answers WHERE diagnostic_test_id = :test_id)
ORDER BY
  q.parametro_irt_a * (1 / (1 + EXP(-q.parametro_irt_a * (:current_theta - q.parametro_irt_b)))) DESC
LIMIT 1;
```

---

## 📈 **MÉTRICAS DE MONITOREO**

### **Tablas de Análisis**
- **Effectiveness**: `question_video_recommendations.confidence_score`
- **Student Engagement**: Videos completados vs. recomendados
- **Learning Outcomes**: Mejora en `diagnostic_tests.final_theta_score`

### **Alertas del Sistema**
- Embeddings desactualizados (> 30 días)
- Baja confianza en recomendaciones (< 0.6)
- Preguntas sin videos asociados

---

## 🔄 **PROCESO DE ACTUALIZACIÓN**

### **Daily Jobs**
1. **Generar embeddings** para contenido nuevo
2. **Recalcular recomendaciones** con nuevos datos
3. **Actualizar parámetros IRT** basado en respuestas

### **Weekly Analysis**
1. **Validar eficacia** de recomendaciones
2. **Optimizar algoritmos** de scoring
3. **Identificar gaps** en catálogo de videos

---

*Última actualización: Septiembre 2025*