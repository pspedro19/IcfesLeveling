#!/usr/bin/env python3
"""
Script para cargar el catálogo completo de YouTube desde CSV
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import uuid
import json
import re
from pathlib import Path

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

def clean_youtube_id(url):
    """Extrae el ID del video de YouTube de la URL"""
    if not url:
        return None
    
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return url.split('/')[-1][:11] if url else None

def calculate_difficulty(tema_principal):
    """Calcula la dificultad basándose en el tema"""
    difficulty_map = {
        'basica': 3,
        'basico': 3,
        'introduccion': 2,
        'fundamental': 2,
        'intermedio': 5,
        'avanzado': 7,
        'complejo': 8,
        'profundo': 8,
        'integral': 6,
        'diferencial': 7,
        'cuantica': 9,
        'relatividad': 9
    }
    
    tema_lower = tema_principal.lower() if tema_principal else ''
    for keyword, diff in difficulty_map.items():
        if keyword in tema_lower:
            return diff
    
    return 5  # Dificultad media por defecto

def calculate_xp(difficulty, duration=900):
    """Calcula XP basándose en dificultad y duración"""
    base_xp = 50
    difficulty_bonus = difficulty * 10
    duration_bonus = (duration // 300) * 10  # 10 XP por cada 5 minutos
    return base_xp + difficulty_bonus + duration_bonus

def load_youtube_catalog():
    """Carga el catálogo de YouTube desde el CSV"""
    
    # Ruta al archivo CSV
    csv_path = Path(__file__).parent.parent / 'database' / 'seed_data' / 'youtube_catalog_extendido_enriquecido.csv'
    
    print(f"📁 Cargando archivo: {csv_path}")
    
    try:
        # Leer CSV con punto y coma como separador
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8', on_bad_lines='skip')
        print(f"✅ CSV cargado: {len(df)} registros encontrados")
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Verificar columnas necesarias
        required_columns = ['codigo_tema', 'area_evaluada', 'tema_principal', 'youtube_url']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Columnas faltantes: {missing_columns}")
            print(f"Columnas disponibles: {df.columns.tolist()}")
            return
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Limpiar tabla existente
        cur.execute("DELETE FROM youtube_links")
        print("🗑️ Tabla youtube_links limpiada")
        
        # Preparar datos para inserción
        records = []
        successful = 0
        failed = 0
        
        for idx, row in df.iterrows():
            try:
                # Extraer datos
                codigo_tema = row.get('codigo_tema', f'CODE{idx:04d}')
                area_evaluada = row.get('area_evaluada', 'General')
                tema_principal = row.get('tema_principal', 'Tema General')
                canal_sugerido = row.get('canal_sugerido', 'Canal Educativo')
                youtube_url = row.get('youtube_url', '')
                
                # Saltar si no hay URL
                if not youtube_url or pd.isna(youtube_url):
                    failed += 1
                    continue
                
                # Limpiar canal (quitar @)
                if canal_sugerido and isinstance(canal_sugerido, str):
                    canal_sugerido = canal_sugerido.replace('@', '').strip()
                
                # Extraer ID del video
                youtube_id = clean_youtube_id(youtube_url)
                if not youtube_id:
                    failed += 1
                    continue
                
                # Calcular valores
                difficulty = calculate_difficulty(tema_principal)
                duration = 900  # 15 minutos por defecto
                xp = calculate_xp(difficulty, duration)
                
                # Crear título del video
                video_title = f"{tema_principal} - {area_evaluada}"
                if canal_sugerido and canal_sugerido != 'nan':
                    video_title += f" ({canal_sugerido})"
                
                # Preparar registro
                record = (
                    str(uuid.uuid4()),  # id
                    str(codigo_tema),  # codigo_tema
                    area_evaluada,  # area_evaluada
                    tema_principal,  # tema_principal
                    canal_sugerido if canal_sugerido and canal_sugerido != 'nan' else 'Canal Educativo',  # canal_sugerido
                    f"{tema_principal} {area_evaluada}",  # query_sugerida
                    youtube_url,  # youtube_url
                    youtube_id,  # youtube_id
                    video_title,  # video_title
                    canal_sugerido if canal_sugerido and canal_sugerido != 'nan' else 'Canal Educativo',  # channel_name
                    None,  # channel_id
                    duration,  # duration_seconds
                    None,  # view_count
                    None,  # like_count
                    None,  # dislike_count
                    None,  # comment_count
                    'educativo',  # tipo_contenido
                    difficulty,  # nivel_dificultad
                    'comprension',  # proceso_cognitivo
                    'academico',  # contexto_aplicacion
                    4.5,  # calidad_score
                    4.5,  # relevancia_score
                    None,  # ratio_likes
                    None,  # prerequisitos_video
                    duration // 60,  # tiempo_estimado_estudio (en minutos)
                    xp,  # puntos_xp
                    idx + 1,  # orden_recomendacion
                    True,  # verificado_instructor
                    None,  # fecha_verificacion
                    'activo'  # estado
                )
                
                records.append(record)
                successful += 1
                
                if successful % 50 == 0:
                    print(f"  Procesados: {successful} videos...")
                    
            except Exception as e:
                print(f"  ⚠️ Error en fila {idx}: {e}")
                failed += 1
                continue
        
        # Insertar registros en batch
        if records:
            insert_query = """
                INSERT INTO youtube_links (
                    id, codigo_tema, area_evaluada, tema_principal, canal_sugerido,
                    query_sugerida, youtube_url, youtube_id, video_title, channel_name,
                    channel_id, duration_seconds, view_count, like_count, dislike_count,
                    comment_count, tipo_contenido, nivel_dificultad, proceso_cognitivo,
                    contexto_aplicacion, calidad_score, relevancia_score, ratio_likes,
                    prerequisitos_video, tiempo_estimado_estudio, puntos_xp,
                    orden_recomendacion, verificado_instructor, fecha_verificacion, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            execute_batch(cur, insert_query, records, page_size=100)
            conn.commit()
            
            print(f"\n✅ Inserción completada:")
            print(f"  - Videos cargados: {successful}")
            print(f"  - Videos omitidos: {failed}")
            
            # Verificar la carga
            cur.execute("SELECT COUNT(*) FROM youtube_links")
            total = cur.fetchone()[0]
            
            cur.execute("""
                SELECT area_evaluada, COUNT(*) as total 
                FROM youtube_links 
                GROUP BY area_evaluada 
                ORDER BY total DESC
            """)
            
            print(f"\n📊 Resumen por área:")
            for area, count in cur.fetchall():
                print(f"  - {area}: {count} videos")
            
            print(f"\n🎉 Total de videos en la base de datos: {total}")
            
        else:
            print("❌ No se encontraron registros válidos para insertar")
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {csv_path}")
    except pd.errors.EmptyDataError:
        print("❌ El archivo CSV está vacío")
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando carga del catálogo de YouTube...")
    load_youtube_catalog()
    print("✨ Proceso completado")