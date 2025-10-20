#!/usr/bin/env python3
"""
Simple test script to verify model relationships
"""

import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps', 'backend')
sys.path.insert(0, backend_path)

def test_direct_model_imports():
    """Test importing models directly without config dependency"""
    print("Testing direct model imports...")
    
    try:
        # Import models directly
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        print("[PASS] Direct model imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Direct model import failed: {e}")
        return False

def test_relationship_attributes():
    """Test that relationships are properly defined"""
    print("Testing relationship attributes...")
    
    try:
        from app.models.user import User
        from app.models.notification import Notification
        
        # Check User has notifications relationship
        if hasattr(User, 'notifications'):
            print("[PASS] User.notifications relationship exists")
        else:
            print("[FAIL] User.notifications relationship missing")
            return False
            
        # Check Notification has user relationship
        if hasattr(Notification, 'user'):
            print("[PASS] Notification.user relationship exists")
        else:
            print("[FAIL] Notification.user relationship missing")
            return False
            
        return True
    except Exception as e:
        print(f"[FAIL] Relationship test failed: {e}")
        return False

def test_foreign_key_consistency():
    """Test foreign key type consistency"""
    print("Testing foreign key type consistency...")
    
    try:
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        from sqlalchemy.dialects.postgresql import UUID
        
        # Get column types
        user_id_type = str(User.id.type)
        notification_user_id_type = str(Notification.user_id.type)
        subscription_user_id_type = str(Subscription.user_id.type)
        
        print(f"User.id type: {user_id_type}")
        print(f"Notification.user_id type: {notification_user_id_type}")
        print(f"Subscription.user_id type: {subscription_user_id_type}")
        
        # Check if all contain UUID
        if 'UUID' in user_id_type and 'UUID' in notification_user_id_type and 'UUID' in subscription_user_id_type:
            print("[PASS] All foreign key types are UUID consistent")
            return True
        else:
            print("[FAIL] Foreign key type mismatch detected")
            return False
            
    except Exception as e:
        print(f"[FAIL] Foreign key consistency test failed: {e}")
        return False

def test_notification_back_populates():
    """Test notification back_populates configuration"""
    print("Testing notification back_populates...")
    
    try:
        # Import models in the right order to avoid circular dependency issues
        from app.models.achievement import Achievement, UserAchievement
        from app.models.notification import Notification
        from app.models.user import User
        
        # Check Notification.user relationship
        notification_user_rel = getattr(Notification, 'user', None)
        if notification_user_rel and hasattr(notification_user_rel.property, 'back_populates'):
            back_pop = notification_user_rel.property.back_populates
            if back_pop == 'notifications':
                print("[PASS] Notification.user back_populates='notifications'")
            else:
                print(f"[FAIL] Notification.user back_populates='{back_pop}', expected 'notifications'")
                return False
        else:
            print("[FAIL] Notification.user relationship or back_populates not found")
            return False
            
        # Check User.notifications relationship
        user_notifications_rel = getattr(User, 'notifications', None)
        if user_notifications_rel and hasattr(user_notifications_rel.property, 'back_populates'):
            back_pop = user_notifications_rel.property.back_populates
            if back_pop == 'user':
                print("[PASS] User.notifications back_populates='user'")
            else:
                print(f"[FAIL] User.notifications back_populates='{back_pop}', expected 'user'")
                return False
        else:
            print("[FAIL] User.notifications relationship or back_populates not found")
            return False
            
        return True
    except Exception as e:
        print(f"[FAIL] back_populates test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("[TEST] RUNNING SIMPLE DATABASE MODEL TESTS")
    print("=" * 60)
    
    tests = [
        test_direct_model_imports,
        test_relationship_attributes,
        test_foreign_key_consistency,
        test_notification_back_populates
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
        print("[SUCCESS] ALL TESTS PASSED! Database model fixes are working correctly.")
        print("[INFO] The critical User-Notification relationship has been fixed.")
        print("[INFO] Foreign key types are now consistent (all UUID).")
    else:
        print("[WARNING] Some tests failed. Review the issues above.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)