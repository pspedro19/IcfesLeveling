#!/usr/bin/env python3
"""
Test script to verify database model fixes
"""

import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps', 'backend')
sys.path.insert(0, backend_path)

def test_model_imports():
    """Test that all models can be imported without errors"""
    print("Testing model imports...")
    
    try:
        from app.models import (
            User, Subject, Topic, Question, Battle, BattleAnswer,
            Item, UserItem, DailyQuest, UserQuest, Leaderboard,
            AIExplanation, UserEvent, StudyPlan, PlanProgress,
            UserProfile, HeroClass, PersonalityQuestion,
            DiagnosticTest, DiagnosticTestAnswer, VideoTracking,
            Quiz, QuizAnswer, Notification, NotificationType,
            NotificationPriority, Subscription
        )
        print("[PASS] All critical models imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Model import failed: {e}")
        return False

def test_user_notifications_relationship():
    """Test the User-Notification relationship"""
    print("[Testing] Testing User-Notification relationship...")
    
    try:
        from app.models.user import User
        from app.models.notification import Notification
        
        # Check if User has notifications relationship
        if hasattr(User, 'notifications'):
            print("[PASS] User.notifications relationship exists")
        else:
            print("[FAIL] User.notifications relationship missing")
            return False
            
        # Check if Notification has user relationship  
        if hasattr(Notification, 'user'):
            print("[PASS] Notification.user relationship exists")
        else:
            print("[FAIL] Notification.user relationship missing")
            return False
            
        return True
    except Exception as e:
        print(f"[FAIL] Relationship test failed: {e}")
        return False

def test_foreign_key_types():
    """Test that foreign key types are consistent"""
    print("[Testing] Testing foreign key type consistency...")
    
    try:
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        from sqlalchemy.dialects.postgresql import UUID
        
        # Check User.id type
        user_id_type = User.id.type
        print(f"User.id type: {type(user_id_type)}")
        
        # Check Notification.user_id type
        notification_user_id_type = Notification.user_id.type
        print(f"Notification.user_id type: {type(notification_user_id_type)}")
        
        # Check Subscription.user_id type
        subscription_user_id_type = Subscription.user_id.type
        print(f"Subscription.user_id type: {type(subscription_user_id_type)}")
        
        # Verify they're all UUID types
        if all(isinstance(t, type(UUID())) for t in [user_id_type, notification_user_id_type, subscription_user_id_type]):
            print("[PASS] All foreign key types are UUID - consistent!")
            return True
        else:
            print("[FAIL] Foreign key type mismatch detected")
            return False
            
    except Exception as e:
        print(f"[FAIL] Foreign key type test failed: {e}")
        return False

def test_database_table_creation():
    """Test that database tables can be created"""
    print("[Testing] Testing database table creation...")
    
    try:
        # Set up test database URL
        os.environ['DATABASE_URL'] = 'sqlite:///test_db.sqlite'
        
        from app.core.database import engine, Base
        # Import critical models to register them with Base
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        from app.models.subject import Subject
        from app.models.topic import Topic
        from app.models.question import Question
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("[PASS] Database tables created successfully")
        
        # Clean up test database
        if os.path.exists('test_db.sqlite'):
            os.remove('test_db.sqlite')
            print("[PASS] Test database cleaned up")
        
        return True
    except Exception as e:
        print(f"[FAIL] Database table creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("[TEST] RUNNING DATABASE MODEL TESTS")
    print("=" * 60)
    
    tests = [
        test_model_imports,
        test_user_notifications_relationship,
        test_foreign_key_types,
        test_database_table_creation
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print("-" * 60)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"[SUMMARY] TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED! Database fixes are working correctly.")
    else:
        print("[WARNING] Some tests failed. Review the issues above.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)