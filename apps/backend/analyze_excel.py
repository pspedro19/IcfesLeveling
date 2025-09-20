#!/usr/bin/env python3
import pandas as pd
import os
import sys

def analyze_excel_file(file_path):
    """Analyze an Excel file and report on image-related fields"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        print(f"\n📊 Analyzing: {file_path}")
        print("="*80)

        # Read Excel file
        df = pd.read_excel(file_path)

        print(f"📈 Total rows: {len(df)}")
        print(f"📈 Total columns: {len(df.columns)}")

        # Print column names
        print("\n📋 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")

        # Look for image-related columns
        image_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in
                        ['imagen', 'image', 'url', 'ruta', 'path', 'file', 'archivo'])]

        if image_columns:
            print(f"\n🖼️  Image-related columns found: {len(image_columns)}")
            for col in image_columns:
                print(f"  • {col}")
                # Show non-null values count and examples
                non_null_count = df[col].notna().sum()
                print(f"    - Non-null values: {non_null_count}/{len(df)}")
                if non_null_count > 0:
                    examples = df[col].dropna().head(3).tolist()
                    print(f"    - Examples: {examples}")
        else:
            print("\n❌ No image-related columns found")

        # Look for Requiere_Imagen column specifically
        if 'Requiere_Imagen' in df.columns:
            print(f"\n🎯 Requiere_Imagen analysis:")
            value_counts = df['Requiere_Imagen'].value_counts()
            print(f"  • Value distribution: {dict(value_counts)}")

            # Show examples where Requiere_Imagen = 1
            requires_image = df[df['Requiere_Imagen'] == 1]
            if len(requires_image) > 0:
                print(f"  • Records requiring images: {len(requires_image)}")
                for i, (idx, row) in enumerate(requires_image.head(3).iterrows()):
                    print(f"    Example {i+1}: ID={row.get('ID_Pregunta', idx)}")
                    for col in image_columns:
                        if col in row and pd.notna(row[col]):
                            print(f"      {col}: {row[col]}")

        # Look for URL patterns
        print(f"\n🔗 URL pattern analysis:")
        url_patterns = {}
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                urls = df[col].dropna().astype(str)
                png_urls = urls[urls.str.contains('\.png|\.jpg|\.jpeg|\.gif|\.pdf', case=False, na=False)]
                if len(png_urls) > 0:
                    url_patterns[col] = png_urls.tolist()

        for col, urls in url_patterns.items():
            print(f"  • {col}: {len(urls)} URLs found")
            for url in urls[:3]:  # Show first 3 examples
                print(f"    - {url}")

    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {str(e)}")

def main():
    # Files to analyze
    files_to_analyze = [
        "/root/IcfesLeveling/database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx",
        "/root/IcfesLeveling/apps/backend/ICFES_questions.xlsx",
        "/root/IcfesLeveling/apps/backend/ICFES2 (1).xlsx"
    ]

    for file_path in files_to_analyze:
        analyze_excel_file(file_path)
        print("\n" + "="*80)

if __name__ == "__main__":
    main()