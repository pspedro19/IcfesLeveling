"""
Video Content Analysis Service
Advanced content analysis for better video-question matching and categorization
"""

import logging
import re
import asyncio
from typing import List, Dict, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, func
from datetime import datetime
import json
import math
from dataclasses import dataclass
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import SnowballStemmer

from ..models.youtube_catalog import YoutubeCatalog
from ..models.question import Question
from ..models.subject import Subject
from ..models.topic import Topic

logger = logging.getLogger(__name__)

# Initialize NLTK components (in production, ensure these are downloaded)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    pass  # In production, handle NLTK data download properly

@dataclass
class ContentFeatures:
    """Content features extracted from text"""
    keywords: List[str]
    concepts: List[str]
    difficulty_indicators: List[str]
    content_type: str
    cognitive_level: str
    educational_objectives: List[str]
    topic_coverage: Dict[str, float]

@dataclass
class SemanticMatch:
    """Semantic matching result"""
    similarity_score: float
    matched_concepts: List[str]
    content_overlap: float
    pedagogical_alignment: float
    difficulty_match: float

class VideoContentAnalysisService:
    """
    Service for analyzing video content and improving question-video matching
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.stemmer = SnowballStemmer('spanish')
        
        # Spanish stopwords + educational stopwords
        self.stop_words = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
            'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como',
            'pero', 'sus', 'le', 'ya', 'o', 'este', 'está', 'tiene', 'más', 'puede', 'todos',
            'video', 'videos', 'clase', 'tutorial', 'explicación', 'aprende', 'aprender',
            'enseñanza', 'educativo', 'curso', 'lección'
        }
        
        # ICFES subject keywords
        self.subject_keywords = {
            'matematicas': [
                'algebra', 'geometria', 'trigonometria', 'calculo', 'estadistica', 'probabilidad',
                'ecuacion', 'funcion', 'derivada', 'integral', 'limite', 'vector', 'matriz',
                'polinomio', 'logaritmo', 'exponencial', 'fraccion', 'numero', 'operacion'
            ],
            'lenguaje': [
                'lectura', 'comprension', 'texto', 'narrativa', 'argumentacion', 'gramatica',
                'ortografia', 'sintaxis', 'semantica', 'pragmatica', 'discurso', 'ensayo',
                'literatura', 'poetica', 'retorica', 'comunicacion'
            ],
            'ciencias': [
                'fisica', 'quimica', 'biologia', 'energia', 'fuerza', 'movimiento', 'atomo',
                'molecula', 'celula', 'genetica', 'evolucion', 'ecosistema', 'reaccion',
                'elemento', 'compuesto', 'experimento', 'laboratorio'
            ],
            'sociales': [
                'historia', 'geografia', 'politica', 'economia', 'sociedad', 'cultura',
                'constitucion', 'democracia', 'territorio', 'poblacion', 'gobierno',
                'conflicto', 'paz', 'derechos', 'ciudadania'
            ],
            'filosofia': [
                'etica', 'moral', 'conocimiento', 'verdad', 'logica', 'razonamiento',
                'argumento', 'premisa', 'conclusion', 'filosofia', 'pensamiento',
                'existencia', 'realidad', 'conciencia'
            ]
        }
        
        # Difficulty indicators
        self.difficulty_indicators = {
            'basico': [
                'introduccion', 'basico', 'fundamental', 'simple', 'facil', 'primero',
                'inicial', 'conceptos', 'definicion', 'que es', 'como', 'principios'
            ],
            'intermedio': [
                'intermedio', 'aplicacion', 'ejemplo', 'practica', 'ejercicio',
                'problemas', 'desarrollo', 'metodo', 'tecnica', 'procedimiento'
            ],
            'avanzado': [
                'avanzado', 'complejo', 'profundo', 'analisis', 'critico', 'demostracion',
                'teoria', 'investigacion', 'especializado', 'experto', 'maestria'
            ]
        }
        
        # Cognitive levels (Bloom's taxonomy in Spanish)
        self.cognitive_levels = {
            'recordar': ['recordar', 'identificar', 'reconocer', 'definir', 'enumerar', 'nombrar'],
            'comprender': ['explicar', 'interpretar', 'resumir', 'clasificar', 'comparar', 'contrastar'],
            'aplicar': ['aplicar', 'usar', 'implementar', 'resolver', 'demostrar', 'ejecutar'],
            'analizar': ['analizar', 'examinar', 'investigar', 'diferenciar', 'organizar', 'estructurar'],
            'evaluar': ['evaluar', 'juzgar', 'criticar', 'valorar', 'justificar', 'argumentar'],
            'crear': ['crear', 'diseñar', 'construir', 'planificar', 'producir', 'generar']
        }
    
    async def analyze_video_content(self, video_id: int) -> ContentFeatures:
        """
        Analyze video content to extract educational features
        
        Args:
            video_id: Video ID to analyze
            
        Returns:
            Extracted content features
        """
        try:
            video = self.db.query(YoutubeCatalog).filter(YoutubeCatalog.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            # Combine all available text
            content_text = self._combine_video_text(video)
            
            # Extract features
            features = ContentFeatures(
                keywords=self._extract_keywords(content_text),
                concepts=self._extract_concepts(content_text),
                difficulty_indicators=self._extract_difficulty_indicators(content_text),
                content_type=self._classify_content_type(content_text),
                cognitive_level=self._classify_cognitive_level(content_text),
                educational_objectives=self._extract_educational_objectives(content_text),
                topic_coverage=self._analyze_topic_coverage(content_text)
            )
            
            # Update video with analysis results
            await self._update_video_analysis(video, features)
            
            return features
            
        except Exception as e:
            logger.error(f"Error analyzing video content: {e}")
            return ContentFeatures(
                keywords=[], concepts=[], difficulty_indicators=[],
                content_type='unknown', cognitive_level='unknown',
                educational_objectives=[], topic_coverage={}
            )
    
    def _combine_video_text(self, video: YoutubeCatalog) -> str:
        """Combine all available text from video"""
        
        text_parts = []
        
        if video.title:
            text_parts.append(video.title)
        
        if video.description:
            text_parts.append(video.description)
        
        if video.transcript:
            text_parts.append(video.transcript)
        
        if video.tema_principal:
            text_parts.append(video.tema_principal)
        
        return ' '.join(text_parts).lower()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        
        try:
            # Tokenize and clean
            words = word_tokenize(text)
            words = [word for word in words if word.isalpha() and len(word) > 2]
            words = [word for word in words if word not in self.stop_words]
            
            # Count frequency
            word_freq = Counter(words)
            
            # Get top keywords
            keywords = [word for word, freq in word_freq.most_common(20)]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract educational concepts from text"""
        
        concepts = []
        
        # Look for concept patterns
        concept_patterns = [
            r'concepto de (\w+)',
            r'definición de (\w+)',
            r'teoría de (\w+)',
            r'principio de (\w+)',
            r'ley de (\w+)',
            r'método de (\w+)'
        ]
        
        for pattern in concept_patterns:
            matches = re.findall(pattern, text)
            concepts.extend(matches)
        
        # Look for subject-specific concepts
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    concepts.append(keyword)
        
        return list(set(concepts))  # Remove duplicates
    
    def _extract_difficulty_indicators(self, text: str) -> List[str]:
        """Extract difficulty level indicators"""
        
        indicators = []
        
        for level, keywords in self.difficulty_indicators.items():
            for keyword in keywords:
                if keyword in text:
                    indicators.append(level)
                    break  # One indicator per level
        
        return indicators
    
    def _classify_content_type(self, text: str) -> str:
        """Classify the type of educational content"""
        
        type_indicators = {
            'explicativo': ['explica', 'enseña', 'concepto', 'teoría', 'definición'],
            'ejercicio_guiado': ['ejercicio', 'problema', 'ejemplo', 'paso a paso', 'resolver'],
            'demostracion': ['demostración', 'prueba', 'experimento', 'laboratorio'],
            'repaso': ['repaso', 'resumen', 'revisión', 'recordar'],
            'evaluacion': ['examen', 'test', 'evaluación', 'quiz', 'preguntas']
        }
        
        scores = {}
        for content_type, indicators in type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            scores[content_type] = score
        
        # Return type with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'explicativo'  # Default
    
    def _classify_cognitive_level(self, text: str) -> str:
        """Classify cognitive level based on Bloom's taxonomy"""
        
        scores = {}
        for level, verbs in self.cognitive_levels.items():
            score = sum(1 for verb in verbs if verb in text)
            scores[level] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'comprender'  # Default
    
    def _extract_educational_objectives(self, text: str) -> List[str]:
        """Extract educational objectives from text"""
        
        objectives = []
        
        # Look for objective patterns
        objective_patterns = [
            r'aprenderás (\w+(?:\s+\w+)*)',
            r'objetivo es (\w+(?:\s+\w+)*)',
            r'vamos a (\w+(?:\s+\w+)*)',
            r'al final podrás (\w+(?:\s+\w+)*)'
        ]
        
        for pattern in objective_patterns:
            matches = re.findall(pattern, text)
            objectives.extend(matches)
        
        return objectives[:5]  # Limit to top 5
    
    def _analyze_topic_coverage(self, text: str) -> Dict[str, float]:
        """Analyze how well video covers different topics"""
        
        coverage = {}
        
        for subject, keywords in self.subject_keywords.items():
            total_keywords = len(keywords)
            covered_keywords = sum(1 for keyword in keywords if keyword in text)
            
            coverage[subject] = covered_keywords / total_keywords if total_keywords > 0 else 0
        
        return coverage
    
    async def _update_video_analysis(self, video: YoutubeCatalog, features: ContentFeatures):
        """Update video record with analysis results"""
        
        try:
            # Update video metadata
            video.processing_status = 'completed'
            video.has_embeddings = True  # Mark as processed
            video.nivel = self._map_difficulty_to_nivel(features.difficulty_indicators)
            
            # Store analysis in competencias field as JSON
            analysis_data = {
                'keywords': features.keywords,
                'concepts': features.concepts,
                'content_type': features.content_type,
                'cognitive_level': features.cognitive_level,
                'educational_objectives': features.educational_objectives,
                'topic_coverage': features.topic_coverage,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            video.competencias = json.dumps(analysis_data)
            video.last_processed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating video analysis: {e}")
            self.db.rollback()
    
    def _map_difficulty_to_nivel(self, difficulty_indicators: List[str]) -> str:
        """Map difficulty indicators to nivel field"""
        
        if 'avanzado' in difficulty_indicators:
            return 'avanzado'
        elif 'intermedio' in difficulty_indicators:
            return 'intermedio'
        elif 'basico' in difficulty_indicators:
            return 'básico'
        else:
            return 'intermedio'  # Default
    
    async def calculate_semantic_similarity(
        self,
        video_id: int,
        question_id: str
    ) -> SemanticMatch:
        """
        Calculate semantic similarity between video and question
        
        Args:
            video_id: Video ID
            question_id: Question ID
            
        Returns:
            Semantic matching result
        """
        try:
            # Get video and question
            video = self.db.query(YoutubeCatalog).filter(YoutubeCatalog.id == video_id).first()
            question = self.db.query(Question).filter(Question.id == question_id).first()
            
            if not video or not question:
                raise ValueError("Video or question not found")
            
            # Get content features
            video_features = await self.analyze_video_content(video_id)
            question_text = f"{question.text} {question.explanation or ''}"
            question_keywords = self._extract_keywords(question_text.lower())
            question_concepts = self._extract_concepts(question_text.lower())
            
            # Calculate similarity components
            keyword_similarity = self._calculate_keyword_similarity(
                video_features.keywords, question_keywords
            )
            
            concept_similarity = self._calculate_concept_similarity(
                video_features.concepts, question_concepts
            )
            
            content_overlap = self._calculate_content_overlap(
                video, question
            )
            
            pedagogical_alignment = self._calculate_pedagogical_alignment(
                video_features, question
            )
            
            difficulty_match = self._calculate_difficulty_match(
                video_features, question
            )
            
            # Combined similarity score
            similarity_score = (
                keyword_similarity * 0.3 +
                concept_similarity * 0.3 +
                content_overlap * 0.2 +
                pedagogical_alignment * 0.1 +
                difficulty_match * 0.1
            )
            
            # Find matched concepts
            matched_concepts = list(set(video_features.concepts) & set(question_concepts))
            
            return SemanticMatch(
                similarity_score=similarity_score,
                matched_concepts=matched_concepts,
                content_overlap=content_overlap,
                pedagogical_alignment=pedagogical_alignment,
                difficulty_match=difficulty_match
            )
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return SemanticMatch(
                similarity_score=0.0,
                matched_concepts=[],
                content_overlap=0.0,
                pedagogical_alignment=0.0,
                difficulty_match=0.0
            )
    
    def _calculate_keyword_similarity(
        self,
        video_keywords: List[str],
        question_keywords: List[str]
    ) -> float:
        """Calculate keyword-based similarity"""
        
        if not video_keywords or not question_keywords:
            return 0.0
        
        # Use Jaccard similarity
        set1 = set(video_keywords)
        set2 = set(question_keywords)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_concept_similarity(
        self,
        video_concepts: List[str],
        question_concepts: List[str]
    ) -> float:
        """Calculate concept-based similarity"""
        
        if not video_concepts or not question_concepts:
            return 0.0
        
        # Weight concept matches higher than keyword matches
        set1 = set(video_concepts)
        set2 = set(question_concepts)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        jaccard = intersection / union if union > 0 else 0.0
        
        # Boost score for concept matches
        return min(1.0, jaccard * 1.5)
    
    def _calculate_content_overlap(
        self,
        video: YoutubeCatalog,
        question: Question
    ) -> float:
        """Calculate content overlap based on metadata"""
        
        overlap = 0.0
        
        # Topic match
        if video.topic_id and question.topic_id and video.topic_id == question.topic_id:
            overlap += 0.5
        
        # Subject match
        if video.subject_id and question.subject_id and video.subject_id == question.subject_id:
            overlap += 0.3
        
        # Area match
        if video.area_evaluada and question.subject:
            if video.area_evaluada.lower() in question.subject.name.lower():
                overlap += 0.2
        
        return min(1.0, overlap)
    
    def _calculate_pedagogical_alignment(
        self,
        video_features: ContentFeatures,
        question: Question
    ) -> float:
        """Calculate pedagogical alignment between video and question"""
        
        alignment = 0.0
        
        # Content type alignment
        if video_features.content_type in ['explicativo', 'ejercicio_guiado']:
            alignment += 0.5
        
        # Cognitive level alignment
        question_text = (question.text + ' ' + (question.explanation or '')).lower()
        
        # Simple heuristics for question cognitive level
        if any(word in question_text for word in ['analizar', 'evaluar', 'comparar']):
            if video_features.cognitive_level in ['analizar', 'evaluar']:
                alignment += 0.3
        elif any(word in question_text for word in ['aplicar', 'resolver', 'calcular']):
            if video_features.cognitive_level in ['aplicar', 'comprender']:
                alignment += 0.3
        else:
            if video_features.cognitive_level in ['recordar', 'comprender']:
                alignment += 0.2
        
        return min(1.0, alignment)
    
    def _calculate_difficulty_match(
        self,
        video_features: ContentFeatures,
        question: Question
    ) -> float:
        """Calculate difficulty level match"""
        
        # Map question difficulty to video difficulty indicators
        question_difficulty = question.difficulty_level or 0.5
        
        video_difficulty_score = 0.5  # Default
        
        if 'basico' in video_features.difficulty_indicators:
            video_difficulty_score = 0.3
        elif 'intermedio' in video_features.difficulty_indicators:
            video_difficulty_score = 0.6
        elif 'avanzado' in video_features.difficulty_indicators:
            video_difficulty_score = 0.9
        
        # Calculate proximity
        diff = abs(question_difficulty - video_difficulty_score)
        
        return max(0.0, 1.0 - diff * 2)  # Scale difference to 0-1
    
    async def batch_analyze_videos(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        Batch analyze videos for content features
        
        Args:
            limit: Number of videos to process
            offset: Starting offset
            
        Returns:
            Batch processing results
        """
        try:
            # Get unprocessed videos
            videos = self.db.query(YoutubeCatalog).filter(
                or_(
                    YoutubeCatalog.processing_status == 'pending',
                    YoutubeCatalog.has_embeddings == False
                )
            ).offset(offset).limit(limit).all()
            
            results = {
                'processed': 0,
                'errors': 0,
                'total': len(videos)
            }
            
            for video in videos:
                try:
                    await self.analyze_video_content(video.id)
                    results['processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing video {video.id}: {e}")
                    results['errors'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch video analysis: {e}")
            return {
                'processed': 0,
                'errors': 1,
                'total': 0,
                'error': str(e)
            }
    
    async def get_content_analysis_report(self, video_id: int) -> Dict:
        """
        Get comprehensive content analysis report for a video
        
        Args:
            video_id: Video ID
            
        Returns:
            Content analysis report
        """
        try:
            video = self.db.query(YoutubeCatalog).filter(YoutubeCatalog.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            features = await self.analyze_video_content(video_id)
            
            report = {
                'video_id': video_id,
                'title': video.title,
                'analysis_date': datetime.utcnow().isoformat(),
                'content_features': {
                    'keywords': features.keywords,
                    'concepts': features.concepts,
                    'difficulty_level': features.difficulty_indicators,
                    'content_type': features.content_type,
                    'cognitive_level': features.cognitive_level,
                    'educational_objectives': features.educational_objectives,
                    'topic_coverage': features.topic_coverage
                },
                'quality_metrics': {
                    'has_transcript': bool(video.transcript),
                    'has_description': bool(video.description),
                    'content_richness': len(features.keywords) + len(features.concepts),
                    'educational_value': len(features.educational_objectives)
                },
                'recommendations': self._generate_content_recommendations(features, video)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating content analysis report: {e}")
            return {
                'video_id': video_id,
                'error': str(e)
            }
    
    def _generate_content_recommendations(
        self,
        features: ContentFeatures,
        video: YoutubeCatalog
    ) -> List[str]:
        """Generate recommendations for improving video content"""
        
        recommendations = []
        
        if len(features.keywords) < 5:
            recommendations.append("Consider adding more descriptive keywords in title/description")
        
        if len(features.concepts) < 3:
            recommendations.append("Enhance content with more educational concepts")
        
        if not features.educational_objectives:
            recommendations.append("Add clear learning objectives to video description")
        
        if not video.transcript:
            recommendations.append("Add transcript for better content analysis")
        
        if features.content_type == 'unknown':
            recommendations.append("Clarify the educational purpose of the video")
        
        return recommendations