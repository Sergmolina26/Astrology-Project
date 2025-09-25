#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class BusinessHoursValidationTester:
    def __init__(self, base_url="https://astro-booking-3.preview.emergentagent.com"):
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

    def setup_authentication(self):
        """Setup authentication for testing"""
        test_email = f"biz_hours_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Business Hours Test User",
            "email": test_email,
            "password": "TestPass123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', register_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log_test("Authentication Setup", True, f"Registered user: {test_email}")
            return True
        else:
            self.log_test("Authentication Setup", False, "Failed to register user", response)
            return False

    def get_next_weekday(self, days_ahead=1):
        """Get next weekday (Monday-Friday) for testing"""
        date = datetime.now() + timedelta(days=days_ahead)
        while date.weekday() > 4:  # Skip weekends (Saturday=5, Sunday=6)
            date += timedelta(days=1)
        return date

    def test_session_ending_after_6pm(self):
        """Test that sessions ending after 6:00 PM are rejected (5:30 PM - 6:30 PM should fail)"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 5:30 PM to 6:30 PM (should fail - ends after 6 PM)
        start_time = next_weekday.replace(hour=17, minute=30, second=0, microsecond=0)  # 5:30 PM
        end_time = start_time + timedelta(hours=1)  # 6:30 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 5:30 PM - 6:30 PM booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 400)  # Expect 400 error
        
        # Check if the request was properly rejected (400 status) and contains the right error message
        if not success and response.get('status_code') == 400 and "6:00 PM" in str(response):
            self.log_test("Session Ending After 6 PM (5:30-6:30)", True, 
                         f"Correctly rejected session ending at 6:30 PM: {response.get('detail', 'Unknown error')}")
            return True
        else:
            self.log_test("Session Ending After 6 PM (5:30-6:30)", False, 
                         "Failed to reject session ending after 6 PM", response)
            return False

    def test_session_ending_exactly_at_6pm(self):
        """Test that sessions ending exactly at 6:00 PM are rejected"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 5:00 PM to 6:00 PM (should fail - ends exactly at 6 PM)
        start_time = next_weekday.replace(hour=17, minute=0, second=0, microsecond=0)  # 5:00 PM
        end_time = next_weekday.replace(hour=18, minute=0, second=0, microsecond=0)  # 6:00 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 5:00 PM - 6:00 PM booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 400)  # Expect 400 error
        
        # Check if the request was properly rejected (400 status) and contains the right error message
        if not success and response.get('status_code') == 400 and "6:00 PM" in str(response):
            self.log_test("Session Ending Exactly at 6 PM (5:00-6:00)", True, 
                         f"Correctly rejected session ending exactly at 6:00 PM: {response.get('detail', 'Unknown error')}")
            return True
        else:
            self.log_test("Session Ending Exactly at 6 PM (5:00-6:00)", False, 
                         "Failed to reject session ending exactly at 6 PM", response)
            return False

    def test_valid_session_before_6pm(self):
        """Test that valid sessions ending before 6:00 PM still work (4:00 PM - 5:00 PM should succeed)"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 4:00 PM to 5:00 PM (should succeed - ends before 6 PM)
        start_time = next_weekday.replace(hour=16, minute=0, second=0, microsecond=0)  # 4:00 PM
        end_time = next_weekday.replace(hour=17, minute=0, second=0, microsecond=0)  # 5:00 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 4:00 PM - 5:00 PM booking (should succeed)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)  # Expect success
        
        if success and 'id' in response:
            self.log_test("Valid Session Before 6 PM (4:00-5:00)", True, 
                         f"Successfully created session ending at 5:00 PM: {response['id']}")
            return True
        else:
            self.log_test("Valid Session Before 6 PM (4:00-5:00)", False, 
                         "Failed to create valid session ending before 6 PM", response)
            return False

    def test_session_starting_before_10am(self):
        """Test that sessions starting before 10:00 AM are rejected"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 9:00 AM to 10:00 AM (should fail - starts before 10 AM)
        start_time = next_weekday.replace(hour=9, minute=0, second=0, microsecond=0)  # 9:00 AM
        end_time = next_weekday.replace(hour=10, minute=0, second=0, microsecond=0)  # 10:00 AM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 9:00 AM - 10:00 AM booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 400)  # Expect 400 error
        
        # Check if the request was properly rejected (400 status) and contains the right error message
        if not success and response.get('status_code') == 400 and "10:00 AM" in str(response):
            self.log_test("Session Starting Before 10 AM", True, 
                         f"Correctly rejected session starting at 9:00 AM: {response.get('detail', 'Unknown error')}")
            return True
        else:
            self.log_test("Session Starting Before 10 AM", False, 
                         "Failed to reject session starting before 10 AM", response)
            return False

    def test_weekend_session_rejection(self):
        """Test that weekend sessions are rejected"""
        # Get next Saturday
        date = datetime.now() + timedelta(days=1)
        while date.weekday() != 5:  # Saturday = 5
            date += timedelta(days=1)
        
        # Create session on Saturday (should fail)
        start_time = date.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM Saturday
        end_time = start_time + timedelta(hours=1)  # 3:00 PM Saturday
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing Saturday booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 400)  # Expect 400 error
        
        # Check if the request was properly rejected (400 status) and contains the right error message
        if not success and response.get('status_code') == 400 and ("Monday through Friday" in str(response) or "weekday" in str(response)):
            self.log_test("Weekend Session Rejection", True, 
                         f"Correctly rejected Saturday session: {response.get('detail', 'Unknown error')}")
            return True
        else:
            self.log_test("Weekend Session Rejection", False, 
                         "Failed to reject weekend session", response)
            return False

    def test_valid_business_hours_session(self):
        """Test that sessions within valid business hours work correctly"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 2:00 PM to 3:00 PM on weekday (should succeed)
        start_time = next_weekday.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        end_time = next_weekday.replace(hour=15, minute=0, second=0, microsecond=0)  # 3:00 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing valid business hours session"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)  # Expect success
        
        if success and 'id' in response:
            self.log_test("Valid Business Hours Session", True, 
                         f"Successfully created session within business hours: {response['id']}")
            return True
        else:
            self.log_test("Valid Business Hours Session", False, 
                         "Failed to create session within valid business hours", response)
            return False

    def test_edge_case_5_59_pm_end(self):
        """Test edge case: session ending at 5:59 PM (should succeed)"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 4:59 PM to 5:59 PM (should succeed - ends before 6 PM)
        start_time = next_weekday.replace(hour=16, minute=59, second=0, microsecond=0)  # 4:59 PM
        end_time = next_weekday.replace(hour=17, minute=59, second=0, microsecond=0)  # 5:59 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 4:59 PM - 5:59 PM booking (edge case)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)  # Expect success
        
        if success and 'id' in response:
            self.log_test("Edge Case Session Ending at 5:59 PM", True, 
                         f"Successfully created session ending at 5:59 PM: {response['id']}")
            return True
        else:
            self.log_test("Edge Case Session Ending at 5:59 PM", False, 
                         "Failed to create session ending at 5:59 PM", response)
            return False

    def test_edge_case_6_01_pm_end(self):
        """Test edge case: session ending at 6:01 PM (should fail)"""
        next_weekday = self.get_next_weekday()
        
        # Create session from 5:01 PM to 6:01 PM (should fail - ends after 6 PM)
        start_time = next_weekday.replace(hour=17, minute=1, second=0, microsecond=0)  # 5:01 PM
        end_time = next_weekday.replace(hour=18, minute=1, second=0, microsecond=0)  # 6:01 PM
        
        session_data = {
            "service_type": "tarot-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 5:01 PM - 6:01 PM booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 400)  # Expect 400 error
        
        # Check if the request was properly rejected (400 status) and contains the right error message
        if not success and response.get('status_code') == 400 and "6:00 PM" in str(response):
            self.log_test("Edge Case Session Ending at 6:01 PM", True, 
                         f"Correctly rejected session ending at 6:01 PM: {response.get('detail', 'Unknown error')}")
            return True
        else:
            self.log_test("Edge Case Session Ending at 6:01 PM", False, 
                         "Failed to reject session ending at 6:01 PM", response)
            return False

    def run_business_hours_tests(self):
        """Run all business hours validation tests"""
        print("🕐 Starting Business Hours Validation Tests...")
        print("=" * 60)
        print("Testing the fix: end_datetime.hour >= 18 (was > 18)")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        print("\n🔍 SPECIFIC BUSINESS HOURS VALIDATION TESTS:")
        
        # Test the specific scenarios mentioned in the review request
        print("\n1. Testing sessions ending after 6:00 PM (should be rejected):")
        self.test_session_ending_after_6pm()
        
        print("\n2. Testing sessions ending exactly at 6:00 PM (should be rejected):")
        self.test_session_ending_exactly_at_6pm()
        
        print("\n3. Testing valid sessions ending before 6:00 PM (should work):")
        self.test_valid_session_before_6pm()
        
        print("\n4. Testing other business hours constraints:")
        self.test_session_starting_before_10am()
        self.test_weekend_session_rejection()
        self.test_valid_business_hours_session()
        
        print("\n5. Testing edge cases:")
        self.test_edge_case_5_59_pm_end()
        self.test_edge_case_6_01_pm_end()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Business Hours Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All business hours validation tests passed!")
            print("✅ The fix (end_datetime.hour >= 18) is working correctly!")
            return True
        else:
            print("⚠️  Some business hours tests failed - check details above")
            return False

    def save_results(self, filename: str = "/app/business_hours_test_results.json"):
        """Save test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_focus": "Business Hours Validation Fix",
            "fix_description": "Changed condition from end_datetime.hour > 18 to end_datetime.hour >= 18",
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_details": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Test results saved to: {filename}")

def main():
    tester = BusinessHoursValidationTester()
    success = tester.run_business_hours_tests()
    tester.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())