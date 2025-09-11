#!/usr/bin/env python3
"""
Generador SQL Offline para ICFES Leveling
Genera archivo SQL completo para carga posterior
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid
from datetime import datetime
import numpy as np

# Configuración de logging sin emojis para compatibilidad
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

class OfflineSQLGenerator:
    """Generador de SQL offline para carga posterior"""
    
    def __init__(self):
        self.data_dir = Path(r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions")
        self.excel_file = self.data_dir / "ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
        self.report_file = self.data_dir / "ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS_transformation_report.json"
        self.output_dir = Path(r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\seed_data")
        self.output_dir.mkdir(exist_ok=True)

    def load_transformation_report(self) -> Dict[str, Any]:
        """Carga el reporte de transformación de rutas"""
        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            logger.info(f"Reporte cargado: {report['stats']}")
            return report
        except Exception as e:
            logger.error(f"Error cargando reporte: {e}")
            raise

    def load_excel_data(self) -> pd.DataFrame:
        """Carga datos desde Excel con rutas actualizadas"""
        try:
            df = pd.read_excel(self.excel_file)
            logger.info(f"Excel cargado: {len(df)} filas")
            return df
        except Exception as e:
            logger.error(f"Error cargando Excel: {e}")
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
                    logger.warning(f"Pregunta en fila {index+2} tiene datos incompletos")
                    
            except Exception as e:
                logger.error(f"Error procesando fila {index+2}: {e}")
                continue
        
        logger.info(f"{len(questions)} preguntas válidas procesadas")
        return questions

    def escape_sql_string(self, value: str) -> str:
        """Escapa strings para SQL"""
        if not value:
            return "NULL"
        # Reemplazar comillas simples con dos comillas simples
        escaped = value.replace("'", "''")
        return f"'{escaped}'"

    def generate_sql_file(self, questions: List[QuestionData]) -> str:
        """Genera archivo SQL completo"""
        sql_lines = []
        
        # Header
        sql_lines.extend([
            "-- ICFES Leveling - Carga Completa de Preguntas",
            f"-- Generado: {datetime.now().isoformat()}",
            f"-- Total preguntas: {len(questions)}",
            "",
            "-- Crear tabla si no existe",
            """CREATE TABLE IF NOT EXISTS questions (
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
);""",
            "",
            "-- Índices para optimización",
            "CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);",
            "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);",
            "CREATE INDEX IF NOT EXISTS idx_questions_requires_image ON questions(requires_image);",
            "CREATE INDEX IF NOT EXISTS idx_questions_irt_difficulty ON questions(irt_difficulty);",
            "",
            "-- Limpiar datos existentes",
            "DELETE FROM questions;",
            "",
            "-- Insertar preguntas",
            "INSERT INTO questions (",
            "    id, subject, competence, component, difficulty,",
            "    question_text, option_a, option_b, option_c, option_d,",
            "    correct_answer, explanation, image_url, requires_image,",
            "    irt_difficulty, irt_discrimination, irt_guessing",
            ") VALUES"
        ])
        
        # Generar VALUES para cada pregunta
        for i, q in enumerate(questions):
            comma = "," if i < len(questions) - 1 else ";"
            
            values = f"""(
    '{q.id}',
    {self.escape_sql_string(q.subject)},
    {self.escape_sql_string(q.competence)},
    {self.escape_sql_string(q.component)},
    {self.escape_sql_string(q.difficulty)},
    {self.escape_sql_string(q.question_text)},
    {self.escape_sql_string(q.option_a)},
    {self.escape_sql_string(q.option_b)},
    {self.escape_sql_string(q.option_c)},
    {self.escape_sql_string(q.option_d)},
    {self.escape_sql_string(q.correct_answer)},
    {self.escape_sql_string(q.explanation)},
    {self.escape_sql_string(q.image_url) if q.image_url else "NULL"},
    {str(q.requires_image).lower()},
    {q.irt_difficulty},
    {q.irt_discrimination},
    {q.irt_guessing}
){comma}"""
            
            sql_lines.append(values)
        
        # Footer con estadísticas
        sql_lines.extend([
            "",
            "-- Verificar carga",
            "SELECT",
            "    COUNT(*) as total_questions,",
            "    COUNT(CASE WHEN requires_image THEN 1 END) as with_images,",
            "    COUNT(DISTINCT subject) as subjects,",
            "    AVG(irt_difficulty) as avg_difficulty",
            "FROM questions;",
            "",
            "-- Estadísticas por materia",
            "SELECT subject, COUNT(*) as count",
            "FROM questions",
            "GROUP BY subject",
            "ORDER BY count DESC;",
            "",
            f"-- COMPLETADO: {len(questions)} preguntas cargadas"
        ])
        
        return "\n".join(sql_lines)

    def generate_summary_report(self, questions: List[QuestionData]) -> Dict[str, Any]:
        """Genera reporte resumen de la carga"""
        # Contar por materia
        subject_counts = {}
        difficulty_counts = {}
        image_counts = {'with_image': 0, 'without_image': 0}
        
        for q in questions:
            # Por materia
            subject_counts[q.subject] = subject_counts.get(q.subject, 0) + 1
            
            # Por dificultad
            difficulty_counts[q.difficulty] = difficulty_counts.get(q.difficulty, 0) + 1
            
            # Por imagen
            if q.requires_image:
                image_counts['with_image'] += 1
            else:
                image_counts['without_image'] += 1
        
        # Calcular promedios IRT
        irt_difficulties = [q.irt_difficulty for q in questions]
        irt_discriminations = [q.irt_discrimination for q in questions]
        irt_guessings = [q.irt_guessing for q in questions]
        
        return {
            'total_questions': len(questions),
            'by_subject': subject_counts,
            'by_difficulty': difficulty_counts,
            'by_image': image_counts,
            'irt_averages': {
                'difficulty': round(np.mean(irt_difficulties), 3),
                'discrimination': round(np.mean(irt_discriminations), 3),
                'guessing': round(np.mean(irt_guessings), 3)
            },
            'generated_at': datetime.now().isoformat()
        }

    def run_offline_generation(self) -> Dict[str, Any]:
        """Ejecuta generación offline completa"""
        start_time = datetime.now()
        
        try:
            logger.info("Iniciando generación SQL offline")
            
            # 1. Cargar datos
            report = self.load_transformation_report()
            df = self.load_excel_data()
            
            # 2. Procesar y limpiar
            questions = self.clean_and_validate_data(df, report)
            
            # 3. Generar SQL
            sql_content = self.generate_sql_file(questions)
            
            # 4. Escribir archivo SQL
            sql_file_path = self.output_dir / "complete_questions_load.sql"
            with open(sql_file_path, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            
            # 5. Generar reporte resumen
            summary = self.generate_summary_report(questions)
            
            # 6. Escribir reporte JSON
            report_file_path = self.output_dir / "load_summary_report.json"
            with open(report_file_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            final_result = {
                'status': 'SUCCESS',
                'duration_seconds': round(duration, 2),
                'sql_file': str(sql_file_path),
                'report_file': str(report_file_path),
                'questions_processed': len(questions),
                'summary': summary
            }
            
            logger.info(f"Generación completada: {len(questions)} preguntas en {duration:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Error en generación: {e}")
            raise

def main():
    """Función principal"""
    generator = OfflineSQLGenerator()
    
    try:
        result = generator.run_offline_generation()
        
        # Imprimir resumen final
        print("\n" + "="*60)
        print("RESUMEN DE GENERACIÓN SQL OFFLINE")
        print("="*60)
        print(f"Estado: {result['status']}")
        print(f"Duración: {result['duration_seconds']}s")
        print(f"Preguntas procesadas: {result['questions_processed']}")
        print(f"Archivo SQL: {result['sql_file']}")
        print(f"Reporte: {result['report_file']}")
        
        summary = result['summary']
        print(f"\nTotal preguntas: {summary['total_questions']}")
        
        print("\nPor Materia:")
        for subject, count in summary['by_subject'].items():
            print(f"   - {subject}: {count}")
        
        print("\nPor Dificultad:")
        for difficulty, count in summary['by_difficulty'].items():
            print(f"   - {difficulty}: {count}")
        
        print(f"\nCon imágenes: {summary['by_image']['with_image']}")
        print(f"Sin imágenes: {summary['by_image']['without_image']}")
        
        print("\nParámetros IRT Promedio:")
        irt = summary['irt_averages']
        print(f"   - Dificultad (b): {irt['difficulty']}")
        print(f"   - Discriminación (a): {irt['discrimination']}")
        print(f"   - Adivinanza (c): {irt['guessing']}")
        
        print("="*60)
        print("ARCHIVO SQL LISTO PARA CARGA EN POSTGRESQL")
        print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(exit_code := main())