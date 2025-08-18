#!/usr/bin/env python3
"""
Script para importar datos ICFES desde Excel automáticamente durante la inicialización del Docker
"""
import os
import sys
import time
import pandas as pd
import psycopg2
import json
from typing import Dict, List, Optional

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
    'database': os.getenv('DB_NAME', 'gameplay_db'),
    'user': os.getenv('DB_USER', 'gameplay'),
    'password': os.getenv('DB_PASSWORD', 'gameplay123')
}

class ICFESDataImporter:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.imported_questions = 0
        self.errors = []
        
    def connect_db(self, max_retries=10, retry_delay=5):
        """Conectar a la base de datos con reintentos"""
        for attempt in range(max_retries):
            try:
                print(f"Intento {attempt + 1} de conexión a la base de datos...")
                self.conn = psycopg2.connect(**DB_CONFIG)
                self.conn.autocommit = True
                self.cursor = self.conn.cursor()
                print("✅ Conexión exitosa a la base de datos")
                return True
            except Exception as e:
                print(f"❌ Error de conexión (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    print("❌ No se pudo conectar a la base de datos después de todos los intentos")
                    return False
    
    def load_subjects_mapping(self) -> Dict[str, str]:
        """Mapear áreas evaluadas a subjects existentes usando el sistema inteligente dinámico"""
        try:
            # Usar el endpoint de mapping inteligente del sistema dinámico
            import requests
            try:
                response = requests.get('http://localhost:4000/api/v1/subjects/mapping/import', timeout=5)
                if response.status_code == 200:
                    api_data = response.json()
                    mapping = api_data.get('mapping', {})
                    total_subjects = api_data.get('total_subjects', 0)
                    total_aliases = api_data.get('total_aliases', 0)
                    
                    print(f"🚀 Mapping inteligente cargado desde API:")
                    print(f"   📚 {total_subjects} materias principales")
                    print(f"   🔄 {total_aliases} total de aliases y variaciones")
                    print(f"   📋 {len(mapping)} entradas de mapeo inteligente")
                    
                    return mapping
                else:
                    print(f"⚠️ API no disponible (HTTP {response.status_code}), usando fallback")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error conectando con API dinâmica: {e}, usando fallback")
            
            # Fallback: consulta directa a la base de datos con lógica inteligente
            return self._load_intelligent_mapping_direct()
            
        except Exception as e:
            print(f"❌ Error cargando subjects mapping inteligente: {e}")
            return self._get_fallback_mapping()
    
    def _load_intelligent_mapping_direct(self) -> Dict[str, str]:
        """Carga mapping inteligente directamente desde la base de datos"""
        try:
            # Obtener subjects y aliases básicos
            query = """
            SELECT DISTINCT 
                COALESCE(sa.alias_name, s.name) as name,
                s.id::text as subject_id,
                s.name as subject_name
            FROM subjects s
            LEFT JOIN subject_aliases sa ON s.id = sa.subject_id
            UNION
            SELECT s.name, s.id::text, s.name
            FROM subjects s
            ORDER BY name
            """
            
            self.cursor.execute(query)
            mappings = self.cursor.fetchall()
            
            subject_mapping = {}
            subjects_info = {}
            
            # Procesar mappings básicos
            for name, subject_id, subject_name in mappings:
                name = str(name).strip()
                subject_mapping[name] = str(subject_id)
                subject_mapping[name.lower()] = str(subject_id)
                subjects_info[str(subject_id)] = subject_name
            
            # Agregar variaciones inteligentes para cada subject
            for subject_id, subject_name in subjects_info.items():
                intelligent_variations = self._generate_intelligent_variations(subject_name)
                for variation in intelligent_variations:
                    if variation not in subject_mapping:  # No sobrescribir mappings existentes
                        subject_mapping[variation] = subject_id
            
            print(f"📋 Mapping inteligente directo cargado: {len(subject_mapping)} entradas")
            return subject_mapping
            
        except Exception as e:
            print(f"❌ Error en mapping directo: {e}")
            return self._get_fallback_mapping()
    
    def _generate_intelligent_variations(self, subject_name: str) -> List[str]:
        """Generar variaciones inteligentes de nombres de materias para mejor matching"""
        variations = []
        name_lower = subject_name.lower()
        
        # Mapeos inteligentes comunes en español
        intelligent_mappings = {
            'matemáticas': ['matematica', 'matematicas', 'math', 'mathematics', 'mates'],
            'lectura crítica': ['lectura critica', 'lenguaje', 'español', 'language', 'reading', 'lectura'],
            'ciencias naturales': ['ciencias', 'naturales', 'science', 'natural sciences', 'fisica', 'quimica', 'biologia'],
            'sociales y ciudadanas': ['sociales', 'ciudadanas', 'social', 'social sciences', 'historia', 'geografia'],
            'inglés': ['ingles', 'english', 'foreign language', 'segunda lengua', 'idioma extranjero'],
            'filosofía': ['filosofia', 'philosophy', 'etica'],
            'química': ['quimica', 'chemistry'],
            'física': ['fisica', 'physics'],
            'biología': ['biologia', 'biology'],
            'historia': ['history'],
            'geografía': ['geografia', 'geography']
        }
        
        # Encontrar materia base coincidente y agregar sus variaciones
        for base_subject, aliases in intelligent_mappings.items():
            if base_subject in name_lower or any(alias in name_lower for alias in aliases):
                variations.extend(aliases)
                variations.append(base_subject)
        
        # Agregar variaciones comunes (con/sin acentos, plural/singular)
        variations.extend(self._generate_accent_variations(subject_name))
        variations.extend(self._generate_plural_variations(subject_name))
        
        # Remover duplicados y retornar versiones en minúsculas
        unique_variations = list(set([v.lower() for v in variations if v]))
        return unique_variations
    
    def _generate_accent_variations(self, text: str) -> List[str]:
        """Generar variaciones con y sin acentos españoles"""
        accent_map = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        
        variations = [text]
        
        # Versión sin acentos
        no_accent = text
        for accented, plain in accent_map.items():
            no_accent = no_accent.replace(accented, plain)
        variations.append(no_accent)
        
        return variations
    
    def _generate_plural_variations(self, text: str) -> List[str]:
        """Generar variaciones singular/plural"""
        variations = [text]
        text_lower = text.lower()
        
        # Si termina en 's', probar singular
        if text_lower.endswith('s') and len(text_lower) > 2:
            singular = text_lower[:-1]
            variations.append(singular)
            # Caso especial para palabras que terminan en 'es'
            if text_lower.endswith('es') and len(text_lower) > 3:
                variations.append(text_lower[:-2])
        
        # Si no termina en 's', probar plural
        else:
            variations.append(text_lower + 's')
            # Plurales especiales
            if text_lower.endswith(('a', 'e', 'o')):
                variations.append(text_lower + 's')
            else:
                variations.append(text_lower + 'es')
        
        return variations
    
    def _find_subject_id_intelligent(self, area_evaluada: str, subjects_mapping: Dict[str, str]) -> Optional[str]:
        """Buscar subject ID usando matching inteligente con múltiples estrategias"""
        if not area_evaluada:
            return None
        
        area_clean = area_evaluada.strip()
        
        # 1. Matching exacto (case sensitive)
        if area_clean in subjects_mapping:
            return subjects_mapping[area_clean]
        
        # 2. Matching exacto (case insensitive)
        area_lower = area_clean.lower()
        if area_lower in subjects_mapping:
            return subjects_mapping[area_lower]
        
        # 3. Matching con variaciones de acentos
        area_no_accents = self._remove_accents(area_clean)
        if area_no_accents.lower() in subjects_mapping:
            return subjects_mapping[area_no_accents.lower()]
        
        # 4. Buscar por similitud en las claves del mapping
        for mapping_key, subject_id in subjects_mapping.items():
            mapping_key_clean = mapping_key.lower()
            area_lower = area_clean.lower()
            
            # Matching de contención (uno contiene al otro)
            if area_lower in mapping_key_clean or mapping_key_clean in area_lower:
                return subject_id
        
        # 5. Matching por palabras clave
        area_words = set(area_clean.lower().split())
        for mapping_key, subject_id in subjects_mapping.items():
            mapping_words = set(mapping_key.lower().split())
            # Si comparten al menos una palabra significativa (>3 caracteres)
            common_words = [w for w in area_words.intersection(mapping_words) if len(w) > 3]
            if common_words:
                return subject_id
        
        return None
    
    def _remove_accents(self, text: str) -> str:
        """Remover acentos españoles de un texto"""
        accent_map = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u', 'Á': 'A', 'É': 'E', 'Í': 'I', 
            'Ó': 'O', 'Ú': 'U', 'Ñ': 'N', 'Ü': 'U'
        }
        
        result = text
        for accented, plain in accent_map.items():
            result = result.replace(accented, plain)
        return result
    
    def _get_basic_subject_mappings(self) -> Dict[str, str]:
        """Mapeos básicos para compatibilidad temporal"""
        return {
            'Lenguaje': 'Lectura Crítica',
            'Ciencias': 'Ciencias Naturales', 
            'Ciencias Sociales': 'Sociales y Ciudadanas',
            'Sociales': 'Sociales y Ciudadanas',
            'English': 'Inglés'
        }
    
    def _get_fallback_mapping(self) -> Dict[str, str]:
        """Mapeo de emergencia si falla todo lo demás"""
        try:
            self.cursor.execute("SELECT name, id::text FROM subjects LIMIT 10")
            fallback = dict(self.cursor.fetchall())
            print(f"🔄 Usando mapeo de emergencia: {fallback}")
            return fallback
        except:
            return {}
    
    def create_or_get_topic(self, topic_name: str, subject_id: str) -> str:
        """Crear o obtener topic existente"""
        try:
            # Buscar topic existente
            self.cursor.execute(
                "SELECT id FROM topics WHERE name = %s AND subject_id = %s",
                (topic_name, subject_id)
            )
            result = self.cursor.fetchone()
            
            if result:
                return str(result[0])
            
            # Crear nuevo topic
            import uuid
            topic_id = str(uuid.uuid4())
            self.cursor.execute(
                """INSERT INTO topics (id, subject_id, name, description, difficulty_level) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (topic_id, subject_id, topic_name, f"Tema: {topic_name}", 2)
            )
            return topic_id
            
        except Exception as e:
            print(f"Error creando topic {topic_name}: {e}")
            return None
    
    def map_difficulty(self, difficulty_value) -> int:
        """Mapear dificultad a escala 1-5"""
        if pd.isna(difficulty_value):
            return 2
        
        if isinstance(difficulty_value, str):
            difficulty_value = difficulty_value.lower()
            if 'fácil' in difficulty_value or 'facil' in difficulty_value or 'bajo' in difficulty_value:
                return 1
            elif 'medio' in difficulty_value or 'intermedio' in difficulty_value:
                return 2
            elif 'alto' in difficulty_value or 'difícil' in difficulty_value or 'dificil' in difficulty_value:
                return 3
            elif 'muy alto' in difficulty_value or 'muy difícil' in difficulty_value:
                return 4
        
        if isinstance(difficulty_value, (int, float)):
            if difficulty_value <= 1:
                return 1
            elif difficulty_value <= 2:
                return 2
            elif difficulty_value <= 3:
                return 3
            elif difficulty_value <= 4:
                return 4
            else:
                return 5
        
        return 2  # Default
    
    def build_options(self, row) -> dict:
        """Construir opciones de la pregunta combinando texto e imagen"""
        options = {}
        option_letters = ['A', 'B', 'C', 'D', 'E']
        
        for i, letter in enumerate(option_letters):
            col_name = f'Opcion_{letter}'
            image_col_name = f'Imagen_Opcion_{letter}_URL'
            
            # Construir opción con texto e imagen si están disponibles
            option_content = {
                'text': '',
                'image_url': '',
                'has_both': False
            }
            
            # Verificar texto
            if col_name in row and pd.notna(row[col_name]):
                option_content['text'] = str(row[col_name]).strip()
            
            # Verificar imagen
            if image_col_name in row and pd.notna(row[image_col_name]):
                option_content['image_url'] = str(row[image_col_name]).strip()
            
            # Determinar si tiene ambos
            if option_content['text'] and option_content['image_url']:
                option_content['has_both'] = True
                # Para compatibilidad, mantener el texto como valor principal
                options[letter] = option_content['text']
            elif option_content['text']:
                options[letter] = option_content['text']
            elif option_content['image_url']:
                # Si solo hay imagen, dejar el texto vacío y confiar en options_images
                options[letter] = ""
        
        return options
    
    def build_options_images(self, row) -> dict:
        """Construir diccionario de URLs de imágenes para opciones"""
        options_images = {}
        option_letters = ['A', 'B', 'C', 'D', 'E']
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        # Buscar en ambas ubicaciones: carpeta raíz mathimg y carpeta pública de Next.js
        mathimg_dir_repo = os.path.join(repo_root, 'mathimg')
        mathimg_dir_public = os.path.join(repo_root, 'apps', 'frontend', 'public', 'mathimg')
        public_prefix = '/mathimg/'

        def resolve_public_path(raw_path: str) -> str:
            base_name = os.path.basename(raw_path)
            # Preferir archivo exactamente como está escrito (respetar mayúsculas)
            candidate_repo = os.path.join(mathimg_dir_repo, base_name)
            candidate_public = os.path.join(mathimg_dir_public, base_name)
            if os.path.exists(candidate_public) or os.path.exists(candidate_repo):
                return public_prefix + base_name
            # Aun si no encontramos el archivo local, normalizamos a /mathimg/<nombre>
            # para permitir servirlo si el front ya lo tiene copiado
            return public_prefix + base_name

        for letter in option_letters:
            image_col_name = f'Imagen_Opcion_{letter}_URL'
            if image_col_name in row and pd.notna(row[image_col_name]):
                raw_path = str(row[image_col_name]).strip()
                options_images[letter] = resolve_public_path(raw_path)
        
        return options_images
    
    def build_tags(self, row) -> List[str]:
        """Construir tags para la pregunta"""
        tags = []
        
        # Agregar tags basados en las columnas disponibles
        if 'Area_Evaluada' in row and pd.notna(row['Area_Evaluada']):
            tags.append(str(row['Area_Evaluada']).lower().replace(' ', '_'))
        
        if 'Tema_Especifico' in row and pd.notna(row['Tema_Especifico']):
            tags.append(str(row['Tema_Especifico']).lower().replace(' ', '_'))
        
        if 'Competencia' in row and pd.notna(row['Competencia']):
            tags.append(str(row['Competencia']).lower().replace(' ', '_'))
        
        return tags
    
    def import_excel_data(self, excel_file_path: str) -> Dict[str, any]:
        """Importar datos desde archivo Excel"""
        try:
            print(f"🔄 Leyendo archivo Excel: {excel_file_path}")
            
            # Leer el archivo Excel
            if not os.path.exists(excel_file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {excel_file_path}")
            
            # Intentar leer diferentes hojas
            xl_file = pd.ExcelFile(excel_file_path)
            print(f"📋 Hojas disponibles: {xl_file.sheet_names}")
            
            # Usar la primera hoja o buscar una hoja específica
            sheet_name = xl_file.sheet_names[0]
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)

            # Resolver rutas de imágenes locales: si hay carpeta 'mathimg' en el repo,
            # construir rutas públicas servibles por Next: '/mathimg/<archivo>'
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            mathimg_dir_repo = os.path.join(repo_root, 'mathimg')
            mathimg_dir_public = os.path.join(repo_root, 'apps', 'frontend', 'public', 'mathimg')
            public_prefix = '/mathimg/'

            # Índice de archivos para resolver nombre con mayúsculas/minúsculas correctas
            def build_lower_map(dir_path: str):
                try:
                    return {f.lower(): f for f in os.listdir(dir_path)} if os.path.isdir(dir_path) else {}
                except Exception:
                    return {}

            lower_map_repo = build_lower_map(mathimg_dir_repo)
            lower_map_public = build_lower_map(mathimg_dir_public)

            def resolve_basename_case_insensitive(base_name: str) -> str:
                if not base_name:
                    return base_name
                key = base_name.lower()
                if key in lower_map_public:
                    return lower_map_public[key]
                if key in lower_map_repo:
                    return lower_map_repo[key]
                return base_name
            
            print(f"📊 Total de filas en el Excel: {len(df)}")
            print(f"📋 Columnas disponibles: {list(df.columns)}")
            
            subjects_mapping = self.load_subjects_mapping()
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Validar datos mínimos requeridos
                    if pd.isna(row.get('Pregunta', '')) or pd.isna(row.get('Respuesta_Correcta', '')):
                        self.errors.append(f"Fila {index + 2}: Faltan datos obligatorios (Pregunta o Respuesta_Correcta)")
                        continue
                    
                    # Obtener área evaluada con matching inteligente
                    area_evaluada = None
                    if 'Area_Evaluada' in row and pd.notna(row['Area_Evaluada']):
                        area_evaluada = str(row['Area_Evaluada']).strip()
                    elif 'Área_Evaluada' in row and pd.notna(row['Área_Evaluada']):
                        area_evaluada = str(row['Área_Evaluada']).strip()
                    else:
                        area_evaluada = 'Matemáticas'
                    
                    # Buscar subject ID usando matching inteligente
                    subject_id = self._find_subject_id_intelligent(area_evaluada, subjects_mapping)
                    
                    if not subject_id:
                        self.errors.append(f"Fila {index + 2}: Área evaluada no reconocida: '{area_evaluada}' (probadas {len(subjects_mapping)} variaciones)")
                        continue
                    
                    # Crear o obtener topic
                    tema_especifico = None
                    if 'Tema_Especifico' in row and pd.notna(row['Tema_Especifico']):
                        tema_especifico = str(row['Tema_Especifico']).strip()
                    elif 'Tema_Específico' in row and pd.notna(row['Tema_Específico']):
                        tema_especifico = str(row['Tema_Específico']).strip()
                    else:
                        tema_especifico = 'General'
                    topic_id = self.create_or_get_topic(tema_especifico, subject_id)
                    
                    if not topic_id:
                        self.errors.append(f"Fila {index + 2}: No se pudo crear topic: {tema_especifico}")
                        continue
                    
                    # Construir pregunta con soporte para imagen
                    import uuid
                    question_id = str(uuid.uuid4())
                    
                    # Construir texto de pregunta: usar 'Pregunta' si existe, si no usar 'Contexto' como fallback
                    question_text = ''
                    if 'Pregunta' in row and pd.notna(row['Pregunta']):
                        question_text = str(row['Pregunta']).strip()
                    if not question_text and 'Contexto' in row and pd.notna(row['Contexto']):
                        question_text = str(row['Contexto']).strip()
                    question_image_url = ''
                    
                    # Verificar si hay imagen de pregunta
                    if 'Imagen_Pregunta_URL' in row and pd.notna(row['Imagen_Pregunta_URL']):
                        raw_path = str(row['Imagen_Pregunta_URL']).strip()
                        base_name = resolve_basename_case_insensitive(os.path.basename(raw_path))
                        question_image_url = public_prefix + base_name
                    
                    # Si hay contexto adicional, incluirlo
                    if 'Contexto' in row and pd.notna(row['Contexto']):
                        context = str(row['Contexto']).strip()
                        if question_text and context and context not in question_text:
                            question_text = f"{context}\n\n{question_text}"
                    
                    # Preparar campos multimedia
                    def norm_img_cell(val: Optional[str]) -> Optional[str]:
                        if val is None:
                            return None
                        sval = str(val).strip()
                        if not sval:
                            return None
                        bname = resolve_basename_case_insensitive(os.path.basename(sval))
                        # Usar carpeta pública si existe; si no, igualmente normalizar
                        return public_prefix + bname

                    opcion_a_texto = str(row['Opcion_A']).strip() if 'Opcion_A' in row and pd.notna(row['Opcion_A']) else None
                    opcion_b_texto = str(row['Opcion_B']).strip() if 'Opcion_B' in row and pd.notna(row['Opcion_B']) else None
                    opcion_c_texto = str(row['Opcion_C']).strip() if 'Opcion_C' in row and pd.notna(row['Opcion_C']) else None
                    opcion_d_texto = str(row['Opcion_D']).strip() if 'Opcion_D' in row and pd.notna(row['Opcion_D']) else None

                    opcion_a_imagen = norm_img_cell(str(row['Imagen_Opcion_A_URL'])) if 'Imagen_Opcion_A_URL' in row and pd.notna(row['Imagen_Opcion_A_URL']) else None
                    opcion_b_imagen = norm_img_cell(str(row['Imagen_Opcion_B_URL'])) if 'Imagen_Opcion_B_URL' in row and pd.notna(row['Imagen_Opcion_B_URL']) else None
                    opcion_c_imagen = norm_img_cell(str(row['Imagen_Opcion_C_URL'])) if 'Imagen_Opcion_C_URL' in row and pd.notna(row['Imagen_Opcion_C_URL']) else None
                    opcion_d_imagen = norm_img_cell(str(row['Imagen_Opcion_D_URL'])) if 'Imagen_Opcion_D_URL' in row and pd.notna(row['Imagen_Opcion_D_URL']) else None

                    correct_letter = str(row['Respuesta_Correcta']).strip().lower() if pd.notna(row.get('Respuesta_Correcta')) else ''

                    question_data = {
                        'id': question_id,
                        'topic_id': topic_id,
                        'subject_id': subject_id,
                        'question_text': question_text if question_text else None,
                        'question_type': 'multiple_choice',
                        'difficulty': self.map_difficulty(row.get('Nivel_Dificultad')),
                        'correct_answer': correct_letter.upper(),
                        'options': self.build_options(row),
                        'explanation': str(row.get('Explicación_Respuesta', row.get('Afirmacion', ''))).strip() if pd.notna(row.get('Explicación_Respuesta', row.get('Afirmacion'))) else '',
                        'hint': str(row.get('Pista_1', '')).strip() if pd.notna(row.get('Pista_1')) else '',
                        'tags': self.build_tags(row),
                        'image_url': question_image_url,
                        'options_images': self.build_options_images(row),
                        # multimedia columns
                        'pregunta_texto': question_text if question_text else None,
                        'pregunta_imagen': norm_img_cell(question_image_url) if question_image_url else None,
                        'opcion_a_texto': opcion_a_texto,
                        'opcion_a_imagen': opcion_a_imagen,
                        'opcion_b_texto': opcion_b_texto,
                        'opcion_b_imagen': opcion_b_imagen,
                        'opcion_c_texto': opcion_c_texto,
                        'opcion_c_imagen': opcion_c_imagen,
                        'opcion_d_texto': opcion_d_texto,
                        'opcion_d_imagen': opcion_d_imagen,
                        'respuesta_correcta': correct_letter,
                    }
                    
                    # Insertar en la base de datos
                    self.cursor.execute(
                        """
                        INSERT INTO questions (
                            id, topic_id, subject_id,
                            question_text, question_type, difficulty,
                            correct_answer, options, explanation, hint, tags,
                            pregunta_texto, pregunta_imagen,
                            opcion_a_texto, opcion_a_imagen,
                            opcion_b_texto, opcion_b_imagen,
                            opcion_c_texto, opcion_c_imagen,
                            opcion_d_texto, opcion_d_imagen,
                            respuesta_correcta
                        ) VALUES (
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s
                        )
                        """,
                        (
                            question_data['id'],
                            question_data['topic_id'],
                            question_data['subject_id'],
                            question_data['question_text'],
                            question_data['question_type'],
                            question_data['difficulty'],
                            question_data['correct_answer'],
                            json.dumps(question_data['options']),
                            question_data['explanation'],
                            question_data['hint'],
                            question_data['tags'],
                            question_data['pregunta_texto'],
                            question_data['pregunta_imagen'],
                            question_data['opcion_a_texto'],
                            question_data['opcion_a_imagen'],
                            question_data['opcion_b_texto'],
                            question_data['opcion_b_imagen'],
                            question_data['opcion_c_texto'],
                            question_data['opcion_c_imagen'],
                            question_data['opcion_d_texto'],
                            question_data['opcion_d_imagen'],
                            question_data['respuesta_correcta'],
                        )
                    )
                    
                    self.imported_questions += 1
                    
                    # Log cada 100 preguntas
                    if self.imported_questions % 100 == 0:
                        print(f"📈 Procesadas {self.imported_questions} preguntas...")
                
                except Exception as e:
                    self.errors.append(f"Fila {index + 2}: Error procesando - {str(e)}")
                    continue
            
            return {
                'imported_questions': self.imported_questions,
                'errors': self.errors
            }
            
        except Exception as e:
            print(f"❌ Error importando Excel: {e}")
            return {
                'imported_questions': 0,
                'errors': [f"Error general: {str(e)}"]
            }
    
    def close_connection(self):
        """Cerrar conexión a la base de datos"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main():
    print("🚀 Iniciando importación de datos ICFES...")
    
    # Ruta del archivo Excel
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_excel = os.path.join(repo_root, "ICFES2 (1).xlsx")
    excel_file = os.environ.get("ICFES_EXCEL_PATH", default_excel)
    
    # Verificar que el archivo existe
    if not os.path.exists(excel_file):
        print(f"❌ Archivo Excel no encontrado: {excel_file}")
        return False
    
    # Crear importador
    importer = ICFESDataImporter()
    
    try:
        # Conectar a la base de datos
        if not importer.connect_db():
            return False
        
        # Verificar que las tablas existen
        importer.cursor.execute("SELECT COUNT(*) FROM subjects")
        subjects_count = importer.cursor.fetchone()[0]
        print(f"📚 Materias en la base de datos: {subjects_count}")
        
        if subjects_count == 0:
            print("⚠️ No hay materias en la base de datos. Asegúrate de que el seed data se haya ejecutado primero.")
            return False
        
        # Verificar si ya hay preguntas importadas
        importer.cursor.execute("SELECT COUNT(*) FROM questions")
        existing_questions = importer.cursor.fetchone()[0]
        print(f"❓ Preguntas existentes: {existing_questions}")
        
        if existing_questions > 100:  # Si ya hay más de 100 preguntas, probablemente ya se importó
            print("✅ Ya existen preguntas en la base de datos. Saltando importación.")
            return True
        
        # Importar datos
        result = importer.import_excel_data(excel_file)
        
        print(f"✅ Importación completada:")
        print(f"   📊 Preguntas importadas: {result['imported_questions']}")
        print(f"   ❌ Errores encontrados: {len(result['errors'])}")
        
        if result['errors']:
            print("🔍 Primeros 5 errores:")
            for error in result['errors'][:5]:
                print(f"   - {error}")
        
        return result['imported_questions'] > 0
        
    except Exception as e:
        print(f"❌ Error durante la importación: {e}")
        return False
    
    finally:
        importer.close_connection()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)