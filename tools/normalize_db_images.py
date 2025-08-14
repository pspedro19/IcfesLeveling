#!/usr/bin/env python3
import os
import json
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'gameplay_db')
DB_USER = os.getenv('DB_USER', 'gameplay')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'gameplay123')

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PUBLIC_MATHIMG_DIR = os.path.join(REPO_ROOT, 'apps', 'frontend', 'public', 'mathimg')
PUBLIC_PREFIX = '/mathimg/'

def build_lower_map(dir_path: str):
    try:
        return {f.lower(): f for f in os.listdir(dir_path)} if os.path.isdir(dir_path) else {}
    except Exception:
        return {}

def resolve_basename_case_insensitive(base_name: str, lower_map: dict) -> str:
    if not base_name:
        return base_name
    key = base_name.lower()
    return lower_map.get(key, base_name)

def main():
    lower_map_public = build_lower_map(PUBLIC_MATHIMG_DIR)
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT id, image_url, options_images FROM questions")
    rows = cur.fetchall()

    updated = 0
    for qid, image_url, options_images in rows:
        new_image_url = None
        if image_url:
            bname = os.path.basename(str(image_url))
            bname = resolve_basename_case_insensitive(bname, lower_map_public)
            new_image_url = PUBLIC_PREFIX + bname

        new_options_images = {}
        try:
            if isinstance(options_images, str):
                oi = json.loads(options_images) if options_images else {}
            else:
                oi = options_images or {}
        except Exception:
            oi = {}

        for letter in ['A','B','C','D','E']:
            val = oi.get(letter) or oi.get(letter.lower())
            if not val:
                continue
            bname = os.path.basename(str(val))
            bname = resolve_basename_case_insensitive(bname, lower_map_public)
            new_options_images[letter] = PUBLIC_PREFIX + bname

        # Derivar columnas multimedia por compatibilidad
        opcion_a_imagen = new_options_images.get('A')
        opcion_b_imagen = new_options_images.get('B')
        opcion_c_imagen = new_options_images.get('C')
        opcion_d_imagen = new_options_images.get('D')

        cur.execute(
            """
            UPDATE questions
            SET image_url = COALESCE(%s, image_url),
                options_images = CASE WHEN %s::text <> '{}' THEN %s ELSE options_images END,
                pregunta_imagen = COALESCE(%s, pregunta_imagen),
                opcion_a_imagen = COALESCE(%s, opcion_a_imagen),
                opcion_b_imagen = COALESCE(%s, opcion_b_imagen),
                opcion_c_imagen = COALESCE(%s, opcion_c_imagen),
                opcion_d_imagen = COALESCE(%s, opcion_d_imagen)
            WHERE id = %s
            """,
            (
                new_image_url,
                json.dumps(new_options_images),
                json.dumps(new_options_images),
                new_image_url,
                opcion_a_imagen,
                opcion_b_imagen,
                opcion_c_imagen,
                opcion_d_imagen,
                qid,
            )
        )
        updated += 1

    cur.close()
    conn.close()
    print(f"Normalized image paths for {updated} questions → /mathimg/<archivo> (case-insensitive)")

if __name__ == '__main__':
    main()


