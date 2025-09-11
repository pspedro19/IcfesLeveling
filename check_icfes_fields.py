import pandas as pd
import os

file_path = os.path.join('database', 'allquestions', 'ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx')

print('Checking ICFES Excel file:', file_path)
print('='*60)

if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    print(f'Total rows: {len(df)}')
    print(f'Total columns: {len(df.columns)}')
    print()
    
    print('Key ICFES fields found:')
    key_fields = ['Competencia', 'Componente', 'Proceso_Cognitivo', 'Tipo_Conocimiento', 'Afirmación', 'Evidencia']
    
    for field in key_fields:
        if field in df.columns:
            unique_count = df[field].nunique() if not df[field].isnull().all() else 0
            sample = df[field].dropna().iloc[0] if not df[field].dropna().empty else 'N/A'
            print(f'[FOUND] {field}: {unique_count} unique values | Sample: {str(sample)[:80]}...')
        else:
            print(f'[MISSING] {field}: NOT FOUND')
    
    print()
    print('All columns in Excel:')
    for i, col in enumerate(df.columns):
        print(f'{i+1:2d}. {col}')
else:
    print('File not found!')