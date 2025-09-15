#!/usr/bin/env python3
"""
Advanced Semantic Similarity Engine for ICFES Video Matching
============================================================

A comprehensive semantic similarity engine that uses state-of-the-art
embedding models and advanced similarity algorithms to match failed
questions with relevant YouTube educational videos.

Features:
- Multi-model embedding support (OpenAI, Sentence Transformers, Custom)
- Advanced similarity metrics (Cosine, Euclidean, Jaccard, Custom weighted)
- Contextual understanding with ICFES-specific domain knowledge
- Caching and performance optimization
- Batch processing capabilities
- Real-time similarity scoring

Author: Claude Code Assistant (Video Matching Specialist)
Date: 2025-09-11
"""

import asyncio
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import openai
from sentence_transformers import SentenceTransformer
import torch
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.feature_extraction.text import TfidfVectorizer
import hashlib
import json
import time
from datetime import datetime, timedelta
import redis
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingModel(Enum):
    """Supported embedding models"""
    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_LARGE = "text-embedding-3-large"
    OPENAI_3_SMALL = "text-embedding-3-small"
    SENTENCE_BERT = "all-MiniLM-L6-v2"
    SENTENCE_BERT_MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"
    SENTENCE_BERT_LARGE = "all-mpnet-base-v2"
    CUSTOM_ICFES = "icfes-domain-specific"

class SimilarityMetric(Enum):
    """Supported similarity metrics"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"
    JACCARD = "jaccard"
    WEIGHTED_HYBRID = "weighted_hybrid"
    ICFES_SPECIALIZED = "icfes_specialized"

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model: EmbeddingModel
    dimensions: int
    max_tokens: int = 8000
    batch_size: int = 32
    cache_ttl: int = 86400  # 24 hours
    use_preprocessing: bool = True
    normalize_vectors: bool = True
    
@dataclass
class SimilarityConfig:
    """Configuration for similarity computation"""
    primary_metric: SimilarityMetric
    secondary_metrics: List[SimilarityMetric] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    threshold: float = 0.7
    top_k: int = 10
    use_reranking: bool = True

@dataclass
class ContentItem:
    """Represents a content item for similarity matching"""
    id: Union[int, str]
    title: str
    description: str
    content_type: str  # 'question', 'video', 'explanation'
    subject_area: str
    topic: str
    competency: str
    difficulty_level: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None
    
    def get_combined_text(self) -> str:
        """Get combined text for embedding generation"""
        components = []
        
        if self.title:
            components.append(f"Título: {self.title}")
        if self.description:
            components.append(f"Descripción: {self.description}")
        if self.raw_text:
            components.append(f"Contenido: {self.raw_text}")
        if self.subject_area:
            components.append(f"Área: {self.subject_area}")
        if self.topic:
            components.append(f"Tema: {self.topic}")
        if self.competency:
            components.append(f"Competencia: {self.competency}")
        if self.difficulty_level:
            components.append(f"Dificultad: {self.difficulty_level}")
            
        return " | ".join(components)

@dataclass 
class SimilarityResult:
    """Result of similarity computation"""
    content_id: Union[int, str]
    similarity_score: float
    primary_score: float
    secondary_scores: Dict[str, float]
    metadata: Dict[str, Any]
    explanation: str
    confidence: float
    processing_time_ms: float

class TextPreprocessor:
    """Advanced text preprocessing for ICFES content"""
    
    def __init__(self):
        self.icfes_terms = self._load_icfes_vocabulary()
        self.stopwords = self._load_spanish_stopwords()
        
    def _load_icfes_vocabulary(self) -> Dict[str, str]:
        """Load ICFES-specific vocabulary and synonyms"""
        return {
            # Mathematics
            "algebra": "álgebra matemática ecuaciones",
            "geometria": "geometría figuras espaciales",
            "trigonometria": "trigonometría seno coseno tangente",
            "calculo": "cálculo derivadas integrales límites",
            
            # Physics  
            "mecanica": "mecánica física fuerzas movimiento",
            "termodinamica": "termodinámica calor temperatura",
            "electromagnetismo": "electromagnetismo campos eléctricos magnéticos",
            "optica": "óptica luz ondas refracción",
            
            # Chemistry
            "estequiometria": "estequiometría reacciones químicas moles",
            "quimica_organica": "química orgánica compuestos carbono",
            "tabla_periodica": "tabla periódica elementos químicos",
            
            # Biology
            "genetica": "genética herencia ADN cromosomas",
            "ecologia": "ecología ecosistemas medio ambiente",
            "anatomia": "anatomía cuerpo humano sistemas",
            
            # Language
            "comprension_lectora": "comprensión lectora textos interpretación",
            "gramatica": "gramática sintaxis morfología",
            "literatura": "literatura obras autores análisis",
            
            # Social Sciences
            "historia": "historia eventos cronología",
            "geografia": "geografía mapas ubicación espacial",
            "civica": "cívica constitución derechos deberes"
        }
    
    def _load_spanish_stopwords(self) -> set:
        """Load Spanish stopwords"""
        return {
            'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con',
            'contra', 'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante',
            'e', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'erais',
            'eran', 'eras', 'es', 'esa', 'esas', 'ese', 'eso', 'esos', 'esta',
            'estaba', 'estabais', 'estaban', 'estabas', 'estad', 'estada', 'estadas',
            'estado', 'estados', 'estamos', 'estando', 'estar', 'estaremos', 'estará',
            'estarán', 'estarás', 'estaré', 'estaréis', 'estaría', 'estaríais',
            'estaríamos', 'estarían', 'estarías', 'estas', 'este', 'estemos',
            'esto', 'estos', 'estoy', 'estuve', 'estuviera', 'estuvierais',
            'estuvieran', 'estuvieras', 'estuvieron', 'estuviese', 'estuvieseis',
            'estuviesen', 'estuvieses', 'estuvimos', 'estuviste', 'estuvisteis',
            'estuvo', 'está', 'estábamos', 'estáis', 'están', 'estás', 'esté',
            'estéis', 'estén', 'estés', 'fue', 'fuera', 'fuerais', 'fueran',
            'fueras', 'fueron', 'fuese', 'fueseis', 'fuesen', 'fueses', 'fui',
            'fuimos', 'fuiste', 'fuisteis', 'ha', 'habida', 'habidas', 'habido',
            'habidos', 'habiendo', 'habremos', 'habrá', 'habrán', 'habrás',
            'habré', 'habréis', 'habría', 'habríais', 'habríamos', 'habrían',
            'habrías', 'habéis', 'había', 'habíais', 'habíamos', 'habían',
            'habías', 'han', 'has', 'hasta', 'hay', 'haya', 'hayamos', 'hayan',
            'hayas', 'hayáis', 'he', 'hemos', 'hube', 'hubiera', 'hubierais',
            'hubieran', 'hubieras', 'hubieron', 'hubiese', 'hubieseis', 'hubiesen',
            'hubieses', 'hubimos', 'hubiste', 'hubisteis', 'hubo', 'la', 'las',
            'le', 'les', 'lo', 'los', 'me', 'mi', 'mis', 'mucho', 'muchos',
            'muy', 'más', 'mí', 'mía', 'mías', 'mío', 'míos', 'nada', 'ni',
            'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestras', 'nuestro',
            'nuestros', 'o', 'os', 'otra', 'otras', 'otro', 'otros', 'para',
            'pero', 'poco', 'por', 'porque', 'que', 'quien', 'quienes', 'qué',
            'se', 'sea', 'seamos', 'sean', 'seas', 'seáis', 'ser', 'seremos',
            'será', 'serán', 'serás', 'seré', 'seréis', 'sería', 'seríais',
            'seríamos', 'serían', 'serías', 'si', 'sido', 'siendo', 'sin', 'sobre',
            'sois', 'somos', 'son', 'soy', 'su', 'sus', 'suya', 'suyas', 'suyo',
            'suyos', 'sí', 'también', 'tanto', 'te', 'tendremos', 'tendrá',
            'tendrán', 'tendrás', 'tendré', 'tendréis', 'tendría', 'tendríais',
            'tendríamos', 'tendrían', 'tendrías', 'tened', 'tenemos', 'tenga',
            'tengamos', 'tengan', 'tengas', 'tengáis', 'tengo', 'tenida', 'tenidas',
            'tenido', 'tenidos', 'teniendo', 'tenéis', 'tenía', 'teníais',
            'teníamos', 'tenían', 'tenías', 'ti', 'tiene', 'tienen', 'tienes',
            'todo', 'todos', 'tu', 'tus', 'tuve', 'tuviera', 'tuvierais',
            'tuvieran', 'tuvieras', 'tuvieron', 'tuviese', 'tuvieseis', 'tuviesen',
            'tuvieses', 'tuvimos', 'tuviste', 'tuvisteis', 'tuvo', 'tuya', 'tuyas',
            'tuyo', 'tuyos', 'tú', 'un', 'una', 'uno', 'unos', 'vosotras',
            'vosotros', 'vuestra', 'vuestras', 'vuestro', 'vuestros', 'y', 'ya',
            'yo', 'él', 'éramos'
        }
    
    def preprocess_text(self, text: str) -> str:
        """Advanced preprocessing tailored for ICFES content"""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep Spanish accents and ñ
        import re
        text = re.sub(r'[^\w\sáéíóúñü]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Expand ICFES-specific terms
        for term, expansion in self.icfes_terms.items():
            text = text.replace(term, f"{term} {expansion}")
        
        # Remove stopwords while preserving important context
        words = text.split()
        filtered_words = []
        
        for i, word in enumerate(words):
            if word not in self.stopwords or len(word) > 6:
                filtered_words.append(word)
        
        return ' '.join(filtered_words).strip()

class EmbeddingCache:
    """Redis-based caching system for embeddings"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.cache_available = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            self.cache_available = False
            self.memory_cache = {}
    
    def _generate_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model combination"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{model}:{text_hash}"
    
    def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Retrieve embedding from cache"""
        if not self.cache_available:
            return self.memory_cache.get(self._generate_cache_key(text, model))
            
        try:
            key = self._generate_cache_key(text, model)
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
        
        return None
    
    def set_embedding(self, text: str, model: str, embedding: List[float], ttl: int = 86400):
        """Store embedding in cache"""
        key = self._generate_cache_key(text, model)
        
        if not self.cache_available:
            self.memory_cache[key] = embedding
            return
            
        try:
            self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(embedding)
            )
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

class AdvancedSemanticSimilarityEngine:
    """
    Advanced semantic similarity engine for ICFES video matching
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
        similarity_config: Optional[SimilarityConfig] = None,
        enable_caching: bool = True
    ):
        # Initialize OpenAI client
        self.openai_client = None
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Set default configurations
        self.embedding_config = embedding_config or EmbeddingConfig(
            model=EmbeddingModel.OPENAI_3_LARGE,
            dimensions=3072
        )
        
        self.similarity_config = similarity_config or SimilarityConfig(
            primary_metric=SimilarityMetric.COSINE,
            secondary_metrics=[SimilarityMetric.DOT_PRODUCT],
            weights={'semantic': 0.6, 'topic': 0.3, 'difficulty': 0.1}
        )
        
        # Initialize components
        self.preprocessor = TextPreprocessor()
        self.cache = EmbeddingCache() if enable_caching else None
        
        # Load sentence transformers if needed
        self.sentence_models = {}
        self._load_sentence_transformers()
        
        # Initialize TF-IDF for fallback similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words=list(self.preprocessor.stopwords)
        )
        
        logger.info("AdvancedSemanticSimilarityEngine initialized successfully")
    
    def _load_sentence_transformers(self):
        """Load sentence transformer models"""
        sentence_models = [
            EmbeddingModel.SENTENCE_BERT,
            EmbeddingModel.SENTENCE_BERT_MULTILINGUAL,
            EmbeddingModel.SENTENCE_BERT_LARGE
        ]
        
        for model_enum in sentence_models:
            try:
                model = SentenceTransformer(model_enum.value)
                self.sentence_models[model_enum] = model
                logger.info(f"Loaded sentence transformer: {model_enum.value}")
            except Exception as e:
                logger.warning(f"Could not load {model_enum.value}: {e}")
    
    async def generate_embedding(
        self, 
        text: str, 
        model: EmbeddingModel = None
    ) -> List[float]:
        """Generate embedding for given text"""
        
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return [0.0] * self.embedding_config.dimensions
        
        model = model or self.embedding_config.model
        
        # Preprocess text if enabled
        if self.embedding_config.use_preprocessing:
            processed_text = self.preprocessor.preprocess_text(text)
        else:
            processed_text = text
        
        # Check cache first
        if self.cache:
            cached_embedding = self.cache.get_embedding(processed_text, model.value)
            if cached_embedding:
                logger.debug(f"Retrieved embedding from cache for model {model.value}")
                return cached_embedding
        
        # Generate new embedding
        try:
            embedding = await self._generate_embedding_by_model(processed_text, model)
            
            # Normalize if configured
            if self.embedding_config.normalize_vectors:
                embedding = self._normalize_vector(embedding)
            
            # Cache the result
            if self.cache:
                self.cache.set_embedding(
                    processed_text, 
                    model.value, 
                    embedding,
                    self.embedding_config.cache_ttl
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_config.dimensions
    
    async def _generate_embedding_by_model(
        self, 
        text: str, 
        model: EmbeddingModel
    ) -> List[float]:
        """Generate embedding using specific model"""
        
        if model in [EmbeddingModel.OPENAI_ADA_002, EmbeddingModel.OPENAI_3_LARGE, EmbeddingModel.OPENAI_3_SMALL]:
            return await self._generate_openai_embedding(text, model)
        
        elif model in self.sentence_models:
            return self._generate_sentence_transformer_embedding(text, model)
        
        else:
            raise ValueError(f"Unsupported embedding model: {model}")
    
    async def _generate_openai_embedding(
        self, 
        text: str, 
        model: EmbeddingModel
    ) -> List[float]:
        """Generate embedding using OpenAI API"""
        
        if not self.openai_client:
            logger.warning("OpenAI client not available, using fallback")
            return [0.0] * self.embedding_config.dimensions
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=model.value,
                input=text[:self.embedding_config.max_tokens]
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    def _generate_sentence_transformer_embedding(
        self, 
        text: str, 
        model: EmbeddingModel
    ) -> List[float]:
        """Generate embedding using Sentence Transformer"""
        
        if model not in self.sentence_models:
            raise ValueError(f"Sentence transformer model not loaded: {model}")
        
        try:
            model_instance = self.sentence_models[model]
            embedding = model_instance.encode([text])[0]
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Sentence transformer error: {e}")
            raise
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length"""
        np_vector = np.array(vector)
        norm = np.linalg.norm(np_vector)
        if norm == 0:
            return vector
        return (np_vector / norm).tolist()
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float],
        metric: SimilarityMetric = None
    ) -> float:
        """Compute similarity between two embeddings"""
        
        metric = metric or self.similarity_config.primary_metric
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        
        try:
            if metric == SimilarityMetric.COSINE:
                return cosine_similarity(vec1, vec2)[0][0]
            
            elif metric == SimilarityMetric.EUCLIDEAN:
                distance = euclidean_distances(vec1, vec2)[0][0]
                # Convert distance to similarity (0-1 scale)
                return 1.0 / (1.0 + distance)
            
            elif metric == SimilarityMetric.DOT_PRODUCT:
                return np.dot(vec1[0], vec2[0])
            
            elif metric == SimilarityMetric.MANHATTAN:
                distance = np.sum(np.abs(vec1[0] - vec2[0]))
                return 1.0 / (1.0 + distance)
            
            elif metric == SimilarityMetric.WEIGHTED_HYBRID:
                # Combine multiple metrics
                cosine_sim = cosine_similarity(vec1, vec2)[0][0]
                dot_product = np.dot(vec1[0], vec2[0])
                
                # Weighted combination
                return 0.7 * cosine_sim + 0.3 * min(dot_product, 1.0)
            
            elif metric == SimilarityMetric.ICFES_SPECIALIZED:
                return self._compute_icfes_specialized_similarity(vec1[0], vec2[0])
            
            else:
                logger.warning(f"Unknown similarity metric: {metric}, using cosine")
                return cosine_similarity(vec1, vec2)[0][0]
                
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def _compute_icfes_specialized_similarity(
        self, 
        vec1: np.ndarray, 
        vec2: np.ndarray
    ) -> float:
        """ICFES-specialized similarity computation"""
        
        # Weighted combination of multiple metrics with ICFES-specific adjustments
        cosine_sim = cosine_similarity(vec1.reshape(1, -1), vec2.reshape(1, -1))[0][0]
        
        # Compute element-wise similarity for topic alignment
        element_similarity = 1.0 - np.mean(np.abs(vec1 - vec2))
        
        # Combine with domain-specific weights
        specialized_score = (
            0.6 * cosine_sim +
            0.3 * element_similarity +
            0.1 * min(np.dot(vec1, vec2), 1.0)
        )
        
        return max(0.0, min(1.0, specialized_score))
    
    async def find_most_similar_content(
        self,
        query_item: ContentItem,
        candidate_items: List[ContentItem],
        top_k: Optional[int] = None
    ) -> List[SimilarityResult]:
        """Find most similar content items to the query"""
        
        top_k = top_k or self.similarity_config.top_k
        start_time = time.time()
        
        # Generate embedding for query
        query_text = query_item.get_combined_text()
        query_embedding = await self.generate_embedding(query_text)
        
        results = []
        
        # Batch process candidate items
        batch_size = self.embedding_config.batch_size
        
        for i in range(0, len(candidate_items), batch_size):
            batch = candidate_items[i:i + batch_size]
            batch_results = await self._process_candidate_batch(
                query_item, query_embedding, batch
            )
            results.extend(batch_results)
        
        # Sort by primary similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Apply reranking if enabled
        if self.similarity_config.use_reranking and len(results) > top_k:
            results = self._rerank_results(query_item, results[:top_k * 2])
        
        processing_time = (time.time() - start_time) * 1000
        
        # Return top results with processing time
        final_results = results[:top_k]
        for result in final_results:
            result.processing_time_ms = processing_time / len(final_results)
        
        logger.info(f"Processed {len(candidate_items)} candidates in {processing_time:.2f}ms")
        return final_results
    
    async def _process_candidate_batch(
        self,
        query_item: ContentItem,
        query_embedding: List[float],
        candidates: List[ContentItem]
    ) -> List[SimilarityResult]:
        """Process a batch of candidate items"""
        
        batch_results = []
        
        # Generate embeddings for all candidates in parallel
        candidate_texts = [item.get_combined_text() for item in candidates]
        candidate_embeddings = await asyncio.gather(*[
            self.generate_embedding(text) for text in candidate_texts
        ])
        
        # Compute similarities
        for candidate, embedding in zip(candidates, candidate_embeddings):
            try:
                # Primary similarity
                primary_score = self.compute_similarity(
                    query_embedding, 
                    embedding,
                    self.similarity_config.primary_metric
                )
                
                # Secondary similarities
                secondary_scores = {}
                for metric in self.similarity_config.secondary_metrics:
                    secondary_scores[metric.value] = self.compute_similarity(
                        query_embedding, embedding, metric
                    )
                
                # Compute weighted final score
                final_score = self._compute_weighted_score(
                    primary_score, secondary_scores, query_item, candidate
                )
                
                # Generate explanation
                explanation = self._generate_similarity_explanation(
                    query_item, candidate, primary_score, secondary_scores
                )
                
                # Compute confidence
                confidence = self._compute_confidence_score(
                    primary_score, secondary_scores, query_item, candidate
                )
                
                result = SimilarityResult(
                    content_id=candidate.id,
                    similarity_score=final_score,
                    primary_score=primary_score,
                    secondary_scores=secondary_scores,
                    metadata={
                        'candidate_title': candidate.title,
                        'subject_match': query_item.subject_area == candidate.subject_area,
                        'topic_match': query_item.topic == candidate.topic,
                        'competency_match': query_item.competency == candidate.competency
                    },
                    explanation=explanation,
                    confidence=confidence,
                    processing_time_ms=0.0  # Will be set later
                )
                
                batch_results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing candidate {candidate.id}: {e}")
                continue
        
        return batch_results
    
    def _compute_weighted_score(
        self,
        primary_score: float,
        secondary_scores: Dict[str, float],
        query_item: ContentItem,
        candidate_item: ContentItem
    ) -> float:
        """Compute weighted similarity score"""
        
        # Start with primary semantic similarity
        weighted_score = primary_score * self.similarity_config.weights.get('semantic', 0.6)
        
        # Add topic-based bonus
        topic_bonus = 0.0
        if query_item.subject_area == candidate_item.subject_area:
            topic_bonus += 0.1
        if query_item.topic == candidate_item.topic:
            topic_bonus += 0.1
        if query_item.competency == candidate_item.competency:
            topic_bonus += 0.1
        
        weighted_score += topic_bonus * self.similarity_config.weights.get('topic', 0.3)
        
        # Add difficulty matching bonus
        difficulty_bonus = 0.0
        if (query_item.difficulty_level and candidate_item.difficulty_level and 
            query_item.difficulty_level == candidate_item.difficulty_level):
            difficulty_bonus = 0.1
        
        weighted_score += difficulty_bonus * self.similarity_config.weights.get('difficulty', 0.1)
        
        # Incorporate secondary scores
        for metric, score in secondary_scores.items():
            weight = self.similarity_config.weights.get(metric, 0.05)
            weighted_score += score * weight
        
        return min(1.0, max(0.0, weighted_score))
    
    def _generate_similarity_explanation(
        self,
        query_item: ContentItem,
        candidate_item: ContentItem,
        primary_score: float,
        secondary_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable explanation for similarity score"""
        
        explanations = []
        
        # Primary similarity explanation
        if primary_score > 0.8:
            explanations.append("Alto nivel de similitud semántica")
        elif primary_score > 0.6:
            explanations.append("Similitud semántica moderada")
        else:
            explanations.append("Similitud semántica baja")
        
        # Topic matching explanations
        if query_item.subject_area == candidate_item.subject_area:
            explanations.append("Misma área temática")
        
        if query_item.topic == candidate_item.topic:
            explanations.append("Mismo tema específico")
        
        if query_item.competency == candidate_item.competency:
            explanations.append("Misma competencia ICFES")
        
        # Secondary score explanations
        for metric, score in secondary_scores.items():
            if score > 0.7:
                explanations.append(f"Alta {metric} ({score:.2f})")
        
        return " | ".join(explanations) if explanations else "Similitud calculada"
    
    def _compute_confidence_score(
        self,
        primary_score: float,
        secondary_scores: Dict[str, float],
        query_item: ContentItem,
        candidate_item: ContentItem
    ) -> float:
        """Compute confidence score for the similarity result"""
        
        # Base confidence from primary score
        confidence = primary_score
        
        # Boost confidence if multiple metrics agree
        if secondary_scores:
            avg_secondary = np.mean(list(secondary_scores.values()))
            if abs(primary_score - avg_secondary) < 0.2:  # Agreement threshold
                confidence += 0.1
        
        # Boost confidence for exact topic matches
        if query_item.subject_area == candidate_item.subject_area:
            confidence += 0.05
        if query_item.topic == candidate_item.topic:
            confidence += 0.1
        
        # Reduce confidence for very different content types
        if query_item.content_type != candidate_item.content_type:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _rerank_results(
        self,
        query_item: ContentItem,
        results: List[SimilarityResult]
    ) -> List[SimilarityResult]:
        """Apply additional reranking logic"""
        
        # Simple reranking: prioritize results with high confidence
        # and exact topic matches
        
        for result in results:
            rerank_boost = 0.0
            
            # Boost for high confidence
            if result.confidence > 0.8:
                rerank_boost += 0.05
            
            # Boost for exact matches
            if result.metadata.get('subject_match'):
                rerank_boost += 0.03
            if result.metadata.get('topic_match'):
                rerank_boost += 0.05
            if result.metadata.get('competency_match'):
                rerank_boost += 0.02
            
            # Apply boost
            result.similarity_score = min(1.0, result.similarity_score + rerank_boost)
        
        # Re-sort after reranking
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics and performance metrics"""
        
        stats = {
            'embedding_config': {
                'model': self.embedding_config.model.value,
                'dimensions': self.embedding_config.dimensions,
                'cache_enabled': self.cache is not None
            },
            'similarity_config': {
                'primary_metric': self.similarity_config.primary_metric.value,
                'secondary_metrics': [m.value for m in self.similarity_config.secondary_metrics],
                'threshold': self.similarity_config.threshold,
                'top_k': self.similarity_config.top_k
            },
            'loaded_models': {
                'openai_available': self.openai_client is not None,
                'sentence_transformers': list(self.sentence_models.keys())
            }
        }
        
        if self.cache and self.cache.cache_available:
            try:
                cache_info = self.cache.redis_client.info()
                stats['cache_stats'] = {
                    'connected_clients': cache_info.get('connected_clients'),
                    'used_memory_human': cache_info.get('used_memory_human'),
                    'keyspace_hits': cache_info.get('keyspace_hits', 0),
                    'keyspace_misses': cache_info.get('keyspace_misses', 0)
                }
            except Exception as e:
                stats['cache_stats'] = {'error': str(e)}
        
        return stats

# Factory function for easy initialization
def create_similarity_engine(
    openai_api_key: Optional[str] = None,
    model: EmbeddingModel = EmbeddingModel.OPENAI_3_LARGE,
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE,
    enable_caching: bool = True
) -> AdvancedSemanticSimilarityEngine:
    """Factory function to create a configured similarity engine"""
    
    embedding_config = EmbeddingConfig(
        model=model,
        dimensions=3072 if model == EmbeddingModel.OPENAI_3_LARGE else 1536,
        use_preprocessing=True,
        normalize_vectors=True
    )
    
    similarity_config = SimilarityConfig(
        primary_metric=similarity_metric,
        secondary_metrics=[SimilarityMetric.DOT_PRODUCT],
        weights={'semantic': 0.6, 'topic': 0.3, 'difficulty': 0.1},
        threshold=0.7,
        top_k=10
    )
    
    return AdvancedSemanticSimilarityEngine(
        openai_api_key=openai_api_key,
        embedding_config=embedding_config,
        similarity_config=similarity_config,
        enable_caching=enable_caching
    )

if __name__ == "__main__":
    # Example usage and testing
    async def test_similarity_engine():
        """Test the similarity engine with sample data"""
        
        # Initialize engine
        engine = create_similarity_engine()
        
        # Create sample content items
        failed_question = ContentItem(
            id=1,
            title="Pregunta sobre álgebra lineal",
            description="Resolver sistema de ecuaciones lineales con 3 variables",
            content_type="question",
            subject_area="Matemáticas",
            topic="Álgebra",
            competency="Razonamiento y argumentación",
            difficulty_level="intermedio"
        )
        
        video_candidates = [
            ContentItem(
                id=101,
                title="Sistemas de ecuaciones lineales - Método de eliminación",
                description="Aprende a resolver sistemas de ecuaciones con el método de eliminación gaussiana",
                content_type="video",
                subject_area="Matemáticas",
                topic="Álgebra",
                competency="Razonamiento y argumentación",
                difficulty_level="intermedio"
            ),
            ContentItem(
                id=102,
                title="Introducción a la química orgánica",
                description="Conceptos básicos de química orgánica y compuestos del carbono",
                content_type="video",
                subject_area="Química",
                topic="Química orgánica",
                competency="Uso comprensivo del conocimiento científico",
                difficulty_level="básico"
            )
        ]
        
        # Find similar content
        results = await engine.find_most_similar_content(
            failed_question, 
            video_candidates,
            top_k=5
        )
        
        # Print results
        print("Similarity Results:")
        print("=" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Content ID: {result.content_id}")
            print(f"   Similarity Score: {result.similarity_score:.3f}")
            print(f"   Primary Score: {result.primary_score:.3f}")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Explanation: {result.explanation}")
            print(f"   Processing Time: {result.processing_time_ms:.2f}ms")
            print("-" * 30)
        
        # Print engine stats
        stats = engine.get_engine_stats()
        print("\nEngine Statistics:")
        print(json.dumps(stats, indent=2, default=str))
    
    # Run the test
    asyncio.run(test_similarity_engine())