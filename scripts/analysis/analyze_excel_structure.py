#!/usr/bin/env python3
"""
Script to analyze the Excel file structure and understand the data format
"""

import pandas as pd
import os
import sys
from pathlib import Path

def analyze_excel_structure(excel_path: str):
    """Analyze the Excel file to understand its structure"""
    try:
        print(f"Analyzing Excel file: {excel_path}")
        
        # Read Excel file
        df = pd.read_excel(excel_path)
        
        print(f"\n" + "="*80)
        print(f"EXCEL FILE ANALYSIS REPORT")
        print(f"="*80)
        
        print(f"\nBASIC INFORMATION:")
        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}")
        print(f"   File size: {os.path.getsize(excel_path) / (1024*1024):.2f} MB")
        
        print(f"\nCOLUMN NAMES ({len(df.columns)} columns):")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. '{col}'")
        
        print(f"\nSAMPLE DATA (First 3 rows):")
        print(df.head(3).to_string())
        
        print(f"\nDATA TYPES:")
        print(df.dtypes)
        
        print(f"\nNON-NULL COUNTS:")
        print(df.count())
        
        print(f"\nPOTENTIAL SUBJECT MAPPING:")
        # Look for subject/area columns
        subject_cols = [col for col in df.columns if any(keyword in col.lower() 
                       for keyword in ['area', 'subject', 'materia', 'evaluada', 'tema'])]
        
        for col in subject_cols:
            if not df[col].isna().all():
                unique_values = df[col].dropna().unique()
                print(f"   Column '{col}': {len(unique_values)} unique values")
                for val in sorted(unique_values)[:10]:  # Show first 10
                    count = len(df[df[col] == val])
                    print(f"      - '{val}': {count} questions")
                if len(unique_values) > 10:
                    print(f"      ... and {len(unique_values) - 10} more values")
        
        print(f"\nIMAGE COLUMNS:")
        image_cols = [col for col in df.columns if any(keyword in col.lower() 
                     for keyword in ['imagen', 'image', 'url', 'ruta', 'path'])]
        
        for col in image_cols:
            non_null_count = df[col].count()
            print(f"   Column '{col}': {non_null_count} non-null values")
            if non_null_count > 0:
                sample_values = df[col].dropna().head(3).tolist()
                for val in sample_values:
                    print(f"      Sample: '{val}'")
        
        print(f"\nQUESTION COMPLETENESS:")
        # Check for complete questions (question + options + correct answer)
        question_cols = [col for col in df.columns if any(keyword in col.lower() 
                        for keyword in ['pregunta', 'question', 'enunciado'])]
        option_cols = [col for col in df.columns if any(keyword in col.lower() 
                      for keyword in ['opcion', 'option']) and any(letter in col.lower() 
                      for letter in ['a', 'b', 'c', 'd'])]
        answer_cols = [col for col in df.columns if any(keyword in col.lower() 
                      for keyword in ['respuesta', 'correcta', 'answer', 'correct'])]
        
        print(f"   Question columns found: {len(question_cols)}")
        print(f"   Option columns found: {len(option_cols)}")
        print(f"   Answer columns found: {len(answer_cols)}")
        
        if question_cols:
            main_question_col = question_cols[0]
            complete_questions = df[main_question_col].count()
            print(f"   Complete questions: {complete_questions}")
        
        print(f"\nMETADATA COLUMNS:")
        metadata_keywords = ['dificultad', 'difficulty', 'competencia', 'cognitive', 'tiempo', 'time', 
                           'nivel', 'level', 'proceso', 'process', 'conocimiento', 'knowledge']
        metadata_cols = [col for col in df.columns if any(keyword in col.lower() 
                        for keyword in metadata_keywords)]
        
        for col in metadata_cols:
            non_null_count = df[col].count()
            print(f"   Column '{col}': {non_null_count} values")
            if non_null_count > 0:
                unique_values = df[col].dropna().unique()
                print(f"      Unique values: {len(unique_values)}")
                for val in list(unique_values)[:5]:  # Show first 5
                    print(f"         - '{val}'")
        
        print(f"\n" + "="*80)
        
        return df
        
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")
        return None

def main():
    excel_path = r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions\ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"Excel file not found: {excel_path}")
        return
    
    analyze_excel_structure(excel_path)

if __name__ == "__main__":
    main()