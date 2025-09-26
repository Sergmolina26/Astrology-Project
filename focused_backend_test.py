#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class FocusedCelestiaAPITester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
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

    def test_backend_server_status(self):
        """Test if backend server is running properly"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/tarot/spreads", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Server Status", True, f"Server responding on {self.base_url}")
                return True
            else:
                self.log_test("Backend Server Status", False, f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Server Status", False, f"Server connection failed: {str(e)}")
            return False

    def test_create_admin_user(self):
        """Test creating admin user and check if readers exist"""
        success, response = self.make_request('POST', 'admin/create-admin', None, 200)
        
        if success:
            if response.get('created'):
                self.log_test("Admin User Creation", True, f"Admin created: {response.get('admin_email')}")
            else:
                self.log_test("Admin User Check", True, f"Admin already exists: {response.get('admin_email')}")
            return True
        else:
            self.log_test("Admin User Creation", False, "Failed to create/check admin user", response)
            return False

    def register_test_user(self):
        """Register a test user for session testing"""
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
            self.log_test("Test User Registration", True, f"Registered user: {test_email}")
            return True
        else:
            self.log_test("Test User Registration", False, "Failed to register user", response)
            return False

    def test_no_reader_available_error(self):
        """Test session creation to reproduce 'no reader available' error"""
        if not self.token:
            if not self.register_test_user():
                return False

        # Try to create a session - should work if admin/reader exists
        start_time = datetime.now() + timedelta(days=1, hours=12)  # Tomorrow at noon
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing reader availability"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            self.log_test("Session Creation - Reader Available", True, 
                         f"Session created successfully: {response['id']}")
            return True
        elif not success and "No reader available" in str(response):
            self.log_test("Session Creation - No Reader Error", False, 
                         "Confirmed 'No reader available' error exists", response)
            return False
        else:
            self.log_test("Session Creation - Other Error", False, 
                         "Session creation failed for different reason", response)
            return False

    def test_session_duration_calculation(self):
        """Test session duration calculation fix"""
        if not hasattr(self, 'session_id'):
            self.log_test("Session Duration Test", False, "No session available for duration test")
            return False

        # Get the session details
        success, response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
        
        if success and 'start_at' in response and 'end_at' in response:
            start_time = datetime.fromisoformat(response['start_at'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(response['end_at'].replace('Z', '+00:00'))
            
            # Calculate expected duration in minutes
            duration_delta = end_time - start_time
            expected_minutes = int(duration_delta.total_seconds() / 60)
            
            # Check if the session shows correct duration (60 minutes, not 6 hours)
            if expected_minutes == 60:
                self.log_test("Session Duration Calculation", True, 
                             f"Duration correctly calculated as {expected_minutes} minutes")
                return True
            else:
                self.log_test("Session Duration Calculation", False, 
                             f"Duration calculation issue: {expected_minutes} minutes")
                return False
        else:
            self.log_test("Session Duration Calculation", False, 
                         "Failed to retrieve session for duration test", response)
            return False

    def test_business_hours_validation(self):
        """Test business hours validation (10 AM-6 PM, Monday-Friday)"""
        if not self.token:
            if not self.register_test_user():
                return False

        # Test 1: Try to book before 10 AM (should fail)
        early_start = datetime.now() + timedelta(days=1)
        early_start = early_start.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
        early_end = early_start + timedelta(hours=1)
        
        early_session_data = {
            "service_type": "tarot-reading",
            "start_at": early_start.isoformat(),
            "end_at": early_end.isoformat(),
            "client_message": "Testing early hours"
        }
        
        success, response = self.make_request('POST', 'sessions', early_session_data, 200)
        
        if not success and "10:00 AM" in str(response):
            self.log_test("Business Hours - Before 10 AM", True, 
                         "Correctly rejected booking before 10 AM")
        else:
            self.log_test("Business Hours - Before 10 AM", False, 
                         "Failed to reject early booking", response)

        # Test 2: Try to book after 6 PM (should fail)
        late_start = datetime.now() + timedelta(days=1)
        late_start = late_start.replace(hour=17, minute=30, second=0, microsecond=0)  # 5:30 PM
        late_end = late_start + timedelta(hours=1)  # Ends at 6:30 PM
        
        late_session_data = {
            "service_type": "tarot-reading",
            "start_at": late_start.isoformat(),
            "end_at": late_end.isoformat(),
            "client_message": "Testing late hours"
        }
        
        success, response = self.make_request('POST', 'sessions', late_session_data, 200)
        
        if not success and "6:00 PM" in str(response):
            self.log_test("Business Hours - After 6 PM", True, 
                         "Correctly rejected booking after 6 PM")
        else:
            self.log_test("Business Hours - After 6 PM", False, 
                         "Failed to reject late booking", response)

        # Test 3: Try to book on weekend (should fail)
        # Find next Saturday
        next_saturday = datetime.now() + timedelta(days=1)
        while next_saturday.weekday() != 5:  # Saturday = 5
            next_saturday += timedelta(days=1)
        
        weekend_start = next_saturday.replace(hour=12, minute=0, second=0, microsecond=0)
        weekend_end = weekend_start + timedelta(hours=1)
        
        weekend_session_data = {
            "service_type": "tarot-reading",
            "start_at": weekend_start.isoformat(),
            "end_at": weekend_end.isoformat(),
            "client_message": "Testing weekend booking"
        }
        
        success, response = self.make_request('POST', 'sessions', weekend_session_data, 200)
        
        if not success and "Monday through Friday" in str(response):
            self.log_test("Business Hours - Weekend", True, 
                         "Correctly rejected weekend booking")
            return True
        else:
            self.log_test("Business Hours - Weekend", False, 
                         "Failed to reject weekend booking", response)
            return False

    def test_valid_business_hours_booking(self):
        """Test that valid business hours booking works"""
        if not self.token:
            if not self.register_test_user():
                return False

        # Find next weekday
        next_weekday = datetime.now() + timedelta(days=1)
        while next_weekday.weekday() > 4:  # Monday=0, Friday=4
            next_weekday += timedelta(days=1)
        
        # Book at 2 PM (valid time)
        valid_start = next_weekday.replace(hour=14, minute=0, second=0, microsecond=0)
        valid_end = valid_start + timedelta(hours=1)
        
        valid_session_data = {
            "service_type": "tarot-reading",
            "start_at": valid_start.isoformat(),
            "end_at": valid_end.isoformat(),
            "client_message": "Testing valid business hours"
        }
        
        success, response = self.make_request('POST', 'sessions', valid_session_data, 200)
        
        if success and 'id' in response:
            self.valid_session_id = response['id']
            self.log_test("Business Hours - Valid Time", True, 
                         f"Successfully booked during business hours: {response['id']}")
            return True
        else:
            self.log_test("Business Hours - Valid Time", False, 
                         "Failed to book during valid business hours", response)
            return False

    def check_database_users(self):
        """Check if there are existing users with admin or reader roles"""
        # Try to get admin dashboard stats (only works if admin exists and we're authenticated as admin)
        # First, let's try to create admin to see if one exists
        success, response = self.make_request('POST', 'admin/create-admin', None, 200)
        
        if success:
            admin_exists = not response.get('created', True)  # If created=False, admin exists
            admin_email = response.get('admin_email', 'Unknown')
            
            if admin_exists:
                self.log_test("Database Users - Admin Check", True, 
                             f"Admin user exists: {admin_email}")
            else:
                self.log_test("Database Users - Admin Check", True, 
                             f"Admin user created: {admin_email}")
            
            # Try to register a reader to see if one exists
            reader_data = {
                "name": "Test Reader",
                "email": f"reader_test_{datetime.now().strftime('%H%M%S')}@celestia.com",
                "password": "ReaderPass123!",
                "role": "reader"
            }
            
            success2, response2 = self.make_request('POST', 'auth/register-reader', reader_data, 200)
            
            if not success2 and "already exists" in str(response2):
                self.log_test("Database Users - Reader Check", True, 
                             "Reader user already exists in database")
            elif success2:
                self.log_test("Database Users - Reader Check", True, 
                             "Reader user created successfully")
            else:
                self.log_test("Database Users - Reader Check", False, 
                             "Failed to check/create reader", response2)
            
            return True
        else:
            self.log_test("Database Users - Admin Check", False, 
                         "Failed to check admin user", response)
            return False

    def run_focused_tests(self):
        """Run focused tests based on the review request"""
        print("🔍 Starting Focused Backend Tests for Reported Issues...")
        print("=" * 60)
        
        # 1. Check if backend server is running properly
        print("\n🖥️  Backend Server Status:")
        self.test_backend_server_status()
        
        # 2. Check if there are existing users with admin or reader roles
        print("\n👥 Database Users Check:")
        self.check_database_users()
        
        # 3. Test session creation to reproduce "no reader available" error
        print("\n📅 Session Creation - Reader Availability:")
        self.test_no_reader_available_error()
        
        # 4. Test session duration calculation fix
        print("\n⏱️  Session Duration Calculation:")
        self.test_session_duration_calculation()
        
        # 5. Test business hours validation
        print("\n🕐 Business Hours Validation:")
        self.test_business_hours_validation()
        self.test_valid_business_hours_booking()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Focused Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Print specific findings
        print("\n🔍 SPECIFIC FINDINGS:")
        for result in self.test_results:
            if not result['success']:
                print(f"   ❌ {result['test_name']}: {result['details']}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All focused tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

def main():
    tester = FocusedCelestiaAPITester()
    success = tester.run_focused_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())