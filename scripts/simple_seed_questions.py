#!/usr/bin/env python3
"""
Simple Seed Questions Script - ICFES Leveling System
Uses raw SQL to avoid SQLAlchemy metadata conflicts.
"""

import argparse
import pandas as pd
import asyncio
import asyncpg
import hashlib
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json
import sys
import os

# Import path transformer
try:
    from path_transformer import PathTransformer
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from path_transformer import PathTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleQuestionSeeder:
    """Simple question seeder using raw SQL queries"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
        self.path_transformer = PathTransformer()
        
        # Subject mapping - IMPORTANTE: El Excel usa "Lectura Crítica" pero la BD tiene "Lenguaje"
        self.subject_mapping = {
            'matematicas': 'Matemáticas',
            'ciencias naturales': 'Ciencias Naturales',  
            'ciencias sociales': 'Ciencias Sociales',
            'lectura critica': 'Lenguaje',  # Excel -> DB mapping
            'lectura crítica': 'Lenguaje',  # Excel -> DB mapping
            'lenguaje': 'Lenguaje',
            'español': 'Lenguaje',
            'ingles': 'Inglés',
            'inglés': 'Inglés'
        }
        
        self.stats = {
            'questions_processed': 0,
            'questions_loaded': 0,
            'subjects_created': 0,
            'topics_created': 0,
            'images_validated': 0,
            'images_missing': 0
        }
    
    def normalize_text(self, text: Any) -> str:
        """Normalize text input"""
        if pd.isna(text) or text is None:
            return ""
        return str(text).strip()
    
    def generate_key(self, statement: str, subject: str) -> str:
        """Generate unique key for question"""
        content = f"{statement}:{subject}".encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    def map_subject_name(self, subject_raw: str) -> str:
        """Map Excel subject name to system name"""
        if not subject_raw:
            return "Matemáticas"
        subject_clean = self.normalize_text(subject_raw).lower()
        return self.subject_mapping.get(subject_clean, subject_raw.title())
    
    def validate_image_path(self, image_path: str) -> tuple[str, bool]:
        """Validate and transform image path"""
        if not image_path or pd.isna(image_path):
            return "", False
        
        relative_path, exists, _ = self.path_transformer.transform_path_to_relative(image_path)
        
        if exists:
            self.stats['images_validated'] += 1
        else:
            self.stats['images_missing'] += 1
        
        return relative_path, exists
    
    async def ensure_subject_exists(self, conn, subject_name: str) -> str:
        """Ensure subject exists in database, return subject ID"""
        # Check if exists
        result = await conn.fetchrow(
            "SELECT id FROM subjects WHERE name = $1", subject_name
        )
        
        if result:
            return str(result['id'])
        
        # Create new subject
        subject_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO subjects (id, name, description, is_active, created_at, updated_at) 
               VALUES ($1, $2, $3, $4, NOW(), NOW())""",
            subject_id, subject_name, f"Materia {subject_name} del ICFES", True
        )
        
        self.stats['subjects_created'] += 1
        logger.info(f"Subject created: {subject_name}")
        return subject_id
    
    async def ensure_topic_exists(self, conn, subject_id: str, topic_name: str, competence: str = "") -> str:
        """Ensure topic exists in database, return topic ID"""
        # Check if exists
        result = await conn.fetchrow(
            "SELECT id FROM topics WHERE subject_id = $1 AND name = $2", 
            subject_id, topic_name
        )
        
        if result:
            return str(result['id'])
        
        # Create new topic
        topic_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO topics (id, subject_id, name, description, competence, is_active, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())""",
            topic_id, subject_id, topic_name, f"Tema: {topic_name}", competence, True
        )
        
        self.stats['topics_created'] += 1
        logger.info(f"Topic created: {topic_name}")
        return topic_id
    
    async def process_question_row(self, conn, row: Dict[str, Any], subject_cache: Dict, topic_cache: Dict) -> bool:
        """Process a single question row"""
        try:
            self.stats['questions_processed'] += 1
            
            # Extract basic data
            subject_name = self.map_subject_name(row.get('Área_Evaluada', ''))
            topic_name = self.normalize_text(row.get('Tema_Específico', 'General'))
            competence = self.normalize_text(row.get('Competencia', ''))
            statement = self.normalize_text(row.get('Pregunta', ''))
            
            if not statement:
                return False
            
            # Get or create subject
            if subject_name not in subject_cache:
                subject_cache[subject_name] = await self.ensure_subject_exists(conn, subject_name)
            subject_id = subject_cache[subject_name]
            
            # Get or create topic  
            topic_key = (subject_id, topic_name)
            if topic_key not in topic_cache:
                topic_cache[topic_key] = await self.ensure_topic_exists(conn, subject_id, topic_name, competence)
            topic_id = topic_cache[topic_key]
            
            # Generate natural key
            natural_key = self.generate_key(statement, subject_name)
            
            # Check if question already exists
            existing = await conn.fetchrow(
                "SELECT id FROM questions WHERE natural_key = $1", natural_key
            )
            
            if existing:
                return False  # Skip duplicate
            
            # Process images
            image_data = {}
            image_columns = ['Imagen_Pregunta_URL', 'Imagen_Opcion_A_URL', 'Imagen_Opcion_B_URL', 
                           'Imagen_Opcion_C_URL', 'Imagen_Opcion_D_URL', 'Imagen_Contexto_Comp']
            
            for img_col in image_columns:
                if img_col in row and row[img_col]:
                    clean_path, exists = self.validate_image_path(row[img_col])
                    if clean_path:
                        image_data[img_col] = clean_path
            
            # Extract answer options
            options = []
            for opt in ['A', 'B', 'C', 'D']:
                option_text = self.normalize_text(row.get(f'Opción_{opt}', ''))
                if option_text:
                    image_key = f'Imagen_Opcion_{opt}_URL'
                    image_url = image_data.get(image_key, '')
                    options.append({
                        'key': opt,
                        'text': option_text,
                        'image_url': image_url
                    })
            
            # Get correct answer and IRT parameters
            correct_answer = self.normalize_text(row.get('Respuesta_Correcta', 'A'))
            irt_a = float(row.get('Parámetro_A', 1.0)) if pd.notna(row.get('Parámetro_A')) else 1.0
            irt_b = float(row.get('Parámetro_B', 0.0)) if pd.notna(row.get('Parámetro_B')) else 0.0  
            irt_c = float(row.get('Parámetro_C', 0.25)) if pd.notna(row.get('Parámetro_C')) else 0.25
            
            # Insert question
            question_id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO questions (
                    id, natural_key, subject_id, topic_id, statement, 
                    options, correct_answer, difficulty, 
                    image_url, context_image_url,
                    irt_discrimination, irt_difficulty, irt_guessing,
                    is_active, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW()
                )""",
                question_id, natural_key, subject_id, topic_id, statement,
                json.dumps(options), correct_answer, 'mid',
                image_data.get('Imagen_Pregunta_URL', ''),
                image_data.get('Imagen_Contexto_Comp', ''),
                irt_a, irt_b, irt_c, True
            )
            
            self.stats['questions_loaded'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing question row: {e}")
            return False
    
    async def load_questions_from_excel(self, excel_path: str, with_images: bool = False, batch_size: int = 500):
        """Load questions from Excel file"""
        logger.info(f"Starting question load from: {excel_path}")
        logger.info(f"Batch size: {batch_size}, With images: {with_images}")
        
        # Read Excel
        df = pd.read_excel(excel_path)
        logger.info(f"Excel loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Filter rows with images if requested
        if with_images:
            image_columns = ['Imagen_Pregunta_URL', 'Imagen_Opcion_A_URL', 'Imagen_Opcion_B_URL', 
                           'Imagen_Opcion_C_URL', 'Imagen_Opcion_D_URL', 'Imagen_Contexto_Comp']
            
            has_images = df[image_columns].notna().any(axis=1)
            df = df[has_images]
            logger.info(f"Filtered to questions with images: {len(df)} rows")
        
        # Connect to database
        conn = await asyncpg.connect(self.database_url)
        
        try:
            subject_cache = {}
            topic_cache = {}
            
            # Process in batches
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")
                
                for idx, row in batch.iterrows():
                    await self.process_question_row(conn, row.to_dict(), subject_cache, topic_cache)
                
                # Log progress
                logger.info(f"Processed {min(i+batch_size, len(df))}/{len(df)} questions")
        
        finally:
            await conn.close()
        
        # Generate final report
        report = {
            'stats': self.stats,
            'excel_info': {
                'total_rows': len(df),
                'processed_rows': self.stats['questions_processed']
            },
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        return report

async def main():
    parser = argparse.ArgumentParser(description="Simple Question Seeder for ICFES")
    parser.add_argument('--excel', required=True, help='Path to Excel file')
    parser.add_argument('--with-images', action='store_true', help='Only load questions with images')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size for processing')
    parser.add_argument('--database-url', help='Database URL')
    
    args = parser.parse_args()
    
    if not Path(args.excel).exists():
        logger.error(f"Excel file not found: {args.excel}")
        return 1
    
    seeder = SimpleQuestionSeeder(args.database_url)
    
    try:
        report = await seeder.load_questions_from_excel(
            args.excel, 
            with_images=args.with_images,
            batch_size=args.batch_size
        )
        
        # Print summary
        print("\n" + "="*50)
        print("QUESTION LOADING COMPLETED")
        print("="*50)
        print(f"Questions processed: {report['stats']['questions_processed']}")
        print(f"Questions loaded: {report['stats']['questions_loaded']}")
        print(f"Subjects created: {report['stats']['subjects_created']}")
        print(f"Topics created: {report['stats']['topics_created']}")
        print(f"Images validated: {report['stats']['images_validated']}")
        print(f"Images missing: {report['stats']['images_missing']}")
        
        # Save report
        report_path = args.excel.replace('.xlsx', '_simple_load_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved: {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))