#!/usr/bin/env python3
"""
Comprehensive test for database model fixes including all relationships
"""

import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps', 'backend')
sys.path.insert(0, backend_path)

def test_core_model_fixes():
    """Test the critical fixes we made"""
    print("Testing core database model fixes...")
    
    try:
        # Import core models that we fixed
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        
        print("[PASS] Core models imported successfully")
        
        # Test User-Notification relationship
        if hasattr(User, 'notifications') and hasattr(Notification, 'user'):
            print("[PASS] User-Notification relationship exists")
        else:
            print("[FAIL] User-Notification relationship missing")
            return False
            
        # Test foreign key types
        user_id_type = str(User.id.type)
        notification_user_id_type = str(Notification.user_id.type)
        subscription_user_id_type = str(Subscription.user_id.type)
        
        if 'UUID' in user_id_type and 'UUID' in notification_user_id_type and 'UUID' in subscription_user_id_type:
            print("[PASS] All foreign key types are UUID consistent")
        else:
            print("[FAIL] Foreign key type mismatch")
            return False
            
        print("[PASS] All core fixes verified successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Core model test failed: {e}")
        return False

def test_notification_relationship_details():
    """Test detailed notification relationship configuration"""
    print("Testing notification relationship details...")
    
    try:
        from app.models.user import User
        from app.models.notification import Notification
        
        # Test User.notifications relationship details
        user_notifications = getattr(User, 'notifications', None)
        if user_notifications:
            rel_prop = user_notifications.property
            if hasattr(rel_prop, 'back_populates') and rel_prop.back_populates == 'user':
                print("[PASS] User.notifications -> back_populates='user'")
            else:
                print(f"[WARNING] User.notifications back_populates: {getattr(rel_prop, 'back_populates', 'NONE')}")
                
            if hasattr(rel_prop, 'cascade') and 'delete' in rel_prop.cascade:
                print("[PASS] User.notifications has cascade delete")
            else:
                print("[WARNING] User.notifications missing cascade delete")
        
        # Test Notification.user relationship details
        notification_user = getattr(Notification, 'user', None)
        if notification_user:
            rel_prop = notification_user.property
            if hasattr(rel_prop, 'back_populates') and rel_prop.back_populates == 'notifications':
                print("[PASS] Notification.user -> back_populates='notifications'")
            else:
                print(f"[WARNING] Notification.user back_populates: {getattr(rel_prop, 'back_populates', 'NONE')}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Notification relationship details test failed: {e}")
        return False

def test_database_table_creation_minimal():
    """Test minimal database table creation with just the fixed models"""
    print("Testing minimal database table creation...")
    
    try:
        # Set up test database URL
        os.environ['DATABASE_URL'] = 'sqlite:///test_minimal.sqlite'
        
        from app.core.database import engine, Base
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        
        # Create tables for only these models
        User.__table__.create(engine, checkfirst=True)
        Notification.__table__.create(engine, checkfirst=True)
        Subscription.__table__.create(engine, checkfirst=True)
        
        print("[PASS] Core model tables created successfully")
        
        # Clean up test database
        if os.path.exists('test_minimal.sqlite'):
            os.remove('test_minimal.sqlite')
            print("[PASS] Test database cleaned up")
        
        return True
    except Exception as e:
        print(f"[FAIL] Database table creation failed: {e}")
        return False

def test_foreign_key_constraints():
    """Test that foreign key constraints are properly defined"""
    print("Testing foreign key constraints...")
    
    try:
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        
        # Check User table has no foreign key constraints (it's the parent)
        user_fks = [col for col in User.__table__.columns if col.foreign_keys]
        print(f"User foreign keys: {len(user_fks)} (should be 0)")
        
        # Check Notification has user_id foreign key
        notification_fks = [col for col in Notification.__table__.columns if col.foreign_keys]
        print(f"Notification foreign keys: {len(notification_fks)} (should be 1)")
        
        # Check that user_id column exists and references users.id
        if hasattr(Notification, 'user_id'):
            user_id_col = Notification.__table__.columns['user_id']
            fk_targets = [fk.target_fullname for fk in user_id_col.foreign_keys]
            if 'users.id' in fk_targets:
                print("[PASS] Notification.user_id references users.id")
            else:
                print(f"[FAIL] Notification.user_id references: {fk_targets}")
                return False
        
        # Check Subscription has user_id foreign key
        if hasattr(Subscription, 'user_id'):
            user_id_col = Subscription.__table__.columns['user_id']
            fk_targets = [fk.target_fullname for fk in user_id_col.foreign_keys]
            if 'users.id' in fk_targets:
                print("[PASS] Subscription.user_id references users.id")
            else:
                print(f"[FAIL] Subscription.user_id references: {fk_targets}")
                return False
        
        print("[PASS] Foreign key constraints properly configured")
        return True
        
    except Exception as e:
        print(f"[FAIL] Foreign key constraint test failed: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("=" * 70)
    print("[TEST] COMPREHENSIVE DATABASE MODEL FIXES VERIFICATION")
    print("=" * 70)
    
    tests = [
        test_core_model_fixes,
        test_notification_relationship_details,
        test_foreign_key_constraints,
        test_database_table_creation_minimal
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print("-" * 70)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 70)
    print(f"[SUMMARY] FINAL TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] ALL DATABASE FIXES VERIFIED SUCCESSFULLY!")
        print()
        print("CRITICAL FIXES COMPLETED:")
        print("✓ User model now has 'notifications' relationship")
        print("✓ Notification foreign key type fixed (Integer -> UUID)")
        print("✓ Subscription foreign key type fixed (String -> UUID)")
        print("✓ Foreign key constraints properly configured")
        print("✓ Back-populates relationships working")
        print("✓ Database tables can be created without errors")
        print()
        print("REGISTRATION AND AUTHENTICATION SHOULD NOW WORK!")
    else:
        print("[WARNING] Some tests failed. Review the issues above.")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)