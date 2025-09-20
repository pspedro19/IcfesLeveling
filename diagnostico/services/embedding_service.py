import asyncio
import time
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import hashlib

import openai
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.models.content_embeddings import ContentEmbeddings
from app.models.youtube_catalog import YoutubeCatalog
from app.core.database import get_db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Servicio para generar y gestionar embeddings vectoriales usando OpenAI
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API key no configurada correctamente en .env")
        
        # Configurar cliente OpenAI
        openai.api_key = self.api_key
        
        # Configuración del modelo
        self.model_name = "text-embedding-3-large"
        self.max_tokens = 8191  # Límite máximo para text-embedding-3-large
        self.vector_dimensions = 3072
        
        # Rate limiting para OpenAI API
        self.requests_per_minute = 3000  # Límite típico para tier 1
        self.tokens_per_minute = 1000000
        self.current_requests = 0
        self.current_tokens = 0
        self.minute_start = time.time()
        
        # Weights para scoring combinado
        self.content_weights = {
            'title': 0.3,
            'description': 0.2,
            'transcript': 0.5
        }
    
    async def check_rate_limits(self, estimated_tokens: int = 1000):
        """Verifica y gestiona los límites de rate de OpenAI"""
        current_time = time.time()
        
        # Reset counters cada minuto
        if current_time - self.minute_start >= 60:
            self.current_requests = 0
            self.current_tokens = 0
            self.minute_start = current_time
        
        # Esperar si estamos cerca de los límites
        if (self.current_requests >= self.requests_per_minute * 0.9 or 
            self.current_tokens + estimated_tokens >= self.tokens_per_minute * 0.9):
            
            wait_time = 60 - (current_time - self.minute_start)
            if wait_time > 0:
                logger.info(f"Rate limit approached. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time + 1)
                self.current_requests = 0
                self.current_tokens = 0
                self.minute_start = time.time()
    
    def estimate_tokens(self, text: str) -> int:
        """Estima el número de tokens en un texto (aproximación)"""
        # Aproximación: 1 token ≈ 4 caracteres para español
        return len(text) // 4
    
    def clean_text(self, text: str) -> str:
        """Limpia y prepara el texto para embedding"""
        if not text:
            return ""
        
        # Remover caracteres problemáticos y normalizar
        cleaned = text.strip()
        cleaned = ' '.join(cleaned.split())  # Normalizar espacios en blanco
        
        # Truncar si es muy largo
        estimated_tokens = self.estimate_tokens(cleaned)
        if estimated_tokens > self.max_tokens:
            # Truncar manteniendo palabras completas
            words = cleaned.split()
            truncated_words = []
            current_tokens = 0
            
            for word in words:
                word_tokens = self.estimate_tokens(word)
                if current_tokens + word_tokens > self.max_tokens:
                    break
                truncated_words.append(word)
                current_tokens += word_tokens
            
            cleaned = ' '.join(truncated_words)
            logger.warning(f"Text truncated from {estimated_tokens} to {current_tokens} estimated tokens")
        
        return cleaned
    
    async def generate_embedding(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """
        Genera embedding para un texto usando OpenAI API
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        cleaned_text = self.clean_text(text)
        estimated_tokens = self.estimate_tokens(cleaned_text)
        
        # Check rate limits
        await self.check_rate_limits(estimated_tokens)
        
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                # Llamada a OpenAI API
                response = await openai.Embedding.acreate(
                    model=self.model_name,
                    input=cleaned_text
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                # Update rate limiting counters
                self.current_requests += 1
                self.current_tokens += estimated_tokens
                
                # Extract embedding vector
                embedding = response['data'][0]['embedding']
                
                logger.info(f"Generated embedding in {processing_time}ms for {estimated_tokens} tokens")
                return embedding
                
            except openai.error.RateLimitError as e:
                wait_time = min(60 * (2 ** attempt), 300)  # Exponential backoff max 5 min
                logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}")
                await asyncio.sleep(wait_time)
                
            except openai.error.InvalidRequestError as e:
                logger.error(f"Invalid request: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Error generating embedding (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        logger.error(f"Failed to generate embedding after {retry_count} attempts")
        return None
    
    async def create_content_embedding(
        self, 
        db: Session, 
        content_type: str,
        content_id: int,
        embedding_type: str,
        source_text: str,
        **metadata
    ) -> Optional[ContentEmbeddings]:
        """
        Crea un embedding para contenido específico
        """
        if not source_text or not source_text.strip():
            logger.warning(f"Empty source text for {content_type}:{content_id}:{embedding_type}")
            return None
        
        # Verificar si ya existe un embedding para este contenido
        text_hash = ContentEmbeddings.create_text_hash(source_text)
        existing = db.query(ContentEmbeddings).filter(
            and_(
                ContentEmbeddings.content_type == content_type,
                ContentEmbeddings.content_id == content_id,
                ContentEmbeddings.embedding_type == embedding_type,
                ContentEmbeddings.source_text_hash == text_hash,
                ContentEmbeddings.is_active == 'true'
            )
        ).first()
        
        if existing:
            logger.info(f"Embedding already exists for {content_type}:{content_id}:{embedding_type}")
            return existing
        
        # Generar nuevo embedding
        start_time = time.time()
        embedding_vector = await self.generate_embedding(source_text)
        processing_time = int((time.time() - start_time) * 1000)
        
        if not embedding_vector:
            logger.error(f"Failed to generate embedding for {content_type}:{content_id}")
            return None
        
        # Crear registro en base de datos
        embedding_record = ContentEmbeddings(
            content_type=content_type,
            content_id=content_id,
            content_uuid=metadata.get('content_uuid'),
            embedding_type=embedding_type,
            model_name=self.model_name,
            vector_dimensions=len(embedding_vector),
            embedding_vector=embedding_vector,
            source_text=source_text,
            source_text_hash=text_hash,
            subject_area=metadata.get('subject_area'),
            topic=metadata.get('topic'),
            difficulty_level=metadata.get('difficulty_level'),
            language=metadata.get('language', 'es'),
            processing_time_ms=processing_time,
            token_count=self.estimate_tokens(source_text)
        )
        
        try:
            db.add(embedding_record)
            db.commit()
            db.refresh(embedding_record)
            
            logger.info(f"Created embedding for {content_type}:{content_id}:{embedding_type}")
            return embedding_record
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving embedding: {e}")
            return None
    
    async def process_youtube_video_embeddings(
        self, 
        db: Session, 
        video: YoutubeCatalog,
        force_regenerate: bool = False
    ) -> Dict[str, Optional[ContentEmbeddings]]:
        """
        Procesa todos los embeddings para un video de YouTube
        """
        logger.info(f"Processing embeddings for video: {video.codigo_tema} - {video.title[:50]}")
        
        embeddings = {}
        metadata = {
            'content_uuid': video.uuid,
            'subject_area': video.area_evaluada,
            'topic': video.tema_principal,
            'difficulty_level': video.nivel,
            'language': 'es'
        }
        
        # Title embedding
        if video.title:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'youtube_video', video.id, 'title')
            
            embeddings['title'] = await self.create_content_embedding(
                db=db,
                content_type='youtube_video',
                content_id=video.id,
                embedding_type='title',
                source_text=video.title,
                **metadata
            )
        
        # Description embedding
        if video.description:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'youtube_video', video.id, 'description')
            
            embeddings['description'] = await self.create_content_embedding(
                db=db,
                content_type='youtube_video',
                content_id=video.id,
                embedding_type='description',
                source_text=video.description,
                **metadata
            )
        
        # Transcript embedding
        if video.transcript:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'youtube_video', video.id, 'transcript')
            
            embeddings['transcript'] = await self.create_content_embedding(
                db=db,
                content_type='youtube_video',
                content_id=video.id,
                embedding_type='transcript',
                source_text=video.transcript,
                **metadata
            )
        
        # Combined embedding (título + descripción + transcripción ponderada)
        combined_text = self._create_combined_text(video)
        if combined_text:
            if force_regenerate:
                self._deactivate_existing_embeddings(db, 'youtube_video', video.id, 'combined')
            
            embeddings['combined'] = await self.create_content_embedding(
                db=db,
                content_type='youtube_video',
                content_id=video.id,
                embedding_type='combined',
                source_text=combined_text,
                **metadata
            )
        
        # Actualizar estado del video
        video.has_embeddings = any(e is not None for e in embeddings.values())
        video.processing_status = 'completed' if video.has_embeddings else 'error'
        video.last_processed_at = datetime.utcnow()
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating video status: {e}")
        
        return embeddings
    
    def _create_combined_text(self, video: YoutubeCatalog) -> str:
        """Crea texto combinado ponderado para embedding"""
        parts = []
        
        if video.title:
            # Repetir título según su peso
            title_repeat = int(self.content_weights['title'] * 10)
            parts.extend([video.title] * max(1, title_repeat))
        
        if video.description:
            # Repetir descripción según su peso
            desc_repeat = int(self.content_weights['description'] * 10)
            parts.extend([video.description] * max(1, desc_repeat))
        
        if video.transcript:
            # Repetir transcripción según su peso
            transcript_repeat = int(self.content_weights['transcript'] * 10)
            parts.extend([video.transcript] * max(1, transcript_repeat))
        
        return " ".join(parts)
    
    def _deactivate_existing_embeddings(
        self, 
        db: Session, 
        content_type: str, 
        content_id: int, 
        embedding_type: str
    ):
        """Desactiva embeddings existentes (soft delete)"""
        db.query(ContentEmbeddings).filter(
            and_(
                ContentEmbeddings.content_type == content_type,
                ContentEmbeddings.content_id == content_id,
                ContentEmbeddings.embedding_type == embedding_type
            )
        ).update({'is_active': 'false'})
        db.commit()
    
    async def batch_process_videos(
        self, 
        db: Session,
        batch_size: int = 10,
        max_videos: Optional[int] = None,
        filter_processed: bool = True
    ) -> Dict[str, int]:
        """
        Procesa embeddings para videos en lotes
        """
        logger.info(f"Starting batch processing with batch_size={batch_size}")
        
        # Query base para videos pendientes
        query = db.query(YoutubeCatalog)
        
        if filter_processed:
            query = query.filter(
                or_(
                    YoutubeCatalog.has_embeddings == False,
                    YoutubeCatalog.has_embeddings.is_(None)
                )
            )
        
        if max_videos:
            query = query.limit(max_videos)
        
        videos = query.all()
        total_videos = len(videos)
        
        logger.info(f"Found {total_videos} videos to process")
        
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Procesar en lotes
        for i in range(0, total_videos, batch_size):
            batch = videos[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_videos-1)//batch_size + 1}")
            
            for video in batch:
                try:
                    embeddings = await self.process_youtube_video_embeddings(db, video)
                    
                    if any(e is not None for e in embeddings.values()):
                        stats['successful'] += 1
                        logger.info(f"✓ Processed {video.codigo_tema}: {video.title[:50]}")
                    else:
                        stats['failed'] += 1
                        logger.error(f"✗ Failed {video.codigo_tema}: {video.title[:50]}")
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"Error processing video {video.codigo_tema}: {e}")
            
            # Pausa entre lotes para rate limiting
            if i + batch_size < total_videos:
                await asyncio.sleep(2)
        
        logger.info(f"Batch processing completed: {stats}")
        return stats