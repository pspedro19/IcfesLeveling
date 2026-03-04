#!/usr/bin/env python3
"""
Carga el catálogo de videos YouTube a la base de datos.

Uso:
    python database/seed_data/load_youtube_videos.py

Requiere:
    - PostgreSQL corriendo
    - Archivo: database/catalogs/youtube_catalog_complete.csv
"""

import csv
import os
import psycopg2
from uuid import uuid4

# Configuración
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5433"),
    "database": os.getenv("POSTGRES_DB", "gameplay_db"),
    "user": os.getenv("POSTGRES_USER", "gameplay"),
    "password": os.getenv("POSTGRES_PASSWORD", "gameplay123")
}

CSV_PATH = "database/catalogs/youtube_catalog_complete.csv"

# Mapeo de nombres de materia a subject_id
# Los nombres deben coincidir con area_evaluada del CSV (en minúsculas)
SUBJECT_MAP = {
    "matemáticas": None,
    "lenguaje": None,
    "ciencias naturales": None,
    "ciencias sociales": None,
    "inglés": None,
    "ingles": None
}


def get_subject_ids(cursor):
    """Obtener IDs de materias de la base de datos"""
    cursor.execute("SELECT id, name FROM subjects")
    for row in cursor.fetchall():
        subject_id, name = row
        name_lower = name.lower().strip()

        # Mapeo directo por nombre exacto
        if name_lower == "matemáticas":
            SUBJECT_MAP["matemáticas"] = subject_id
        elif name_lower == "lenguaje":
            SUBJECT_MAP["lenguaje"] = subject_id
        elif name_lower == "ciencias naturales":
            SUBJECT_MAP["ciencias naturales"] = subject_id
        elif name_lower == "ciencias sociales":
            SUBJECT_MAP["ciencias sociales"] = subject_id
        elif name_lower == "inglés":
            SUBJECT_MAP["inglés"] = subject_id
            SUBJECT_MAP["ingles"] = subject_id

    print(f"Materias encontradas: {SUBJECT_MAP}")


def load_videos():
    """Cargar videos desde CSV a la base de datos"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Obtener IDs de materias
    get_subject_ids(cursor)

    # Leer CSV
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        # Use comma as delimiter for this specific file
        reader = csv.DictReader(f, delimiter=',')

        inserted = 0
        skipped = 0

        for row in reader:
            youtube_id = row.get("youtube_id") or row.get("youtube_video_id")
            if not youtube_id:
                skipped += 1
                continue

            # Determinar subject_id from 'area_evaluada'
            subject_name = row.get("area_evaluada", "").lower().strip()
            subject_id = SUBJECT_MAP.get(subject_name)
            
            if not subject_id:
                print(f"Warning: Subject ID not found for '{subject_name}'")
                skipped += 1
                continue

            # Insertar video
            try:
                cursor.execute("""
                    INSERT INTO youtube_videos
                    (id, youtube_id, title, channel_name, subject_id, difficulty_level, tags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (youtube_id) DO NOTHING
                """, (
                    str(uuid4()),
                    youtube_id,
                    row.get("tema_principal", "Sin título"),
                    row.get("canal_sugerido", ""),
                    subject_id,
                    5, # Default difficulty
                    '[]' # Default tags
                ))
                inserted += 1
            except Exception as e:
                print(f"Error insertando {youtube_id}: {e}")
                skipped += 1

        conn.commit()
        print(f"Videos insertados: {inserted}, Saltados: {skipped}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    load_videos()
