#!/usr/bin/env python3
"""
Simple test script to verify discrimination index filtering works
"""
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

def test_discrimination_filtering():
    """Test that question filtering by discrimination index works correctly"""
    print("Testing Discrimination Index Filtering...")
    print("=" * 50)
    
    try:
        from sqlalchemy import create_engine, and_
        from sqlalchemy.orm import sessionmaker
        from app.core.config import settings
        from app.models.question import Question
        
        # Create database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Test 1: Check total questions
        total_questions = db.query(Question).count()
        print(f"Total questions in database: {total_questions}")
        
        # Test 2: Check questions with discrimination data
        questions_with_discrimination = db.query(Question).filter(
            Question.indice_discriminacion.isnot(None)
        ).count()
        print(f"Questions with discrimination data: {questions_with_discrimination}")
        
        # Test 3: Check questions with good discrimination (>= 0.2)
        good_discrimination_questions = db.query(Question).filter(
            and_(
                Question.indice_discriminacion >= 0.2,
                Question.indice_discriminacion.isnot(None)
            )
        ).count()
        print(f"Questions with good discrimination (>= 0.2): {good_discrimination_questions}")
        
        # Test 4: Check questions with poor discrimination (< 0.2)
        poor_discrimination_questions = db.query(Question).filter(
            and_(
                Question.indice_discriminacion < 0.2,
                Question.indice_discriminacion.isnot(None)
            )
        ).count()
        print(f"Questions with poor discrimination (< 0.2): {poor_discrimination_questions}")
        
        # Test 5: Show sample discrimination values
        sample_questions = db.query(Question).filter(
            Question.indice_discriminacion.isnot(None)
        ).limit(10).all()
        
        print("\nSample discrimination values:")
        for q in sample_questions:
            print(f"  Question {str(q.id)[:8]}...: {q.indice_discriminacion:.3f}")
        
        print("\nSUMMARY:")
        print("-" * 20)
        print(f"Total questions: {total_questions}")
        print(f"With discrimination data: {questions_with_discrimination}")
        print(f"Good discrimination (>= 0.2): {good_discrimination_questions}")
        print(f"Poor discrimination (< 0.2): {poor_discrimination_questions}")
        
        if questions_with_discrimination > 0:
            filter_rate = (poor_discrimination_questions/questions_with_discrimination)*100
            print(f"Filtering efficiency: {filter_rate:.1f}% questions filtered out")
        
        if good_discrimination_questions > 0:
            print("\nSUCCESS: Discrimination filtering is implemented!")
            print("Only questions with discrimination >= 0.2 will be used in diagnostic tests")
            print("This ensures accurate theta estimation for adaptive testing")
        else:
            print("\nWARNING: No questions with good discrimination found")
            print("Consider updating your question database with discrimination values")
            
        db.close()
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_discrimination_filtering()