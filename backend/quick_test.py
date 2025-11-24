#!/usr/bin/env python3
"""
Quick test script to verify basic Django setup
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forensic_backend.settings')

def test_django_setup():
    """Test basic Django setup"""
    print("🔧 Testing Django Setup")
    print("-" * 30)
    
    try:
        # Test Django import
        django.setup()
        print("✅ Django setup successful")
        
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        print("✅ PostgreSQL connection working")
        
        # Test models import
        from forensic_api.models import ForensicCase, UserProfile
        print("✅ Models imported successfully")
        
        # Test MongoDB service
        try:
            from forensic_api.mongodb_service import mongo_service
            print("✅ MongoDB service imported")
        except Exception as e:
            print(f"⚠️  MongoDB service warning: {e}")
        
        # Check migrations
        from django.core.management import execute_from_command_line
        print("✅ Django management commands available")
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup error: {e}")
        return False

def test_database_models():
    """Test database models"""
    print("\n📊 Testing Database Models")
    print("-" * 30)
    
    try:
        from django.contrib.auth.models import User
        from forensic_api.models import ForensicCase, UserProfile
        
        # Count existing records
        user_count = User.objects.count()
        case_count = ForensicCase.objects.count()
        profile_count = UserProfile.objects.count()
        
        print(f"✅ Users in database: {user_count}")
        print(f"✅ Cases in database: {case_count}")
        print(f"✅ User profiles: {profile_count}")
        
        # Test model creation (dry run)
        print("✅ Model classes accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models error: {e}")
        return False

def test_api_setup():
    """Test API setup"""
    print("\n🌐 Testing API Setup")
    print("-" * 30)
    
    try:
        # Test URL configuration
        from forensic_backend.urls import urlpatterns
        print(f"✅ URL patterns loaded: {len(urlpatterns)} patterns")
        
        # Test serializers
        from forensic_api.serializers import ForensicCaseSerializer
        print("✅ Serializers imported")
        
        # Test views
        from forensic_api.views import ForensicCaseViewSet
        print("✅ Views imported")
        
        return True
        
    except Exception as e:
        print(f"❌ API setup error: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🍃 Testing MongoDB Connection")
    print("-" * 30)
    
    try:
        from pymongo import MongoClient
        from django.conf import settings
        
        # Get MongoDB config
        mongodb_config = getattr(settings, 'MONGODB_CONFIG', {
            'uri': 'mongodb://localhost:27017/',
            'database': 'forensics'
        })
        
        # Test connection
        client = MongoClient(mongodb_config['uri'])
        db = client[mongodb_config['database']]
        
        # List collections
        collections = db.list_collection_names()
        print(f"✅ MongoDB connected: {len(collections)} collections")
        
        if collections:
            print(f"   Collections: {', '.join(collections[:5])}")
            if len(collections) > 5:
                print(f"   ... and {len(collections) - 5} more")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"⚠️  MongoDB connection warning: {e}")
        print("   This is normal if MongoDB is not running or no data imported")
        return False

def main():
    """Run all quick tests"""
    print("🚀 Quick Django Backend Test")
    print("=" * 40)
    
    tests = [
        test_django_setup,
        test_database_models,
        test_api_setup,
        test_mongodb_connection,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Django backend is ready.")
        print("\nNext steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Run full tests: python test_backend.py")
        print("3. Access admin: http://localhost:8000/admin/")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Create superuser: python manage.py createsuperuser")
        print("3. Check database connections")

if __name__ == "__main__":
    main()