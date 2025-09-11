#!/usr/bin/env python3
"""
Script to verify image paths consistency between Excel and physical files
"""

import pandas as pd
import os
from pathlib import Path

def normalize_path(path_str):
    """Normalize path for comparison"""
    if pd.isna(path_str) or path_str == ' ':
        return None
    # Convert to Windows path style and normalize
    normalized = str(Path(path_str)).replace('/', '\\')
    return normalized

def verify_image_paths():
    excel_path = r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions\ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
    base_path = r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions"
    
    print("VERIFICACIÓN DE CONSISTENCIA DE RUTAS - MULTIMEDIA")
    print("="*80)
    
    df = pd.read_excel(excel_path)
    
    # Image columns to check
    image_columns = [
        'Imagen_Pregunta_URL',
        'Imagen_Opcion_A_URL', 
        'Imagen_Opcion_B_URL',
        'Imagen_Opcion_C_URL',
        'Imagen_Opcion_D_URL',
        'Imagen_Contexto_Comp'
    ]
    
    total_paths = 0
    existing_files = 0
    missing_files = 0
    missing_file_list = []
    
    for col in image_columns:
        print(f"\n--- Analizando columna: {col} ---")
        non_null_count = df[col].count()
        print(f"Rutas no vacías: {non_null_count}")
        
        col_total = 0
        col_existing = 0
        col_missing = 0
        
        for idx, path in df[col].dropna().items():
            if path and path != ' ':
                col_total += 1
                total_paths += 1
                
                # Try to find the file in the current structure
                original_path = normalize_path(path)
                
                # Extract filename from original path
                if original_path:
                    filename = os.path.basename(original_path)
                    
                    # Search for file in current directory structure
                    found = False
                    for root, dirs, files in os.walk(base_path):
                        if filename in files:
                            found = True
                            col_existing += 1
                            existing_files += 1
                            break
                    
                    if not found:
                        col_missing += 1
                        missing_files += 1
                        missing_file_list.append({
                            'row': idx + 1,
                            'column': col,
                            'filename': filename,
                            'original_path': original_path
                        })
        
        print(f"  Total rutas: {col_total}")
        print(f"  Archivos encontrados: {col_existing}")
        print(f"  Archivos faltantes: {col_missing}")
        if col_total > 0:
            print(f"  Porcentaje encontrado: {(col_existing/col_total)*100:.1f}%")
    
    # Summary
    print(f"\n" + "="*80)
    print(f"RESUMEN GENERAL")
    print(f"="*80)
    print(f"Total de rutas en Excel: {total_paths}")
    print(f"Archivos físicos encontrados: {existing_files}")
    print(f"Archivos faltantes: {missing_files}")
    print(f"Porcentaje de consistencia: {(existing_files/total_paths)*100:.1f}%")
    
    # Show distribution by subject
    print(f"\nDISTRIBUCIÓN POR MATERIA:")
    subject_counts = df['Área_Evaluada'].value_counts()
    for subject, count in subject_counts.items():
        print(f"  {subject}: {count} preguntas")
    
    # List some missing files
    if missing_file_list:
        print(f"\nPRIMEROS 10 ARCHIVOS FALTANTES:")
        for item in missing_file_list[:10]:
            print(f"  Fila {item['row']}: {item['filename']}")
    
    return {
        'total_paths': total_paths,
        'existing_files': existing_files,
        'missing_files': missing_files,
        'missing_list': missing_file_list
    }

if __name__ == "__main__":
    verify_image_paths()