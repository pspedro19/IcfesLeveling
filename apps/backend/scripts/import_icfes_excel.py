#!/usr/bin/env python3
"""
Script para importar preguntas ICFES desde archivo Excel
Uso: python import_icfes_excel.py --file "ICFES2 (1).xlsx" --validate
"""

import pandas as pd
import uuid
import json
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
import argparse
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db, engine
from app.models.question import Question, Topic
from app.models.subject import Subject
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ICFESExcelImporter:
    def __init__(self, db: Session):
        self.db = db
        self.subjects_mapping = self._load_subjects_mapping()
        self.topics_mapping = self._load_topics_mapping()
        self.imported_questions = 0
        self.errors = []
        self.warnings = []

    def _load_subjects_mapping(self) -> Dict[str, str]:
        """Mapear áreas evaluadas a subjects existentes"""
        subjects = self.db.query(Subject).all()
        mapping = {}
        
        # Mapeo directo
        area_to_subject = {
            'Matemáticas': 'Matemáticas',
            'Lenguaje': 'Lenguaje', 
            'Ciencias Naturales': 'Ciencias Naturales',
            'Ciencias Sociales': 'Ciencias Sociales',
            'Inglés': 'Inglés',
            'Matematicas': 'Matemáticas',  # Variante sin tilde
            'Ciencias': 'Ciencias Naturales',  # Abreviado
            'Sociales': 'Ciencias Sociales',  # Abreviado
            'English': 'Inglés',  # Variante en inglés
        }
        
        for subject in subjects:
            for area, subject_name in area_to_subject.items():
                if subject.name == subject_name:
                    mapping[area] = str(subject.id)
        
        logger.info(f"Subjects mapping loaded: {mapping}")
        return mapping

    def _load_topics_mapping(self) -> Dict[str, str]:
        """Mapear temas específicos a topics existentes"""
        topics = self.db.query(Topic).all()
        mapping = {}
        
        # Mapeo de temas comunes
        tema_to_topic = {
            'Álgebra': 'Álgebra Básica',
            'Geometría': 'Geometría Euclidiana',
            'Cálculo': 'Cálculo Diferencial',
            'Probabilidad': 'Probabilidad',
            'Comprensión Lectora': 'Comprensión Lectora',
            'Gramática': 'Gramática',
            'Literatura': 'Literatura',
            'Física': 'Mecánica Clásica',
            'Química': 'Química Orgánica',
            'Biología': 'Biología Celular',
            'Historia': 'Historia',
            'Geografía': 'Geografía',
            'Filosofía': 'Filosofía',
        }
        
        for topic in topics:
            for tema, topic_name in tema_to_topic.items():
                if topic.name == topic_name:
                    mapping[tema] = str(topic.id)
        
        logger.info(f"Topics mapping loaded: {mapping}")
        return mapping

    def _create_or_get_topic(self, tema_especifico: str, subject_id: str) -> str:
        """Crear topic si no existe o obtener el existente"""
        if tema_especifico in self.topics_mapping:
            return self.topics_mapping[tema_especifico]
        
        # Crear nuevo topic
        topic = Topic(
            id=uuid.uuid4(),
            subject_id=subject_id,
            name=tema_especifico,
            description=f"Tema específico: {tema_especifico}",
            difficulty_level=1
        )
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        
        # Actualizar mapping
        self.topics_mapping[tema_especifico] = str(topic.id)
        logger.info(f"Created new topic: {tema_especifico}")
        
        return str(topic.id)

    def _map_difficulty(self, nivel_dificultad: str) -> int:
        """Mapear nivel de dificultad a escala 1-10"""
        if pd.isna(nivel_dificultad):
            return 5
        
        nivel = str(nivel_dificultad).lower().strip()
        
        # Mapeo de dificultad
        difficulty_mapping = {
            'bajo': 1,
            'baja': 1,
            'facil': 2,
            'fácil': 2,
            'basico': 3,
            'básico': 3,
            'medio': 5,
            'intermedio': 5,
            'alto': 8,
            'alta': 8,
            'dificil': 9,
            'difícil': 9,
            'muy alto': 10,
            'muy alta': 10,
        }
        
        # Buscar coincidencias parciales
        for key, value in difficulty_mapping.items():
            if key in nivel:
                return value
        
        # Si es numérico, convertir
        try:
            num_difficulty = int(nivel)
            if 1 <= num_difficulty <= 10:
                return num_difficulty
        except ValueError:
            pass
        
        # Por defecto
        return 5

    def _build_options(self, row: pd.Series) -> Dict[str, str]:
        """Construir objeto options desde las columnas A, B, C, D"""
        options = {}
        
        for option in ['A', 'B', 'C', 'D']:
            option_value = row.get(f'Opcion_{option}', '')
            if pd.notna(option_value) and str(option_value).strip():
                options[option] = str(option_value).strip()
        
        return options

    def _build_options_images(self, row: pd.Series) -> Optional[Dict[str, str]]:
        """Construir objeto options_images desde las URLs de imágenes"""
        options_images = {}
        has_images = False
        
        for option in ['A', 'B', 'C', 'D']:
            image_url = row.get(f'Imagen_Opcion_{option}_URL', '')
            if pd.notna(image_url) and str(image_url).strip():
                options_images[option] = str(image_url).strip()
                has_images = True
        
        return options_images if has_images else None

    def _build_power_stats(self, row: pd.Series) -> Dict[str, any]:
        """Construir objeto power_stats con metadatos"""
        power_stats = {
            "discrimination_index": 0.5,
            "success_rate": 0.6,
            "estimated_time": int(row.get('Tiempo_Estimado', 60)),
            "xp_reward": int(row.get('Puntos_XP', 10)),
            "original_id": str(row.get('ID_Pregunta', '')),
            "bank_origin": str(row.get('Banco_Origen', '')),
            "question_type": str(row.get('Tipo_Pregunta', 'multiple_choice')),
            "cognitive_process": str(row.get('Proceso_Cognitivo', '')),
            "knowledge_type": str(row.get('Tipo_Conocimiento', '')),
            "performance_level": str(row.get('Nivel_Desempeno_Esperado', '')),
            "school_grade": str(row.get('Grado_Escolar', '')),
            "application_period": str(row.get('Periodo_Aplicacion', '')),
        }
        
        return power_stats

    def _build_tags(self, row: pd.Series) -> List[str]:
        """Construir array de tags desde competencias y procesos cognitivos"""
        tags = []
        
        # Competencia
        competencia = row.get('Competencia', '')
        if pd.notna(competencia) and str(competencia).strip():
            tags.append(str(competencia).strip())
        
        # Proceso cognitivo
        proceso = row.get('Proceso_Cognitivo', '')
        if pd.notna(proceso) and str(proceso).strip():
            tags.append(str(proceso).strip())
        
        # Tipo de conocimiento
        tipo_conocimiento = row.get('Tipo_Conocimiento', '')
        if pd.notna(tipo_conocimiento) and str(tipo_conocimiento).strip():
            tags.append(str(tipo_conocimiento).strip())
        
        # Área temática
        area_tematica = row.get('Area_Tematica', '')
        if pd.notna(area_tematica) and str(area_tematica).strip():
            tags.append(str(area_tematica).strip())
        
        return tags

    def _validate_question_data(self, row: pd.Series) -> List[str]:
        """Validar datos de la pregunta antes de importar"""
        errors = []
        
        # Validar pregunta
        pregunta = row.get('Pregunta', '')
        if pd.isna(pregunta) or not str(pregunta).strip():
            errors.append("Pregunta está vacía")
        
        # Validar respuesta correcta
        respuesta_correcta = row.get('Respuesta_Correcta', '')
        if pd.isna(respuesta_correcta) or str(respuesta_correcta).strip() not in ['A', 'B', 'C', 'D']:
            errors.append("Respuesta correcta debe ser A, B, C o D")
        
        # Validar opciones
        options = self._build_options(row)
        if len(options) < 2:
            errors.append("Debe tener al menos 2 opciones")
        
        if respuesta_correcta and respuesta_correcta not in options:
            errors.append("Respuesta correcta no coincide con las opciones disponibles")
        
        # Validar área evaluada
        area_evaluada = row.get('Area_Evaluada', '')
        if pd.isna(area_evaluada) or str(area_evaluada).strip() not in self.subjects_mapping:
            errors.append(f"Área evaluada '{area_evaluada}' no está mapeada a un subject")
        
        return errors

    def import_excel(self, file_path: str, validate_only: bool = False) -> Dict[str, any]:
        """Importar preguntas desde archivo Excel"""
        try:
            logger.info(f"Leyendo archivo Excel: {file_path}")
            df = pd.read_excel(file_path)
            
            logger.info(f"Archivo leído: {len(df)} filas encontradas")
            
            # Validar columnas requeridas
            required_columns = [
                'Pregunta', 'Respuesta_Correcta', 'Opcion_A', 'Opcion_B', 
                'Opcion_C', 'Opcion_D', 'Area_Evaluada', 'Tema_Especifico'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Columnas faltantes: {missing_columns}")
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Validar datos
                    errors = self._validate_question_data(row)
                    if errors:
                        self.errors.append(f"Fila {index + 2}: {'; '.join(errors)}")
                        continue
                    
                    if validate_only:
                        self.imported_questions += 1
                        continue
                    
                    # Mapear subject
                    area_evaluada = str(row['Area_Evaluada']).strip()
                    subject_id = self.subjects_mapping.get(area_evaluada)
                    if not subject_id:
                        self.errors.append(f"Fila {index + 2}: Área evaluada '{area_evaluada}' no mapeada")
                        continue
                    
                    # Mapear topic
                    tema_especifico = str(row['Tema_Especifico']).strip()
                    topic_id = self._create_or_get_topic(tema_especifico, subject_id)
                    
                    # Construir pregunta
                    question = Question(
                        id=uuid.uuid4(),
                        topic_id=topic_id,
                        subject_id=subject_id,
                        question_text=str(row['Pregunta']).strip(),
                        question_type='multiple_choice',
                        difficulty=self._map_difficulty(row.get('Nivel_Dificultad')),
                        correct_answer=str(row['Respuesta_Correcta']).strip(),
                        options=self._build_options(row),
                        explanation=row.get('Afirmacion', ''),
                        hint=row.get('Contexto', ''),
                        tags=self._build_tags(row),
                        power_stats=self._build_power_stats(row),
                        image_url=row.get('Imagen_Pregunta_URL', ''),
                        options_images=self._build_options_images(row),
                        is_validated='pending'
                    )
                    
                    # Validar pregunta
                    validation_errors = question.validate_question()
                    if validation_errors:
                        self.errors.append(f"Fila {index + 2}: {'; '.join(validation_errors)}")
                        continue
                    
                    # Guardar en BD
                    self.db.add(question)
                    self.imported_questions += 1
                    
                    # Log cada 100 preguntas
                    if self.imported_questions % 100 == 0:
                        logger.info(f"Procesadas {self.imported_questions} preguntas...")
                        if not validate_only:
                            self.db.commit()
                
                except Exception as e:
                    self.errors.append(f"Fila {index + 2}: Error procesando - {str(e)}")
                    continue
            
            # Commit final
            if not validate_only:
                self.db.commit()
            
            logger.info(f"Importación completada: {self.imported_questions} preguntas procesadas")
            
            return {
                "imported_questions": self.imported_questions,
                "errors": self.errors,
                "warnings": self.warnings
            }
            
        except Exception as e:
            logger.error(f"Error leyendo archivo Excel: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Importar preguntas ICFES desde Excel')
    parser.add_argument('--file', required=True, help='Ruta al archivo Excel')
    parser.add_argument('--validate', action='store_true', help='Solo validar, no importar')
    parser.add_argument('--clear', action='store_true', help='Limpiar preguntas existentes antes de importar')
    
    args = parser.parse_args()
    
    # Verificar archivo
    if not os.path.exists(args.file):
        logger.error(f"Archivo no encontrado: {args.file}")
        sys.exit(1)
    
    # Conectar a BD
    db = next(get_db())
    
    try:
        importer = ICFESExcelImporter(db)
        
        # Limpiar si se solicita
        if args.clear:
            logger.info("Limpiando preguntas existentes...")
            db.query(Question).delete()
            db.commit()
            logger.info("Preguntas existentes eliminadas")
        
        # Importar
        result = importer.import_excel(args.file, validate_only=args.validate)
        
        # Mostrar resultados
        print(f"\n{'='*50}")
        print(f"RESULTADOS DE LA IMPORTACIÓN")
        print(f"{'='*50}")
        print(f"✅ Preguntas procesadas: {result['imported_questions']}")
        print(f"❌ Errores: {len(result['errors'])}")
        print(f"⚠️  Advertencias: {len(result['warnings'])}")
        
        if result['errors']:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in result['errors'][:10]:  # Mostrar solo los primeros 10
                print(f"  - {error}")
            if len(result['errors']) > 10:
                print(f"  ... y {len(result['errors']) - 10} errores más")
        
        if result['warnings']:
            print(f"\n⚠️  ADVERTENCIAS:")
            for warning in result['warnings'][:5]:
                print(f"  - {warning}")
        
        print(f"\n{'='*50}")
        
    except Exception as e:
        logger.error(f"Error en la importación: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 