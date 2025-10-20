#!/usr/bin/env python3
"""
ICFES Excel Data Analysis Script
Analyzes the complete ICFES database Excel file and generates comprehensive statistics.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

def analyze_icfes_excel(file_path):
    """
    Comprehensive analysis of the ICFES Excel database file.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        dict: Analysis results
    """
    
    print("=" * 80)
    print("ICFES EXCEL DATABASE ANALYSIS")
    print("=" * 80)
    print(f"File: {file_path}")
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Read the Excel file
        print("Loading Excel file...")
        df = pd.read_excel(file_path)
        print(f"File loaded successfully!")
        print()
        
        # Basic information
        print("BASIC FILE INFORMATION")
        print("-" * 40)
        print(f"Total rows: {len(df):,}")
        print(f"Total columns: {len(df.columns)}")
        print(f"File size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
        print()
        
        # Column analysis
        print("COLUMN ANALYSIS")
        print("-" * 40)
        print(f"Expected columns: 81")
        print(f"Actual columns: {len(df.columns)}")
        print("\nAll column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")
        print()
        
        # Data types analysis
        print("DATA TYPES ANALYSIS")
        print("-" * 40)
        dtype_summary = df.dtypes.value_counts()
        for dtype, count in dtype_summary.items():
            print(f"{dtype}: {count} columns")
        print()
        
        # Missing values analysis
        print("MISSING VALUES ANALYSIS")
        print("-" * 40)
        missing_summary = df.isnull().sum()
        missing_pct = (missing_summary / len(df) * 100).round(2)
        
        print("Columns with missing values:")
        for col in missing_summary[missing_summary > 0].index:
            count = missing_summary[col]
            pct = missing_pct[col]
            print(f"  {col}: {count:,} ({pct}%)")
        
        total_missing = missing_summary.sum()
        total_cells = len(df) * len(df.columns)
        overall_missing_pct = (total_missing / total_cells * 100)
        print(f"\nTotal missing values: {total_missing:,} ({overall_missing_pct:.2f}% of all cells)")
        print()
        
        # Key field analysis
        analysis_results = {
            'basic_info': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'file_size_mb': round(os.path.getsize(file_path) / (1024*1024), 2)
            },
            'columns': df.columns.tolist(),
            'missing_analysis': {
                'total_missing': int(total_missing),
                'overall_missing_pct': round(overall_missing_pct, 2),
                'columns_with_missing': {col: {'count': int(missing_summary[col]), 'percentage': float(missing_pct[col])} 
                                       for col in missing_summary[missing_summary > 0].index}
            }
        }
        
        # Analyze key fields if they exist
        key_fields = [
            'Área_Evaluada', 'Area_Evaluada', 'area_evaluada',
            'Competencia', 'competencia',
            'Componente', 'componente', 
            'Tema_Específico', 'Tema_Especifico', 'tema_especifico',
            'Nivel_Dificultad', 'nivel_dificultad', 'dificultad',
            'Grado_Escolar', 'grado_escolar', 'grado'
        ]
        
        found_key_fields = {}
        for field in key_fields:
            if field in df.columns:
                found_key_fields[field] = field
                break
        
        print("KEY FIELDS ANALYSIS")
        print("-" * 40)
        
        # Area Evaluada
        area_columns = [col for col in df.columns if 'area' in col.lower() or 'área' in col.lower()]
        if area_columns:
            area_col = area_columns[0]
            print(f"{area_col} (Subject Areas):")
            area_counts = df[area_col].value_counts()
            for area, count in area_counts.head(10).items():
                print(f"  {area}: {count:,}")
            if len(area_counts) > 10:
                print(f"  ... and {len(area_counts) - 10} more areas")
            print(f"  Total unique areas: {len(area_counts)}")
            analysis_results['area_evaluada'] = area_counts.to_dict()
            print()
        
        # Competencia
        comp_columns = [col for col in df.columns if 'competencia' in col.lower()]
        if comp_columns:
            comp_col = comp_columns[0]
            print(f"{comp_col} (Competencies):")
            comp_counts = df[comp_col].value_counts()
            for comp, count in comp_counts.head(10).items():
                print(f"  {comp}: {count:,}")
            if len(comp_counts) > 10:
                print(f"  ... and {len(comp_counts) - 10} more competencies")
            print(f"  Total unique competencies: {len(comp_counts)}")
            analysis_results['competencia'] = comp_counts.to_dict()
            print()
        
        # Componente
        component_columns = [col for col in df.columns if 'componente' in col.lower()]
        if component_columns:
            comp_col = component_columns[0]
            print(f"{comp_col} (Components):")
            comp_counts = df[comp_col].value_counts()
            for comp, count in comp_counts.head(10).items():
                print(f"  {comp}: {count:,}")
            if len(comp_counts) > 10:
                print(f"  ... and {len(comp_counts) - 10} more components")
            print(f"  Total unique components: {len(comp_counts)}")
            analysis_results['componente'] = comp_counts.to_dict()
            print()
        
        # Tema Específico
        tema_columns = [col for col in df.columns if 'tema' in col.lower()]
        if tema_columns:
            tema_col = tema_columns[0]
            print(f"{tema_col} (Specific Topics):")
            tema_counts = df[tema_col].value_counts()
            for tema, count in tema_counts.head(15).items():
                print(f"  {tema}: {count:,}")
            if len(tema_counts) > 15:
                print(f"  ... and {len(tema_counts) - 15} more topics")
            print(f"  Total unique topics: {len(tema_counts)}")
            analysis_results['tema_especifico'] = tema_counts.to_dict()
            print()
        
        # Difficulty Level
        dif_columns = [col for col in df.columns if 'dificultad' in col.lower() or 'nivel' in col.lower()]
        difficulty_col = None
        for col in dif_columns:
            if 'dificultad' in col.lower():
                difficulty_col = col
                break
        
        if difficulty_col:
            print(f"{difficulty_col} (Difficulty Levels):")
            dif_counts = df[difficulty_col].value_counts()
            for dif, count in dif_counts.items():
                pct = (count / len(df) * 100)
                print(f"  {dif}: {count:,} ({pct:.1f}%)")
            analysis_results['nivel_dificultad'] = dif_counts.to_dict()
            print()
        
        # Grade Level
        grade_columns = [col for col in df.columns if 'grado' in col.lower()]
        if grade_columns:
            grade_col = grade_columns[0]
            print(f"{grade_col} (School Grades):")
            grade_counts = df[grade_col].value_counts().sort_index()
            for grade, count in grade_counts.items():
                pct = (count / len(df) * 100)
                print(f"  Grade {grade}: {count:,} ({pct:.1f}%)")
            analysis_results['grado_escolar'] = grade_counts.to_dict()
            print()
        
        # Sample data
        print("SAMPLE DATA (First 3 rows)")
        print("-" * 40)
        print(df.head(3).to_string())
        print()
        
        # Descriptive statistics for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            print("NUMERIC COLUMNS STATISTICS")
            print("-" * 40)
            print(df[numeric_cols].describe().round(2))
            print()
        
        # Memory usage
        print("MEMORY USAGE")
        print("-" * 40)
        memory_usage = df.memory_usage(deep=True)
        total_memory = memory_usage.sum()
        print(f"Total memory usage: {total_memory / (1024*1024):.2f} MB")
        
        # Top memory consuming columns
        print("\nTop 10 memory consuming columns:")
        top_memory = memory_usage.sort_values(ascending=False).head(10)
        for col, mem in top_memory.items():
            if col != 'Index':
                print(f"  {col}: {mem / (1024*1024):.2f} MB")
        print()
        
        # Summary
        print("ANALYSIS SUMMARY")
        print("-" * 40)
        print(f"Successfully analyzed {len(df):,} questions")
        print(f"Found {len(df.columns)} columns (expected 81)")
        print(f"Data completeness: {100 - overall_missing_pct:.1f}%")
        
        if area_columns:
            print(f"Subject areas: {len(df[area_columns[0]].unique())} unique")
        if grade_columns:
            print(f"Grade levels: {len(df[grade_columns[0]].unique())} unique")
        if difficulty_col:
            print(f"Difficulty levels: {len(df[difficulty_col].unique())} unique")
        
        print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed analysis to JSON
        output_file = 'icfes_analysis_report.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Detailed report saved to: {output_file}")
        
        return analysis_results
        
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        return None

if __name__ == "__main__":
    file_path = r"database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
    
    if os.path.exists(file_path):
        results = analyze_icfes_excel(file_path)
        if results:
            print("\nAnalysis completed successfully!")
        else:
            print("\nAnalysis failed!")
    else:
        print(f"File not found: {file_path}")
        print("\nChecking for similar files...")
        
        # Check if directory exists and list similar files
        dir_path = os.path.dirname(file_path)
        if os.path.exists(dir_path):
            excel_files = [f for f in os.listdir(dir_path) if f.endswith(('.xlsx', '.xls'))]
            if excel_files:
                print("Found Excel files in directory:")
                for f in excel_files:
                    print(f"  - {f}")
            else:
                print("No Excel files found in directory")
        else:
            print(f"Directory does not exist: {dir_path}")