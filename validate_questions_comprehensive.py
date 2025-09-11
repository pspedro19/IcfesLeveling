#!/usr/bin/env python3
"""
Comprehensive Questions Validation Script

This script validates all loaded questions in the database according to:
1. COUNT questions per subject
2. Verify all IRT parameters are numeric
3. Check all image paths exist
4. Ensure all Respuesta_Correcta are lowercase (a,b,c,d)
5. Verify competencies are loaded
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

try:
    from app.core.database import get_db
    from app.models.question import Question
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine, text
    from app.core.config import settings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

def validate_questions():
    """Run comprehensive validation on all questions"""
    
    print("=" * 80)
    print("COMPREHENSIVE QUESTIONS VALIDATION REPORT")
    print("=" * 80)
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create database connection using .env file DATABASE_URL
    db_url = os.getenv('DATABASE_URL', 'postgresql://gameplay:gameplay123@localhost:5433/gameplay_db')
    print(f"Using database URL: {db_url}")
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    validation_results = {}
    
    try:
        # 1. COUNT QUESTIONS PER SUBJECT
        print("1. QUESTIONS COUNT BY SUBJECT")
        print("-" * 50)
        
        subject_counts = db.execute(text("""
            SELECT subject, COUNT(*) as count 
            FROM questions 
            GROUP BY subject 
            ORDER BY subject
        """)).fetchall()
        
        total_questions = 0
        subjects_data = {}
        
        for subject, count in subject_counts:
            print(f"{subject:25}: {count:6} questions")
            subjects_data[subject] = count
            total_questions += count
            
        print(f"{'TOTAL':25}: {total_questions:6} questions")
        print()
        
        validation_results['questions_by_subject'] = subjects_data
        validation_results['total_questions'] = total_questions
        
        # 2. VERIFY IRT PARAMETERS ARE NUMERIC
        print("2. IRT PARAMETERS VALIDATION")
        print("-" * 50)
        
        # Check for non-numeric IRT parameters
        irt_issues = db.execute(text("""
            SELECT id, subject, 
                   CASE 
                       WHEN irt_discrimination IS NULL OR irt_discrimination = '' THEN 'discrimination_null'
                       WHEN NOT irt_discrimination ~ '^[+-]?([0-9]*[.])?[0-9]+$' THEN 'discrimination_invalid'
                       ELSE NULL
                   END as discrimination_issue,
                   CASE 
                       WHEN irt_difficulty IS NULL OR irt_difficulty = '' THEN 'difficulty_null'
                       WHEN NOT irt_difficulty ~ '^[+-]?([0-9]*[.])?[0-9]+$' THEN 'difficulty_invalid'
                       ELSE NULL
                   END as difficulty_issue,
                   CASE 
                       WHEN irt_guessing IS NULL OR irt_guessing = '' THEN 'guessing_null'
                       WHEN NOT irt_guessing ~ '^[+-]?([0-9]*[.])?[0-9]+$' THEN 'guessing_invalid'
                       ELSE NULL
                   END as guessing_issue,
                   irt_discrimination, irt_difficulty, irt_guessing
            FROM questions 
            WHERE (irt_discrimination IS NULL OR irt_discrimination = '' OR NOT irt_discrimination ~ '^[+-]?([0-9]*[.])?[0-9]+$')
               OR (irt_difficulty IS NULL OR irt_difficulty = '' OR NOT irt_difficulty ~ '^[+-]?([0-9]*[.])?[0-9]+$')
               OR (irt_guessing IS NULL OR irt_guessing = '' OR NOT irt_guessing ~ '^[+-]?([0-9]*[.])?[0-9]+$')
        """)).fetchall()
        
        if irt_issues:
            print(f"FOUND {len(irt_issues)} questions with IRT parameter issues:")
            for issue in irt_issues[:10]:  # Show first 10
                print(f"  Question ID {issue.id} ({issue.subject}):")
                if issue.discrimination_issue:
                    print(f"    - Discrimination: {issue.discrimination_issue} ('{issue.irt_discrimination}')")
                if issue.difficulty_issue:
                    print(f"    - Difficulty: {issue.difficulty_issue} ('{issue.irt_difficulty}')")
                if issue.guessing_issue:
                    print(f"    - Guessing: {issue.guessing_issue} ('{issue.irt_guessing}')")
            if len(irt_issues) > 10:
                print(f"  ... and {len(irt_issues) - 10} more")
        else:
            print("✓ ALL IRT parameters are properly formatted as numeric values")
            
        print()
        validation_results['irt_issues_count'] = len(irt_issues)
        
        # 3. CHECK IMAGE PATHS EXIST
        print("3. IMAGE PATHS VALIDATION")
        print("-" * 50)
        
        # Get all unique image paths
        image_paths = db.execute(text("""
            SELECT DISTINCT image_path 
            FROM questions 
            WHERE image_path IS NOT NULL 
              AND image_path != '' 
              AND image_path != 'null'
        """)).fetchall()
        
        print(f"Total unique image paths to check: {len(image_paths)}")
        
        missing_images = []
        existing_images = 0
        
        for (image_path,) in image_paths:
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
            for img in missing_images[:10]:  # Show first 10
                print(f"  - {img}")
            if len(missing_images) > 10:
                print(f"  ... and {len(missing_images) - 10} more")
        else:
            print("✓ ALL image paths exist")
            
        print(f"Images found: {existing_images}")
        print(f"Images missing: {len(missing_images)}")
        print()
        
        validation_results['images_existing'] = existing_images
        validation_results['images_missing'] = len(missing_images)
        
        # 4. VERIFY RESPUESTA_CORRECTA FORMAT
        print("4. CORRECT ANSWER FORMAT VALIDATION")
        print("-" * 50)
        
        # Check for invalid correct answers
        invalid_answers = db.execute(text("""
            SELECT id, subject, respuesta_correcta 
            FROM questions 
            WHERE respuesta_correcta NOT IN ('a', 'b', 'c', 'd')
               OR respuesta_correcta IS NULL
        """)).fetchall()
        
        if invalid_answers:
            print(f"FOUND {len(invalid_answers)} questions with invalid correct answers:")
            answer_counts = {}
            for q in invalid_answers:
                ans = q.respuesta_correcta or 'NULL'
                answer_counts[ans] = answer_counts.get(ans, 0) + 1
                
            for answer, count in answer_counts.items():
                print(f"  '{answer}': {count} questions")
                
            # Show examples
            print("\nExamples:")
            for q in invalid_answers[:5]:
                print(f"  Question ID {q.id} ({q.subject}): '{q.respuesta_correcta}'")
        else:
            print("✓ ALL correct answers are properly formatted (a, b, c, d)")
            
        print()
        validation_results['invalid_answers_count'] = len(invalid_answers)
        
        # 5. VERIFY COMPETENCIES ARE LOADED
        print("5. COMPETENCIES VALIDATION")
        print("-" * 50)
        
        # Check competencies
        competency_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_questions,
                COUNT(competencia) as questions_with_competency,
                COUNT(DISTINCT competencia) as unique_competencies
            FROM questions
        """)).fetchone()
        
        print(f"Total questions: {competency_stats.total_questions}")
        print(f"Questions with competency: {competency_stats.questions_with_competency}")
        print(f"Unique competencies: {competency_stats.unique_competencies}")
        
        # Show competencies by subject
        competencies_by_subject = db.execute(text("""
            SELECT subject, COUNT(DISTINCT competencia) as unique_competencies,
                   COUNT(*) as total_questions,
                   COUNT(competencia) as questions_with_competency
            FROM questions 
            GROUP BY subject
            ORDER BY subject
        """)).fetchall()
        
        print("\nCompetencies by subject:")
        for row in competencies_by_subject:
            coverage = (row.questions_with_competency / row.total_questions) * 100 if row.total_questions > 0 else 0
            print(f"  {row.subject:25}: {row.unique_competencies:3} competencies, {coverage:5.1f}% coverage")
        
        # Show most common competencies
        top_competencies = db.execute(text("""
            SELECT competencia, COUNT(*) as count
            FROM questions 
            WHERE competencia IS NOT NULL
            GROUP BY competencia
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()
        
        print("\nTop 10 competencies:")
        for comp, count in top_competencies:
            print(f"  {comp:50}: {count:4} questions")
        
        print()
        validation_results['competencies'] = {
            'total_questions': competency_stats.total_questions,
            'questions_with_competency': competency_stats.questions_with_competency,
            'unique_competencies': competency_stats.unique_competencies,
            'coverage_percentage': (competency_stats.questions_with_competency / competency_stats.total_questions) * 100 if competency_stats.total_questions > 0 else 0
        }
        
        # 6. ADDITIONAL VALIDATIONS
        print("6. ADDITIONAL VALIDATIONS")
        print("-" * 50)
        
        # Check for questions with missing essential fields
        essential_field_issues = db.execute(text("""
            SELECT 
                COUNT(CASE WHEN question_text IS NULL OR question_text = '' THEN 1 END) as missing_question_text,
                COUNT(CASE WHEN option_a IS NULL OR option_a = '' THEN 1 END) as missing_option_a,
                COUNT(CASE WHEN option_b IS NULL OR option_b = '' THEN 1 END) as missing_option_b,
                COUNT(CASE WHEN option_c IS NULL OR option_c = '' THEN 1 END) as missing_option_c,
                COUNT(CASE WHEN option_d IS NULL OR option_d = '' THEN 1 END) as missing_option_d,
                COUNT(CASE WHEN subject IS NULL OR subject = '' THEN 1 END) as missing_subject
            FROM questions
        """)).fetchone()
        
        print("Missing essential fields:")
        print(f"  Question text: {essential_field_issues.missing_question_text}")
        print(f"  Option A: {essential_field_issues.missing_option_a}")
        print(f"  Option B: {essential_field_issues.missing_option_b}")
        print(f"  Option C: {essential_field_issues.missing_option_c}")
        print(f"  Option D: {essential_field_issues.missing_option_d}")
        print(f"  Subject: {essential_field_issues.missing_subject}")
        
        validation_results['essential_fields'] = {
            'missing_question_text': essential_field_issues.missing_question_text,
            'missing_option_a': essential_field_issues.missing_option_a,
            'missing_option_b': essential_field_issues.missing_option_b,
            'missing_option_c': essential_field_issues.missing_option_c,
            'missing_option_d': essential_field_issues.missing_option_d,
            'missing_subject': essential_field_issues.missing_subject
        }
        
        # SUMMARY
        print()
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        issues_found = 0
        
        print(f"✓ Total questions loaded: {total_questions}")
        print(f"✓ Subjects covered: {len(subjects_data)}")
        
        if validation_results['irt_issues_count'] == 0:
            print("✓ All IRT parameters are numeric")
        else:
            print(f"⚠ {validation_results['irt_issues_count']} questions have IRT parameter issues")
            issues_found += validation_results['irt_issues_count']
        
        if validation_results['images_missing'] == 0:
            print("✓ All image paths exist")
        else:
            print(f"⚠ {validation_results['images_missing']} image files are missing")
            issues_found += validation_results['images_missing']
        
        if validation_results['invalid_answers_count'] == 0:
            print("✓ All correct answers are properly formatted")
        else:
            print(f"⚠ {validation_results['invalid_answers_count']} questions have invalid correct answer format")
            issues_found += validation_results['invalid_answers_count']
        
        competency_coverage = validation_results['competencies']['coverage_percentage']
        if competency_coverage > 95:
            print(f"✓ Competencies well covered ({competency_coverage:.1f}%)")
        else:
            print(f"⚠ Competency coverage could be improved ({competency_coverage:.1f}%)")
        
        print()
        if issues_found == 0:
            print("🎉 ALL VALIDATIONS PASSED! Database is in excellent condition.")
        else:
            print(f"⚠ Found {issues_found} total issues that should be addressed.")
        
        print("=" * 80)
        
        # Save validation results to JSON file
        validation_results['timestamp'] = datetime.now().isoformat()
        validation_results['total_issues'] = issues_found
        
        with open('validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed validation report saved to: validation_report.json")
        
        return validation_results
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()

if __name__ == "__main__":
    validate_questions()