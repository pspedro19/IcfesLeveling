#!/usr/bin/env python3
"""
Comprehensive Questions Validation Script using Docker

This script validates all loaded questions in the database using Docker connection:
1. COUNT questions per subject
2. Verify all IRT parameters are numeric
3. Check all image paths exist
4. Ensure all Respuesta_Correcta are lowercase (a,b,c,d)
5. Verify competencies are loaded
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Docker container name
DOCKER_CONTAINER = "icfes_postgres"

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'gameplay_db',
    'username': 'gameplay',
    'password': 'gameplay123'
}

def execute_sql_query(sql: str):
    """Execute SQL query in Docker container and return results"""
    try:
        cmd = [
            'docker', 'exec', '-i', DOCKER_CONTAINER,
            'psql', '-U', DB_CONFIG['username'], '-d', DB_CONFIG['database'],
            '-t', '-c', sql
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Error executing SQL: {result.stderr}")
            return None
            
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        print(f"Timeout executing SQL: {sql[:100]}...")
        return None
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return None

def validate_questions():
    """Run comprehensive validation on all questions"""
    
    print("=" * 80)
    print("COMPREHENSIVE QUESTIONS VALIDATION REPORT")
    print("=" * 80)
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Docker container: {DOCKER_CONTAINER}")
    print()
    
    validation_results = {}
    
    try:
        # 1. COUNT QUESTIONS PER SUBJECT
        print("1. QUESTIONS COUNT BY SUBJECT")
        print("-" * 50)
        
        sql = """
        SELECT s.name as subject, COUNT(q.id) as count 
        FROM subjects s
        LEFT JOIN questions q ON s.id = q.subject_id
        GROUP BY s.name, s.id
        ORDER BY s.name;
        """
        
        result = execute_sql_query(sql)
        if result:
            total_questions = 0
            subjects_data = {}
            
            for line in result.split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        subject = parts[0].strip()
                        count = int(parts[1].strip())
                        print(f"{subject:25}: {count:6} questions")
                        subjects_data[subject] = count
                        total_questions += count
            
            print(f"{'TOTAL':25}: {total_questions:6} questions")
            print()
            
            validation_results['questions_by_subject'] = subjects_data
            validation_results['total_questions'] = total_questions
        else:
            print("Failed to get question counts by subject")
            return None
        
        # 2. VERIFY IRT PARAMETERS ARE NUMERIC
        print("2. IRT PARAMETERS VALIDATION")
        print("-" * 50)
        
        # Check for non-numeric IRT parameters in power_stats JSON
        sql = """
        SELECT id, subject_id,
               CASE 
                   WHEN power_stats::json->>'irt_a' !~ '^[+-]?([0-9]*[.])?[0-9]+$' THEN 'irt_a_invalid'
                   WHEN power_stats::json->>'irt_b' !~ '^[+-]?([0-9]*[.])?[0-9]+$' THEN 'irt_b_invalid'
                   WHEN power_stats::json->>'irt_c' !~ '^[+-]?([0-9]*[.])?[0-9]+$' THEN 'irt_c_invalid'
                   ELSE NULL
               END as issue,
               power_stats::json->>'irt_a' as irt_a,
               power_stats::json->>'irt_b' as irt_b,
               power_stats::json->>'irt_c' as irt_c
        FROM questions 
        WHERE power_stats IS NOT NULL
          AND (power_stats::json->>'irt_a' !~ '^[+-]?([0-9]*[.])?[0-9]+$'
           OR power_stats::json->>'irt_b' !~ '^[+-]?([0-9]*[.])?[0-9]+$'
           OR power_stats::json->>'irt_c' !~ '^[+-]?([0-9]*[.])?[0-9]+$')
        LIMIT 10;
        """
        
        result = execute_sql_query(sql)
        irt_issues_count = 0
        
        if result and result.strip():
            lines = [line for line in result.split('\n') if line.strip()]
            irt_issues_count = len(lines)
            print(f"FOUND {irt_issues_count} questions with IRT parameter issues:")
            for line in lines[:10]:
                print(f"  {line}")
        else:
            print("[OK] ALL IRT parameters are properly formatted as numeric values")
            
        print()
        validation_results['irt_issues_count'] = irt_issues_count
        
        # 3. CHECK IMAGE PATHS EXIST  
        print("3. IMAGE PATHS VALIDATION")
        print("-" * 50)
        
        # Get all unique image paths using a subquery
        sql = """
        SELECT DISTINCT image_path 
        FROM (
            SELECT pregunta_imagen as image_path FROM questions WHERE pregunta_imagen IS NOT NULL AND pregunta_imagen != ''
            UNION ALL
            SELECT opcion_a_imagen as image_path FROM questions WHERE opcion_a_imagen IS NOT NULL AND opcion_a_imagen != ''
            UNION ALL
            SELECT opcion_b_imagen as image_path FROM questions WHERE opcion_b_imagen IS NOT NULL AND opcion_b_imagen != ''
            UNION ALL
            SELECT opcion_c_imagen as image_path FROM questions WHERE opcion_c_imagen IS NOT NULL AND opcion_c_imagen != ''
            UNION ALL
            SELECT opcion_d_imagen as image_path FROM questions WHERE opcion_d_imagen IS NOT NULL AND opcion_d_imagen != ''
        ) AS all_images;
        """
        
        result = execute_sql_query(sql)
        if result:
            image_paths = [line.strip() for line in result.split('\n') if line.strip()]
            print(f"Total unique image paths to check: {len(image_paths)}")
            
            missing_images = []
            existing_images = 0
            
            for image_path in image_paths:
                if image_path:
                    # Check in multiple possible locations
                    possible_paths = [
                        os.path.join("apps", "frontend", "public", image_path.lstrip('/')),
                        os.path.join("apps", "frontend", "public", "images", image_path.lstrip('/')),
                        os.path.join("database", "images", image_path.lstrip('/')),
                        image_path
                    ]
                    
                    found = False
                    for path in possible_paths:
                        if os.path.exists(path):
                            found = True
                            existing_images += 1
                            break
                    
                    if not found:
                        missing_images.append(image_path)
            
            if missing_images:
                print(f"FOUND {len(missing_images)} missing image files:")
                for img in missing_images[:10]:
                    print(f"  - {img}")
                if len(missing_images) > 10:
                    print(f"  ... and {len(missing_images) - 10} more")
            else:
                print("[OK] ALL image paths exist")
                
            print(f"Images found: {existing_images}")
            print(f"Images missing: {len(missing_images)}")
            print()
            
            validation_results['images_existing'] = existing_images
            validation_results['images_missing'] = len(missing_images)
        else:
            print("Failed to get image paths")
            validation_results['images_existing'] = 0
            validation_results['images_missing'] = 0
        
        # 4. VERIFY RESPUESTA_CORRECTA FORMAT
        print("4. CORRECT ANSWER FORMAT VALIDATION")
        print("-" * 50)
        
        # Check for invalid correct answers
        sql = """
        SELECT id, subject_id, respuesta_correcta 
        FROM questions 
        WHERE respuesta_correcta NOT IN ('a', 'b', 'c', 'd')
           OR respuesta_correcta IS NULL
        LIMIT 10;
        """
        
        result = execute_sql_query(sql)
        invalid_answers_count = 0
        
        if result and result.strip():
            lines = [line for line in result.split('\n') if line.strip()]
            invalid_answers_count = len(lines)
            print(f"FOUND {invalid_answers_count} questions with invalid correct answers:")
            for line in lines:
                print(f"  {line}")
        else:
            print("[OK] ALL correct answers are properly formatted (a, b, c, d)")
            
        print()
        validation_results['invalid_answers_count'] = invalid_answers_count
        
        # 5. VERIFY COMPETENCIES ARE LOADED
        print("5. COMPETENCIES VALIDATION")
        print("-" * 50)
        
        # Check competencies from tags
        sql = """
        SELECT 
            COUNT(*) as total_questions,
            COUNT(CASE WHEN array_length(tags, 1) > 0 THEN 1 END) as questions_with_tags,
            COUNT(DISTINCT tags[1]) as unique_first_tags
        FROM questions
        WHERE tags IS NOT NULL;
        """
        
        result = execute_sql_query(sql)
        if result:
            parts = result.split('|')
            if len(parts) >= 3:
                total_questions = int(parts[0].strip())
                questions_with_tags = int(parts[1].strip())
                unique_tags = int(parts[2].strip())
                
                print(f"Total questions: {total_questions}")
                print(f"Questions with tags/competencies: {questions_with_tags}")
                print(f"Unique first-level tags: {unique_tags}")
                
                coverage = (questions_with_tags / total_questions) * 100 if total_questions > 0 else 0
                print(f"Tag coverage: {coverage:.1f}%")
        
        # Show competencies by subject
        sql = """
        SELECT s.name as subject,
               COUNT(DISTINCT q.tags[1]) as unique_competencies,
               COUNT(q.id) as total_questions,
               COUNT(CASE WHEN array_length(q.tags, 1) > 0 THEN 1 END) as questions_with_tags
        FROM subjects s
        LEFT JOIN questions q ON s.id = q.subject_id
        WHERE q.tags IS NOT NULL
        GROUP BY s.name
        ORDER BY s.name;
        """
        
        result = execute_sql_query(sql)
        if result:
            print("\nCompetencies by subject:")
            for line in result.split('\n'):
                if '|' in line and line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        subject = parts[0].strip()
                        unique_competencies = int(parts[1].strip())
                        total_questions = int(parts[2].strip())
                        questions_with_tags = int(parts[3].strip())
                        coverage = (questions_with_tags / total_questions) * 100 if total_questions > 0 else 0
                        print(f"  {subject:25}: {unique_competencies:3} competencies, {coverage:5.1f}% coverage")
        
        # Show most common competencies
        sql = """
        SELECT tags[1] as competencia, COUNT(*) as count
        FROM questions 
        WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
        GROUP BY tags[1]
        ORDER BY count DESC
        LIMIT 10;
        """
        
        result = execute_sql_query(sql)
        if result:
            print("\nTop 10 competencies:")
            for line in result.split('\n'):
                if '|' in line and line.strip():
                    parts = line.split('|')
                    if len(parts) >= 2:
                        comp = parts[0].strip()
                        count = int(parts[1].strip())
                        print(f"  {comp:50}: {count:4} questions")
        
        print()
        
        # 6. ADDITIONAL VALIDATIONS
        print("6. ADDITIONAL VALIDATIONS")
        print("-" * 50)
        
        # Check for questions with missing essential fields
        sql = """
        SELECT 
            COUNT(CASE WHEN pregunta_texto IS NULL OR pregunta_texto = '' THEN 1 END) as missing_question_text,
            COUNT(CASE WHEN opcion_a_texto IS NULL OR opcion_a_texto = '' THEN 1 END) as missing_option_a,
            COUNT(CASE WHEN opcion_b_texto IS NULL OR opcion_b_texto = '' THEN 1 END) as missing_option_b,
            COUNT(CASE WHEN opcion_c_texto IS NULL OR opcion_c_texto = '' THEN 1 END) as missing_option_c,
            COUNT(CASE WHEN opcion_d_texto IS NULL OR opcion_d_texto = '' THEN 1 END) as missing_option_d,
            COUNT(CASE WHEN subject_id IS NULL THEN 1 END) as missing_subject
        FROM questions;
        """
        
        result = execute_sql_query(sql)
        if result:
            parts = result.split('|')
            if len(parts) >= 6:
                missing_fields = {
                    'missing_question_text': int(parts[0].strip()),
                    'missing_option_a': int(parts[1].strip()),
                    'missing_option_b': int(parts[2].strip()),
                    'missing_option_c': int(parts[3].strip()),
                    'missing_option_d': int(parts[4].strip()),
                    'missing_subject': int(parts[5].strip())
                }
                
                print("Missing essential fields:")
                print(f"  Question text: {missing_fields['missing_question_text']}")
                print(f"  Option A: {missing_fields['missing_option_a']}")
                print(f"  Option B: {missing_fields['missing_option_b']}")
                print(f"  Option C: {missing_fields['missing_option_c']}")
                print(f"  Option D: {missing_fields['missing_option_d']}")
                print(f"  Subject: {missing_fields['missing_subject']}")
                
                validation_results['essential_fields'] = missing_fields
        
        # SUMMARY
        print()
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        issues_found = 0
        
        print(f"[OK] Total questions loaded: {validation_results.get('total_questions', 0)}")
        print(f"[OK] Subjects covered: {len(validation_results.get('questions_by_subject', {}))}")
        
        if validation_results.get('irt_issues_count', 0) == 0:
            print("[OK] All IRT parameters are numeric")
        else:
            print(f"[WARN] {validation_results.get('irt_issues_count', 0)} questions have IRT parameter issues")
            issues_found += validation_results.get('irt_issues_count', 0)
        
        if validation_results.get('images_missing', 0) == 0:
            print("[OK] All image paths exist")
        else:
            print(f"[WARN] {validation_results.get('images_missing', 0)} image files are missing")
            issues_found += validation_results.get('images_missing', 0)
        
        if validation_results.get('invalid_answers_count', 0) == 0:
            print("[OK] All correct answers are properly formatted")
        else:
            print(f"[WARN] {validation_results.get('invalid_answers_count', 0)} questions have invalid correct answer format")
            issues_found += validation_results.get('invalid_answers_count', 0)
        
        print()
        if issues_found == 0:
            print("[SUCCESS] ALL VALIDATIONS PASSED! Database is in excellent condition.")
        else:
            print(f"[WARN] Found {issues_found} total issues that should be addressed.")
        
        print("=" * 80)
        
        # Save validation results to JSON file
        validation_results['timestamp'] = datetime.now().isoformat()
        validation_results['total_issues'] = issues_found
        
        with open('validation_report_docker.json', 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed validation report saved to: validation_report_docker.json")
        
        return validation_results
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_docker_container():
    """Check if Docker container is running"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', f'name={DOCKER_CONTAINER}'], 
                              capture_output=True, text=True)
        if DOCKER_CONTAINER not in result.stdout:
            print(f"[ERROR] Docker container '{DOCKER_CONTAINER}' is not running")
            print("Please start the PostgreSQL container first")
            return False
        else:
            print(f"[OK] Docker container '{DOCKER_CONTAINER}' is running")
            return True
    except Exception as e:
        print(f"[ERROR] Error checking Docker: {e}")
        return False

if __name__ == "__main__":
    if not check_docker_container():
        sys.exit(1)
    
    result = validate_questions()
    if result is None:
        sys.exit(1)
    else:
        sys.exit(0)