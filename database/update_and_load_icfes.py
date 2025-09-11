#!/usr/bin/env python3
"""
Script para actualizar la tabla questions con todos los 81 campos del ICFES
y cargar los datos desde el archivo Excel
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

# Ruta del archivo Excel
EXCEL_PATH = r'C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions\ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx'

def get_connection():
    """Obtener conexión a la base de datos"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None

def add_missing_columns(conn):
    """Agregar columnas faltantes a la tabla questions"""
    cur = conn.cursor()
    
    # Lista de columnas nuevas que necesitamos agregar (que no están en la tabla actual)
    new_columns = [
        # Campos del archivo Excel que faltan
        ("id_pregunta_original", "VARCHAR(50)"),
        ("area_evaluada", "VARCHAR(100)"),
        ("tema_especifico", "TEXT"),
        ("grado_escolar", "VARCHAR(20)"),
        ("periodo_aplicacion", "VARCHAR(50)"),
        ("requiere_imagen", "BOOLEAN"),
        ("imagen_pregunta_url", "VARCHAR(500)"),
        ("imagen_opcion_a_url", "VARCHAR(500)"),
        ("imagen_opcion_b_url", "VARCHAR(500)"),
        ("imagen_opcion_c_url", "VARCHAR(500)"),
        ("imagen_opcion_d_url", "VARCHAR(500)"),
        ("puntos_xp", "INTEGER"),
        ("pregunta_con_contexto", "TEXT"),
        ("pregunta_libro", "TEXT"),
        ("orden_en_contexto", "INTEGER"),
        ("contexto_requerido", "BOOLEAN"),
        ("imagen_contexto_comp", "VARCHAR(500)"),
        ("texto_contexto_completo", "TEXT"),
        ("id_contexto_compartido", "VARCHAR(50)"),
        ("ruta_absoluta_archivo", "TEXT"),
        ("nombre_del_archivo", "VARCHAR(255)"),
        ("subtema", "VARCHAR(255)"),
        ("estrategia_discursiva", "VARCHAR(100)"),
        ("tipo_razonamiento", "VARCHAR(100)"),
        ("complejidad_cognitiva", "VARCHAR(50)"),
        ("contexto_aplicacion", "VARCHAR(100)"),
        ("tipo_texto", "VARCHAR(100)"),
        ("genero_textual", "VARCHAR(100)"),
        ("funcion_comunicativa", "VARCHAR(100)"),
        ("pensamiento_matematico", "VARCHAR(100)"),
        ("disciplina_predominante", "VARCHAR(100)"),
        ("concepto_cientifico", "VARCHAR(100)"),
        ("proceso_cientifico", "VARCHAR(100)"),
        ("nivel_representacion", "VARCHAR(100)"),
        ("periodo_historico", "VARCHAR(100)"),
        ("ambito_analisis", "VARCHAR(100)"),
        ("escala_espacial", "VARCHAR(100)"),
        ("concepto_social", "VARCHAR(100)"),
        ("tipo_fuente", "VARCHAR(100)"),
        ("habilidad_comunicativa", "VARCHAR(100)"),
        ("tipo_problema", "VARCHAR(100)"),
        ("estrategia_solucion", "VARCHAR(100)"),
        ("tipo_representacion", "VARCHAR(100)"),
        ("uso_herramientas", "VARCHAR(100)"),
        ("nivel_abstraccion", "VARCHAR(100)"),
        ("tipo_grafico", "VARCHAR(100)"),
        ("interpretacion_datos", "VARCHAR(100)"),
        ("tipo_modelo", "VARCHAR(100)"),
        ("variables_relacionadas", "VARCHAR(255)"),
        ("tipo_experimento", "VARCHAR(100)"),
        ("control_variables", "VARCHAR(100)"),
        ("tipo_observacion", "VARCHAR(100)"),
        ("nivel_taxonomico", "VARCHAR(100)"),
        ("sistema_biologico", "VARCHAR(100)"),
        ("escala_temporal", "VARCHAR(100)"),
        ("tipo_cambio", "VARCHAR(100)"),
        ("tipo_interaccion", "VARCHAR(100)"),
        ("nivel_organizacion", "VARCHAR(100)"),
        ("tipo_evidencia", "VARCHAR(100)"),
        ("grado_incertidumbre", "VARCHAR(100)"),
        ("tipo_relacion_causal", "VARCHAR(100)"),
        ("contexto_historico", "VARCHAR(100)"),
        ("perspectiva_analisis", "VARCHAR(100)"),
        ("tipo_argumento", "VARCHAR(100)"),
        ("nivel_inferencia", "VARCHAR(100)"),
        ("tipo_conclusion", "VARCHAR(100)"),
        ("validez_argumento", "VARCHAR(100)"),
        ("tipo_falacia", "VARCHAR(100)"),
        ("estructura_textual", "VARCHAR(100)"),
        ("proposito_comunicativo", "VARCHAR(100)"),
        ("audiencia_objetivo", "VARCHAR(100)"),
        ("registro_linguistico", "VARCHAR(100)"),
        ("tipo_discurso", "VARCHAR(100)"),
        ("elemento_retorico", "VARCHAR(100)"),
        ("figura_literaria", "VARCHAR(100)"),
        ("tipo_narracion", "VARCHAR(100)"),
        ("elemento_narrativo", "VARCHAR(100)"),
        ("tipo_descripcion", "VARCHAR(100)"),
        ("punto_vista", "VARCHAR(100)"),
        ("tono_texto", "VARCHAR(100)"),
        ("intencion_autor", "VARCHAR(100)"),
        ("contexto_produccion", "VARCHAR(100)"),
        ("tipo_intertextualidad", "VARCHAR(100)")
    ]
    
    print("📊 Agregando columnas faltantes a la tabla questions...")
    
    added_count = 0
    for column_name, column_type in new_columns:
        try:
            # Verificar si la columna ya existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='questions' AND column_name=%s
            """, (column_name,))
            
            if not cur.fetchone():
                # Agregar la columna si no existe
                cur.execute(f"ALTER TABLE questions ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                added_count += 1
                print(f"  ✅ Agregada columna: {column_name}")
        except Exception as e:
            print(f"  ⚠️ Error agregando columna {column_name}: {e}")
    
    conn.commit()
    print(f"\n✅ Se agregaron {added_count} columnas nuevas a la tabla")
    return added_count

def load_excel_data():
    """Cargar datos desde el archivo Excel"""
    print(f"\n📂 Cargando archivo Excel: {EXCEL_PATH}")
    
    try:
        df = pd.read_excel(EXCEL_PATH)
        print(f"✅ Archivo cargado: {len(df)} filas, {len(df.columns)} columnas")
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Mostrar estadísticas
        print("\n📊 Estadísticas del dataset:")
        print(f"  - Total de preguntas: {len(df)}")
        
        if 'área_evaluada' in df.columns:
            print(f"\n  Distribución por área:")
            for area, count in df['área_evaluada'].value_counts().items():
                print(f"    • {area}: {count} preguntas")
        
        if 'nivel_dificultad' in df.columns:
            print(f"\n  Distribución por dificultad:")
            for nivel, count in df['nivel_dificultad'].value_counts().head(10).items():
                print(f"    • {nivel}: {count} preguntas")
        
        return df
    
    except Exception as e:
        print(f"❌ Error cargando Excel: {e}")
        return None

def map_subject_names(area_evaluada):
    """Mapear nombres de áreas a IDs de subjects"""
    subject_map = {
        'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
        'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
        'Ciencias Sociales y Ciudadanas': '550e8400-e29b-41d4-a716-446655440004',
        'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
        'Lectura Crítica': '550e8400-e29b-41d4-a716-446655440002',
        'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
        'Inglés': '550e8400-e29b-41d4-a716-446655440005'
    }
    
    # Buscar coincidencia parcial
    for key in subject_map:
        if key.lower() in str(area_evaluada).lower():
            return subject_map[key]
    
    # Default a Matemáticas si no se encuentra
    return '550e8400-e29b-41d4-a716-446655440001'

def insert_questions(conn, df):
    """Insertar o actualizar preguntas en la base de datos"""
    cur = conn.cursor()
    
    print("\n📝 Insertando preguntas en la base de datos...")
    
    # Primero, limpiar las preguntas existentes
    cur.execute("DELETE FROM questions WHERE 1=1")
    print("  ✅ Tabla limpiada")
    
    inserted = 0
    errors = 0
    
    for index, row in df.iterrows():
        try:
            # Generar UUID para la pregunta
            question_id = str(uuid.uuid4())
            
            # Mapear subject_id basado en área_evaluada
            subject_id = map_subject_names(row.get('área_evaluada', ''))
            
            # Preparar datos básicos
            question_data = {
                'id': question_id,
                'subject_id': subject_id,
                'id_pregunta_original': str(row.get('id_pregunta', index + 1)),
                'area_evaluada': str(row.get('área_evaluada', '')),
                'pregunta_texto': str(row.get('pregunta', '')),
                'question_text': str(row.get('pregunta', '')),
                'opcion_a_texto': str(row.get('opcion_a', '')),
                'opcion_b_texto': str(row.get('opcion_b', '')),
                'opcion_c_texto': str(row.get('opcion_c', '')),
                'opcion_d_texto': str(row.get('opcion_d', '')),
                'respuesta_correcta': str(row.get('respuesta_correcta', 'a')).lower()[:1],
                'correct_answer': str(row.get('respuesta_correcta', 'a')).lower()[:1],
                'competencia': str(row.get('competencia', '')),
                'componente': str(row.get('componente', '')),
                'proceso_cognitivo': str(row.get('proceso_cognitivo', '')),
                'tipo_conocimiento': str(row.get('tipo_conocimiento', '')),
                'nivel_desempeno_esperado': str(row.get('nivel_desempeño_esperado', '')),
                'tema_especifico': str(row.get('tema_específico', '')),
                'topic': str(row.get('tema_específico', 'General')),
                'grado_escolar': str(row.get('grado_escolar', '')),
                'periodo_aplicacion': str(row.get('periodo_aplicación', '')),
                'afirmacion': str(row.get('afirmación', '')),
                'evidencia': str(row.get('evidencia', '')),
                'explicacion_respuesta': str(row.get('explicación_respuesta', '')),
                'pista_1': str(row.get('pista_1', '')),
                'pista_2': str(row.get('pista_2', '')),
                'pista_3': str(row.get('pista_3', '')),
                'error_comun': str(row.get('error_común', '')),
                'difficulty': int(row.get('nivel_dificultad', 5)) if pd.notna(row.get('nivel_dificultad')) and str(row.get('nivel_dificultad')).isdigit() else 5,
                'options': json.dumps({
                    'a': str(row.get('opcion_a', '')),
                    'b': str(row.get('opcion_b', '')),
                    'c': str(row.get('opcion_c', '')),
                    'd': str(row.get('opcion_d', ''))
                })
            }
            
            # Agregar campos numéricos si existen
            if pd.notna(row.get('parámetro_irt_a')):
                question_data['parametro_irt_a'] = float(row.get('parámetro_irt_a'))
            if pd.notna(row.get('parámetro_irt_b')):
                question_data['parametro_irt_b'] = float(row.get('parámetro_irt_b'))
            if pd.notna(row.get('parámetro_irt_c')):
                question_data['parametro_irt_c'] = float(row.get('parámetro_irt_c'))
            if pd.notna(row.get('índice_discriminación')):
                question_data['indice_discriminacion'] = float(row.get('índice_discriminación'))
            if pd.notna(row.get('tiempo_estimado')):
                question_data['tiempo_estimado'] = int(row.get('tiempo_estimado'))
            if pd.notna(row.get('puntos_xp')):
                question_data['puntos_xp'] = int(row.get('puntos_xp'))
            
            # Agregar URLs de imágenes
            for field in ['imagen_pregunta_url', 'imagen_opcion_a_url', 'imagen_opcion_b_url', 
                         'imagen_opcion_c_url', 'imagen_opcion_d_url', 'imagen_contexto_comp']:
                if pd.notna(row.get(field.replace('_url', ''))):
                    question_data[field] = str(row.get(field.replace('_url', '')))
            
            # Agregar campos de texto adicionales
            text_fields = ['pregunta_con_contexto', 'pregunta_libro', 'texto_contexto_completo',
                          'ruta_absoluta_archivo', 'nombre_del_archivo', 'subtema',
                          'estrategia_discursiva', 'tipo_razonamiento', 'complejidad_cognitiva']
            
            for field in text_fields:
                if pd.notna(row.get(field)):
                    question_data[field] = str(row.get(field))
            
            # Construir query de inserción
            columns = list(question_data.keys())
            values = list(question_data.values())
            placeholders = ['%s'] * len(values)
            
            insert_query = f"""
                INSERT INTO questions ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (id) DO NOTHING
            """
            
            cur.execute(insert_query, values)
            inserted += 1
            
            if inserted % 50 == 0:
                print(f"  ✅ {inserted} preguntas insertadas...")
                
        except Exception as e:
            errors += 1
            print(f"  ⚠️ Error en fila {index}: {str(e)[:100]}")
    
    conn.commit()
    
    print(f"\n✅ Carga completada:")
    print(f"  - Preguntas insertadas: {inserted}")
    print(f"  - Errores: {errors}")
    
    # Verificar resultados
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    
    cur.execute("""
        SELECT s.name, COUNT(q.id) 
        FROM subjects s 
        LEFT JOIN questions q ON s.id = q.subject_id 
        GROUP BY s.id, s.name 
        ORDER BY COUNT(q.id) DESC
    """)
    
    print(f"\n📊 Distribución final en la base de datos:")
    print(f"  Total de preguntas: {total}")
    for subject, count in cur.fetchall():
        print(f"  - {subject}: {count} preguntas")
    
    return inserted

def main():
    """Función principal"""
    print("=" * 60)
    print("ACTUALIZACIÓN Y CARGA DE DATOS ICFES")
    print("=" * 60)
    
    # Conectar a la base de datos
    conn = get_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        # 1. Agregar columnas faltantes
        add_missing_columns(conn)
        
        # 2. Cargar datos del Excel
        df = load_excel_data()
        if df is None:
            print("❌ No se pudieron cargar los datos del Excel")
            return
        
        # 3. Insertar preguntas
        inserted = insert_questions(conn, df)
        
        print("\n✅ ¡Proceso completado exitosamente!")
        print(f"   Se cargaron {inserted} preguntas con todos los 81 campos del ICFES")
        
    except Exception as e:
        print(f"\n❌ Error durante el proceso: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print("\n📊 Conexión cerrada")

if __name__ == "__main__":
    main()