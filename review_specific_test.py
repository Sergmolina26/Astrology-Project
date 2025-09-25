#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ReviewSpecificTester:
    def __init__(self, base_url="https://astro-booking-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.issues_found = []

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
        if not success:
            self.issues_found.append(f"{name}: {details}")

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

    def setup_test_user(self):
        """Setup test user for testing"""
        test_email = f"review_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Review Test User",
            "email": test_email,
            "password": "TestPass123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', register_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"✅ Test user registered: {test_email}")
            return True
        else:
            print(f"❌ Failed to register test user: {response}")
            return False

    def test_1_backend_server_running(self):
        """1. Check if backend server is running properly"""
        print("\n🖥️  TEST 1: Backend Server Status")
        try:
            response = requests.get(f"{self.base_url}/api/tarot/spreads", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Server Running", True, f"Server responding correctly on {self.base_url}")
                return True
            else:
                self.log_test("Backend Server Running", False, f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Server Running", False, f"Server connection failed: {str(e)}")
            return False

    def test_2_existing_users_database(self):
        """2. Check if there are existing users with admin or reader roles"""
        print("\n👥 TEST 2: Database Users Check")
        
        # Check admin user
        success, response = self.make_request('POST', 'admin/create-admin', None, 200)
        
        if success:
            admin_exists = not response.get('created', True)
            admin_email = response.get('admin_email', 'Unknown')
            
            if admin_exists:
                self.log_test("Admin User Exists", True, f"Admin user found: {admin_email}")
            else:
                self.log_test("Admin User Created", True, f"Admin user created: {admin_email}")
            
            # Check reader by trying to register one
            reader_data = {
                "name": "Test Reader Check",
                "email": f"reader_check_{datetime.now().strftime('%H%M%S')}@celestia.com",
                "password": "ReaderPass123!",
                "role": "reader"
            }
            
            success2, response2 = self.make_request('POST', 'auth/register-reader', reader_data, 200)
            
            if not success2 and "already exists" in str(response2):
                self.log_test("Reader User Exists", True, "Reader user already exists in database")
                return True
            elif success2:
                self.log_test("Reader User Available", True, "Reader functionality working - new reader can be created")
                return True
            else:
                self.log_test("Reader User Check", False, f"Reader check failed: {response2}")
                return False
        else:
            self.log_test("Admin User Check", False, f"Admin check failed: {response}")
            return False

    def test_3_no_reader_available_error(self):
        """3. Test session creation to reproduce 'no reader available' error"""
        print("\n📅 TEST 3: Session Creation - Reader Availability")
        
        if not self.token:
            if not self.setup_test_user():
                return False

        # Create session during valid business hours
        next_weekday = datetime.now() + timedelta(days=1)
        while next_weekday.weekday() > 4:  # Find next weekday
            next_weekday += timedelta(days=1)
        
        start_time = next_weekday.replace(hour=14, minute=0, second=0, microsecond=0)  # 2 PM
        end_time = start_time + timedelta(hours=1)  # 3 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing reader availability"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            self.log_test("Session Creation Success", True, 
                         f"Session created successfully - no 'reader available' error: {response['id']}")
            return True
        elif not success and "No reader available" in str(response):
            self.log_test("No Reader Available Error", False, 
                         "CONFIRMED: 'No reader available' error exists", response)
            return False
        else:
            self.log_test("Session Creation Other Error", False, 
                         f"Session creation failed for different reason: {response}")
            return False

    def test_4_session_duration_calculation(self):
        """4. Test session duration calculation fix"""
        print("\n⏱️  TEST 4: Session Duration Calculation Fix")
        
        if not hasattr(self, 'session_id'):
            # Create a session for testing
            if not self.token:
                if not self.setup_test_user():
                    return False
            
            next_weekday = datetime.now() + timedelta(days=1)
            while next_weekday.weekday() > 4:
                next_weekday += timedelta(days=1)
            
            start_time = next_weekday.replace(hour=15, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)  # Exactly 60 minutes
            
            session_data = {
                "service_type": "tarot-reading",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": "Testing duration calculation"
            }
            
            success, response = self.make_request('POST', 'sessions', session_data, 200)
            if not success:
                self.log_test("Duration Test Setup", False, "Could not create session for duration test")
                return False
            self.session_id = response['id']

        # Get session details and check duration
        success, response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
        
        if success and 'start_at' in response and 'end_at' in response:
            start_time = datetime.fromisoformat(response['start_at'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(response['end_at'].replace('Z', '+00:00'))
            
            duration_delta = end_time - start_time
            duration_minutes = int(duration_delta.total_seconds() / 60)
            duration_hours = duration_delta.total_seconds() / 3600
            
            # Check if it's showing 60 minutes (correct) vs 6 hours (bug)
            if duration_minutes == 60 and duration_hours == 1.0:
                self.log_test("Session Duration Fix", True, 
                             f"Duration correctly calculated: {duration_minutes} minutes (1 hour)")
                return True
            elif duration_hours == 6.0:
                self.log_test("Session Duration Bug", False, 
                             f"BUG CONFIRMED: Duration showing as {duration_hours} hours instead of 1 hour")
                return False
            else:
                self.log_test("Session Duration Unexpected", False, 
                             f"Unexpected duration: {duration_minutes} minutes ({duration_hours} hours)")
                return False
        else:
            self.log_test("Session Duration Test", False, 
                         "Could not retrieve session for duration test")
            return False

    def test_5_business_hours_validation(self):
        """5. Check business hours validation (10 AM-6 PM, Monday-Friday)"""
        print("\n🕐 TEST 5: Business Hours Validation")
        
        if not self.token:
            if not self.setup_test_user():
                return False

        all_passed = True

        # Test A: Before 10 AM (should fail)
        next_weekday = datetime.now() + timedelta(days=1)
        while next_weekday.weekday() > 4:
            next_weekday += timedelta(days=1)
        
        early_start = next_weekday.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
        early_end = early_start + timedelta(hours=1)
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": early_start.isoformat(),
            "end_at": early_end.isoformat(),
            "client_message": "Testing before 10 AM"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if not success and "10:00 AM" in str(response):
            self.log_test("Business Hours - Before 10 AM", True, "Correctly rejected booking before 10 AM")
        else:
            self.log_test("Business Hours - Before 10 AM", False, "Failed to reject early booking")
            all_passed = False

        # Test B: After 6 PM - CRITICAL TEST for the reported bug
        late_start = next_weekday.replace(hour=17, minute=30, second=0, microsecond=0)  # 5:30 PM
        late_end = late_start + timedelta(hours=1)  # 6:30 PM (should be rejected)
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": late_start.isoformat(),
            "end_at": late_end.isoformat(),
            "client_message": "Testing after 6 PM"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if not success and "6:00 PM" in str(response):
            self.log_test("Business Hours - After 6 PM", True, "Correctly rejected booking ending after 6 PM")
        else:
            self.log_test("Business Hours - After 6 PM BUG", False, 
                         "BUG CONFIRMED: System allows bookings ending after 6 PM")
            all_passed = False

        # Test C: Weekend (should fail)
        next_saturday = datetime.now() + timedelta(days=1)
        while next_saturday.weekday() != 5:  # Saturday = 5
            next_saturday += timedelta(days=1)
        
        weekend_start = next_saturday.replace(hour=12, minute=0, second=0, microsecond=0)
        weekend_end = weekend_start + timedelta(hours=1)
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": weekend_start.isoformat(),
            "end_at": weekend_end.isoformat(),
            "client_message": "Testing weekend"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if not success and "Monday through Friday" in str(response):
            self.log_test("Business Hours - Weekend", True, "Correctly rejected weekend booking")
        else:
            self.log_test("Business Hours - Weekend", False, "Failed to reject weekend booking")
            all_passed = False

        # Test D: Valid time (should succeed)
        valid_start = next_weekday.replace(hour=14, minute=0, second=0, microsecond=0)  # 2 PM
        valid_end = valid_start + timedelta(hours=1)  # 3 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": valid_start.isoformat(),
            "end_at": valid_end.isoformat(),
            "client_message": "Testing valid business hours"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.log_test("Business Hours - Valid Time", True, "Successfully booked during valid hours")
        else:
            self.log_test("Business Hours - Valid Time", False, "Failed to book during valid hours")
            all_passed = False

        return all_passed

    def run_review_tests(self):
        """Run all tests based on the review request"""
        print("🔍 REVIEW-SPECIFIC BACKEND TESTING")
        print("Testing reported issues:")
        print("1. Backend server running properly")
        print("2. Existing users in database (admin/reader roles)")
        print("3. 'No reader available' error reproduction")
        print("4. Session duration calculation fix verification")
        print("5. Business hours validation (10 AM-6 PM, Mon-Fri)")
        print("=" * 70)
        
        # Run all tests
        test1_result = self.test_1_backend_server_running()
        test2_result = self.test_2_existing_users_database()
        test3_result = self.test_3_no_reader_available_error()
        test4_result = self.test_4_session_duration_calculation()
        test5_result = self.test_5_business_hours_validation()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 REVIEW TEST RESULTS: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 CRITICAL FINDINGS:")
        if self.issues_found:
            for issue in self.issues_found:
                print(f"   ❌ {issue}")
        else:
            print("   ✅ No critical issues found")
        
        print("\n📋 REVIEW SUMMARY:")
        print(f"   1. Backend Server: {'✅ RUNNING' if test1_result else '❌ ISSUES'}")
        print(f"   2. Database Users: {'✅ FOUND' if test2_result else '❌ MISSING'}")
        print(f"   3. Reader Available: {'✅ WORKING' if test3_result else '❌ ERROR EXISTS'}")
        print(f"   4. Duration Calc: {'✅ FIXED' if test4_result else '❌ BUG EXISTS'}")
        print(f"   5. Business Hours: {'✅ WORKING' if test5_result else '❌ BUG EXISTS'}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ReviewSpecificTester()
    success = tester.run_review_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())