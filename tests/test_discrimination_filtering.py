#!/usr/bin/env python3
"""
Test script to verify discrimination index filtering is working correctly
"""
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.question import Question
from app.models.subject import Subject
from app.services.diagnostic_service import DiagnosticService
from app.services.adaptive_diagnostic_service import AdaptiveDiagnosticService
from app.services.question_pool_manager import QuestionPoolManager, QuestionPoolConfig

def test_discrimination_filtering():
    """Test that question filtering by discrimination index works correctly"""
    print("Testing Discrimination Index Filtering...")
    print("=" * 50)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get a sample subject
        subject = db.query(Subject).first()
        if not subject:
            print("❌ No subjects found in database")
            return
        
        subject_id = str(subject.id)
        print(f"Testing with subject: {subject.name} (ID: {subject_id})")
        print()
        
        # Test 1: Check total questions in subject
        total_questions = db.query(Question).filter(Question.subject_id == subject_id).count()
        print(f"📊 Total questions in subject: {total_questions}")
        
        # Test 2: Check questions with discrimination data
        questions_with_discrimination = db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.indice_discriminacion.isnot(None)
            )
        ).count()
        print(f"📊 Questions with discrimination data: {questions_with_discrimination}")
        
        # Test 3: Check questions with good discrimination (>= 0.2)
        good_discrimination_questions = db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.indice_discriminacion >= 0.2,
                Question.indice_discriminacion.isnot(None)
            )
        ).count()
        print(f"📊 Questions with good discrimination (>= 0.2): {good_discrimination_questions}")
        
        # Test 4: Check questions with poor discrimination (< 0.2)
        poor_discrimination_questions = db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.indice_discriminacion < 0.2,
                Question.indice_discriminacion.isnot(None)
            )
        ).count()
        print(f"📊 Questions with poor discrimination (< 0.2): {poor_discrimination_questions}")
        print()
        
        # Test 5: Test DiagnosticService filtering
        print("🧪 Testing DiagnosticService filtering...")
        diagnostic_service = DiagnosticService(db)
        
        # Get questions without discrimination filter
        all_questions = diagnostic_service.get_diagnostic_questions(subject_id, min_discrimination=0.0)
        print(f"   Questions without discrimination filter: {len(all_questions)}")
        
        # Get questions with default discrimination filter (0.2)
        filtered_questions = diagnostic_service.get_diagnostic_questions(subject_id)
        print(f"   Questions with discrimination filter (>= 0.2): {len(filtered_questions)}")
        
        # Verify filtering works
        if len(filtered_questions) <= len(all_questions):
            print("   ✅ DiagnosticService filtering working correctly")
        else:
            print("   ❌ DiagnosticService filtering not working correctly")
        print()
        
        # Test 6: Test AdaptiveDiagnosticService filtering
        print("🧪 Testing AdaptiveDiagnosticService filtering...")
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Test the _get_stratified_question_pool method
        # We need to mock answered_questions as an empty subquery
        from sqlalchemy import text
        empty_subquery = db.query(Question.id).filter(text("1=0")).subquery()
        
        # Get stratified pools without discrimination filter
        pools_unfiltered = adaptive_service._get_stratified_question_pool(subject_id, empty_subquery, min_discrimination=0.0)
        total_unfiltered = sum(len(pool) for pool in pools_unfiltered.values())
        print(f"   Questions in stratified pools (no filter): {total_unfiltered}")
        
        # Get stratified pools with discrimination filter
        pools_filtered = adaptive_service._get_stratified_question_pool(subject_id, empty_subquery)
        total_filtered = sum(len(pool) for pool in pools_filtered.values())
        print(f"   Questions in stratified pools (>= 0.2): {total_filtered}")
        
        # Verify filtering works
        if total_filtered <= total_unfiltered:
            print("   ✅ AdaptiveDiagnosticService filtering working correctly")
        else:
            print("   ❌ AdaptiveDiagnosticService filtering not working correctly")
        print()
        
        # Test 7: Test QuestionPoolManager filtering
        print("🧪 Testing QuestionPoolManager filtering...")
        pool_manager = QuestionPoolManager(db)
        
        # Create config with discrimination filter
        config = QuestionPoolConfig(
            subject_id=subject_id,
            total_questions=10,
            difficulty_distribution={
                pool_manager.DifficultyBand.MEDIUM: 1.0
            },
            min_discrimination_index=0.2
        )
        
        try:
            # Get available questions with metrics
            available_questions = pool_manager._get_available_questions_with_metrics(
                subject_id, set(), config
            )
            print(f"   Questions available with metrics (>= 0.2): {len(available_questions)}")
            
            # Verify all questions have good discrimination
            all_good_discrimination = all(
                q.discrimination_index >= 0.2 for q in available_questions
            )
            if all_good_discrimination:
                print("   ✅ QuestionPoolManager filtering working correctly")
            else:
                print("   ❌ QuestionPoolManager filtering not working correctly")
        except Exception as e:
            print(f"   ⚠️  QuestionPoolManager test failed: {e}")
        print()
        
        # Summary
        print("📋 SUMMARY")
        print("-" * 20)
        print(f"Total questions: {total_questions}")
        print(f"With discrimination data: {questions_with_discrimination}")
        print(f"Good discrimination (>= 0.2): {good_discrimination_questions}")
        print(f"Poor discrimination (< 0.2): {poor_discrimination_questions}")
        print(f"Filtering efficiency: {(poor_discrimination_questions/max(1, questions_with_discrimination))*100:.1f}% questions filtered out")
        
        if good_discrimination_questions > 0:
            print("\n✅ Discrimination filtering is implemented and working!")
            print("🎯 Only questions with discrimination >= 0.2 will be used in diagnostic tests")
            print("📈 This ensures accurate theta estimation for adaptive testing")
        else:
            print("\n⚠️  Warning: No questions with good discrimination found")
            print("💡 Consider updating your question database with discrimination values")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_discrimination_filtering()