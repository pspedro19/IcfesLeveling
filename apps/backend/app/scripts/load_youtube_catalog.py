#!/usr/bin/env python3
"""
Script para carga masiva del catálogo YouTube desde CSV
PASO 8: Cargar catálogo YouTube completo con validaciones
"""

import csv
import sys
import os
import re
import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Agregar el path del backend para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import SessionLocal, engine
from app.models.youtube_catalog import YoutubeCatalog
from app.models import Base

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_catalog_load.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class YouTubeCatalogLoader:
    """
    Cargador del catálogo YouTube desde archivo CSV
    """
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.session: Session = SessionLocal()
        self.stats = {
            'total_rows': 0,
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'duplicate_youtube_ids': 0
        }
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Extrae el ID de YouTube de una URL
        Soporta múltiples formatos de URL de YouTube
        """
        if not url:
            return None
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*?v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                youtube_id = match.group(1)
                # Limpiar parámetros adicionales como &t=126s
                if '&' in youtube_id:
                    youtube_id = youtube_id.split('&')[0]
                return youtube_id
        
        logger.warning(f"Could not extract YouTube ID from URL: {url}")
        return None
    
    def normalize_url(self, url: str, youtube_id: str) -> str:
        """Normaliza la URL a formato estándar de YouTube"""
        if youtube_id:
            return f"https://www.youtube.com/watch?v={youtube_id}"
        return url
    
    def validate_row(self, row: Dict[str, str], row_number: int) -> Tuple[bool, List[str]]:
        """
        Valida una fila del CSV
        Retorna (es_válida, lista_de_errores)
        """
        errors = []
        
        # Campos obligatorios
        required_fields = ['codigo_tema', 'area_evaluada', 'tema_principal', 'youtube_url']
        for field in required_fields:
            if not row.get(field, '').strip():
                errors.append(f"Campo obligatorio vacío: {field}")
        
        # Validar formato de código tema
        codigo_tema = row.get('codigo_tema', '').strip()
        if codigo_tema and not re.match(r'^[A-Z]{2}\d{3}$', codigo_tema):
            errors.append(f"Formato inválido de codigo_tema: {codigo_tema} (esperado: XX999)")
        
        # Validar URL de YouTube
        youtube_url = row.get('youtube_url', '').strip()
        if youtube_url:
            youtube_id = self.extract_youtube_id(youtube_url)
            if not youtube_id:
                errors.append(f"URL de YouTube inválida: {youtube_url}")
        
        # Validar área evaluada
        valid_areas = [
            'Ciencias Naturales', 'Matemáticas', 'Lenguaje', 'Sociales', 
            'Inglés', 'Filosofía', 'Física', 'Química', 'Biología'
        ]
        area = row.get('area_evaluada', '').strip()
        if area and area not in valid_areas:
            logger.warning(f"Área no reconocida en fila {row_number}: {area}")
        
        return len(errors) == 0, errors
    
    def map_subject_and_topic_ids(self, area_evaluada: str, tema_principal: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Mapea área y tema a IDs del sistema ICFES
        TODO: Implementar mapping real con base de datos
        """
        # Mapping básico - debería consultarse desde la BD real
        subject_mapping = {
            'Ciencias Naturales': 1,
            'Matemáticas': 2,
            'Lenguaje': 3,
            'Sociales': 4,
            'Inglés': 5,
            'Filosofía': 6,
            'Física': 7,
            'Química': 8,
            'Biología': 9
        }
        
        subject_id = subject_mapping.get(area_evaluada)
        # topic_id se podría mapear con una consulta más específica
        topic_id = None  # TODO: Implementar mapping de temas
        
        return subject_id, topic_id
    
    def process_row(self, row: Dict[str, str], row_number: int) -> bool:
        """
        Procesa una fila individual del CSV
        """
        try:
            # Validar fila
            is_valid, errors = self.validate_row(row, row_number)
            if not is_valid:
                logger.error(f"Fila {row_number} inválida: {'; '.join(errors)}")
                self.stats['errors'] += 1
                return False
            
            # Extraer y limpiar datos
            codigo_tema = row['codigo_tema'].strip()
            area_evaluada = row['area_evaluada'].strip()
            tema_principal = row['tema_principal'].strip()
            canal_sugerido = row.get('canal_sugerido', '').strip()
            youtube_url = row['youtube_url'].strip()
            transcript = row.get('transcript', '').strip()
            tema_tag = row.get('tema tag', '').strip()  # Nota el espacio en el nombre
            
            # Extraer YouTube ID
            youtube_id = self.extract_youtube_id(youtube_url)
            if not youtube_id:
                logger.error(f"Fila {row_number}: No se pudo extraer YouTube ID de {youtube_url}")
                self.stats['errors'] += 1
                return False
            
            # Normalizar URL
            normalized_url = self.normalize_url(youtube_url, youtube_id)
            
            # Verificar si ya existe por YouTube ID
            existing = self.session.query(YoutubeCatalog).filter(
                YoutubeCatalog.youtube_id == youtube_id
            ).first()
            
            if existing:
                # Actualizar registro existente
                existing.url = normalized_url
                existing.area_evaluada = area_evaluada
                existing.tema_principal = tema_principal
                existing.canal_sugerido = canal_sugerido or existing.canal_sugerido
                existing.transcript = transcript or existing.transcript
                existing.tema_tag = tema_tag or existing.tema_tag
                existing.updated_at = datetime.utcnow()
                
                # Mapear subject/topic IDs
                subject_id, topic_id = self.map_subject_and_topic_ids(area_evaluada, tema_principal)
                existing.subject_id = subject_id
                existing.topic_id = topic_id
                
                self.stats['updated'] += 1
                logger.info(f"Actualizado video existente: {codigo_tema} - {youtube_id}")
                
            else:
                # Crear nuevo registro
                subject_id, topic_id = self.map_subject_and_topic_ids(area_evaluada, tema_principal)
                
                video = YoutubeCatalog(
                    youtube_id=youtube_id,
                    url=normalized_url,
                    title=tema_principal,  # Usar tema como título inicial
                    description=f"Video educativo sobre {tema_principal}",
                    channel_name=canal_sugerido.replace('@', '') if canal_sugerido else None,
                    codigo_tema=codigo_tema,
                    area_evaluada=area_evaluada,
                    tema_principal=tema_principal,
                    canal_sugerido=canal_sugerido,
                    transcript=transcript if transcript else None,
                    tema_tag=tema_tag if tema_tag else None,
                    subject_id=subject_id,
                    topic_id=topic_id,
                    processing_status='pending',
                    is_processed=False,
                    has_embeddings=False
                )
                
                self.session.add(video)
                self.stats['inserted'] += 1
                logger.info(f"Insertado nuevo video: {codigo_tema} - {youtube_id}")
            
            self.stats['processed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error procesando fila {row_number}: {e}")
            self.stats['errors'] += 1
            self.session.rollback()
            return False
    
    def detect_csv_encoding(self) -> str:
        """Detecta la codificación del archivo CSV"""
        try:
            import chardet
            with open(self.csv_file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                return encoding
        except ImportError:
            logger.warning("chardet not available, using utf-8")
            return 'utf-8'
        except Exception as e:
            logger.warning(f"Error detecting encoding: {e}, using utf-8")
            return 'utf-8'
    
    def load_catalog(self, batch_size: int = 50) -> Dict[str, int]:
        """
        Carga el catálogo completo desde el CSV
        """
        logger.info(f"Iniciando carga del catálogo desde: {self.csv_file_path}")
        
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"Archivo CSV no encontrado: {self.csv_file_path}")
        
        # Detectar encoding
        encoding = self.detect_csv_encoding()
        
        try:
            with open(self.csv_file_path, 'r', encoding=encoding, newline='') as csvfile:
                # Detectar delimitador
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                delimiter = ';' if ';' in sample else ','
                logger.info(f"Using delimiter: '{delimiter}'")
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                # Validar headers
                expected_headers = ['codigo_tema', 'area_evaluada', 'tema_principal', 'canal_sugerido', 'youtube_url']
                missing_headers = [h for h in expected_headers if h not in reader.fieldnames]
                if missing_headers:
                    raise ValueError(f"Headers faltantes en CSV: {missing_headers}")
                
                logger.info(f"Headers encontrados: {list(reader.fieldnames)}")
                
                # Procesar filas
                batch_count = 0
                for row_number, row in enumerate(reader, start=2):  # start=2 porque la línea 1 son headers
                    self.stats['total_rows'] += 1
                    
                    # Procesar fila
                    success = self.process_row(row, row_number)
                    
                    # Commit en lotes
                    if batch_count >= batch_size:
                        try:
                            self.session.commit()
                            logger.info(f"Committed batch ending at row {row_number}")
                            batch_count = 0
                        except Exception as e:
                            logger.error(f"Error committing batch: {e}")
                            self.session.rollback()
                    
                    batch_count += 1
                
                # Commit final
                try:
                    self.session.commit()
                    logger.info("Final commit completed")
                except Exception as e:
                    logger.error(f"Error in final commit: {e}")
                    self.session.rollback()
                
        except UnicodeDecodeError as e:
            logger.error(f"Error de codificación: {e}. Prueba con encoding diferente")
            raise
        except Exception as e:
            logger.error(f"Error leyendo archivo CSV: {e}")
            raise
        
        return self.stats
    
    def print_summary(self):
        """Imprime resumen de la carga"""
        logger.info("\n" + "="*50)
        logger.info("RESUMEN DE CARGA DEL CATÁLOGO YOUTUBE")
        logger.info("="*50)
        logger.info(f"Total filas procesadas: {self.stats['total_rows']}")
        logger.info(f"Filas válidas procesadas: {self.stats['processed']}")
        logger.info(f"Registros insertados: {self.stats['inserted']}")
        logger.info(f"Registros actualizados: {self.stats['updated']}")
        logger.info(f"Registros omitidos: {self.stats['skipped']}")
        logger.info(f"Errores: {self.stats['errors']}")
        logger.info("="*50)
        
        if self.stats['errors'] > 0:
            logger.warning(f"Se encontraron {self.stats['errors']} errores. Revisa el log para detalles.")

def create_tables():
    """Crea las tablas necesarias si no existen"""
    logger.info("Creando tablas de base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas/verificadas correctamente")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Carga masiva del catálogo YouTube')
    parser.add_argument(
        '--csv-file', 
        required=True,
        help='Ruta al archivo CSV del catálogo YouTube'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Tamaño del lote para commits (default: 50)'
    )
    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Crear tablas de base de datos antes de la carga'
    )
    
    args = parser.parse_args()
    
    try:
        if args.create_tables:
            create_tables()
        
        with YouTubeCatalogLoader(args.csv_file) as loader:
            stats = loader.load_catalog(batch_size=args.batch_size)
            loader.print_summary()
            
            # Exit code basado en resultados
            if stats['errors'] > stats['processed'] // 2:  # Más del 50% errores
                sys.exit(1)
            elif stats['errors'] > 0:
                sys.exit(2)  # Algunos errores pero mayoría exitosa
            else:
                sys.exit(0)  # Todo exitoso
            
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()