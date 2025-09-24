#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class CelestiaAPITester:
    def __init__(self, base_url="https://mystictarot-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_auth_register(self):
        """Test user registration"""
        test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Test User",
            "email": test_email,
            "password": "TestPass123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', register_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log_test("User Registration", True, f"Registered user: {test_email}")
            return True
        else:
            self.log_test("User Registration", False, "Failed to register user", response)
            return False

    def test_auth_login(self):
        """Test user login with existing credentials"""
        if not self.token:
            self.log_test("User Login", False, "No token available from registration")
            return False
            
        # Test /auth/me endpoint to verify token works
        success, response = self.make_request('GET', 'auth/me', None, 200)
        
        if success and 'id' in response:
            self.log_test("User Login/Token Verification", True, f"User authenticated: {response.get('name')}")
            return True
        else:
            self.log_test("User Login/Token Verification", False, "Failed to verify user token", response)
            return False

    def test_birth_data_creation(self):
        """Test creating birth data"""
        birth_data = {
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "time_accuracy": "exact",
            "birth_place": "New York, NY",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200)
        
        if success and 'id' in response:
            self.birth_data_id = response['id']
            self.log_test("Birth Data Creation", True, f"Created birth data: {response['id']}")
            return True
        else:
            self.log_test("Birth Data Creation", False, "Failed to create birth data", response)
            return False

    def test_get_birth_data(self):
        """Test retrieving birth data"""
        if not self.user_id:
            self.log_test("Get Birth Data", False, "No user ID available")
            return False
            
        success, response = self.make_request('GET', f'birth-data/{self.user_id}', None, 200)
        
        if success and isinstance(response, list):
            self.log_test("Get Birth Data", True, f"Retrieved {len(response)} birth data records")
            return True
        else:
            self.log_test("Get Birth Data", False, "Failed to retrieve birth data", response)
            return False

    def test_astrology_chart_generation(self):
        """Test generating astrology chart"""
        if not hasattr(self, 'birth_data_id'):
            self.log_test("Astrology Chart Generation", False, "No birth data ID available")
            return False
            
        success, response = self.make_request('POST', f'astrology/chart?birth_data_id={self.birth_data_id}', None, 200)
        
        if success and 'planets' in response and 'houses' in response:
            self.chart_id = response['id']
            planet_count = len(response['planets'])
            house_count = len(response['houses'])
            self.log_test("Astrology Chart Generation", True, f"Generated chart with {planet_count} planets and {house_count} houses")
            return True
        else:
            self.log_test("Astrology Chart Generation", False, "Failed to generate astrology chart", response)
            return False

    def test_get_astrology_charts(self):
        """Test retrieving astrology charts"""
        if not self.user_id:
            self.log_test("Get Astrology Charts", False, "No user ID available")
            return False
            
        success, response = self.make_request('GET', f'astrology/charts/{self.user_id}', None, 200)
        
        if success and isinstance(response, list):
            self.log_test("Get Astrology Charts", True, f"Retrieved {len(response)} astrology charts")
            return True
        else:
            self.log_test("Get Astrology Charts", False, "Failed to retrieve astrology charts", response)
            return False

    def test_tarot_spreads(self):
        """Test getting tarot spreads"""
        success, response = self.make_request('GET', 'tarot/spreads', None, 200)
        
        if success and isinstance(response, list) and len(response) > 0:
            self.spreads = response
            spread_names = [spread['name'] for spread in response]
            self.log_test("Get Tarot Spreads", True, f"Retrieved {len(response)} spreads: {', '.join(spread_names)}")
            return True
        else:
            self.log_test("Get Tarot Spreads", False, "Failed to retrieve tarot spreads", response)
            return False

    def test_tarot_cards(self):
        """Test getting tarot cards"""
        success, response = self.make_request('GET', 'tarot/cards', None, 200)
        
        if success and isinstance(response, list) and len(response) > 0:
            self.cards = response
            card_names = [card['name'] for card in response[:3]]  # Show first 3
            self.log_test("Get Tarot Cards", True, f"Retrieved {len(response)} cards including: {', '.join(card_names)}")
            return True
        else:
            self.log_test("Get Tarot Cards", False, "Failed to retrieve tarot cards", response)
            return False

    def test_tarot_reading(self):
        """Test creating a tarot reading"""
        if not hasattr(self, 'spreads') or not self.spreads:
            self.log_test("Create Tarot Reading", False, "No spreads available")
            return False
            
        # Use the first spread
        spread_id = self.spreads[0]['id']
        
        success, response = self.make_request('POST', f'tarot/reading?spread_id={spread_id}', None, 200)
        
        if success and 'cards' in response and len(response['cards']) > 0:
            self.reading_id = response['id']
            card_count = len(response['cards'])
            spread_name = self.spreads[0]['name']
            self.log_test("Create Tarot Reading", True, f"Created {spread_name} reading with {card_count} cards")
            return True
        else:
            self.log_test("Create Tarot Reading", False, "Failed to create tarot reading", response)
            return False

    def test_sessions_creation(self):
        """Test creating a session"""
        # First create a reader user for session creation
        reader_email = f"reader_{datetime.now().strftime('%H%M%S')}@celestia.com"
        reader_data = {
            "name": "Test Reader",
            "email": reader_email,
            "password": "ReaderPass123!",
            "role": "reader"
        }
        
        success, response = self.make_request('POST', 'auth/register', reader_data, 200)
        
        if not success:
            self.log_test("Session Creation (Reader Setup)", False, "Failed to create reader user", response)
            return False
            
        # Store original token and switch to reader
        original_token = self.token
        original_user_id = self.user_id
        self.token = response['access_token']
        reader_id = response['user']['id']
        
        # Create session
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            "client_id": original_user_id,
            "service_type": "Astrology Reading - 60min",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat()
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            self.log_test("Session Creation", True, f"Created session: {response['service_type']}")
            
            # Restore original token
            self.token = original_token
            self.user_id = original_user_id
            return True
        else:
            self.log_test("Session Creation", False, "Failed to create session", response)
            # Restore original token
            self.token = original_token
            self.user_id = original_user_id
            return False

    def test_get_sessions(self):
        """Test retrieving sessions"""
        success, response = self.make_request('GET', 'sessions', None, 200)
        
        if success and isinstance(response, list):
            self.log_test("Get Sessions", True, f"Retrieved {len(response)} sessions")
            return True
        else:
            self.log_test("Get Sessions", False, "Failed to retrieve sessions", response)
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🌟 Starting Celestia API Tests...")
        print("=" * 50)
        
        # Authentication tests
        print("\n🔐 Authentication Tests:")
        if not self.test_auth_register():
            print("❌ Registration failed - stopping tests")
            return False
            
        self.test_auth_login()
        
        # Astrology tests
        print("\n⭐ Astrology Tests:")
        self.test_birth_data_creation()
        self.test_get_birth_data()
        self.test_astrology_chart_generation()
        self.test_get_astrology_charts()
        
        # Tarot tests
        print("\n🔮 Tarot Tests:")
        self.test_tarot_spreads()
        self.test_tarot_cards()
        self.test_tarot_reading()
        
        # Session tests
        print("\n📅 Session Tests:")
        self.test_sessions_creation()
        self.test_get_sessions()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

    def save_results(self, filename: str = "/app/test_reports/backend_test_results.json"):
        """Save test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_details": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Test results saved to: {filename}")

def main():
    tester = CelestiaAPITester()
    success = tester.run_all_tests()
    tester.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())