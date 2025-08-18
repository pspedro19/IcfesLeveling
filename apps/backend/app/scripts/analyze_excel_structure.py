#!/usr/bin/env python3
"""Analyze Excel file structure to understand the data"""

import pandas as pd
import json

def analyze_excel():
    """Analyze the ICFES Excel file structure"""
    
    # Try both possible file paths
    file_paths = [
        '/app/ICFES2 (1).xlsx',
        '/app/ICFES2.xlsx',
        'ICFES2 (1).xlsx',
        'ICFES2.xlsx'
    ]
    
    df = None
    for path in file_paths:
        try:
            df = pd.read_excel(path)
            print(f"✅ Successfully loaded: {path}")
            break
        except:
            continue
    
    if df is None:
        print("❌ Could not load Excel file")
        return
    
    print("\n📊 EXCEL FILE ANALYSIS")
    print("=" * 60)
    
    # Basic info
    print(f"\n📈 Basic Information:")
    print(f"  - Total rows: {len(df)}")
    print(f"  - Total columns: {len(df.columns)}")
    
    # Column names and types
    print(f"\n📋 Column Names and Data Types:")
    for i, col in enumerate(df.columns, 1):
        non_null = df[col].notna().sum()
        unique_vals = df[col].nunique()
        dtype = str(df[col].dtype)
        print(f"  {i:2}. '{col}'")
        print(f"      - Type: {dtype}")
        print(f"      - Non-null: {non_null}/{len(df)}")
        print(f"      - Unique values: {unique_vals}")
        
        # Show sample values
        sample_vals = df[col].dropna().head(3).tolist()
        if sample_vals:
            print(f"      - Samples: {sample_vals[:3]}")
    
    # Look for question-related columns
    print(f"\n🔍 Detected Question-Related Columns:")
    question_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(term in col_lower for term in ['pregunta', 'question', 'texto', 'enunciado']):
            question_cols.append(col)
            print(f"  - Question text: '{col}'")
        elif any(term in col_lower for term in ['opcion', 'option', 'alternativa']):
            print(f"  - Option: '{col}'")
        elif any(term in col_lower for term in ['respuesta', 'answer', 'correcta']):
            print(f"  - Answer: '{col}'")
        elif any(term in col_lower for term in ['materia', 'subject', 'area', 'asignatura']):
            print(f"  - Subject: '{col}'")
        elif any(term in col_lower for term in ['tema', 'topic', 'topico']):
            print(f"  - Topic: '{col}'")
        elif any(term in col_lower for term in ['dificultad', 'difficulty', 'nivel']):
            print(f"  - Difficulty: '{col}'")
    
    # Sample data
    print(f"\n📝 Sample Data (First 2 rows):")
    print("-" * 60)
    for idx in range(min(2, len(df))):
        print(f"\nRow {idx + 1}:")
        for col in df.columns:
            val = df.iloc[idx][col]
            if pd.notna(val):
                print(f"  {col}: {str(val)[:100]}")
    
    # Analyze unique values in key columns
    print(f"\n🏷️ Unique Values in Key Columns:")
    for col in df.columns:
        col_lower = col.lower()
        if any(term in col_lower for term in ['materia', 'subject', 'area', 'tipo', 'type', 'categoria']):
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) <= 20:
                print(f"\n  {col}:")
                for val in unique_vals:
                    print(f"    - {val}")

if __name__ == "__main__":
    analyze_excel()