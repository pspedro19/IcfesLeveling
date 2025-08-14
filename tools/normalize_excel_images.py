#!/usr/bin/env python3
import os
import sys
import pandas as pd

EXCEL_PATH = os.environ.get('EXCEL_PATH', 'ICFES2 (1).xlsx')
OUTPUT_CSV = os.environ.get('OUTPUT_CSV', 'ICFES2_normalized.csv')

IMAGE_COLS = [
    'Imagen_Pregunta_URL',
    'Imagen_Opcion_A_URL',
    'Imagen_Opcion_B_URL',
    'Imagen_Opcion_C_URL',
    'Imagen_Opcion_D_URL',
]

# Detect repo root relative to this script if running locally
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MATHIMG_DIRS = [
    os.path.join(REPO_ROOT, 'mathimg'),
    os.path.join(REPO_ROOT, 'apps', 'frontend', 'public', 'mathimg'),
]
PUBLIC_PREFIX = '/mathimg/'

# Preload available filenames in mathimg dirs for fuzzy matching
AVAILABLE_FILES = []
for d in MATHIMG_DIRS:
    if os.path.isdir(d):
        for name in os.listdir(d):
            if name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                AVAILABLE_FILES.append(name)

def normalize_token(s: str) -> str:
    return ''.join(ch for ch in s.lower() if ch.isalnum())

def find_best_file(base: str) -> str | None:
    """Return best matching filename in AVAILABLE_FILES for given base path or name."""
    if not base:
        return None
    bname = os.path.basename(base)
    # Exact match
    for d in MATHIMG_DIRS:
        if os.path.exists(os.path.join(d, bname)):
            return bname
    # Try by normalized stem substring
    stem = os.path.splitext(bname)[0]
    nstem = normalize_token(stem)
    best = None
    best_score = 0
    for fname in AVAILABLE_FILES:
        nfile = normalize_token(os.path.splitext(fname)[0])
        # simple score: length of common substring intersection
        score = 0
        # direct containment
        if nstem and nstem in nfile:
            score = len(nstem)
        elif nfile in nstem:
            score = len(nfile)
        # fall back to shared digits
        digits = ''.join(ch for ch in nstem if ch.isdigit())
        if not score and digits and digits in nfile:
            score = len(digits)
        if score > best_score:
            best_score = score
            best = fname
    # require a minimal score to avoid wrong mappings (slightly relaxed)
    if best and best_score >= 2:
        return best
    return None


def resolve_image(value: object) -> object:
    if pd.isna(value):
        return value
    try:
        s = str(value).strip()
    except Exception:
        return value
    if not s:
        return s
    # Try to find a best filename in our mathimg pool
    best = find_best_file(s)
    if best:
        return PUBLIC_PREFIX + best
    # Otherwise, keep original value (could be an external URL)
    return s


def main():
    if not os.path.exists(EXCEL_PATH):
        print(f"ERROR: Excel not found: {EXCEL_PATH}")
        sys.exit(1)

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet = xls.sheet_names[0]
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)

    # Normalize only the image columns that exist in the sheet
    present_cols = [c for c in IMAGE_COLS if c in df.columns]
    if not present_cols:
        print("WARNING: No image columns found to normalize.")
    for col in present_cols:
        df[col] = df[col].apply(resolve_image)

    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"OK: Wrote normalized CSV → {OUTPUT_CSV}")


if __name__ == '__main__':
    main()


