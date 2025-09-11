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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, engine
from app.models.topic import Topic
from app.models.question import Question
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
        self.warnings = []

    def _load_subjects_mapping(self) -> Dict[str, str]:
        """Mapear áreas evaluadas a subjects existentes"""
        subjects = self.db.query(Subject).all()
        mapping = {}
        
        # Mapeo directo - Excel "Área_Evaluada" -> Database Subject Name
        area_to_subject = {
            'Matemáticas': 'Matemáticas',
            'Lenguaje': 'Lenguaje', 
            'Lectura Crítica': 'Lenguaje',  # ICFES Excel uses "Lectura Crítica" but DB has "Lenguaje"
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
        """Construir objeto options desde las columnas A, B, C, D.

        Soporta encabezados normalizados (opcion_a) y variantes con tildes/espacios (Opción_A, Opcion A).
        """
        options: Dict[str, str] = {}
        # Probar claves en orden de mayor probabilidad
        for option in ['A', 'B', 'C', 'D']:
            raw = None
            for key in [
                f'opcion_{option.lower()}',
                f'Opcion_{option}',
                f'Opción_{option}',
                f'Opcion {option}',
                f'Opción {option}'
            ]:
                val = row.get(key, '')
                if pd.notna(val) and str(val).strip():
                    raw = val
                    break
            if raw is not None and str(raw).strip():
                options[option] = str(raw).strip()
        return options

    def _build_options_images(self, row: pd.Series) -> Optional[Dict[str, str]]:
        """Construir objeto options_images desde las URLs de imágenes.

        Soporta claves normalizadas y variantes.
        """
        options_images: Dict[str, str] = {}
        has_images = False
        for option in ['A', 'B', 'C', 'D']:
            raw = None
            for key in [
                f'imagen_opcion_{option.lower()}_url',
                f'Imagen_Opcion_{option}_URL',
                f'Imagen Opcion {option} URL'
            ]:
                val = row.get(key, '')
                if pd.notna(val) and str(val).strip():
                    raw = val
                    break
            if raw is not None and str(raw).strip():
                options_images[option] = self._normalize_image_path(str(raw).strip())
                has_images = True
        return options_images if has_images else None

    def _normalize_image_path(self, value: str) -> str:
        """Normaliza cualquier referencia a imagen a /mathimg/<archivo> si es una ruta local o nombre."""
        try:
            s = (value or '').strip()
            if not s:
                return s
            # Si ya es absoluta hacia public
            if s.startswith('/mathimg/'):
                return s
            # Si contiene carpeta mathimg o es un path/nombre, quedarnos con el basename
            import os
            base = os.path.basename(s)
            # Si parece URL http(s), dejar tal cual
            if s.startswith('http://') or s.startswith('https://'):
                return s
            return '/mathimg/' + base
        except Exception:
            return value

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

    def _safe_get_string(self, row: pd.Series, column: str) -> str:
        """Safely get a string value from row, handling variants and missing values"""
        # Try multiple column name variants
        variants = [
            column,
            column.replace('_', ' '),
            column.replace('_', ''),
            column.replace('ó', 'o').replace('é', 'e').replace('í', 'i').replace('á', 'a').replace('ú', 'u'),
            column.replace('ñ', 'n')
        ]
        
        for variant in variants:
            if variant in row.index:
                value = row.get(variant, '')
                if pd.notna(value) and str(value).strip():
                    return str(value).strip()
        
        return None

    def _safe_get_int(self, row: pd.Series, column: str) -> int:
        """Safely get an integer value from row, handling variants and missing values"""
        # Try multiple column name variants
        variants = [
            column,
            column.replace('_', ' '),
            column.replace('_', ''),
            column.replace('ó', 'o').replace('é', 'e').replace('í', 'i').replace('á', 'a').replace('ú', 'u'),
            column.replace('ñ', 'n')
        ]
        
        for variant in variants:
            if variant in row.index:
                value = row.get(variant, '')
                if pd.notna(value):
                    try:
                        if isinstance(value, str) and 'minuto' in value.lower():
                            # Extract number from "3 minutos" -> 180 seconds
                            import re
                            match = re.search(r'\d+', str(value))
                            if match:
                                return int(match.group()) * 60
                        else:
                            return int(float(str(value)))
                    except (ValueError, TypeError):
                        continue
        
        return None

    def _validate_question_data(self, row: pd.Series, resolved_columns: Dict[str, str]) -> List[str]:
        """Validar datos de la pregunta antes de importar usando columnas normalizadas"""
        errors = []
        
        # Validar pregunta
        pregunta = row.get(resolved_columns.get('pregunta', ''), '')
        if pd.isna(pregunta) or not str(pregunta).strip():
            errors.append("Pregunta está vacía")
        
        # Validar respuesta correcta
        respuesta_correcta = row.get(resolved_columns.get('respuesta_correcta', ''), '')
        if pd.isna(respuesta_correcta) or str(respuesta_correcta).strip() not in ['A', 'B', 'C', 'D']:
            errors.append("Respuesta correcta debe ser A, B, C o D")
        
        # Validar opciones
        options = self._build_options(row)
        if len(options) < 2:
            errors.append("Debe tener al menos 2 opciones")
        
        if respuesta_correcta and respuesta_correcta not in options:
            errors.append("Respuesta correcta no coincide con las opciones disponibles")
        
        # Validar área evaluada
        area_evaluada = row.get(resolved_columns.get('area_evaluada', ''), '')
        if pd.isna(area_evaluada) or str(area_evaluada).strip() not in self.subjects_mapping:
            errors.append(f"Área evaluada '{area_evaluada}' no está mapeada a un subject")
        
        return errors

    def import_excel(self, file_path: str, validate_only: bool = False) -> Dict[str, any]:
        """Importar preguntas desde archivo Excel.

        La función es tolerante a variaciones de encabezados en el archivo Excel.
        Normaliza encabezados (quita acentos, reemplaza espacios por guiones bajos y convierte a minúsculas)
        y acepta alias comunes para las columnas requeridas, por ejemplo:
        - Area_Evaluada: "Área Evaluada", "Area Evaluada", "area_evaluada"
        - Tema_Especifico: "Tema Específico", "Tema Especifico", "tema_especifico"
        - Respuesta_Correcta: "Respuesta Correcta"
        - Opcion_X: "Opción X", "Opcion X"
        - Imagen_*: acepta variantes con/ sin guion bajo
        """
        try:
            logger.info(f"Leyendo archivo Excel: {file_path}")
            df = pd.read_excel(file_path)

            # Normalizar nombres de columnas para ser más tolerantes
            import unicodedata

            def normalize_header(s: str) -> str:
                s = str(s or "").strip()
                # Quitar acentos
                s = unicodedata.normalize('NFKD', s)
                s = ''.join(c for c in s if not unicodedata.combining(c))
                # Unificar separadores y minúsculas
                s = s.replace(" ", "_").replace("-", "_")
                s = s.replace("__", "_")
                return s.lower()

            original_columns = list(df.columns)
            normalized_columns = {col: normalize_header(col) for col in df.columns}
            df.rename(columns=normalized_columns, inplace=True)

            logger.info(f"Archivo leído: {len(df)} filas encontradas")

            # Mapa de alias -> nombre canónico esperado
            alias_to_canonical = {
                # requeridas
                'pregunta': 'pregunta',
                'respuesta_correcta': 'respuesta_correcta',
                'opcion_a': 'opcion_a',
                'opcion_b': 'opcion_b',
                'opcion_c': 'opcion_c',
                'opcion_d': 'opcion_d',
                'area_evaluada': 'area_evaluada',
                'area_evaluada_': 'area_evaluada',
                'areaevaluada': 'area_evaluada',
                'tema_especifico': 'tema_especifico',
                'tema_especifico_': 'tema_especifico',
                'temaespecifico': 'tema_especifico',

                # opcionales/compat
                'imagen_pregunta_url': 'imagen_pregunta_url',
                'imagen_opcion_a_url': 'imagen_opcion_a_url',
                'imagen_opcion_b_url': 'imagen_opcion_b_url',
                'imagen_opcion_c_url': 'imagen_opcion_c_url',
                'imagen_opcion_d_url': 'imagen_opcion_d_url',
            }

            # Intentar mapear variantes con y sin tildes
            def find_col(*candidates: str) -> str | None:
                for c in candidates:
                    key = normalize_header(c)
                    # Revisar directo
                    if key in df.columns:
                        return key
                    # Revisar alias
                    if key in alias_to_canonical and alias_to_canonical[key] in df.columns:
                        return alias_to_canonical[key]
                return None

            # Asegurar que existan las columnas requeridas (en su forma normalizada)
            required_candidates = {
                'pregunta': ('Pregunta', 'pregunta'),
                'respuesta_correcta': ('Respuesta_Correcta', 'Respuesta Correcta', 'respuesta_correcta'),
                'opcion_a': ('Opcion_A', 'Opción_A', 'Opcion A', 'Opción A', 'opcion_a'),
                'opcion_b': ('Opcion_B', 'Opción_B', 'Opcion B', 'Opción B', 'opcion_b'),
                'opcion_c': ('Opcion_C', 'Opción_C', 'Opcion C', 'Opción C', 'opcion_c'),
                'opcion_d': ('Opcion_D', 'Opción_D', 'Opcion D', 'Opción D', 'opcion_d'),
                'area_evaluada': ('Area_Evaluada', 'Área_Evaluada', 'Area Evaluada', 'Área Evaluada', 'area_evaluada'),
                'tema_especifico': ('Tema_Especifico', 'Tema Especifico', 'Tema Específico', 'tema_especifico'),
            }

            resolved_columns: dict[str, str] = {}
            missing: list[str] = []
            for canonical, candidates in required_candidates.items():
                found = find_col(*candidates)
                if found:
                    resolved_columns[canonical] = found
                else:
                    missing.append(canonical)

            if missing:
                # Si faltan, reporte qué encabezados originales encontró para diagnóstico
                logger.error(
                    "Encabezados originales: %s", original_columns
                )
                raise ValueError(
                    f"Columnas faltantes tras normalización: {missing}"
                )
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Validar datos
                    errors = self._validate_question_data(row, resolved_columns)
                    if errors:
                        self.errors.append(f"Fila {index + 2}: {'; '.join(errors)}")
                        continue
                    
                    if validate_only:
                        self.imported_questions += 1
                        continue
                    
                    # Mapear subject
                    area_evaluada = str(row[resolved_columns['area_evaluada']]).strip()
                    subject_id = self.subjects_mapping.get(area_evaluada)
                    if not subject_id:
                        self.errors.append(f"Fila {index + 2}: Área evaluada '{area_evaluada}' no mapeada")
                        continue
                    
                    # Mapear topic
                    tema_especifico = str(row[resolved_columns['tema_especifico']]).strip()
                    topic_id = self._create_or_get_topic(tema_especifico, subject_id)
                    
                    # Construir pregunta
                    # Preparar campos detallados de pregunta/opciones
                    preg_texto = str(row[resolved_columns['pregunta']]).strip()
                    # imagen de la pregunta (soportar variantes)
                    imagen_preg_key = find_col('Imagen_Pregunta_URL', 'Imagen Pregunta URL', 'imagen_pregunta_url')
                    preg_imagen = None
                    if imagen_preg_key and pd.notna(row.get(imagen_preg_key, '')):
                        preg_imagen = self._normalize_image_path(str(row.get(imagen_preg_key, '') or '').strip())

                    opcion_map = {}
                    for opt in ['A','B','C','D']:
                        texto_key = find_col(f'Opcion_{opt}', f'Opción_{opt}', f'Opcion {opt}', f'Opción {opt}', f'opcion_{opt.lower()}')
                        img_key = find_col(f'Imagen_Opcion_{opt}_URL', f'Imagen Opcion {opt} URL', f'imagen_opcion_{opt.lower()}_url')
                        texto_val = None
                        imagen_val = None
                        if texto_key and pd.notna(row.get(texto_key, '')):
                            texto_val = str(row.get(texto_key, '') or '').strip()
                        if img_key and pd.notna(row.get(img_key, '')):
                            imagen_val = self._normalize_image_path(str(row.get(img_key, '') or '').strip())
                        opcion_map[opt] = {
                            'texto': texto_val,
                            'imagen': imagen_val
                        }

                    correct_raw = str(row[resolved_columns['respuesta_correcta']]).strip()
                    correct_norm = correct_raw.lower()

                    question = Question(
                        id=uuid.uuid4(),
                        topic_id=topic_id,
                        subject_id=subject_id,
                        # Nuevos campos normalizados
                        pregunta_texto=preg_texto or None,
                        pregunta_imagen=preg_imagen or None,
                        opcion_a_texto=opcion_map['A']['texto'],
                        opcion_a_imagen=opcion_map['A']['imagen'],
                        opcion_b_texto=opcion_map['B']['texto'],
                        opcion_b_imagen=opcion_map['B']['imagen'],
                        opcion_c_texto=opcion_map['C']['texto'],
                        opcion_c_imagen=opcion_map['C']['imagen'],
                        opcion_d_texto=opcion_map['D']['texto'],
                        opcion_d_imagen=opcion_map['D']['imagen'],
                        respuesta_correcta=correct_norm,
                        # Compatibilidad legacy
                        question_text=preg_texto or None,
                        question_type='multiple_choice',
                        difficulty=self._map_difficulty(row.get('Nivel_Dificultad')),
                        correct_answer=correct_raw,
                        options=self._build_options(row),
                        explanation=row.get('Afirmacion', ''),
                        hint=row.get('Contexto', ''),
                        tags=self._build_tags(row),
                        power_stats=self._build_power_stats(row),
                        # CAMPOS ICFES - Competencias y componentes
                        competencia=self._safe_get_string(row, 'Competencia'),
                        componente=self._safe_get_string(row, 'Componente'),
                        proceso_cognitivo=self._safe_get_string(row, 'Proceso_Cognitivo'),
                        tipo_conocimiento=self._safe_get_string(row, 'Tipo_Conocimiento'),
                        afirmacion=self._safe_get_string(row, 'Afirmación'),
                        evidencia=self._safe_get_string(row, 'Evidencia'),
                        nivel_desempeno_esperado=self._safe_get_string(row, 'Nivel_Desempeño_Esperado'),
                        tiempo_estimado=self._safe_get_int(row, 'Tiempo_Estimado'),
                        # Sistema de ayuda gradual  
                        pista_1=self._safe_get_string(row, 'Pista_1'),
                        pista_2=self._safe_get_string(row, 'Pista_2'),
                        pista_3=self._safe_get_string(row, 'Pista_3'),
                        explicacion_respuesta=self._safe_get_string(row, 'Explicación_Respuesta'),
                        error_comun=self._safe_get_string(row, 'Error_Común')
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