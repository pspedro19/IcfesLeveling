#!/usr/bin/env python3
"""
Sistema Final de Carga de Datos ICFES Leveling
Carga completa de las ~2733 preguntas procesadas con rutas limpias
"""

import asyncio
import asyncpg
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid
from datetime import datetime
import numpy as np

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class QuestionData:
    """Estructura para datos de pregunta"""
    id: str
    subject: str
    competence: str
    component: str
    difficulty: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str
    image_url: Optional[str]
    requires_image: bool
    irt_difficulty: float
    irt_discrimination: float
    irt_guessing: float

class FinalDataLoader:
    """Cargador final de datos con todas las preguntas procesadas"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'icfes_leveling',
            'user': 'gameplay',
            'password': 'gameplay123'
        }
        self.data_dir = Path(r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions")
        self.excel_file = self.data_dir / "ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
        self.report_file = self.data_dir / "ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS_transformation_report.json"
        
    async def connect_database(self) -> asyncpg.Connection:
        """Conecta a la base de datos PostgreSQL"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            logger.info("✅ Conexión exitosa a PostgreSQL")
            return conn
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise

    def load_transformation_report(self) -> Dict[str, Any]:
        """Carga el reporte de transformación de rutas"""
        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            logger.info(f"✅ Reporte cargado: {report['stats']}")
            return report
        except Exception as e:
            logger.error(f"❌ Error cargando reporte: {e}")
            raise

    def load_excel_data(self) -> pd.DataFrame:
        """Carga datos desde Excel con rutas actualizadas"""
        try:
            df = pd.read_excel(self.excel_file)
            logger.info(f"✅ Excel cargado: {len(df)} filas")
            return df
        except Exception as e:
            logger.error(f"❌ Error cargando Excel: {e}")
            raise

    def generate_irt_parameters(self, difficulty: str) -> tuple[float, float, float]:
        """Genera parámetros IRT 3PL basados en dificultad"""
        difficulty_map = {
            'Muy Fácil': (-2.0, 0.8, 0.15),
            'Fácil': (-1.0, 1.0, 0.18),
            'Medio': (0.0, 1.2, 0.20),
            'Difícil': (1.0, 1.4, 0.22),
            'Muy Difícil': (2.0, 1.6, 0.25)
        }
        
        base_params = difficulty_map.get(difficulty, (0.0, 1.2, 0.20))
        
        # Agregar variación aleatoria
        b_param = base_params[0] + np.random.normal(0, 0.3)
        a_param = max(0.5, base_params[1] + np.random.normal(0, 0.2))
        c_param = max(0.1, min(0.3, base_params[2] + np.random.normal(0, 0.05)))
        
        return round(b_param, 3), round(a_param, 3), round(c_param, 3)

    def clean_and_validate_data(self, df: pd.DataFrame, report: Dict[str, Any]) -> List[QuestionData]:
        """Limpia y valida datos para carga final"""
        questions = []
        
        for index, row in df.iterrows():
            try:
                # Generar ID único
                question_id = str(uuid.uuid4())
                
                # Mapear materias
                subject_map = {
                    'Matematicas': 'Matemáticas',
                    'Ciencias Naturales': 'Ciencias Naturales',
                    'Lectura Critica': 'Lectura Crítica',
                    'Ciencias Sociales': 'Ciencias Sociales',
                    'Ingles': 'Inglés'
                }
                
                subject = subject_map.get(str(row.get('Materia', '')), 'General')
                
                # Procesar imagen
                image_url = None
                requires_image = False
                
                if pd.notna(row.get('Requiere_Imagen')) and str(row.get('Requiere_Imagen')).strip().lower() == 'true':
                    requires_image = True
                    # Buscar ruta transformada en el reporte
                    if str(row.get('Ruta_Imagen_Pregunta', '')).strip():
                        image_url = str(row['Ruta_Imagen_Pregunta']).replace('\\', '/')
                
                # Generar parámetros IRT
                difficulty_level = str(row.get('Nivel_Dificultad', 'Medio'))
                b_param, a_param, c_param = self.generate_irt_parameters(difficulty_level)
                
                question = QuestionData(
                    id=question_id,
                    subject=subject,
                    competence=str(row.get('Competencia', 'General')),
                    component=str(row.get('Componente', 'General')),
                    difficulty=difficulty_level,
                    question_text=str(row.get('Pregunta', '')).strip(),
                    option_a=str(row.get('Opcion_A', '')).strip(),
                    option_b=str(row.get('Opcion_B', '')).strip(),
                    option_c=str(row.get('Opcion_C', '')).strip(),
                    option_d=str(row.get('Opcion_D', '')).strip(),
                    correct_answer=str(row.get('Respuesta_Correcta', 'A')).strip().upper(),
                    explanation=str(row.get('Explicacion', '')).strip(),
                    image_url=image_url,
                    requires_image=requires_image,
                    irt_difficulty=b_param,
                    irt_discrimination=a_param,
                    irt_guessing=c_param
                )
                
                # Validar datos críticos
                if (question.question_text and 
                    question.option_a and question.option_b and 
                    question.option_c and question.option_d and 
                    question.correct_answer in ['A', 'B', 'C', 'D']):
                    questions.append(question)
                else:
                    logger.warning(f"⚠️ Pregunta en fila {index+2} tiene datos incompletos")
                    
            except Exception as e:
                logger.error(f"❌ Error procesando fila {index+2}: {e}")
                continue
        
        logger.info(f"✅ {len(questions)} preguntas válidas procesadas")
        return questions

    async def create_database_tables(self, conn: asyncpg.Connection):
        """Crea tablas necesarias en la base de datos"""
        
        # Tabla de preguntas
        create_questions_table = """
        CREATE TABLE IF NOT EXISTS questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            subject VARCHAR(100) NOT NULL,
            competence VARCHAR(200),
            component VARCHAR(200),
            difficulty VARCHAR(50),
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
            explanation TEXT,
            image_url TEXT,
            requires_image BOOLEAN DEFAULT false,
            irt_difficulty DECIMAL(6,3) DEFAULT 0.0,
            irt_discrimination DECIMAL(6,3) DEFAULT 1.0,
            irt_guessing DECIMAL(6,3) DEFAULT 0.2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Índices para optimización
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);",
            "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);",
            "CREATE INDEX IF NOT EXISTS idx_questions_requires_image ON questions(requires_image);",
            "CREATE INDEX IF NOT EXISTS idx_questions_irt_difficulty ON questions(irt_difficulty);",
        ]
        
        try:
            await conn.execute(create_questions_table)
            logger.info("✅ Tabla questions creada/verificada")
            
            for index_sql in create_indexes:
                await conn.execute(index_sql)
            logger.info("✅ Índices creados/verificados")
            
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            raise

    async def insert_questions_batch(self, conn: asyncpg.Connection, questions: List[QuestionData]):
        """Inserta preguntas en lotes para mejor performance"""
        batch_size = 100
        total_inserted = 0
        
        try:
            # Limpiar tabla existente
            await conn.execute("DELETE FROM questions;")
            logger.info("🧹 Tabla questions limpiada")
            
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i + batch_size]
                
                # Preparar datos para inserción
                insert_data = []
                for q in batch:
                    insert_data.append((
                        q.id, q.subject, q.competence, q.component, q.difficulty,
                        q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
                        q.correct_answer, q.explanation, q.image_url, q.requires_image,
                        q.irt_difficulty, q.irt_discrimination, q.irt_guessing
                    ))
                
                # Inserción en lote
                insert_query = """
                INSERT INTO questions (
                    id, subject, competence, component, difficulty,
                    question_text, option_a, option_b, option_c, option_d,
                    correct_answer, explanation, image_url, requires_image,
                    irt_difficulty, irt_discrimination, irt_guessing
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """
                
                await conn.executemany(insert_query, insert_data)
                total_inserted += len(batch)
                logger.info(f"📥 Insertadas {total_inserted}/{len(questions)} preguntas")
        
        except Exception as e:
            logger.error(f"❌ Error insertando preguntas: {e}")
            raise
        
        return total_inserted

    async def verify_data_integrity(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """Verifica integridad de datos cargados"""
        try:
            # Estadísticas generales
            total_count = await conn.fetchval("SELECT COUNT(*) FROM questions")
            
            # Por materia
            subject_stats = await conn.fetch("""
                SELECT subject, COUNT(*) as count 
                FROM questions 
                GROUP BY subject 
                ORDER BY count DESC
            """)
            
            # Por dificultad
            difficulty_stats = await conn.fetch("""
                SELECT difficulty, COUNT(*) as count 
                FROM questions 
                GROUP BY difficulty 
                ORDER BY count DESC
            """)
            
            # Con imágenes
            image_stats = await conn.fetch("""
                SELECT requires_image, COUNT(*) as count 
                FROM questions 
                GROUP BY requires_image
            """)
            
            # Parámetros IRT promedio
            irt_stats = await conn.fetchrow("""
                SELECT 
                    AVG(irt_difficulty) as avg_difficulty,
                    AVG(irt_discrimination) as avg_discrimination,
                    AVG(irt_guessing) as avg_guessing
                FROM questions
            """)
            
            integrity_report = {
                'total_questions': total_count,
                'by_subject': [{'subject': row['subject'], 'count': row['count']} for row in subject_stats],
                'by_difficulty': [{'difficulty': row['difficulty'], 'count': row['count']} for row in difficulty_stats],
                'by_image': [{'has_image': row['requires_image'], 'count': row['count']} for row in image_stats],
                'irt_averages': {
                    'difficulty': round(float(irt_stats['avg_difficulty']), 3),
                    'discrimination': round(float(irt_stats['avg_discrimination']), 3),
                    'guessing': round(float(irt_stats['avg_guessing']), 3)
                }
            }
            
            logger.info("✅ Verificación de integridad completada")
            return integrity_report
            
        except Exception as e:
            logger.error(f"❌ Error en verificación: {e}")
            raise

    async def run_complete_load(self) -> Dict[str, Any]:
        """Ejecuta carga completa de datos"""
        start_time = datetime.now()
        
        try:
            logger.info("🚀 Iniciando carga completa de datos ICFES")
            
            # 1. Cargar reporte y Excel
            report = self.load_transformation_report()
            df = self.load_excel_data()
            
            # 2. Procesar y limpiar datos
            questions = self.clean_and_validate_data(df, report)
            
            # 3. Conectar a base de datos
            conn = await self.connect_database()
            
            try:
                # 4. Crear tablas
                await self.create_database_tables(conn)
                
                # 5. Insertar preguntas
                inserted_count = await self.insert_questions_batch(conn, questions)
                
                # 6. Verificar integridad
                integrity_report = await self.verify_data_integrity(conn)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                final_report = {
                    'status': 'SUCCESS',
                    'duration_seconds': round(duration, 2),
                    'original_rows': len(df),
                    'valid_questions': len(questions),
                    'inserted_count': inserted_count,
                    'integrity': integrity_report,
                    'timestamp': end_time.isoformat()
                }
                
                logger.info(f"🎉 ¡Carga completa exitosa! {inserted_count} preguntas en {duration:.2f}s")
                return final_report
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"💥 Error en carga completa: {e}")
            raise

async def main():
    """Función principal"""
    loader = FinalDataLoader()
    
    try:
        result = await loader.run_complete_load()
        
        # Imprimir resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN FINAL DE CARGA")
        print("="*60)
        print(f"✅ Estado: {result['status']}")
        print(f"⏱️  Duración: {result['duration_seconds']}s")
        print(f"📈 Filas originales: {result['original_rows']}")
        print(f"✅ Preguntas válidas: {result['valid_questions']}")
        print(f"📥 Insertadas: {result['inserted_count']}")
        print(f"🗂️  Total en BD: {result['integrity']['total_questions']}")
        
        print("\n📚 Por Materia:")
        for item in result['integrity']['by_subject']:
            print(f"   • {item['subject']}: {item['count']}")
        
        print("\n🎯 Por Dificultad:")
        for item in result['integrity']['by_difficulty']:
            print(f"   • {item['difficulty']}: {item['count']}")
        
        print("\n🖼️  Con Imágenes:")
        for item in result['integrity']['by_image']:
            status = "Sí" if item['has_image'] else "No"
            print(f"   • {status}: {item['count']}")
        
        print("\n📊 Parámetros IRT Promedio:")
        irt = result['integrity']['irt_averages']
        print(f"   • Dificultad (b): {irt['difficulty']}")
        print(f"   • Discriminación (a): {irt['discrimination']}")
        print(f"   • Adivinanza (c): {irt['guessing']}")
        
        print("="*60)
        print("🎉 ¡SISTEMA ICFES LEVELING COMPLETAMENTE CARGADO!")
        print("="*60)
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)