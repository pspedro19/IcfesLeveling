#!/usr/bin/env python3
"""
Script para procesamiento en lotes de embeddings
PASO 9: Sistema de generación de embeddings con batch processing
"""

import asyncio
import sys
import os
import logging
import argparse
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Agregar el path del backend para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import SessionLocal, engine
from app.models.youtube_catalog import YoutubeCatalog
from app.models.content_embeddings import ContentEmbeddings
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embeddings_batch_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EmbeddingBatchProcessor:
    """
    Procesador de embeddings en lotes con gestión de rate limits
    """
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 3):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.session: Session = SessionLocal()
        
        # Inicializar servicio de embeddings
        self.embedding_service = EmbeddingService()
        
        self.stats = {
            'total_videos': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'embeddings_created': 0,
            'start_time': datetime.utcnow()
        }
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_videos_to_process(
        self, 
        limit: Optional[int] = None,
        force_reprocess: bool = False,
        filter_by_area: Optional[str] = None,
        filter_by_codigo: Optional[str] = None
    ) -> List[YoutubeCatalog]:
        """
        Obtiene videos que necesitan procesamiento de embeddings
        """
        query = self.session.query(YoutubeCatalog)
        
        # Filtros condicionales
        if not force_reprocess:
            query = query.filter(
                or_(
                    YoutubeCatalog.has_embeddings == False,
                    YoutubeCatalog.has_embeddings.is_(None),
                    YoutubeCatalog.processing_status == 'error'
                )
            )
        
        if filter_by_area:
            query = query.filter(YoutubeCatalog.area_evaluada == filter_by_area)
        
        if filter_by_codigo:
            query = query.filter(YoutubeCatalog.codigo_tema.like(f"{filter_by_codigo}%"))
        
        # Ordenar por prioridad (áreas más importantes primero)
        priority_order = [
            'Matemáticas',
            'Ciencias Naturales', 
            'Lenguaje',
            'Sociales',
            'Física',
            'Química',
            'Biología'
        ]
        
        # Aplicar ordenamiento personalizado
        case_conditions = []
        for i, area in enumerate(priority_order):
            case_conditions.append((YoutubeCatalog.area_evaluada == area, i))
        
        if case_conditions:
            from sqlalchemy import case
            priority_field = case(
                case_conditions,
                else_=len(priority_order)
            )
            query = query.order_by(priority_field, YoutubeCatalog.codigo_tema)
        else:
            query = query.order_by(YoutubeCatalog.area_evaluada, YoutubeCatalog.codigo_tema)
        
        if limit:
            query = query.limit(limit)
        
        videos = query.all()
        logger.info(f"Found {len(videos)} videos to process")
        return videos
    
    async def process_video_embeddings(self, video: YoutubeCatalog) -> Dict[str, bool]:
        """
        Procesa embeddings para un video específico
        """
        logger.info(f"Processing embeddings for {video.codigo_tema}: {video.title[:50] if video.title else video.tema_principal[:50]}")
        
        try:
            # Marcar como en procesamiento
            video.processing_status = 'processing'
            self.session.commit()
            
            # Generar embeddings usando el servicio
            embeddings = await self.embedding_service.process_youtube_video_embeddings(
                db=self.session,
                video=video,
                force_regenerate=False
            )
            
            # Contar embeddings creados
            created_count = sum(1 for e in embeddings.values() if e is not None)
            self.stats['embeddings_created'] += created_count
            
            success = created_count > 0
            if success:
                self.stats['successful'] += 1
                logger.info(f"✓ Successfully processed {video.codigo_tema} - created {created_count} embeddings")
            else:
                self.stats['failed'] += 1
                video.processing_status = 'error'
                video.error_message = "No se pudieron generar embeddings"
                logger.error(f"✗ Failed to process {video.codigo_tema} - no embeddings created")
            
            self.session.commit()
            return embeddings
            
        except Exception as e:
            self.stats['failed'] += 1
            video.processing_status = 'error'
            video.error_message = str(e)[:500]  # Truncar mensaje de error
            
            try:
                self.session.commit()
            except Exception as commit_error:
                logger.error(f"Error saving error state: {commit_error}")
                self.session.rollback()
            
            logger.error(f"✗ Error processing {video.codigo_tema}: {e}")
            return {}
    
    async def process_batch(self, batch: List[YoutubeCatalog]) -> Dict[str, int]:
        """
        Procesa un lote de videos de forma concurrente
        """
        batch_stats = {'successful': 0, 'failed': 0}
        
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(video):
            async with semaphore:
                result = await self.process_video_embeddings(video)
                if any(e is not None for e in result.values()):
                    batch_stats['successful'] += 1
                else:
                    batch_stats['failed'] += 1
                return result
        
        # Procesar videos del lote concurrentemente
        tasks = [process_with_semaphore(video) for video in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return batch_stats
    
    async def run_batch_processing(
        self,
        max_videos: Optional[int] = None,
        force_reprocess: bool = False,
        filter_by_area: Optional[str] = None,
        filter_by_codigo: Optional[str] = None,
        pause_between_batches: int = 5
    ) -> Dict[str, any]:
        """
        Ejecuta el procesamiento en lotes completo
        """
        logger.info("Starting batch embedding processing...")
        logger.info(f"Configuration: batch_size={self.batch_size}, max_concurrent={self.max_concurrent}")
        
        # Obtener videos a procesar
        videos = self.get_videos_to_process(
            limit=max_videos,
            force_reprocess=force_reprocess,
            filter_by_area=filter_by_area,
            filter_by_codigo=filter_by_codigo
        )
        
        self.stats['total_videos'] = len(videos)
        
        if not videos:
            logger.info("No videos found to process")
            return self.stats
        
        logger.info(f"Processing {len(videos)} videos in batches of {self.batch_size}")
        
        # Procesar en lotes
        total_batches = (len(videos) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(0, len(videos), self.batch_size):
            current_batch = batch_idx // self.batch_size + 1
            batch = videos[batch_idx:batch_idx + self.batch_size]
            
            logger.info(f"\nProcessing batch {current_batch}/{total_batches} ({len(batch)} videos)")
            
            # Procesar lote
            batch_start_time = datetime.utcnow()
            batch_stats = await self.process_batch(batch)
            batch_duration = (datetime.utcnow() - batch_start_time).total_seconds()
            
            # Actualizar estadísticas globales
            self.stats['processed'] += len(batch)
            
            logger.info(f"Batch {current_batch} completed in {batch_duration:.1f}s: "
                       f"{batch_stats['successful']} successful, {batch_stats['failed']} failed")
            
            # Pausa entre lotes para rate limiting
            if current_batch < total_batches and pause_between_batches > 0:
                logger.info(f"Pausing {pause_between_batches}s before next batch...")
                await asyncio.sleep(pause_between_batches)
        
        # Calcular estadísticas finales
        self.stats['duration'] = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        
        return self.stats
    
    def print_final_stats(self):
        """Imprime estadísticas finales del procesamiento"""
        stats = self.stats
        duration = stats.get('duration', 0)
        
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE PROCESAMIENTO DE EMBEDDINGS")
        logger.info("="*60)
        logger.info(f"Total videos: {stats['total_videos']}")
        logger.info(f"Procesados: {stats['processed']}")
        logger.info(f"Exitosos: {stats['successful']}")
        logger.info(f"Fallidos: {stats['failed']}")
        logger.info(f"Omitidos: {stats['skipped']}")
        logger.info(f"Embeddings creados: {stats['embeddings_created']}")
        logger.info(f"Duración total: {duration:.1f} segundos")
        
        if stats['processed'] > 0:
            success_rate = (stats['successful'] / stats['processed']) * 100
            avg_time = duration / stats['processed']
            logger.info(f"Tasa de éxito: {success_rate:.1f}%")
            logger.info(f"Tiempo promedio por video: {avg_time:.2f} segundos")
        
        logger.info("="*60)
    
    def get_processing_status_summary(self) -> Dict[str, int]:
        """Obtiene resumen del estado de procesamiento"""
        summary = {}
        
        # Estado de procesamiento
        status_counts = self.session.query(
            YoutubeCatalog.processing_status,
            func.count(YoutubeCatalog.id)
        ).group_by(YoutubeCatalog.processing_status).all()
        
        for status, count in status_counts:
            summary[f"status_{status}"] = count
        
        # Videos con embeddings
        with_embeddings = self.session.query(YoutubeCatalog).filter(
            YoutubeCatalog.has_embeddings == True
        ).count()
        
        without_embeddings = self.session.query(YoutubeCatalog).filter(
            or_(
                YoutubeCatalog.has_embeddings == False,
                YoutubeCatalog.has_embeddings.is_(None)
            )
        ).count()
        
        summary['with_embeddings'] = with_embeddings
        summary['without_embeddings'] = without_embeddings
        summary['total_videos'] = with_embeddings + without_embeddings
        
        return summary

async def main():
    """Función principal asíncrona"""
    parser = argparse.ArgumentParser(description='Procesamiento en lotes de embeddings')
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Tamaño del lote (default: 10)'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Máximo procesamiento concurrente (default: 3)'
    )
    parser.add_argument(
        '--max-videos',
        type=int,
        help='Máximo número de videos a procesar'
    )
    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Forzar reprocesamiento de videos ya procesados'
    )
    parser.add_argument(
        '--filter-area',
        type=str,
        help='Filtrar por área específica (ej: Matemáticas)'
    )
    parser.add_argument(
        '--filter-codigo',
        type=str,
        help='Filtrar por prefijo de código (ej: CN para Ciencias Naturales)'
    )
    parser.add_argument(
        '--pause-between-batches',
        type=int,
        default=5,
        help='Pausa en segundos entre lotes (default: 5)'
    )
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Solo mostrar estado actual sin procesar'
    )
    
    args = parser.parse_args()
    
    try:
        with EmbeddingBatchProcessor(
            batch_size=args.batch_size,
            max_concurrent=args.max_concurrent
        ) as processor:
            
            if args.status_only:
                # Solo mostrar estado
                status = processor.get_processing_status_summary()
                logger.info("Estado actual del procesamiento:")
                for key, value in status.items():
                    logger.info(f"  {key}: {value}")
                return
            
            # Ejecutar procesamiento
            stats = await processor.run_batch_processing(
                max_videos=args.max_videos,
                force_reprocess=args.force_reprocess,
                filter_by_area=args.filter_area,
                filter_by_codigo=args.filter_codigo,
                pause_between_batches=args.pause_between_batches
            )
            
            processor.print_final_stats()
            
            # Exit code basado en resultados
            if stats['total_videos'] == 0:
                sys.exit(0)  # Nada que procesar
            elif stats['failed'] > stats['successful']:
                sys.exit(1)  # Más fallos que éxitos
            elif stats['failed'] > 0:
                sys.exit(2)  # Algunos fallos
            else:
                sys.exit(0)  # Todo exitoso
            
    except KeyboardInterrupt:
        logger.info("Procesamiento interrumpido por usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar si hay OpenAI API key configurada
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        logger.error("ERROR: OpenAI API key no configurada en .env")
        logger.error("Configura OPENAI_API_KEY en tu archivo .env para continuar")
        sys.exit(1)
    
    asyncio.run(main())