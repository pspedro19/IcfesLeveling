#!/usr/bin/env python3
"""
Simple Subject Mapping Test
Verify the distribution of questions by subject areas
"""

import pandas as pd

def test_question_distribution():
    """Test the distribution of questions by subject area"""
    try:
        # Load the CSV questions file
        df = pd.read_csv('database/seed_data/questions.csv', encoding='utf-8', low_memory=False)
        
        print(f"Total questions found: {len(df)}")
        print()
        
        # Show distribution by Area_Evaluada
        print("Distribution by 'Area_Evaluada' column:")
        areas = df['Área_Evaluada'].value_counts()
        
        for area, count in areas.items():
            print(f"  {area}: {count} questions")
        
        print()
        print("Expected mapping:")
        print("  'Matemáticas' -> 'Matemáticas' (database)")
        print("  'Lectura Crítica' -> 'Lenguaje' (database)")  
        print("  'Ciencias Naturales' -> 'Ciencias Naturales' (database)")
        print("  'Ciencias Sociales' -> 'Ciencias Sociales' (database)")
        
        print()
        expected_total = sum(areas.values())
        print(f"Total questions that should be imported: {expected_total}")
        
        # Check if we have exactly 480 questions as expected
        if expected_total == 480:
            print("SUCCESS: Found exactly 480 questions as expected!")
        else:
            print(f"WARNING: Expected 480 questions, found {expected_total}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Subject Mapping Verification Test")
    print("=" * 40)
    test_question_distribution()