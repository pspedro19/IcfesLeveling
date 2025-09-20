# 🔌 API ENDPOINTS - SISTEMA DE RECOMENDACIONES

## 📋 **ENDPOINTS PRINCIPALES**

### **🎯 1. DIAGNÓSTICO ADAPTATIVO IRT**

#### `POST /api/v1/diagnostic-public/start-test`
**Descripción**: Inicia un test diagnóstico adaptativo
```json
{
  "subject_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "optional-uuid",
  "test_type": "diagnostic"
}
```

#### `GET /api/v1/diagnostic-public/next-question/{test_id}`
**Descripción**: Obtiene la siguiente pregunta usando IRT
**Algoritmo**: Máxima Información Fisher
```json
Response: {
  "question_id": "uuid",
  "question_text": "string",
  "options": ["A", "B", "C", "D"],
  "current_theta": 0.25,
  "questions_remaining": 8
}
```

#### `POST /api/v1/diagnostic-public/submit-answer`
**Descripción**: Envía respuesta y recalcula theta
```json
{
  "test_id": "uuid",
  "question_id": "uuid",
  "user_answer": "B",
  "response_time_ms": 15000
}
```

### **🎬 2. RECOMENDACIONES INTELIGENTES**

#### `GET /api/v1/diagnostic-public/study-plan/units/by-subject/{subject_id}`
**Descripción**: Plan personalizado basado en debilidades
**Parámetros**:
- `test_id` (opcional): Para personalización IRT
- `difficulty_filter` (opcional): 1-10

```json
Response: {
  "units": [
    {
      "unit_number": 1,
      "title": "Álgebra Básica",
      "videos": [
        {
          "id": "123",
          "title": "Ecuaciones Lineales",
          "url": "https://youtube.com/watch?v=...",
          "similarity_score": 0.89,
          "recommendation_reason": "Basado en errores en preguntas de álgebra"
        }
      ]
    }
  ],
  "personalized": true,
  "identified_weaknesses": ["Álgebra Básica", "Geometría"],
  "total_videos": 15
}
```

#### `GET /api/v1/recommendations/intelligent-videos`
**Descripción**: Recomendaciones usando embeddings vectoriales
**Parámetros**:
- `question_id`: UUID de pregunta fallada
- `limit`: Número de videos (default: 5)
- `min_similarity`: Umbral mínimo (default: 0.6)

### **🤖 3. LLM & EMBEDDINGS**

#### `POST /api/v1/ai/generate-explanation`
**Descripción**: Explicación personalizada usando GPT
```json
{
  "question_id": "uuid",
  "student_answer": "C",
  "correct_answer": "A",
  "student_level": "intermediate",
  "explanation_type": "step_by_step"
}
```

#### `POST /api/v1/embeddings/generate`
**Descripción**: Genera embeddings para contenido
```json
{
  "content_type": "question|video|topic",
  "content_text": "Resuelve la ecuación 2x + 5 = 15",
  "model": "text-embedding-3-large"
}
```

### **📊 4. ANÁLISIS Y MÉTRICAS**

#### `GET /api/v1/analytics/student-progress/{user_id}`
**Descripción**: Progreso del estudiante con IRT
```json
Response: {
  "current_theta": 0.75,
  "theta_progression": [-0.2, 0.1, 0.4, 0.75],
  "improvement_rate": 0.23,
  "identified_weaknesses": [
    {
      "topic": "Álgebra Básica",
      "confidence": 0.85,
      "improvement_needed": "high"
    }
  ]
}
```

---

## 🔧 **PARÁMETROS DE CONFIGURACIÓN**

### **IRT Configuration**
```python
IRT_CONFIG = {
    "max_questions": 20,
    "min_questions": 8,
    "theta_tolerance": 0.3,
    "max_information_weight": 0.7,
    "content_balancing_weight": 0.3
}
```

### **Embedding Configuration**
```python
EMBEDDING_CONFIG = {
    "model": "text-embedding-3-large",
    "dimensions": 3072,
    "similarity_threshold": 0.6,
    "batch_size": 100
}
```

### **Recommendation Weights**
```python
RECOMMENDATION_WEIGHTS = {
    "exact_match": 0.35,
    "semantic_similarity": 0.25,
    "subject_topic_match": 0.20,
    "quality_score": 0.15,
    "popularity": 0.05
}
```

---

## 📈 **MÉTRICAS DE RESPUESTA**

| **Endpoint** | **Avg Response Time** | **Cache TTL** |
|--------------|----------------------|---------------|
| `/next-question` | < 50ms | No cache |
| `/study-plan/units` | < 200ms | 5 min |
| `/intelligent-videos` | < 150ms | 10 min |
| `/generate-explanation` | < 2000ms | 1 hour |

---

## 🔐 **AUTENTICACIÓN**

```http
Authorization: Bearer {jwt_token}
X-API-Key: {api_key}
Content-Type: application/json
```

---

## ⚠️ **CÓDIGOS DE ERROR**

| **Código** | **Descripción** |
|------------|-----------------|
| 400 | Parámetros inválidos |
| 404 | Test/Question no encontrado |
| 429 | Rate limit excedido |
| 500 | Error interno del servidor |
| 503 | Servicio LLM no disponible |