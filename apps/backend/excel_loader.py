#!/usr/bin/env python3
"""
Cargador simple de datos ICFES desde Excel
Convierte preguntas reales a formato compatible con simple_app.py
"""
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def load_icfes_questions():
    """
    Carga preguntas reales ICFES desde Excel y las convierte
    al formato esperado por el frontend
    """
    # Rutas de archivos Excel disponibles
    excel_files = [
        '/root/IcfesLeveling/database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx',
        '/root/IcfesLeveling/apps/backend/ICFES_questions.xlsx',
        '/root/IcfesLeveling/apps/backend/ICFES2 (1).xlsx'
    ]

    all_questions = {}

    # Mapeo de áreas ICFES a subject_id
    subject_mapping = {
        'matematicas': 1,
        'lectura_critica': 2,
        'ciencias_naturales': 3,
        'sociales_ciudadanas': 4,
        'ingles': 5,
        # Variaciones de nombres
        'matemáticas': 1,
        'lectura crítica': 2,
        'ciencias naturales': 3,
        'sociales y ciudadanas': 4,
        'inglés': 5,
        'math': 1,
        'reading': 2,
        'science': 3,
        'social': 4,
        'english': 5
    }

    for excel_path in excel_files:
        if not os.path.exists(excel_path):
            continue

        try:
            print(f"📊 Cargando preguntas desde: {excel_path}")

            # Leer Excel con pandas
            df = pd.read_excel(excel_path)

            print(f"📋 Archivo leído: {len(df)} filas, Columnas: {list(df.columns)}")

            # Procesar cada fila como una pregunta
            for idx, row in df.iterrows():
                try:
                    # Identificar la materia/área
                    subject_id = 1  # Default: Matemáticas

                    # Buscar columnas que puedan indicar materia
                    area_columns = ['Área_Evaluada', 'area', 'materia', 'subject', 'tema', 'competencia', 'componente']
                    for col in area_columns:
                        if col in df.columns:
                            area_value = str(row[col]).lower().strip()
                            for area_name, sid in subject_mapping.items():
                                if area_name in area_value:
                                    subject_id = sid
                                    break
                            break

                    # Buscar texto de la pregunta
                    question_text = ""
                    question_columns = ['Pregunta', 'pregunta', 'question', 'enunciado', 'texto_pregunta', 'pregunta_texto']
                    for col in question_columns:
                        if col in df.columns and pd.notna(row[col]):
                            question_text = str(row[col]).strip()
                            break

                    if not question_text:
                        continue  # Skip si no hay pregunta

                    # Buscar opciones de respuesta
                    options = {}
                    option_letters = ['A', 'B', 'C', 'D']

                    for letter in option_letters:
                        # Buscar columnas de opciones
                        option_cols = [
                            f'Opcion_{letter}',
                            f'opcion_{letter.lower()}',
                            f'option_{letter}',
                            f'alternativa_{letter}',
                            letter,
                            f'respuesta_{letter}'
                        ]

                        for col in option_cols:
                            if col in df.columns and pd.notna(row[col]):
                                options[letter] = str(row[col]).strip()
                                break

                    # Buscar respuesta correcta
                    correct_answer = "A"  # Default
                    correct_cols = ['Respuesta_Correcta', 'respuesta_correcta', 'correct_answer', 'clave', 'key', 'respuesta']
                    for col in correct_cols:
                        if col in df.columns and pd.notna(row[col]):
                            correct_val = str(row[col]).strip().upper()
                            if correct_val in ['A', 'B', 'C', 'D']:
                                correct_answer = correct_val
                            break

                    # Buscar explicación
                    explicacion = ""
                    exp_cols = ['Explicación_Respuesta', 'explicacion', 'explanation', 'justificacion', 'solucion']
                    for col in exp_cols:
                        if col in df.columns and pd.notna(row[col]):
                            explicacion = str(row[col]).strip()
                            break

                    # Procesar campos de imágenes
                    requiere_imagen = False
                    imagen_pregunta_url = ""
                    imagen_opciones_urls = {}
                    imagen_contexto_url = ""

                    # Verificar si requiere imagen
                    req_img_cols = ['Requiere_Imagen', 'requiere_imagen']
                    for col in req_img_cols:
                        if col in df.columns and pd.notna(row[col]):
                            val = str(row[col]).strip().lower()
                            requiere_imagen = val in ['true', '1', 'sí', 'si', 'yes']
                            break

                    # Obtener URL de imagen de pregunta
                    img_pregunta_cols = ['Imagen_Pregunta_URL', 'imagen_pregunta_url', 'imagen_pregunta']
                    for col in img_pregunta_cols:
                        if col in df.columns and pd.notna(row[col]):
                            imagen_pregunta_url = str(row[col]).strip()
                            # Normalizar ruta para sistema Linux
                            if imagen_pregunta_url.startswith('C:\\') or imagen_pregunta_url.startswith('\\'):
                                # Convertir rutas Windows a Linux
                                imagen_pregunta_url = imagen_pregunta_url.replace('\\', '/').replace('C:', '')
                            if not imagen_pregunta_url.startswith('/') and imagen_pregunta_url:
                                imagen_pregunta_url = '/' + imagen_pregunta_url
                            break

                    # Obtener URLs de imágenes de opciones
                    for letra in option_letters:
                        img_opcion_cols = [
                            f'Imagen_Opcion_{letra}_URL',
                            f'imagen_opcion_{letra.lower()}_url',
                            f'imagen_opcion_{letra}'
                        ]
                        for col in img_opcion_cols:
                            if col in df.columns and pd.notna(row[col]):
                                url = str(row[col]).strip()
                                # Normalizar ruta
                                if url.startswith('C:\\') or url.startswith('\\'):
                                    url = url.replace('\\', '/').replace('C:', '')
                                if not url.startswith('/') and url:
                                    url = '/' + url
                                imagen_opciones_urls[letra] = url
                                break

                    # Obtener URL de imagen de contexto
                    img_contexto_cols = ['Imagen_Contexto_Comp', 'imagen_contexto', 'contexto_imagen']
                    for col in img_contexto_cols:
                        if col in df.columns and pd.notna(row[col]):
                            imagen_contexto_url = str(row[col]).strip()
                            # Normalizar ruta
                            if imagen_contexto_url.startswith('C:\\') or imagen_contexto_url.startswith('\\'):
                                imagen_contexto_url = imagen_contexto_url.replace('\\', '/').replace('C:', '')
                            if not imagen_contexto_url.startswith('/') and imagen_contexto_url:
                                imagen_contexto_url = '/' + imagen_contexto_url
                            break

                    # Asegurar que tenemos al menos 2 opciones
                    if len(options) < 2:
                        options = {
                            'A': options.get('A', 'Opción A'),
                            'B': options.get('B', 'Opción B'),
                            'C': options.get('C', 'Opción C'),
                            'D': options.get('D', 'Opción D'),
                        }

                    # Crear pregunta en formato compatible
                    question = {
                        "id": f"real_{subject_id}_{idx}",
                        "question_text": question_text,
                        "pregunta_texto": question_text,
                        "type": "multiple_choice",
                        "options": options,
                        "opcion_a_texto": options.get('A', ''),
                        "opcion_b_texto": options.get('B', ''),
                        "opcion_c_texto": options.get('C', ''),
                        "opcion_d_texto": options.get('D', ''),
                        "correct_answer": correct_answer,
                        "difficulty": 2,  # Medio por defecto
                        "subject_id": str(subject_id),
                        "topic": "Pregunta Real ICFES",
                        "explicacion_respuesta": explicacion or f"La respuesta correcta es {correct_answer}.",
                        "error_comun": "Revisa cuidadosamente cada opción y considera los conceptos fundamentales.",
                        # Campos de imagen
                        "requiere_imagen": requiere_imagen,
                        "imagen_pregunta_url": imagen_pregunta_url,
                        "imagen_opcion_a_url": imagen_opciones_urls.get('A', ''),
                        "imagen_opcion_b_url": imagen_opciones_urls.get('B', ''),
                        "imagen_opcion_c_url": imagen_opciones_urls.get('C', ''),
                        "imagen_opcion_d_url": imagen_opciones_urls.get('D', ''),
                        "imagen_contexto_url": imagen_contexto_url,
                        "imagen_opciones_urls": imagen_opciones_urls  # Para compatibilidad completa
                    }

                    # Agregar a la colección por materia
                    if subject_id not in all_questions:
                        all_questions[subject_id] = []

                    all_questions[subject_id].append(question)

                except Exception as e:
                    print(f"⚠️ Error procesando fila {idx}: {e}")
                    continue

            print(f"✅ Cargadas {sum(len(qs) for qs in all_questions.values())} preguntas desde {excel_path}")

        except Exception as e:
            print(f"❌ Error leyendo {excel_path}: {e}")
            continue

    # Verificar resultados
    total_questions = sum(len(qs) for qs in all_questions.values())
    print(f"\n📊 RESUMEN DE CARGA:")
    print(f"Total preguntas cargadas: {total_questions}")
    for subject_id, questions in all_questions.items():
        subject_names = {1: "Matemáticas", 2: "Lectura Crítica", 3: "Ciencias Naturales", 4: "Sociales", 5: "Inglés"}
        print(f"  - {subject_names.get(subject_id, f'Materia {subject_id}')}: {len(questions)} preguntas")

    return all_questions

if __name__ == "__main__":
    # Prueba del cargador
    questions = load_icfes_questions()
    print(f"\nEjemplo de pregunta cargada:")
    if questions:
        first_subject = list(questions.keys())[0]
        first_question = questions[first_subject][0]
        print(f"ID: {first_question['id']}")
        print(f"Pregunta: {first_question['question_text'][:100]}...")
        print(f"Opciones: {first_question['options']}")
        print(f"Respuesta correcta: {first_question['correct_answer']}")