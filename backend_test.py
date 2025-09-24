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
            "latitude": "40.7128",  # Changed to string
            "longitude": "-74.0060"  # Changed to string
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

    def test_reader_registration(self):
        """Test reader registration system - should prevent multiple readers"""
        reader_email = f"reader_{datetime.now().strftime('%H%M%S')}@celestia.com"
        reader_data = {
            "name": "Test Reader",
            "email": reader_email,
            "password": "ReaderPass123!",
            "role": "reader"
        }
        
        # Try to register a reader - should fail if one already exists
        success, response = self.make_request('POST', 'auth/register-reader', reader_data, 400)
        
        if not success and "already exists" in str(response):
            self.log_test("Reader Registration (Duplicate Prevention)", True, "Correctly prevented duplicate reader registration - reader already exists")
            # Since reader exists, we can't test reader dashboard without credentials
            # But we can verify the system is working
            return True
        else:
            # If no reader exists, try to register one
            success, response = self.make_request('POST', 'auth/register-reader', reader_data, 200)
            if success and 'access_token' in response:
                self.reader_token = response['access_token']
                self.reader_id = response['user']['id']
                self.log_test("Reader Registration (First)", True, f"Successfully registered first reader: {reader_email}")
                
                # Test second reader registration - should fail
                second_reader_email = f"reader2_{datetime.now().strftime('%H%M%S')}@celestia.com"
                second_reader_data = {
                    "name": "Second Reader",
                    "email": second_reader_email,
                    "password": "ReaderPass123!",
                    "role": "reader"
                }
                
                success2, response2 = self.make_request('POST', 'auth/register-reader', second_reader_data, 400)
                
                if not success2 and "already exists" in str(response2):
                    self.log_test("Reader Registration (Duplicate Prevention)", True, "Correctly prevented second reader registration")
                    return True
                else:
                    self.log_test("Reader Registration (Duplicate Prevention)", False, "Failed to prevent duplicate reader", response2)
                    return False
            else:
                self.log_test("Reader Registration (First)", False, "Failed to register first reader", response)
                return False

    def test_get_me_endpoint(self):
        """Test /api/auth/me endpoint"""
        if not self.token:
            self.log_test("Get Me Endpoint", False, "No token available")
            return False
            
        success, response = self.make_request('GET', 'auth/me', None, 200)
        
        if success and 'id' in response and 'email' in response and 'name' in response:
            self.log_test("Get Me Endpoint", True, f"Retrieved user info: {response.get('name')} ({response.get('email')})")
            return True
        else:
            self.log_test("Get Me Endpoint", False, "Failed to retrieve user info", response)
            return False

    def test_reader_dashboard(self):
        """Test reader dashboard access"""
        if not hasattr(self, 'reader_token'):
            # If we don't have reader token, test that non-reader access is denied
            success, response = self.make_request('GET', 'reader/dashboard', None, 403)
            if not success and ('Reader access required' in str(response) or 'Forbidden' in str(response)):
                self.log_test("Reader Dashboard (Access Control)", True, "Correctly denied non-reader access to dashboard")
                return True
            else:
                self.log_test("Reader Dashboard (Access Control)", False, "Failed to deny non-reader access", response)
                return False
            
        # Store original token and switch to reader
        original_token = self.token
        self.token = self.reader_token
        
        success, response = self.make_request('GET', 'reader/dashboard', None, 200)
        
        # Restore original token
        self.token = original_token
        
        if success and 'stats' in response and 'recent_clients' in response:
            stats = response['stats']
            self.log_test("Reader Dashboard", True, f"Dashboard loaded - Total sessions: {stats.get('total_sessions', 0)}")
            return True
        else:
            self.log_test("Reader Dashboard", False, "Failed to load reader dashboard", response)
            return False

    def test_sessions_creation(self):
        """Test creating a session with email and payment link generation"""
        if not hasattr(self, 'reader_id'):
            self.log_test("Session Creation", False, "No reader available")
            return False
            
        # Create session as client
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Looking forward to my reading!"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            # Check if payment link was generated
            has_payment_link = 'payment_link' in response and response['payment_link']
            # Check if amount was set
            has_amount = 'amount' in response and response['amount'] > 0
            
            details = f"Session ID: {response['id']}, Amount: ${response.get('amount', 0)}"
            if has_payment_link:
                details += f", Payment Link: {response['payment_link'][:50]}..."
                
            self.log_test("Session Creation", True, details)
            
            # Test that email confirmation was triggered (check console output)
            print("    📧 Email confirmation should be printed to console (mock implementation)")
            print("    💳 Payment link should be generated")
            print("    🔔 Reader notification should be printed to console")
            
            return True
        else:
            self.log_test("Session Creation", False, "Failed to create session", response)
            return False

    def test_payment_completion(self):
        """Test payment completion flow"""
        if not hasattr(self, 'session_id'):
            self.log_test("Payment Completion", False, "No session available for payment")
            return False
            
        success, response = self.make_request('POST', f'sessions/{self.session_id}/payment/complete', None, 200)
        
        if success and 'message' in response:
            self.log_test("Payment Completion", True, f"Payment completed: {response['message']}")
            
            # Verify session status was updated
            success2, session_response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
            if success2 and session_response.get('payment_status') == 'paid':
                self.log_test("Payment Status Update", True, "Session status updated to paid")
                print("    📧 Payment confirmation email should be printed to console")
                print("    🔔 Reader payment notification should be printed to console")
                return True
            else:
                self.log_test("Payment Status Update", False, "Session status not updated", session_response)
                return False
        else:
            self.log_test("Payment Completion", False, "Failed to complete payment", response)
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
        self.test_get_me_endpoint()
        
        # Reader registration tests
        print("\n👑 Reader Registration Tests:")
        self.test_reader_registration()
        self.test_reader_dashboard()
        
        # Session tests (priority tests)
        print("\n📅 Session Management Tests:")
        self.test_sessions_creation()
        self.test_payment_completion()
        self.test_get_sessions()
        
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
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Print mock implementation notes
        print("\n📝 Mock Implementation Notes:")
        print("   📧 Email functionality uses print statements (not actual emails)")
        print("   💳 Payment links are mock URLs")
        print("   🔔 Reader notifications use print statements")
        
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