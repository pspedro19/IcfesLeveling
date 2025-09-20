#!/usr/bin/env python3
"""
Comprehensive analysis of ICFES Excel seed files
Analyzes data structure, quality, and authenticity
"""

import pandas as pd
import os
import json
from collections import Counter

def analyze_excel_comprehensive():
    """Comprehensive analysis of all Excel files"""

    files_to_analyze = [
        '/root/IcfesLeveling/database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx',
        '/root/IcfesLeveling/apps/backend/ICFES_questions.xlsx',
        '/root/IcfesLeveling/apps/backend/ICFES2 (1).xlsx'
    ]

    analysis_report = {
        'file_analysis': {},
        'consolidated_summary': {},
        'quality_assessment': {},
        'column_mapping': {},
        'import_strategy': {}
    }

    all_questions = []

    for file_path in files_to_analyze:
        if not os.path.exists(file_path):
            continue

        print(f"\n{'='*80}")
        print(f"📊 ANALYZING: {os.path.basename(file_path)}")
        print('='*80)

        try:
            df = pd.read_excel(file_path)

            # Basic file info
            file_info = {
                'path': file_path,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': list(df.columns)
            }

            print(f"📈 Rows: {len(df)}, Columns: {len(df.columns)}")

            # Subject/Area distribution
            area_dist = {}
            if 'Área_Evaluada' in df.columns:
                area_dist = {k: int(v) for k, v in df['Área_Evaluada'].value_counts().to_dict().items()}
                print(f"🎯 Areas: {area_dist}")

            # Question text analysis
            question_columns = ['Pregunta', 'question_text', 'pregunta_texto']
            question_col = None
            for col in question_columns:
                if col in df.columns:
                    question_col = col
                    break

            valid_questions = 0
            sample_questions = []

            if question_col:
                valid_qs = df[question_col].dropna()
                valid_questions = len(valid_qs)
                sample_questions = valid_qs.head(3).tolist()
                print(f"📝 Valid questions: {valid_questions}/{len(df)}")

            # Image analysis
            image_analysis = analyze_images(df)
            print(f"🖼️  Images: {image_analysis['summary']}")

            # Options analysis
            options_analysis = analyze_options(df)
            print(f"🔤 Options: {options_analysis['summary']}")

            # Correct answers analysis
            correct_analysis = analyze_correct_answers(df)
            print(f"✅ Correct answers: {correct_analysis['summary']}")

            # Store file analysis
            analysis_report['file_analysis'][file_path] = {
                'file_info': file_info,
                'area_distribution': area_dist,
                'valid_questions': valid_questions,
                'sample_questions': sample_questions[:2],  # Limit for report
                'image_analysis': image_analysis,
                'options_analysis': options_analysis,
                'correct_analysis': correct_analysis
            }

            # Add to consolidated questions
            for idx, row in df.iterrows():
                if question_col and pd.notna(row[question_col]):
                    all_questions.append({
                        'source_file': file_path,
                        'row_index': idx,
                        'area': row.get('Área_Evaluada', 'Unknown'),
                        'question_text': str(row[question_col])[:200],
                        'has_image': check_has_image(row),
                        'options_count': count_options(row),
                        'correct_answer': row.get('Respuesta_Correcta', 'Unknown')
                    })

        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            continue

    # Consolidated analysis
    print(f"\n{'='*80}")
    print("📋 CONSOLIDATED ANALYSIS")
    print('='*80)

    total_questions = len(all_questions)
    area_counts = Counter(q['area'] for q in all_questions)
    image_questions = sum(1 for q in all_questions if q['has_image'])

    analysis_report['consolidated_summary'] = {
        'total_questions': total_questions,
        'area_distribution': {k: int(v) for k, v in dict(area_counts).items()},
        'questions_with_images': image_questions,
        'image_percentage': round(image_questions/total_questions*100, 1) if total_questions > 0 else 0
    }

    print(f"📊 Total questions: {total_questions}")
    print(f"📊 Area distribution: {dict(area_counts)}")
    print(f"🖼️  Questions with images: {image_questions} ({analysis_report['consolidated_summary']['image_percentage']}%)")

    # Quality assessment
    quality_assessment = assess_quality(all_questions)
    analysis_report['quality_assessment'] = quality_assessment

    print(f"\n🔍 QUALITY ASSESSMENT:")
    for key, value in quality_assessment.items():
        print(f"  {key}: {value}")

    # Column mapping for import
    column_mapping = generate_column_mapping()
    analysis_report['column_mapping'] = column_mapping

    print(f"\n🗂️  COLUMN MAPPING:")
    for target, sources in column_mapping.items():
        print(f"  {target}: {sources}")

    # Import strategy
    import_strategy = generate_import_strategy(analysis_report)
    analysis_report['import_strategy'] = import_strategy

    print(f"\n🚀 IMPORT STRATEGY:")
    for step, details in import_strategy.items():
        print(f"  {step}: {details}")

    return analysis_report

def analyze_images(df):
    """Analyze image-related columns and paths"""
    image_cols = ['Requiere_Imagen', 'Imagen_Pregunta_URL', 'Imagen_Opcion_A_URL',
                  'Imagen_Opcion_B_URL', 'Imagen_Opcion_C_URL', 'Imagen_Opcion_D_URL',
                  'Imagen_Contexto_Comp']

    image_analysis = {
        'columns_found': [],
        'total_image_refs': 0,
        'valid_paths': 0,
        'summary': ''
    }

    for col in image_cols:
        if col in df.columns:
            image_analysis['columns_found'].append(col)
            non_null = df[col].notna().sum()
            image_analysis['total_image_refs'] += non_null

            # Check some paths exist
            if col != 'Requiere_Imagen':
                sample_paths = df[col].dropna().head(5)
                valid_count = 0
                for path in sample_paths:
                    abs_path = convert_to_abs_path(str(path))
                    if os.path.exists(abs_path):
                        valid_count += 1
                image_analysis['valid_paths'] += valid_count

    image_analysis['summary'] = f"{len(image_analysis['columns_found'])} cols, {image_analysis['total_image_refs']} refs, {image_analysis['valid_paths']} valid"
    return image_analysis

def analyze_options(df):
    """Analyze answer options"""
    option_cols = ['Opcion_A', 'Opcion_B', 'Opcion_C', 'Opcion_D']

    options_analysis = {
        'columns_found': [],
        'questions_with_4_options': 0,
        'questions_with_min_options': 0,
        'summary': ''
    }

    for col in option_cols:
        if col in df.columns:
            options_analysis['columns_found'].append(col)

    # Count questions with complete options
    for idx, row in df.iterrows():
        options_count = sum(1 for col in option_cols if col in df.columns and pd.notna(row[col]))
        if options_count == 4:
            options_analysis['questions_with_4_options'] += 1
        if options_count >= 2:
            options_analysis['questions_with_min_options'] += 1

    options_analysis['summary'] = f"{len(options_analysis['columns_found'])} cols, {options_analysis['questions_with_4_options']} complete, {options_analysis['questions_with_min_options']} valid"
    return options_analysis

def analyze_correct_answers(df):
    """Analyze correct answer distribution"""
    correct_analysis = {
        'distribution': {},
        'valid_answers': 0,
        'summary': ''
    }

    if 'Respuesta_Correcta' in df.columns:
        valid_answers = df['Respuesta_Correcta'].dropna()
        correct_analysis['valid_answers'] = len(valid_answers)
        correct_analysis['distribution'] = {k: int(v) for k, v in valid_answers.value_counts().to_dict().items()}

    correct_analysis['summary'] = f"{correct_analysis['valid_answers']} valid, dist: {correct_analysis['distribution']}"
    return correct_analysis

def check_has_image(row):
    """Check if a question row has images"""
    image_cols = ['Imagen_Pregunta_URL', 'Imagen_Opcion_A_URL', 'Imagen_Contexto_Comp']
    return any(pd.notna(row.get(col, '')) and str(row.get(col, '')).strip() for col in image_cols)

def count_options(row):
    """Count valid options in a row"""
    option_cols = ['Opcion_A', 'Opcion_B', 'Opcion_C', 'Opcion_D']
    return sum(1 for col in option_cols if pd.notna(row.get(col, '')))

def convert_to_abs_path(rel_path):
    """Convert relative path to absolute path"""
    if rel_path.startswith('database/'):
        return '/root/IcfesLeveling/' + rel_path
    elif rel_path.startswith('/database/'):
        return '/root/IcfesLeveling' + rel_path
    else:
        return '/root/IcfesLeveling/database/allquestions/' + rel_path.lstrip('/')

def assess_quality(all_questions):
    """Assess overall data quality"""
    if not all_questions:
        return {'error': 'No questions to analyze'}

    total = len(all_questions)

    # Question text quality
    long_questions = sum(1 for q in all_questions if len(q['question_text']) > 50)
    short_questions = sum(1 for q in all_questions if len(q['question_text']) < 20)

    # Options completeness
    complete_options = sum(1 for q in all_questions if q['options_count'] >= 4)

    # Image availability
    with_images = sum(1 for q in all_questions if q['has_image'])

    # Area coverage
    areas_covered = len(set(q['area'] for q in all_questions))

    return {
        'total_questions': total,
        'long_questions_pct': round(long_questions/total*100, 1),
        'short_questions_pct': round(short_questions/total*100, 1),
        'complete_options_pct': round(complete_options/total*100, 1),
        'with_images_pct': round(with_images/total*100, 1),
        'areas_covered': areas_covered,
        'authenticity_score': calculate_authenticity_score(all_questions)
    }

def calculate_authenticity_score(all_questions):
    """Calculate authenticity score based on various factors"""
    if not all_questions:
        return 0

    total = len(all_questions)

    # Factors indicating authentic ICFES questions:
    # 1. Reasonable question length (not too short, not too long)
    reasonable_length = sum(1 for q in all_questions if 30 <= len(q['question_text']) <= 300)

    # 2. Complete options (4 options)
    complete_options = sum(1 for q in all_questions if q['options_count'] >= 4)

    # 3. Has images (many ICFES questions have images)
    with_images = sum(1 for q in all_questions if q['has_image'])

    # 4. Valid correct answers
    valid_correct = sum(1 for q in all_questions if q['correct_answer'] in ['A', 'B', 'C', 'D'])

    # 5. Area diversity
    areas = set(q['area'] for q in all_questions)
    area_diversity_score = min(len(areas) / 5, 1)  # Max 5 areas expected

    # Calculate weighted score
    length_score = reasonable_length / total * 0.2
    options_score = complete_options / total * 0.25
    images_score = with_images / total * 0.2
    correct_score = valid_correct / total * 0.25
    diversity_score = area_diversity_score * 0.1

    total_score = (length_score + options_score + images_score + correct_score + diversity_score) * 100
    return round(total_score, 1)

def generate_column_mapping():
    """Generate column mapping for database import"""
    return {
        'pregunta_texto': ['Pregunta', 'question_text', 'pregunta_texto'],
        'opcion_a_texto': ['Opcion_A', 'opcion_a', 'option_a'],
        'opcion_b_texto': ['Opcion_B', 'opcion_b', 'option_b'],
        'opcion_c_texto': ['Opcion_C', 'opcion_c', 'option_c'],
        'opcion_d_texto': ['Opcion_D', 'opcion_d', 'option_d'],
        'respuesta_correcta': ['Respuesta_Correcta', 'correct_answer', 'respuesta_correcta'],
        'pregunta_imagen': ['Imagen_Pregunta_URL', 'imagen_pregunta_url'],
        'opcion_a_imagen': ['Imagen_Opcion_A_URL', 'imagen_opcion_a_url'],
        'opcion_b_imagen': ['Imagen_Opcion_B_URL', 'imagen_opcion_b_url'],
        'opcion_c_imagen': ['Imagen_Opcion_C_URL', 'imagen_opcion_c_url'],
        'opcion_d_imagen': ['Imagen_Opcion_D_URL', 'imagen_opcion_d_url'],
        'area_evaluada': ['Área_Evaluada', 'area', 'subject'],
        'competencia': ['Competencia', 'competencia'],
        'explicacion': ['Explicación_Respuesta', 'explanation', 'explicacion'],
        'difficulty': ['Nivel_Dificultad', 'difficulty', 'dificultad']
    }

def generate_import_strategy(analysis_report):
    """Generate recommended import strategy"""
    total_questions = analysis_report['consolidated_summary']['total_questions']
    quality_score = analysis_report['quality_assessment']['authenticity_score']

    strategy = {
        'recommended_approach': '',
        'priority_files': [],
        'steps': [],
        'image_handling': '',
        'validation_rules': []
    }

    # Determine approach based on quality
    if quality_score >= 70:
        strategy['recommended_approach'] = 'Direct import with validation'
    elif quality_score >= 50:
        strategy['recommended_approach'] = 'Import with data cleaning'
    else:
        strategy['recommended_approach'] = 'Manual review required'

    # Priority files (largest first)
    file_sizes = []
    for file_path, analysis in analysis_report['file_analysis'].items():
        file_sizes.append((file_path, analysis['file_info']['total_rows']))

    strategy['priority_files'] = [f[0] for f in sorted(file_sizes, key=lambda x: x[1], reverse=True)]

    # Steps
    strategy['steps'] = [
        'Backup existing database',
        'Create staging tables',
        'Import questions with column mapping',
        'Validate image paths',
        'Normalize correct answers',
        'Run quality checks',
        'Migrate to production tables'
    ]

    # Image handling
    strategy['image_handling'] = 'Convert relative paths to absolute, validate existence, create fallbacks'

    # Validation rules
    strategy['validation_rules'] = [
        'Question text must not be empty',
        'Must have at least 2 options',
        'Correct answer must be A, B, C, or D',
        'Image paths must exist if specified',
        'Area must be valid ICFES subject'
    ]

    return strategy

if __name__ == "__main__":
    report = analyze_excel_comprehensive()

    print(f"\n🎯 FINAL RECOMMENDATIONS:")
    print(f"  • Total Questions Available: {report['consolidated_summary']['total_questions']}")
    print(f"  • Data Quality Score: {report['quality_assessment']['authenticity_score']}/100")
    print(f"  • Recommended Approach: {report['import_strategy']['recommended_approach']}")
    print(f"  • Primary Source: {os.path.basename(report['import_strategy']['priority_files'][0]) if report['import_strategy']['priority_files'] else 'None'}")

    # Show detailed sample
    print(f"\n📋 SAMPLE AUTHENTIC QUESTIONS:")
    sample_count = 0
    for file_path, analysis in report['file_analysis'].items():
        if sample_count >= 2:
            break
        print(f"\nFrom {os.path.basename(file_path)}:")
        for i, sample in enumerate(analysis['sample_questions'][:2]):
            if sample_count < 2:
                print(f"  {sample_count + 1}. {sample[:150]}...")
                sample_count += 1