#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class SimpleReviewTester:
    """
    Simple focused testing for the review request requirements
    """
    
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

    def setup_authentication(self):
        """Setup authentication for testing"""
        test_email = f"simple_review_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Simple Review Test User",
            "email": test_email,
            "password": "SimpleTest123!",
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

    def test_business_hours_validation(self):
        """Test business hours validation - focus on 6 PM cutoff"""
        print("\n🕕 Testing Business Hours Validation")
        
        # Use a date far in the future to avoid conflicts
        future_date = datetime.now() + timedelta(days=30)
        
        # Test 1: Session ending after 6:00 PM (should fail)
        late_start = future_date.replace(hour=17, minute=30, second=0, microsecond=0)  # 5:30 PM
        late_end = late_start + timedelta(minutes=45)  # Ends at 6:15 PM
        
        late_session = {
            "service_type": "general-purpose-reading",
            "start_at": late_start.isoformat(),
            "end_at": late_end.isoformat(),
            "client_message": "Testing session ending at 6:15 PM (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', late_session, 200)
        
        if not success and ("6:00 PM" in str(response) or "conclude by" in str(response)):
            self.log_test("Business Hours - After 6 PM Rejection", True, 
                         "Correctly rejected session ending at 6:15 PM")
        else:
            self.log_test("Business Hours - After 6 PM Rejection", False, 
                         "Failed to reject session ending at 6:15 PM", response)
        
        # Test 2: Weekend booking (should fail)
        # Find next Saturday
        days_ahead = 5 - datetime.now().weekday()  # Saturday is 5
        if days_ahead <= 0:
            days_ahead += 7
        next_saturday = datetime.now() + timedelta(days=days_ahead)
        
        weekend_start = next_saturday.replace(hour=11, minute=0, second=0, microsecond=0)
        weekend_end = weekend_start + timedelta(minutes=45)
        
        weekend_session = {
            "service_type": "general-purpose-reading",
            "start_at": weekend_start.isoformat(),
            "end_at": weekend_end.isoformat(),
            "client_message": "Testing Saturday booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', weekend_session, 200)
        
        if not success and ("Monday through Friday" in str(response) or "weekday" in str(response).lower()):
            self.log_test("Business Hours - Weekend Rejection", True, 
                         "Correctly rejected Saturday booking")
        else:
            self.log_test("Business Hours - Weekend Rejection", False, 
                         "Failed to reject Saturday booking", response)
        
        # Test 3: Before 10 AM (should fail)
        early_start = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        early_end = early_start + timedelta(minutes=45)
        
        early_session = {
            "service_type": "general-purpose-reading",
            "start_at": early_start.isoformat(),
            "end_at": early_end.isoformat(),
            "client_message": "Testing 9:00 AM booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', early_session, 200)
        
        if not success and ("10:00 AM" in str(response) or "business hours" in str(response).lower()):
            self.log_test("Business Hours - Before 10 AM Rejection", True, 
                         "Correctly rejected 9:00 AM booking")
        else:
            self.log_test("Business Hours - Before 10 AM Rejection", False, 
                         "Failed to reject 9:00 AM booking", response)

    def test_time_display_storage(self):
        """Test that 10:00 AM sessions are stored and retrieved correctly"""
        print("\n🕐 Testing Time Display and Storage")
        
        # Use a date far in the future to avoid conflicts
        future_date = datetime.now() + timedelta(days=35)
        
        # Create a session for 10:00 AM
        start_time = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=45)
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 10:00 AM time storage"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            stored_start_time = response.get('start_at')
            
            # Parse the stored time
            try:
                stored_start = datetime.fromisoformat(stored_start_time.replace('Z', '+00:00'))
                
                # Check if the hour is preserved correctly (should be 10, not 15/3 PM)
                if stored_start.hour == 10:
                    self.log_test("Time Storage - 10:00 AM Preservation", True, 
                                 f"10:00 AM correctly stored as hour {stored_start.hour}")
                else:
                    self.log_test("Time Storage - 10:00 AM Preservation", False, 
                                 f"10:00 AM incorrectly stored as hour {stored_start.hour} (should be 10)")
                
                # Retrieve the session to verify persistence
                success2, response2 = self.make_request('GET', f'sessions/{session_id}', None, 200)
                
                if success2:
                    retrieved_start = response2.get('start_at')
                    retrieved_start_dt = datetime.fromisoformat(retrieved_start.replace('Z', '+00:00'))
                    
                    if retrieved_start_dt.hour == 10:
                        self.log_test("Time Retrieval - 10:00 AM Persistence", True, 
                                     f"Retrieved session maintains 10:00 AM (hour {retrieved_start_dt.hour})")
                    else:
                        self.log_test("Time Retrieval - 10:00 AM Persistence", False, 
                                     f"Retrieved session shows hour {retrieved_start_dt.hour} instead of 10")
                else:
                    self.log_test("Time Retrieval - Session Fetch", False, 
                                 "Failed to retrieve session", response2)
                    
            except Exception as e:
                self.log_test("Time Storage - Time Parsing", False, 
                             f"Failed to parse stored times: {str(e)}")
        else:
            self.log_test("Time Storage - Session Creation", False, 
                         "Failed to create 10:00 AM session", response)

    def test_services_api(self):
        """Test services API returns correct pricing"""
        print("\n💰 Testing Services API")
        
        success, response = self.make_request('GET', 'services', None, 200)
        
        if success and 'services' in response:
            services = response['services']
            
            # Check for expected services
            expected_services = {
                "general-purpose-reading": {"price": 65.0, "duration": 45},
                "astrological-tarot-session": {"price": 85.0, "duration": 60}
            }
            
            for service in services:
                service_id = service.get('id')
                if service_id in expected_services:
                    expected = expected_services[service_id]
                    actual_price = service.get('price')
                    actual_duration = service.get('duration')
                    
                    if actual_price == expected['price'] and actual_duration == expected['duration']:
                        self.log_test(f"Services API - {service_id}", True, 
                                     f"Correct pricing: ${actual_price}/{actual_duration}min")
                    else:
                        self.log_test(f"Services API - {service_id}", False, 
                                     f"Incorrect: expected ${expected['price']}/{expected['duration']}min, got ${actual_price}/{actual_duration}min")
            
            # Check that removed service is not present
            if any(s.get('id') == 'chart-tarot-combo' for s in services):
                self.log_test("Services API - Removed Service", False, 
                             "chart-tarot-combo should have been removed but is still present")
            else:
                self.log_test("Services API - Removed Service", True, 
                             "chart-tarot-combo correctly removed")
        else:
            self.log_test("Services API", False, "Failed to retrieve services", response)

    def test_double_booking_prevention(self):
        """Test double booking prevention with far future dates"""
        print("\n📅 Testing Double Booking Prevention")
        
        # Use a date very far in the future to avoid conflicts
        future_date = datetime.now() + timedelta(days=60)
        start_time = future_date.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        end_time = start_time + timedelta(minutes=60)  # 3:00 PM
        
        first_session = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "First session for double booking test"
        }
        
        success, response = self.make_request('POST', 'sessions', first_session, 200)
        
        if success and 'id' in response:
            first_session_id = response['id']
            self.log_test("Double Booking - First Session Creation", True, 
                         f"Created first session: {first_session_id}")
            
            # Complete payment to confirm the session
            success2, response2 = self.make_request('POST', f'sessions/{first_session_id}/payment/complete', None, 200)
            
            if success2:
                self.log_test("Double Booking - First Session Payment", True, 
                             "Completed payment for first session")
                
                # Try to create overlapping session (should fail)
                overlapping_start = start_time + timedelta(minutes=30)  # 2:30 PM
                overlapping_end = overlapping_start + timedelta(minutes=60)  # 3:30 PM
                
                overlapping_session = {
                    "service_type": "general-purpose-reading",
                    "start_at": overlapping_start.isoformat(),
                    "end_at": overlapping_end.isoformat(),
                    "client_message": "Overlapping session (should fail)"
                }
                
                success3, response3 = self.make_request('POST', 'sessions', overlapping_session, 200)
                
                if not success3 and ("not available" in str(response3) or "overlap" in str(response3).lower()):
                    self.log_test("Double Booking - Overlap Prevention", True, 
                                 "Successfully prevented overlapping session")
                else:
                    self.log_test("Double Booking - Overlap Prevention", False, 
                                 "Failed to prevent overlapping session", response3)
            else:
                self.log_test("Double Booking - First Session Payment", False, 
                             "Failed to complete payment for first session", response2)
        else:
            self.log_test("Double Booking - First Session Creation", False, 
                         "Failed to create first session", response)

    def run_simple_tests(self):
        """Run simplified review tests"""
        print("🎯 SIMPLE REVIEW TESTING - Core Requirements")
        print("=" * 60)
        print("Testing:")
        print("1. Business Hours Validation (10 AM-6 PM, weekdays only)")
        print("2. Time Display Storage (10:00 AM should remain 10:00 AM)")
        print("3. Services API (correct pricing and removed services)")
        print("4. Double Booking Prevention")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        # Run tests
        self.test_business_hours_validation()
        self.test_time_display_storage()
        self.test_services_api()
        self.test_double_booking_prevention()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Simple Review Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL REVIEW REQUIREMENTS VERIFIED!")
            return True
        else:
            print("\n⚠️ SOME REVIEW REQUIREMENTS FAILED")
            return False

def main():
    tester = SimpleReviewTester()
    success = tester.run_simple_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open("/app/simple_review_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: /app/simple_review_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())