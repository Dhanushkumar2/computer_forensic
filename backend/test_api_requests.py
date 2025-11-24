#!/usr/bin/env python3
"""
Test API requests with curl-like functionality
"""
import requests
import json
import sys
from datetime import datetime


class APITester:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({'Authorization': f'Token {token}'})
    
    def get_auth_token(self, username, password):
        """Get authentication token"""
        print(f"🔐 Getting authentication token for {username}...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api-token-auth/",
                json={'username': username, 'password': password}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data['token']
                self.session.headers.update({'Authorization': f'Token {self.token}'})
                print(f"✅ Token obtained: {self.token[:20]}...")
                return self.token
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def test_endpoint(self, method, endpoint, data=None, description=""):
        """Test an API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        print(f"\n📡 {description or f'{method} {endpoint}'}")
        print(f"URL: {url}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                print(f"❌ Unsupported method: {method}")
                return None
            
            print(f"Status: {response.status_code}")
            
            if response.status_code < 400:
                print("✅ Success")
                
                # Pretty print JSON response
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        if 'results' in json_data:
                            print(f"Results count: {len(json_data['results'])}")
                            if json_data['results']:
                                print("Sample result keys:", list(json_data['results'][0].keys()))
                        else:
                            print("Response keys:", list(json_data.keys()))
                    elif isinstance(json_data, list):
                        print(f"List length: {len(json_data)}")
                        if json_data:
                            print("Sample item keys:", list(json_data[0].keys()) if isinstance(json_data[0], dict) else "Non-dict items")
                    
                    return json_data
                except:
                    print("Response:", response.text[:200] + "..." if len(response.text) > 200 else response.text)
                    return response.text
            else:
                print(f"❌ Error: {response.status_code}")
                print("Response:", response.text)
                return None
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error. Make sure Django server is running:")
            print("   python manage.py runserver")
            return None
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def run_api_tests(self):
        """Run comprehensive API tests"""
        print("🧪 API Endpoint Tests")
        print("=" * 40)
        
        if not self.token:
            print("⚠️  No authentication token. Some tests may fail.")
            print("Use: tester.get_auth_token('username', 'password')")
        
        # Test basic endpoints
        tests = [
            ('GET', '/api/', None, 'API Root'),
            ('GET', '/api/cases/', None, 'List Cases'),
            ('GET', '/api/profiles/me/', None, 'Current User Profile'),
            ('GET', '/api/audit/', None, 'Audit Logs'),
        ]
        
        results = {}
        
        for method, endpoint, data, description in tests:
            result = self.test_endpoint(method, endpoint, data, description)
            results[endpoint] = result
        
        # Test case creation if authenticated
        if self.token:
            print(f"\n📝 Testing Case Creation")
            case_data = {
                "title": f"API Test Case {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Test case created via API",
                "image_path": "/test/api_test.E01",
                "image_name": "api_test.E01",
                "priority": "medium"
            }
            
            case_result = self.test_endpoint('POST', '/api/cases/', case_data, 'Create Test Case')
            
            if case_result and isinstance(case_result, dict) and 'id' in case_result:
                case_id = case_result['id']
                
                # Test case-specific endpoints
                case_tests = [
                    ('GET', f'/api/cases/{case_id}/', None, 'Get Case Detail'),
                    ('GET', f'/api/cases/{case_id}/summary/', None, 'Get Case Summary'),
                    ('GET', f'/api/cases/{case_id}/timeline/', None, 'Get Case Timeline'),
                ]
                
                for method, endpoint, data, description in case_tests:
                    self.test_endpoint(method, endpoint, data, description)
                
                # Test adding a note
                note_data = {
                    "case": case_id,
                    "title": "API Test Note",
                    "content": "This note was created via API test",
                    "is_important": False
                }
                
                self.test_endpoint('POST', '/api/notes/', note_data, 'Add Case Note')
        
        return results


def main():
    """Main test function"""
    print("🌐 Django API Request Tester")
    print("=" * 50)
    
    # Initialize tester
    tester = APITester()
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        print("✅ Django server is running")
    except:
        print("❌ Django server is not running or not accessible")
        print("Start the server with: python manage.py runserver")
        return
    
    # Get credentials
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        tester.get_auth_token(username, password)
    else:
        print("💡 Usage: python test_api_requests.py <username> <password>")
        print("   Or run without credentials for public endpoint tests")
    
    # Run tests
    results = tester.run_api_tests()
    
    print("\n" + "=" * 50)
    print("📊 API Test Summary")
    
    successful_tests = sum(1 for result in results.values() if result is not None)
    total_tests = len(results)
    
    print(f"Successful requests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All API tests passed!")
    else:
        print("⚠️  Some API tests failed. Check the output above.")
    
    print("\n💡 Tips:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Import test data: python manage.py import_case ../test_comprehensive_artifacts.json")
    print("3. Browse API: http://localhost:8000/api/")


if __name__ == "__main__":
    main()