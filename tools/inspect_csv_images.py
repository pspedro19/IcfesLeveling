#!/usr/bin/env python3
import os
import csv

CSV_PATH = os.environ.get('CSV_PATH', 'ICFES2_normalized.csv')
REPORT_PATH = os.environ.get('REPORT_PATH', 'image_mapping_report.txt')

IMAGE_COLS = [
    'Imagen_Pregunta_URL',
    'Imagen_Opcion_A_URL',
    'Imagen_Opcion_B_URL',
    'Imagen_Opcion_C_URL',
    'Imagen_Opcion_D_URL',
]

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PUBLIC_ROOT = os.path.join(REPO_ROOT, 'apps', 'frontend', 'public')
PUBLIC_MATHIMG = os.path.join(PUBLIC_ROOT, 'mathimg')
SRC_MATHIMG = os.path.join(REPO_ROOT, 'mathimg')

def exists_any(base_name: str) -> bool:
    return (
        os.path.exists(os.path.join(PUBLIC_MATHIMG, base_name)) or
        os.path.exists(os.path.join(SRC_MATHIMG, base_name))
    )

def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        return 1

    total_refs = 0
    ok_local = 0
    external = 0
    missing = []

    with open(CSV_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        # Keep only image columns that are present
        cols = [c for c in IMAGE_COLS if c in reader.fieldnames]
        row_index = 1  # header is 1
        for row in reader:
            row_index += 1
            for c in cols:
                v = row.get(c, '')
                if v is None:
                    continue
                s = str(v).strip()
                if not s:
                    continue
                total_refs += 1
                if s.startswith('/mathimg/'):
                    base = os.path.basename(s)
                    if exists_any(base):
                        ok_local += 1
                    else:
                        missing.append((row_index, c, s))
                else:
                    # treat as external or non-normalized path
                    external += 1

    lines = []
    lines.append(f"CSV: {CSV_PATH}")
    lines.append(f"Checked columns: {IMAGE_COLS}")
    lines.append(f"TOTAL_REFERENCES={total_refs}")
    lines.append(f"OK_LOCAL={ok_local}")
    lines.append(f"EXTERNAL_OR_NON_NORMALIZED={external}")
    lines.append(f"MISSING_LOCAL_FILES={len(missing)}")
    if missing:
        lines.append("First 50 missing entries (row, column, value):")
        for m in missing[:50]:
            lines.append(str(m))

    with open(REPORT_PATH, 'w', encoding='utf-8') as rf:
        rf.write('\n'.join(lines) + '\n')

    print('\n'.join(lines))
    print(f"\nReport written to {REPORT_PATH}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())


