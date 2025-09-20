# 🧠 EXPLICACIÓN DETALLADA DE ALGORITMOS

## 🎯 **1. ALGORITMO IRT 3PL (3-Parameter Logistic)**

### **Fórmula Principal**
```
P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
```

**Donde**:
- **θ (theta)**: Habilidad del estudiante (-∞ a +∞)
- **a**: Discriminación del ítem (0.5 - 2.0)
- **b**: Dificultad del ítem (-3.0 a +3.0)
- **c**: Adivinanza (0.10 - 0.25)

### **Implementación en Código**
```python
def get_irt_probability(self, theta: float) -> float:
    """Calculate probability using 3PL model"""
    try:
        a = max(0.1, min(10.0, self.parametro_irt_a))
        b = max(-5.0, min(5.0, self.parametro_irt_b))
        c = max(0.0, min(1.0, self.parametro_irt_c))

        exponent = -a * (theta - b)
        exponent = max(-50, min(50, exponent))
        exp_val = math.exp(exponent)
        probability = c + (1 - c) / (1 + exp_val)

        return max(0.001, min(0.999, probability))
    except:
        return 0.5
```

### **Información Fisher**
```python
def get_irt_information(self, theta: float) -> float:
    """Calculate Fisher information for adaptive selection"""
    p = self.get_irt_probability(theta)
    q = 1 - p
    a = max(0.1, min(10.0, self.parametro_irt_a))
    c = max(0.0, min(1.0, self.parametro_irt_c))

    if p <= c + 1e-10 or q <= 1e-10:
        return 1e-10

    try:
        numerator = a**2 * (p - c)**2 * q
        denominator = p * (1 - c)**2
        return numerator / denominator
    except:
        return 1e-10
```

### **Estimación Maximum Likelihood de Theta**
```python
def estimate_theta_ml(responses, questions):
    """Maximum Likelihood Estimation of student ability"""
    def log_likelihood(theta):
        ll = 0
        for response, question in zip(responses, questions):
            p = question.get_irt_probability(theta)
            if response:
                ll += math.log(p)
            else:
                ll += math.log(1 - p)
        return -ll  # Negative for minimization

    # Buscar theta óptimo
    from scipy.optimize import minimize_scalar
    result = minimize_scalar(log_likelihood, bounds=(-5, 5), method='bounded')
    return result.x
```

---

## 🤖 **2. ALGORITMO DE EMBEDDINGS VECTORIALES**

### **Generación de Embeddings**
```python
class EmbeddingService:
    def __init__(self):
        self.model_name = "text-embedding-3-large"
        self.vector_dimensions = 3072

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        response = await openai.Embedding.acreate(
            model=self.model_name,
            input=text
        )
        return response['data'][0]['embedding']
```

### **Similitud Coseno**
```python
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    import numpy as np

    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
```

### **Búsqueda Vectorial Optimizada**
```sql
-- PostgreSQL con extensión vector
SELECT
    content_id,
    content_type,
    1 - (embedding_vector <=> %s::vector) AS similarity
FROM content_embeddings
WHERE content_type = 'video'
ORDER BY embedding_vector <=> %s::vector
LIMIT 10;
```

---

## 📊 **3. ALGORITMO DE SCORING MULTIDIMENSIONAL**

### **Weights Optimizados**
```python
SCORING_WEIGHTS = {
    'exact_match': 0.35,           # Coincidencia exacta en título/descripción
    'semantic_keywords': 0.25,      # Palabras clave semánticamente relacionadas
    'subject_topic_match': 0.20,   # Coincidencia por subject/topic
    'quality_score': 0.15,         # Calidad del video
    'popularity': 0.05             # Popularidad/engagement
}
```

### **Función de Scoring**
```python
def calculate_recommendation_score(question, video, embeddings_similarity):
    """Calculate multidimensional recommendation score"""

    # 1. Exact Match Score
    exact_match = 0.0
    if any(keyword in video.title.lower() for keyword in extract_keywords(question.text)):
        exact_match = 1.0

    # 2. Semantic Similarity (from embeddings)
    semantic_score = embeddings_similarity

    # 3. Subject/Topic Match
    topic_match = 1.0 if question.subject_id == video.subject_id else 0.0

    # 4. Quality Score
    quality = video.quality_score or 0.8

    # 5. Popularity Score
    popularity = min(1.0, video.view_count / 10000) if video.view_count else 0.5

    # Weighted combination
    final_score = (
        SCORING_WEIGHTS['exact_match'] * exact_match +
        SCORING_WEIGHTS['semantic_keywords'] * semantic_score +
        SCORING_WEIGHTS['subject_topic_match'] * topic_match +
        SCORING_WEIGHTS['quality_score'] * quality +
        SCORING_WEIGHTS['popularity'] * popularity
    )

    return min(1.0, max(0.0, final_score))
```

---

## 🔍 **4. ALGORITMO DE ANÁLISIS DE DEBILIDADES**

### **Extracción de Keywords NLP**
```python
def extract_weakness_topics(incorrect_questions):
    """Extract weakness topics using NLP keyword analysis"""

    topic_keywords = {
        'Álgebra Básica': ['ecuación', 'variable', 'álgebra', 'despeje', 'factorización'],
        'Geometría': ['triángulo', 'círculo', 'área', 'perímetro', 'volumen'],
        'Estadística': ['promedio', 'media', 'mediana', 'datos', 'gráfico'],
        # ... más temas
    }

    weakness_topics = []

    for question in incorrect_questions:
        question_text = (question.text + " " + (question.explanation or "")).lower()

        for topic, keywords in topic_keywords.items():
            if any(keyword in question_text for keyword in keywords):
                if topic not in weakness_topics:
                    weakness_topics.append(topic)

    return weakness_topics
```

### **Priorización por Theta**
```python
def prioritize_weaknesses_by_theta(weaknesses, current_theta):
    """Prioritize weaknesses based on student's theta level"""

    priority_scores = {}

    for topic in weaknesses:
        # Temas más básicos tienen mayor prioridad para theta bajo
        if current_theta < -1.0:  # Estudiante principiante
            priority_scores[topic] = get_basic_topic_priority(topic)
        elif current_theta > 1.0:  # Estudiante avanzado
            priority_scores[topic] = get_advanced_topic_priority(topic)
        else:  # Estudiante intermedio
            priority_scores[topic] = get_intermediate_topic_priority(topic)

    return sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)
```

---

## 🎬 **5. ALGORITMO DE MATCHING PREGUNTA-VIDEO**

### **Pipeline Completo**
```python
async def intelligent_question_video_matching(question_id, db_session):
    """Complete pipeline for intelligent video matching"""

    # 1. Get question details
    question = db_session.query(Question).filter_by(id=question_id).first()

    # 2. Generate/retrieve embeddings
    question_embedding = await embedding_service.get_or_generate_embedding(
        content_type='question',
        content_id=question_id,
        text=question.text
    )

    # 3. Find semantically similar videos
    similar_videos = await embedding_service.find_similar_videos(
        question_embedding,
        subject_id=question.subject_id,
        min_similarity=0.6
    )

    # 4. Calculate multidimensional scores
    scored_recommendations = []
    for video, semantic_similarity in similar_videos:
        score = calculate_recommendation_score(
            question, video, semantic_similarity
        )

        scored_recommendations.append({
            'video': video,
            'similarity_score': score,
            'semantic_similarity': semantic_similarity,
            'recommendation_reason': generate_explanation(question, video)
        })

    # 5. Sort and return top recommendations
    scored_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_recommendations[:5]
```

---

## 🧮 **6. OPTIMIZACIONES DE PERFORMANCE**

### **Caching Estratégico**
```python
class RecommendationCache:
    def __init__(self):
        self.embedding_cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour
        self.recommendation_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes

    def get_cached_recommendations(self, question_id):
        return self.recommendation_cache.get(f"rec:{question_id}")

    def cache_recommendations(self, question_id, recommendations):
        self.recommendation_cache[f"rec:{question_id}"] = recommendations
```

### **Batch Processing de Embeddings**
```python
async def batch_generate_embeddings(content_items, batch_size=100):
    """Generate embeddings in batches for efficiency"""

    results = []
    for i in range(0, len(content_items), batch_size):
        batch = content_items[i:i + batch_size]
        batch_texts = [item.text for item in batch]

        # Single API call for entire batch
        embeddings = await openai.Embedding.acreate(
            model="text-embedding-3-large",
            input=batch_texts
        )

        for j, embedding_data in enumerate(embeddings['data']):
            results.append({
                'content_id': batch[j].id,
                'embedding': embedding_data['embedding']
            })

    return results
```

---

## 📈 **7. MÉTRICAS Y EVALUACIÓN**

### **Precision@K**
```python
def calculate_precision_at_k(recommended_videos, relevant_videos, k=5):
    """Calculate Precision@K for recommendation quality"""
    top_k_recommendations = recommended_videos[:k]
    relevant_in_top_k = len(set(top_k_recommendations) & set(relevant_videos))
    return relevant_in_top_k / k
```

### **Learning Gain Analysis**
```python
def analyze_learning_gain(student_id, before_theta, after_theta, video_ids):
    """Analyze learning improvement after video recommendations"""

    theta_improvement = after_theta - before_theta

    if theta_improvement > 0.2:
        return "high_improvement"
    elif theta_improvement > 0.1:
        return "moderate_improvement"
    else:
        return "low_improvement"
```

---

## ⚡ **8. ALGORITMOS DE OPTIMIZACIÓN**

### **A/B Testing de Algoritmos**
```python
class AlgorithmABTesting:
    def __init__(self):
        self.algorithms = {
            'semantic_heavy': {'semantic': 0.5, 'keyword': 0.3, 'topic': 0.2},
            'balanced': {'semantic': 0.35, 'keyword': 0.35, 'topic': 0.3},
            'keyword_heavy': {'semantic': 0.2, 'keyword': 0.5, 'topic': 0.3}
        }

    def select_algorithm_for_user(self, user_id):
        """Select algorithm variant for A/B testing"""
        hash_value = hash(f"{user_id}_recommendation_algo") % 100

        if hash_value < 33:
            return 'semantic_heavy'
        elif hash_value < 66:
            return 'balanced'
        else:
            return 'keyword_heavy'
```

### **Gradient Descent para Weight Optimization**
```python
def optimize_scoring_weights(training_data, learning_rate=0.01, epochs=1000):
    """Optimize scoring weights using gradient descent"""

    weights = np.array([0.35, 0.25, 0.20, 0.15, 0.05])  # Initial weights

    for epoch in range(epochs):
        predictions = []
        targets = []

        for sample in training_data:
            score = calculate_weighted_score(sample['features'], weights)
            predictions.append(score)
            targets.append(sample['target'])

        # Calculate gradient
        gradient = calculate_gradient(predictions, targets, training_data)

        # Update weights
        weights -= learning_rate * gradient

        # Ensure weights sum to 1
        weights = weights / np.sum(weights)

    return weights
```

---

*Esta documentación detalla los algoritmos core del sistema de recomendaciones inteligentes de ICFES Leveling.*