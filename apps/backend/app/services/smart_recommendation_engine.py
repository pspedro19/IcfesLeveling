"""
Smart Recommendation Engine
Sistema de recomendación inteligente basado en errores del diagnóstico
Sin necesidad de APIs externas o modelos descargados
"""

from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import math
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class SmartRecommendationEngine:
    """Motor de recomendación inteligente usando TF-IDF y similitud coseno"""
    
    def __init__(self, db: Session):
        self.db = db
        self.topic_keywords = self._build_topic_keywords()
        
    def _build_topic_keywords(self) -> Dict[str, List[str]]:
        """Construye un diccionario de palabras clave por tema"""
        return {
            # Matemáticas
            'algebra': ['algebra', 'ecuacion', 'variable', 'incognita', 'lineal', 'cuadratica', 'polinomio'],
            'factorizacion': ['factor', 'factorizar', 'factorizacion', 'producto', 'binomio', 'trinomio'],
            'geometria': ['geometria', 'triangulo', 'circulo', 'area', 'perimetro', 'angulo', 'figura'],
            'trigonometria': ['seno', 'coseno', 'tangente', 'trigonometria', 'angulo', 'radianes'],
            'calculo': ['derivada', 'integral', 'limite', 'calculo', 'funcion', 'continua'],
            'estadistica': ['media', 'mediana', 'moda', 'desviacion', 'probabilidad', 'estadistica'],
            
            # Ciencias Naturales
            'fisica': ['fisica', 'fuerza', 'velocidad', 'aceleracion', 'energia', 'movimiento', 'newton'],
            'quimica': ['quimica', 'elemento', 'compuesto', 'reaccion', 'atomo', 'molecula', 'enlace'],
            'biologia': ['celula', 'organismo', 'genetica', 'adn', 'evolucion', 'ecosistema', 'vida'],
            'ecologia': ['ambiente', 'ecosistema', 'cadena', 'alimenticia', 'biodiversidad', 'conservacion'],
            
            # Lenguaje
            'gramatica': ['gramatica', 'sujeto', 'predicado', 'verbo', 'adjetivo', 'sustantivo', 'oracion'],
            'ortografia': ['ortografia', 'acento', 'tilde', 'puntuacion', 'mayuscula', 'regla'],
            'comprension': ['comprension', 'lectura', 'texto', 'idea', 'principal', 'inferencia', 'interpretacion'],
            'literatura': ['literatura', 'obra', 'autor', 'genero', 'narrativa', 'poesia', 'cuento'],
            
            # Ciencias Sociales
            'historia': ['historia', 'epoca', 'periodo', 'civilizacion', 'guerra', 'revolucion', 'colonial'],
            'geografia': ['geografia', 'pais', 'continente', 'capital', 'relieve', 'clima', 'poblacion'],
            'economia': ['economia', 'mercado', 'oferta', 'demanda', 'precio', 'inflacion', 'comercio'],
            'politica': ['politica', 'democracia', 'gobierno', 'constitucion', 'derechos', 'ciudadania'],
            
            # Inglés
            'grammar': ['grammar', 'verb', 'tense', 'present', 'past', 'future', 'conditional'],
            'vocabulary': ['vocabulary', 'word', 'meaning', 'synonym', 'antonym', 'phrase'],
            'reading': ['reading', 'comprehension', 'text', 'passage', 'understanding'],
            'writing': ['writing', 'essay', 'paragraph', 'sentence', 'composition']
        }
    
    def tokenize(self, text: str) -> List[str]:
        """Tokeniza y normaliza el texto"""
        if not text:
            return []
        
        # Convertir a minúsculas y remover caracteres especiales
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Tokenizar
        tokens = text.split()
        
        # Remover stopwords básicas
        stopwords = {'el', 'la', 'de', 'en', 'y', 'a', 'que', 'es', 'por', 'un', 'una', 
                    'los', 'las', 'del', 'al', 'con', 'para', 'su', 'se', 'lo', 'como',
                    'the', 'of', 'and', 'to', 'in', 'is', 'that', 'it', 'for', 'on'}
        
        return [token for token in tokens if len(token) > 2 and token not in stopwords]
    
    def calculate_tf_idf(self, doc_tokens: List[str], all_docs: List[List[str]]) -> Dict[str, float]:
        """Calcula TF-IDF para un documento"""
        # Term Frequency
        tf = Counter(doc_tokens)
        max_freq = max(tf.values()) if tf else 1
        tf = {term: freq/max_freq for term, freq in tf.items()}
        
        # Inverse Document Frequency
        idf = {}
        total_docs = len(all_docs)
        
        for term in tf:
            docs_with_term = sum(1 for doc in all_docs if term in doc)
            idf[term] = math.log((total_docs + 1) / (docs_with_term + 1))
        
        # TF-IDF
        return {term: tf[term] * idf[term] for term in tf}
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        if not vec1 or not vec2:
            return 0.0
        
        # Obtener términos comunes
        common_terms = set(vec1.keys()) & set(vec2.keys())
        
        if not common_terms:
            return 0.0
        
        # Calcular producto punto
        dot_product = sum(vec1[term] * vec2[term] for term in common_terms)
        
        # Calcular magnitudes
        mag1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        mag2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def identify_weak_topics(self, incorrect_questions: List[Dict]) -> List[str]:
        """Identifica temas débiles basándose en preguntas incorrectas"""
        weak_topics = []
        
        for question in incorrect_questions:
            question_text = question.get('question_text', '')
            tokens = self.tokenize(question_text)
            
            # Buscar coincidencias con palabras clave de temas
            for topic, keywords in self.topic_keywords.items():
                matches = sum(1 for token in tokens if token in keywords)
                if matches >= 2:  # Al menos 2 palabras clave coinciden
                    weak_topics.append(topic)
        
        # Si no hay temas específicos, usar categorías generales
        if not weak_topics:
            for question in incorrect_questions:
                subject_id = question.get('subject_id', '')
                if 'mat' in str(subject_id).lower():
                    weak_topics.extend(['algebra', 'geometria'])
                elif 'leng' in str(subject_id).lower():
                    weak_topics.extend(['comprension', 'gramatica'])
                elif 'cien' in str(subject_id).lower():
                    weak_topics.extend(['fisica', 'biologia'])
        
        return list(set(weak_topics))  # Eliminar duplicados
    
    def get_personalized_videos(
        self, 
        subject_id: str,
        incorrect_questions: List[Dict],
        max_videos: int = 15
    ) -> List[Dict]:
        """
        Obtiene videos personalizados basados en las preguntas incorrectas
        """
        try:
            logger.info(f"🎯 Generando recomendaciones personalizadas para {len(incorrect_questions)} errores")
            
            # 1. Identificar temas débiles
            weak_topics = self.identify_weak_topics(incorrect_questions)
            logger.info(f"📚 Temas débiles identificados: {weak_topics}")
            
            # 2. Obtener área de la materia
            subject_query = text("""
                SELECT name FROM subjects WHERE id = :subject_id
            """)
            subject_result = self.db.execute(subject_query, {'subject_id': subject_id}).first()
            subject_name = subject_result[0] if subject_result else 'General'
            
            # 3. Preparar texto de búsqueda combinando errores
            search_text = ' '.join([
                q.get('question_text', '') + ' ' + q.get('explanation', '')
                for q in incorrect_questions[:5]  # Usar máximo 5 preguntas
            ])
            search_tokens = self.tokenize(search_text)
            
            # 4. Obtener videos candidatos de la base de datos
            videos_query = text("""
                SELECT 
                    youtube_id,
                    video_title,
                    youtube_url,
                    tema_principal,
                    duration_seconds,
                    puntos_xp,
                    canal_sugerido,
                    nivel_dificultad,
                    relevancia_score
                FROM youtube_links
                WHERE area_evaluada LIKE :area
                AND estado = 'activo'
                ORDER BY relevancia_score DESC, orden_recomendacion
                LIMIT 50
            """)
            
            videos = self.db.execute(videos_query, {
                'area': f'%{subject_name}%'
            }).fetchall()
            
            # 5. Calcular relevancia para cada video
            video_scores = []
            all_video_tokens = []
            
            for video in videos:
                video_text = f"{video[1]} {video[3]}"  # title + tema_principal
                video_tokens = self.tokenize(video_text)
                all_video_tokens.append(video_tokens)
            
            # Calcular TF-IDF para búsqueda
            search_tfidf = self.calculate_tf_idf(search_tokens, all_video_tokens)
            
            for idx, video in enumerate(videos):
                video_tokens = all_video_tokens[idx]
                video_tfidf = self.calculate_tf_idf(video_tokens, all_video_tokens)
                
                # Calcular similitud
                similarity = self.cosine_similarity(search_tfidf, video_tfidf)
                
                # Bonus por coincidencia con temas débiles
                tema_principal = video[3].lower() if video[3] else ''
                topic_bonus = 0
                for weak_topic in weak_topics:
                    if weak_topic in tema_principal:
                        topic_bonus += 0.3
                
                # Bonus por nivel de dificultad apropiado
                difficulty = video[7] if video[7] else 5
                difficulty_bonus = 0.1 if 3 <= difficulty <= 7 else 0
                
                # Score final
                final_score = similarity + topic_bonus + difficulty_bonus
                
                video_scores.append({
                    'video': video,
                    'score': final_score,
                    'similarity': similarity,
                    'topic_match': topic_bonus > 0
                })
            
            # 6. Ordenar por score y seleccionar los mejores
            video_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # 7. Formatear resultados
            recommended_videos = []
            for item in video_scores[:max_videos]:
                video = item['video']
                recommended_videos.append({
                    'id': video[0],
                    'title': video[1],
                    'url': video[2],
                    'topic': video[3],
                    'duration': video[4],
                    'xp': video[5],
                    'channel': video[6],
                    'difficulty': video[7],
                    'relevance_score': round(item['score'] * 100, 2),
                    'is_priority': item['topic_match']
                })
            
            logger.info(f"✅ {len(recommended_videos)} videos recomendados")
            
            # Si no hay suficientes videos relevantes, agregar algunos generales
            if len(recommended_videos) < 5:
                general_query = text("""
                    SELECT 
                        youtube_id, video_title, youtube_url, tema_principal,
                        duration_seconds, puntos_xp, canal_sugerido, nivel_dificultad
                    FROM youtube_links
                    WHERE estado = 'activo'
                    AND nivel_dificultad <= 5
                    ORDER BY RANDOM()
                    LIMIT :limit
                """)
                
                additional = self.db.execute(general_query, {
                    'limit': 5 - len(recommended_videos)
                }).fetchall()
                
                for video in additional:
                    recommended_videos.append({
                        'id': video[0],
                        'title': video[1],
                        'url': video[2],
                        'topic': video[3],
                        'duration': video[4],
                        'xp': video[5],
                        'channel': video[6],
                        'difficulty': video[7],
                        'relevance_score': 50.0,
                        'is_priority': False
                    })
            
            return recommended_videos
            
        except Exception as e:
            logger.error(f"❌ Error en recomendación: {e}")
            return self._get_fallback_videos(subject_name, max_videos)
    
    def _get_fallback_videos(self, subject_name: str, limit: int) -> List[Dict]:
        """Videos de respaldo si falla el sistema principal"""
        try:
            query = text("""
                SELECT 
                    youtube_id, video_title, youtube_url, tema_principal,
                    duration_seconds, puntos_xp, canal_sugerido, nivel_dificultad
                FROM youtube_links
                WHERE area_evaluada LIKE :area
                AND estado = 'activo'
                ORDER BY relevancia_score DESC, orden_recomendacion
                LIMIT :limit
            """)
            
            videos = self.db.execute(query, {
                'area': f'%{subject_name}%',
                'limit': limit
            }).fetchall()
            
            return [{
                'id': v[0],
                'title': v[1],
                'url': v[2],
                'topic': v[3],
                'duration': v[4],
                'xp': v[5],
                'channel': v[6],
                'difficulty': v[7],
                'relevance_score': 75.0,
                'is_priority': False
            } for v in videos]
            
        except Exception:
            return []