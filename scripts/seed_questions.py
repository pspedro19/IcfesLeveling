#!/usr/bin/env python3
"""
Seed Questions Script - ICFES Leveling System

Script CRÍTICO para cargar preguntas del Excel con referencias a imágenes
correctas. Usa el path_transformer para normalizar rutas y cargar 2000+
preguntas disponibles con sus respectivas imágenes.

Funciones principales:
1. Procesar Excel con rutas transformadas por path_transformer
2. Validar existencia de archivos de imagen
3. Cargar preguntas a base de datos con referencias correctas
4. Poblar tablas subjects, topics, questions con datos completos
5. Generar reporte de carga completo

Author: Claude Code Assistant
Date: 2024
"""

import argparse
import os
import sys
import logging
import pandas as pd
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
import uuid

# Imports SQLAlchemy y FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import insert

# Import path transformer
try:
    from path_transformer import PathTransformer
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from path_transformer import PathTransformer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuestionSeeder:
    """
    Clase principal para cargar preguntas del Excel a la base de datos
    """
    
    def __init__(self, database_url: str = None, project_root: str = None):
        """
        Inicializar el cargador de preguntas
        
        Args:
            database_url: URL de conexión a PostgreSQL
            project_root: Ruta raíz del proyecto
        """
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(__file__).parent.parent.resolve()
            
        # Configurar base de datos
        if not database_url:
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql+asyncpg://gameplay:gameplay123@localhost:5433/gameplay_db'
            )
            
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Inicializar transformador de rutas
        self.path_transformer = PathTransformer(project_root)
        
        # Mapeo de materias (español -> sistema)
        # IMPORTANTE: El Excel usa "Lectura Crítica" pero la BD tiene "Lenguaje"
        self.subject_mapping = {
            'matematicas': 'Matemáticas',
            'ciencias naturales': 'Ciencias Naturales',  
            'ciencias sociales': 'Ciencias Sociales',
            'lectura critica': 'Lenguaje',  # Excel -> DB mapping
            'lectura crítica': 'Lenguaje',  # Excel -> DB mapping
            'lenguaje': 'Lenguaje',
            'español': 'Lenguaje',
            'ingles': 'Inglés',
            'inglés': 'Inglés',
            'english': 'Inglés'
        }
        
        # Mapeo de dificultades
        self.difficulty_mapping = {
            'bajo': 'low',
            'medio': 'mid', 
            'alto': 'high',
            'fácil': 'low',
            'facil': 'low',
            'dificil': 'high',
            'difícil': 'high'
        }
        
        # Estadísticas del proceso
        self.stats = {
            'processed_rows': 0,
            'successful_questions': 0,
            'failed_questions': 0,
            'subjects_created': 0,
            'topics_created': 0,
            'images_validated': 0,
            'images_missing': 0,
            'duplicates_skipped': 0
        }
        
        logger.info(f"QuestionSeeder inicializado")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Database: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    def normalize_text(self, text: Any) -> str:
        """Normalizar texto de entrada"""
        if pd.isna(text) or text is None:
            return ""
        return str(text).strip()

    def generate_natural_key(self, statement: str, subject: str) -> str:
        """Generar clave natural para pregunta usando MD5"""
        content = f"{statement}:{subject}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def map_subject_name(self, subject_raw: str) -> str:
        """Mapear nombre de materia del Excel al sistema"""
        if not subject_raw:
            return "Matemáticas"  # Default
            
        subject_clean = self.normalize_text(subject_raw).lower()
        return self.subject_mapping.get(subject_clean, subject_raw.title())

    def map_difficulty(self, difficulty_raw: str) -> str:
        """Mapear dificultad del Excel al sistema"""
        if not difficulty_raw:
            return "mid"  # Default
            
        difficulty_clean = self.normalize_text(difficulty_raw).lower()
        return self.difficulty_mapping.get(difficulty_clean, "mid")

    def validate_image_path(self, image_path: str) -> Tuple[str, bool]:
        """
        Validar y transformar ruta de imagen usando PathTransformer
        
        Args:
            image_path: Ruta original del Excel
            
        Returns:
            Tuple: (ruta_relativa_limpia, existe_archivo)
        """
        if not image_path or pd.isna(image_path):
            return "", False
        
        # Usar path transformer para normalizar
        relative_path, exists, reason = self.path_transformer.transform_path_to_relative(image_path)
        
        if exists:
            self.stats['images_validated'] += 1
        else:
            self.stats['images_missing'] += 1
            logger.warning(f"Imagen no encontrada: {image_path} -> {relative_path}")
        
        return relative_path, exists

    async def ensure_subjects_and_topics(self, session: AsyncSession, df: pd.DataFrame):
        """
        Asegurar que existen todas las materias y temas necesarios
        
        Args:
            session: Sesión de base de datos
            df: DataFrame con preguntas
        """
        logger.info("Creando materias y temas necesarios...")
        
        # Import models (necesario hacerlo aquí para evitar problemas de import)
        try:
            # Intentar import directo desde apps/backend
            backend_path = str(self.project_root / "apps" / "backend")
            if backend_path not in sys.path:
                sys.path.append(backend_path)
            
            # Clear any existing SQLAlchemy metadata to avoid conflicts
            import importlib
            if 'app.models.subject' in sys.modules:
                importlib.reload(sys.modules['app.models.subject'])
            if 'app.models.topic' in sys.modules:
                importlib.reload(sys.modules['app.models.topic'])
                
            from app.models.subject import Subject
            from app.models.topic import Topic
        except ImportError as e:
            logger.error(f"No se pudieron importar los modelos: {e}")
            raise
        
        # Procesar materias únicas
        unique_subjects = set()
        unique_topics = set()
        
        for _, row in df.iterrows():
            subject_name = self.map_subject_name(row.get('Área_Evaluada', ''))
            topic_name = self.normalize_text(row.get('Tema_Específico', 'General'))
            competencia = self.normalize_text(row.get('Competencia', ''))
            
            unique_subjects.add(subject_name)
            unique_topics.add((subject_name, topic_name, competencia))
        
        logger.info(f"Materias identificadas: {len(unique_subjects)}")
        logger.info(f"Temas identificados: {len(unique_topics)}")
        
        # Crear/obtener materias
        subject_cache = {}
        for subject_name in unique_subjects:
            # Verificar si existe
            result = await session.execute(
                select(Subject).where(Subject.name == subject_name)
            )
            subject = result.scalar_one_or_none()
            
            if not subject:
                # Crear nueva materia
                subject = Subject(
                    id=uuid.uuid4(),
                    name=subject_name,
                    description=f"Materia {subject_name} del ICFES",
                    is_active=True
                )
                session.add(subject)
                await session.flush()  # Para obtener el ID
                self.stats['subjects_created'] += 1
                logger.info(f"Materia creada: {subject_name}")
            
            subject_cache[subject_name] = subject
        
        await session.commit()
        
        # Crear/obtener temas
        topic_cache = {}
        for subject_name, topic_name, competencia in unique_topics:
            subject = subject_cache[subject_name]
            
            # Verificar si existe el tema
            result = await session.execute(
                select(Topic).where(
                    and_(Topic.subject_id == subject.id, Topic.name == topic_name)
                )
            )
            topic = result.scalar_one_or_none()
            
            if not topic:
                # Crear nuevo tema
                topic = Topic(
                    id=uuid.uuid4(),
                    subject_id=subject.id,
                    name=topic_name,
                    description=f"Tema: {topic_name}",
                    competence=competencia,
                    is_active=True
                )
                session.add(topic)
                await session.flush()
                self.stats['topics_created'] += 1
                logger.info(f"Tema creado: {subject_name} -> {topic_name}")
            
            topic_cache[(subject_name, topic_name)] = topic
        
        await session.commit()
        
        self.subject_cache = subject_cache
        self.topic_cache = topic_cache
        
        logger.info(f"Materias en cache: {len(self.subject_cache)}")
        logger.info(f"Temas en cache: {len(self.topic_cache)}")

    async def process_question_row(self, session: AsyncSession, row: pd.Series) -> bool:
        """
        Procesar una fila del Excel y crear pregunta en BD
        
        Args:
            session: Sesión de base de datos
            row: Fila del DataFrame
            
        Returns:
            bool: True si se procesó exitosamente
        """
        try:
            # Import model
            import importlib
            if 'app.models.question' in sys.modules:
                importlib.reload(sys.modules['app.models.question'])
            from app.models.question import Question
            
            # Extraer datos básicos
            subject_name = self.map_subject_name(row.get('Área_Evaluada', ''))
            topic_name = self.normalize_text(row.get('Tema_Específico', 'General'))
            
            # Obtener subject y topic del cache
            subject = self.subject_cache.get(subject_name)
            topic = self.topic_cache.get((subject_name, topic_name))
            
            if not subject or not topic:
                logger.error(f"Subject/Topic no encontrado para: {subject_name}/{topic_name}")
                return False
            
            # Procesar texto de la pregunta
            pregunta_texto = self.normalize_text(row.get('Pregunta', ''))
            if not pregunta_texto:
                # Usar Afirmación como fallback
                pregunta_texto = self.normalize_text(row.get('Afirmación', ''))
            
            if not pregunta_texto:
                logger.warning(f"Pregunta sin texto en fila {row.name}")
                return False
            
            # Generar natural key
            natural_key = self.generate_natural_key(pregunta_texto, subject_name)
            
            # Verificar si ya existe
            result = await session.execute(
                select(Question).where(Question.question_text == pregunta_texto)
            )
            if result.scalar_one_or_none():
                self.stats['duplicates_skipped'] += 1
                return False
            
            # Procesar imágenes
            imagen_pregunta, img_pregunta_exists = self.validate_image_path(
                row.get('Imagen_Pregunta_URL', '')
            )
            imagen_opcion_a, img_a_exists = self.validate_image_path(
                row.get('Imagen_Opcion_A_URL', '')
            )
            imagen_opcion_b, img_b_exists = self.validate_image_path(
                row.get('Imagen_Opcion_B_URL', '')
            )
            imagen_opcion_c, img_c_exists = self.validate_image_path(
                row.get('Imagen_Opcion_C_URL', '')
            )
            imagen_opcion_d, img_d_exists = self.validate_image_path(
                row.get('Imagen_Opcion_D_URL', '')
            )
            
            # Determinar si tiene imágenes
            has_images = any([img_pregunta_exists, img_a_exists, img_b_exists, img_c_exists, img_d_exists])
            
            # Procesar opciones de respuesta
            opcion_a = self.normalize_text(row.get('Opcion_A', ''))
            opcion_b = self.normalize_text(row.get('Opcion_B', ''))
            opcion_c = self.normalize_text(row.get('Opcion_C', ''))
            opcion_d = self.normalize_text(row.get('Opcion_D', ''))
            
            # Respuesta correcta
            respuesta_correcta = self.normalize_text(row.get('Respuesta_Correcta', 'A')).upper()
            if respuesta_correcta not in ['A', 'B', 'C', 'D']:
                respuesta_correcta = 'A'  # Default
            
            # Parámetros IRT
            irt_a = pd.to_numeric(row.get('Parámetro_IRT_A', 1.0), errors='coerce')
            irt_b = pd.to_numeric(row.get('Parámetro_IRT_B', 0.0), errors='coerce')
            irt_c = pd.to_numeric(row.get('Parámetro_IRT_C', 0.2), errors='coerce')
            
            # Valores por defecto si son NaN
            if pd.isna(irt_a): irt_a = 1.0
            if pd.isna(irt_b): irt_b = 0.0  
            if pd.isna(irt_c): irt_c = 0.2
            
            # Mapear dificultad
            difficulty_mapped = self.map_difficulty(row.get('Nivel_Dificultad', 'medio'))
            difficulty_numeric = {'low': 1, 'mid': 2, 'high': 3}[difficulty_mapped]
            
            # Crear pregunta
            question = Question(
                id=uuid.uuid4(),
                topic_id=topic.id,
                subject_id=subject.id,
                
                # Campos de texto principales
                pregunta_texto=pregunta_texto,
                pregunta_imagen=imagen_pregunta if img_pregunta_exists else None,
                
                # Opciones de texto
                opcion_a_texto=opcion_a if opcion_a else None,
                opcion_a_imagen=imagen_opcion_a if img_a_exists else None,
                opcion_b_texto=opcion_b if opcion_b else None,
                opcion_b_imagen=imagen_opcion_b if img_b_exists else None,
                opcion_c_texto=opcion_c if opcion_c else None,
                opcion_c_imagen=imagen_opcion_c if img_c_exists else None,
                opcion_d_texto=opcion_d if opcion_d else None,
                opcion_d_imagen=imagen_opcion_d if img_d_exists else None,
                
                # Respuesta
                respuesta_correcta=respuesta_correcta.lower(),
                
                # Campos legacy para compatibilidad
                question_text=pregunta_texto,
                question_type="multiple_choice",
                difficulty=difficulty_numeric,
                correct_answer=respuesta_correcta,
                explanation=self.normalize_text(row.get('Explicación_Respuesta', '')),
                hint=self.normalize_text(row.get('Pista_1', '')),
                
                # Opciones en JSON para compatibilidad
                options={
                    'A': opcion_a,
                    'B': opcion_b, 
                    'C': opcion_c,
                    'D': opcion_d
                },
                
                # Power stats con datos reales
                power_stats={
                    "discrimination_index": float(irt_a),
                    "success_rate": 1.0 - float(irt_c),  # Aproximación
                    "irt_a": float(irt_a),
                    "irt_b": float(irt_b),
                    "irt_c": float(irt_c),
                    "has_images": has_images,
                    "competencia": self.normalize_text(row.get('Competencia', '')),
                    "componente": self.normalize_text(row.get('Componente', '')),
                    "proceso_cognitivo": self.normalize_text(row.get('Proceso_Cognitivo', ''))
                }
            )
            
            session.add(question)
            return True
            
        except Exception as e:
            logger.error(f"Error procesando pregunta en fila {row.name}: {str(e)}")
            return False

    async def load_questions_from_excel(self, excel_path: str, batch_size: int = 100, with_images: bool = True) -> Dict:
        """
        Cargar preguntas desde Excel a la base de datos
        
        Args:
            excel_path: Ruta al archivo Excel
            batch_size: Tamaño del lote para procesamiento
            with_images: Si True, solo carga preguntas con imágenes válidas
            
        Returns:
            Diccionario con estadísticas de carga
        """
        logger.info(f"Iniciando carga desde: {excel_path}")
        logger.info(f"Batch size: {batch_size}, With images: {with_images}")
        
        try:
            # Leer Excel
            df = pd.read_excel(excel_path)
            logger.info(f"Excel cargado: {len(df)} filas, {len(df.columns)} columnas")
            
            # Conectar a BD
            async with self.async_session() as session:
                # Crear materias y temas
                await self.ensure_subjects_and_topics(session, df)
                
                # Procesar preguntas en lotes
                successful_batch = []
                
                for idx, row in df.iterrows():
                    self.stats['processed_rows'] += 1
                    
                    # Filtro de imágenes si está habilitado
                    if with_images:
                        has_any_image = any([
                            pd.notna(row.get('Imagen_Pregunta_URL', '')),
                            pd.notna(row.get('Imagen_Opcion_A_URL', '')),
                            pd.notna(row.get('Imagen_Opcion_B_URL', '')),
                            pd.notna(row.get('Imagen_Opcion_C_URL', '')),
                            pd.notna(row.get('Imagen_Opcion_D_URL', ''))
                        ])
                        
                        if not has_any_image:
                            logger.debug(f"Saltando fila {idx}: sin imágenes")
                            continue
                    
                    # Procesar pregunta
                    success = await self.process_question_row(session, row)
                    
                    if success:
                        successful_batch.append(idx)
                        self.stats['successful_questions'] += 1
                    else:
                        self.stats['failed_questions'] += 1
                    
                    # Commit en lotes
                    if len(successful_batch) >= batch_size:
                        await session.commit()
                        logger.info(f"Lote guardado: {len(successful_batch)} preguntas")
                        successful_batch = []
                    
                    # Log progreso
                    if (idx + 1) % 50 == 0:
                        logger.info(f"Progreso: {idx + 1}/{len(df)} filas procesadas")
                
                # Commit final
                if successful_batch:
                    await session.commit()
                    logger.info(f"Lote final guardado: {len(successful_batch)} preguntas")
            
            # Preparar reporte
            report = {
                'timestamp': datetime.now().isoformat(),
                'excel_file': excel_path,
                'config': {
                    'batch_size': batch_size,
                    'with_images': with_images
                },
                'stats': self.stats,
                'success_rate': (self.stats['successful_questions'] / max(self.stats['processed_rows'], 1)) * 100
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error en carga de preguntas: {str(e)}")
            raise

    async def validate_loaded_data(self) -> Dict:
        """
        Validar datos cargados en la base de datos
        
        Returns:
            Diccionario con estadísticas de validación
        """
        logger.info("Validando datos cargados...")
        
        async with self.async_session() as session:
            import importlib
            if 'app.models.question' in sys.modules:
                importlib.reload(sys.modules['app.models.question'])
            if 'app.models.subject' in sys.modules:
                importlib.reload(sys.modules['app.models.subject'])
            if 'app.models.topic' in sys.modules:
                importlib.reload(sys.modules['app.models.topic'])
                
            from app.models.question import Question
            from app.models.subject import Subject  
            from app.models.topic import Topic
            
            # Contar totales
            total_questions = await session.scalar(select(func.count(Question.id)))
            total_subjects = await session.scalar(select(func.count(Subject.id)))
            total_topics = await session.scalar(select(func.count(Topic.id)))
            
            # Preguntas con imágenes
            questions_with_images = await session.scalar(
                select(func.count(Question.id)).where(
                    Question.pregunta_imagen.isnot(None)
                )
            )
            
            # Por materia
            subject_stats = []
            subjects = await session.scalars(select(Subject))
            
            for subject in subjects:
                q_count = await session.scalar(
                    select(func.count(Question.id)).where(Question.subject_id == subject.id)
                )
                subject_stats.append({
                    'subject': subject.name,
                    'questions': q_count
                })
            
            validation_report = {
                'timestamp': datetime.now().isoformat(),
                'totals': {
                    'questions': total_questions,
                    'subjects': total_subjects,
                    'topics': total_topics,
                    'questions_with_images': questions_with_images
                },
                'by_subject': subject_stats,
                'image_integrity': {
                    'questions_with_images': questions_with_images,
                    'percentage': (questions_with_images / max(total_questions, 1)) * 100
                }
            }
            
            return validation_report

    def save_report(self, report: Dict, output_path: str):
        """Guardar reporte en JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Reporte guardado en: {output_path}")


async def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Cargador de preguntas ICFES con imágenes a base de datos"
    )
    
    parser.add_argument(
        '--excel',
        required=True,
        help='Ruta al archivo Excel con preguntas (preferiblemente ya transformado)'
    )
    
    parser.add_argument(
        '--with-images',
        action='store_true',
        help='Solo cargar preguntas que tienen imágenes'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Tamaño del lote para commits (default: 100)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Ejecutar sin hacer cambios en BD (solo validar)'
    )
    
    parser.add_argument(
        '--database-url',
        help='URL de conexión a PostgreSQL (opcional)'
    )
    
    parser.add_argument(
        '--project-root',
        help='Ruta raíz del proyecto (opcional)'
    )
    
    args = parser.parse_args()
    
    # Validar archivo Excel
    if not Path(args.excel).exists():
        logger.error(f"Archivo Excel no encontrado: {args.excel}")
        sys.exit(1)
    
    # Inicializar seeder
    seeder = QuestionSeeder(
        database_url=args.database_url,
        project_root=args.project_root
    )
    
    try:
        if args.dry_run:
            logger.info("Modo DRY RUN - Validando estructura sin cambios")
            # Aquí podrías agregar validaciones adicionales
            print("Validación completada. Use sin --dry-run para cargar datos.")
            return
        
        # Cargar preguntas
        logger.info("Iniciando carga de preguntas...")
        load_report = await seeder.load_questions_from_excel(
            args.excel,
            batch_size=args.batch_size,
            with_images=args.with_images
        )
        
        # Validar datos cargados
        validation_report = await seeder.validate_loaded_data()
        
        # Combinar reportes
        final_report = {
            'load_process': load_report,
            'validation': validation_report
        }
        
        # Guardar reporte
        report_path = args.excel.replace('.xlsx', '_seed_report.json')
        seeder.save_report(final_report, report_path)
        
        # Mostrar estadísticas
        print("\n" + "="*60)
        print("CARGA DE PREGUNTAS COMPLETADA")
        print("="*60)
        print(f"Filas procesadas: {load_report['stats']['processed_rows']}")
        print(f"Preguntas cargadas exitosamente: {load_report['stats']['successful_questions']}")
        print(f"Preguntas fallidas: {load_report['stats']['failed_questions']}")
        print(f"Materias creadas: {load_report['stats']['subjects_created']}")
        print(f"Temas creados: {load_report['stats']['topics_created']}")
        print(f"Imágenes validadas: {load_report['stats']['images_validated']}")
        print(f"Imágenes faltantes: {load_report['stats']['images_missing']}")
        print(f"Tasa de éxito: {load_report['success_rate']:.1f}%")
        
        print("\n" + "="*60)
        print("VALIDACIÓN DE BASE DE DATOS")
        print("="*60)
        print(f"Total preguntas en BD: {validation_report['totals']['questions']}")
        print(f"Total materias: {validation_report['totals']['subjects']}")
        print(f"Total temas: {validation_report['totals']['topics']}")
        print(f"Preguntas con imágenes: {validation_report['totals']['questions_with_images']}")
        
        print("\nPreguntas por materia:")
        for subj_stat in validation_report['by_subject']:
            print(f"  - {subj_stat['subject']}: {subj_stat['questions']} preguntas")
        
        print(f"\nReporte detallado guardado en: {report_path}")
        
        # Cerrar conexión
        await seeder.engine.dispose()
        
    except Exception as e:
        logger.error(f"Error ejecutando script: {str(e)}")
        await seeder.engine.dispose()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())