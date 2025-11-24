#!/usr/bin/env python3
"""
Simple test script to verify Django backend functionality
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forensic_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from rest_framework.authtoken.models import Token
from forensic_api.models import ForensicCase, UserProfile


class BackendTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = Client()
        self.token = None
        self.user = None
        
    def setup_test_user(self):
        """Create test user and get authentication token"""
        print("1. Setting up test user...")
        
        # Create test user
        username = "testuser"
        password = "testpass123"
        email = "test@example.com"
        
        try:
            # Delete existing test user if exists
            User.objects.filter(username=username).delete()
            
            # Create new user
            self.user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name="Test",
                last_name="User"
            )
            
            # Create user profile
            UserProfile.objects.get_or_create(
                user=self.user,
                defaults={
                    'role': 'investigator',
                    'department': 'Testing'
                }
            )
            
            # Create authentication token
            self.token, created = Token.objects.get_or_create(user=self.user)
            
            print(f"✅ Test user created: {username}")
            print(f"✅ Authentication token: {self.token.key}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            return False
    
    def test_authentication(self):
        """Test API authentication"""
        print("\n2. Testing authentication...")
        
        try:
            # Test token authentication
            headers = {'Authorization': f'Token {self.token.key}'}
            response = requests.get(f"{self.base_url}/api/cases/", headers=headers)
            
            if response.status_code == 200:
                print("✅ Token authentication working")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Django server. Make sure it's running:")
            print("   python manage.py runserver")
            return False
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False
    
    def test_case_creation(self):
        """Test creating a forensic case"""
        print("\n3. Testing case creation...")
        
        try:
            headers = {
                'Authorization': f'Token {self.token.key}',
                'Content-Type': 'application/json'
            }
            
            case_data = {
                "title": "Test Case 001",
                "description": "Test case for backend verification",
                "image_path": "/test/path/image.E01",
                "image_name": "test_image.E01",
                "priority": "medium",
                "status": "pending"
            }
            
            response = requests.post(
                f"{self.base_url}/api/cases/",
                headers=headers,
                json=case_data
            )
            
            if response.status_code == 201:
                case = response.json()
                print(f"✅ Case created successfully: {case['case_id']}")
                print(f"   Title: {case['title']}")
                print(f"   Status: {case['status']}")
                return case
            else:
                print(f"❌ Case creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Case creation error: {e}")
            return None
    
    def test_case_retrieval(self, case_id):
        """Test retrieving case information"""
        print("\n4. Testing case retrieval...")
        
        try:
            headers = {'Authorization': f'Token {self.token.key}'}
            
            # Get case list
            response = requests.get(f"{self.base_url}/api/cases/", headers=headers)
            
            if response.status_code == 200:
                cases = response.json()
                print(f"✅ Retrieved {cases['count']} cases")
                
                # Get specific case
                if cases['results']:
                    case = cases['results'][0]
                    case_detail_response = requests.get(
                        f"{self.base_url}/api/cases/{case['id']}/",
                        headers=headers
                    )
                    
                    if case_detail_response.status_code == 200:
                        case_detail = case_detail_response.json()
                        print(f"✅ Case detail retrieved: {case_detail['case_id']}")
                        return case_detail
                    else:
                        print(f"❌ Case detail retrieval failed: {case_detail_response.status_code}")
                
                return cases['results'][0] if cases['results'] else None
            else:
                print(f"❌ Case retrieval failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Case retrieval error: {e}")
            return None
    
    def test_case_notes(self, case_id):
        """Test adding case notes"""
        print("\n5. Testing case notes...")
        
        try:
            headers = {
                'Authorization': f'Token {self.token.key}',
                'Content-Type': 'application/json'
            }
            
            note_data = {
                "case": case_id,
                "title": "Test Note",
                "content": "This is a test note for backend verification",
                "is_important": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/notes/",
                headers=headers,
                json=note_data
            )
            
            if response.status_code == 201:
                note = response.json()
                print(f"✅ Note created successfully: {note['title']}")
                
                # Get notes for case
                notes_response = requests.get(
                    f"{self.base_url}/api/notes/?case_id={case_id}",
                    headers=headers
                )
                
                if notes_response.status_code == 200:
                    notes = notes_response.json()
                    print(f"✅ Retrieved {len(notes)} notes for case")
                    return True
                
            else:
                print(f"❌ Note creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Case notes error: {e}")
            return False
    
    def test_mongodb_integration(self):
        """Test MongoDB integration"""
        print("\n6. Testing MongoDB integration...")
        
        try:
            from forensic_api.mongodb_service import mongo_service
            
            # Test MongoDB connection
            cases = mongo_service.retrieval.get_all_cases()
            print(f"✅ MongoDB connection working")
            print(f"✅ Found {len(cases)} cases in MongoDB")
            
            if cases:
                case_id = cases[0]['case_id']
                print(f"✅ Sample case ID: {case_id}")
                
                # Test case summary
                summary = mongo_service.get_case_summary(case_id)
                if summary:
                    print(f"✅ Case summary retrieved")
                    print(f"   Browser history: {summary['counts'].get('browser_history', 0)}")
                    print(f"   USB devices: {summary['counts'].get('usb_devices', 0)}")
                    print(f"   User activity: {summary['counts'].get('user_activity', 0)}")
                else:
                    print("⚠️  No case summary found (normal if no data imported)")
            
            return True
            
        except Exception as e:
            print(f"❌ MongoDB integration error: {e}")
            print("   Make sure MongoDB is running and data is imported")
            return False
    
    def test_api_endpoints(self, case_id):
        """Test various API endpoints"""
        print("\n7. Testing API endpoints...")
        
        headers = {'Authorization': f'Token {self.token.key}'}
        endpoints_to_test = [
            ('/api/cases/', 'Cases list'),
            ('/api/profiles/me/', 'User profile'),
            ('/api/audit/', 'Audit logs'),
        ]
        
        success_count = 0
        
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
                if response.status_code == 200:
                    print(f"✅ {description}: OK")
                    success_count += 1
                else:
                    print(f"❌ {description}: {response.status_code}")
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
        
        print(f"\n✅ {success_count}/{len(endpoints_to_test)} endpoints working")
        return success_count == len(endpoints_to_test)
    
    def test_search_functionality(self, case_id):
        """Test search functionality"""
        print("\n8. Testing search functionality...")
        
        try:
            headers = {'Authorization': f'Token {self.token.key}'}
            
            # Test case search
            search_response = requests.get(
                f"{self.base_url}/api/cases/?search=test",
                headers=headers
            )
            
            if search_response.status_code == 200:
                results = search_response.json()
                print(f"✅ Case search working: {results['count']} results")
                return True
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Django Backend Tests")
        print("=" * 50)
        
        tests = [
            self.setup_test_user,
            self.test_authentication,
            self.test_mongodb_integration,
        ]
        
        # Run basic tests
        for test in tests:
            if not test():
                print(f"\n❌ Test failed: {test.__name__}")
                return False
        
        # Test case operations
        case = self.test_case_creation()
        if case:
            case_id = case['case_id']
            
            # Run case-specific tests
            case_tests = [
                lambda: self.test_case_retrieval(case_id),
                lambda: self.test_case_notes(case['id']),
                lambda: self.test_api_endpoints(case_id),
                lambda: self.test_search_functionality(case_id),
            ]
            
            for test in case_tests:
                if not test():
                    print(f"\n⚠️  Test had issues: {test}")
        
        print("\n" + "=" * 50)
        print("🎉 Backend tests completed!")
        print("\nNext steps:")
        print("1. Check Django admin: http://localhost:8000/admin/")
        print("2. Browse API: http://localhost:8000/api/")
        print("3. Import real case data:")
        print("   python manage.py import_case ../test_comprehensive_artifacts.json")
        
        return True


def main():
    """Main test function"""
    tester = BackendTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()