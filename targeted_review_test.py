#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class TargetedReviewTester:
    """
    Targeted testing for specific review requirements with careful date selection
    """
    
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

    def get_next_weekday(self, days_ahead=1):
        """Get next weekday (Monday-Friday)"""
        current = datetime.now()
        for i in range(days_ahead, days_ahead + 10):  # Look up to 10 days ahead
            future_date = current + timedelta(days=i)
            if future_date.weekday() < 5:  # Monday=0, Friday=4
                return future_date
        return current + timedelta(days=days_ahead)  # Fallback

    def setup_authentication(self):
        """Setup authentication for testing"""
        test_email = f"targeted_review_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Targeted Review Test User",
            "email": test_email,
            "password": "TargetedTest123!",
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

    def test_time_display_10am(self):
        """Test that 10:00 AM sessions display correctly"""
        print("\n🕐 TEST 1: Time Display Verification (10:00 AM)")
        
        # Get next weekday
        weekday = self.get_next_weekday(30)  # Use far future to avoid conflicts
        start_time = weekday.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=45)
        
        print(f"    Testing with date: {weekday.strftime('%A, %Y-%m-%d')} (weekday: {weekday.weekday()})")
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 10:00 AM time display"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            stored_start_time = response.get('start_at')
            
            # Parse the stored time
            try:
                stored_start = datetime.fromisoformat(stored_start_time.replace('Z', '+00:00'))
                
                if stored_start.hour == 10:
                    self.log_test("Time Display - 10:00 AM Storage", True, 
                                 f"10:00 AM correctly stored as hour {stored_start.hour}")
                    
                    # Retrieve session to verify persistence
                    success2, response2 = self.make_request('GET', f'sessions/{session_id}', None, 200)
                    
                    if success2:
                        retrieved_start = response2.get('start_at')
                        retrieved_start_dt = datetime.fromisoformat(retrieved_start.replace('Z', '+00:00'))
                        
                        if retrieved_start_dt.hour == 10:
                            self.log_test("Time Display - 10:00 AM Retrieval", True, 
                                         f"Retrieved session maintains 10:00 AM (hour {retrieved_start_dt.hour})")
                            return True
                        else:
                            self.log_test("Time Display - 10:00 AM Retrieval", False, 
                                         f"Retrieved session shows hour {retrieved_start_dt.hour} instead of 10")
                            return False
                    else:
                        self.log_test("Time Display - Session Retrieval", False, 
                                     "Failed to retrieve session", response2)
                        return False
                else:
                    self.log_test("Time Display - 10:00 AM Storage", False, 
                                 f"10:00 AM incorrectly stored as hour {stored_start.hour} (should be 10)")
                    return False
                    
            except Exception as e:
                self.log_test("Time Display - Time Parsing", False, 
                             f"Failed to parse stored times: {str(e)}")
                return False
        else:
            self.log_test("Time Display - Session Creation", False, 
                         "Failed to create 10:00 AM session", response)
            return False

    def test_business_hours_validation(self):
        """Test business hours validation"""
        print("\n🕘 TEST 2: Business Hours Validation")
        
        # Get next weekday for valid tests
        weekday = self.get_next_weekday(35)
        print(f"    Testing with date: {weekday.strftime('%A, %Y-%m-%d')} (weekday: {weekday.weekday()})")
        
        # Test 2a: Before 10 AM (should fail)
        early_start = weekday.replace(hour=9, minute=0, second=0, microsecond=0)
        early_end = early_start + timedelta(minutes=45)
        
        early_session = {
            "service_type": "general-purpose-reading",
            "start_at": early_start.isoformat(),
            "end_at": early_end.isoformat(),
            "client_message": "Testing 9:00 AM booking (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', early_session, 200)
        
        if not success and ("10:00 AM" in str(response) or "start at 10" in str(response)):
            self.log_test("Business Hours - Before 10 AM Rejection", True, 
                         "Correctly rejected 9:00 AM booking")
        else:
            self.log_test("Business Hours - Before 10 AM Rejection", False, 
                         "Failed to reject 9:00 AM booking", response)
        
        # Test 2b: Session ending after 6:00 PM (should fail)
        late_start = weekday.replace(hour=17, minute=30, second=0, microsecond=0)  # 5:30 PM
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
        
        # Test 2c: Weekend booking (should fail)
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
            return True
        else:
            self.log_test("Business Hours - Weekend Rejection", False, 
                         "Failed to reject Saturday booking", response)
            return False

    def test_session_end_time_validation(self):
        """Test sessions cannot end after 6:00 PM"""
        print("\n🕕 TEST 3: Session End Time Validation")
        
        # Get next weekday
        weekday = self.get_next_weekday(40)
        print(f"    Testing with date: {weekday.strftime('%A, %Y-%m-%d')} (weekday: {weekday.weekday()})")
        
        # Test 3a: Session ending exactly at 6:00 PM (should succeed)
        perfect_start = weekday.replace(hour=17, minute=15, second=0, microsecond=0)  # 5:15 PM
        perfect_end = perfect_start + timedelta(minutes=45)  # Ends at 6:00 PM
        
        perfect_session = {
            "service_type": "general-purpose-reading",
            "start_at": perfect_start.isoformat(),
            "end_at": perfect_end.isoformat(),
            "client_message": "Testing session ending exactly at 6:00 PM (should succeed)"
        }
        
        success, response = self.make_request('POST', 'sessions', perfect_session, 200)
        
        if success and 'id' in response:
            self.log_test("End Time Validation - Exactly 6:00 PM Acceptance", True, 
                         "Correctly accepted session ending exactly at 6:00 PM")
            
            # Verify the end time
            stored_end_time = response.get('end_at')
            try:
                stored_end = datetime.fromisoformat(stored_end_time.replace('Z', '+00:00'))
                if stored_end.hour == 18 and stored_end.minute == 0:
                    self.log_test("End Time Validation - 6:00 PM Time Verification", True, 
                                 f"Session correctly ends at {stored_end.hour}:00 (6:00 PM)")
                else:
                    self.log_test("End Time Validation - 6:00 PM Time Verification", False, 
                                 f"Session ends at {stored_end.hour}:{stored_end.minute:02d} instead of 18:00")
            except Exception as e:
                self.log_test("End Time Validation - Time Parsing", False, 
                             f"Failed to parse end time: {str(e)}")
        else:
            self.log_test("End Time Validation - Exactly 6:00 PM Acceptance", False, 
                         "Failed to accept session ending exactly at 6:00 PM", response)
        
        # Test 3b: Session ending after 6:00 PM (should fail)
        late_start = weekday.replace(hour=17, minute=30, second=0, microsecond=0)  # 5:30 PM
        late_end = late_start + timedelta(minutes=60)  # Ends at 6:30 PM
        
        late_session = {
            "service_type": "astrological-tarot-session",  # 60 minutes
            "start_at": late_start.isoformat(),
            "end_at": late_end.isoformat(),
            "client_message": "Testing session ending at 6:30 PM (should fail)"
        }
        
        success, response = self.make_request('POST', 'sessions', late_session, 200)
        
        if not success and ("6:00 PM" in str(response) or "conclude by" in str(response)):
            self.log_test("End Time Validation - After 6:00 PM Rejection", True, 
                         "Correctly rejected session ending at 6:30 PM")
            return True
        else:
            self.log_test("End Time Validation - After 6:00 PM Rejection", False, 
                         "Failed to reject session ending at 6:30 PM", response)
            return False

    def test_double_booking_prevention(self):
        """Test double booking prevention"""
        print("\n📅 TEST 4: Double Booking Prevention")
        
        # Get next weekday
        weekday = self.get_next_weekday(45)
        start_time = weekday.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        end_time = start_time + timedelta(minutes=60)  # 3:00 PM
        
        print(f"    Testing with date: {weekday.strftime('%A, %Y-%m-%d')} (weekday: {weekday.weekday()})")
        
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
                    return True
                else:
                    self.log_test("Double Booking - Overlap Prevention", False, 
                                 "Failed to prevent overlapping session", response3)
                    return False
            else:
                self.log_test("Double Booking - First Session Payment", False, 
                             "Failed to complete payment for first session", response2)
                return False
        else:
            self.log_test("Double Booking - First Session Creation", False, 
                         "Failed to create first session", response)
            return False

    def run_targeted_tests(self):
        """Run targeted review tests"""
        print("🎯 TARGETED REVIEW TESTING - Specific Requirements")
        print("=" * 70)
        print("Testing specific fixes for:")
        print("1. Time Display: 10:00 AM should show as '10:00 AM' not '3:00 PM'")
        print("2. Business Hours: Prevent bookings outside 10 AM-6 PM and weekends")
        print("3. Session End Time: Sessions cannot end after 6:00 PM")
        print("4. Double Booking: Calendar blocking prevents overlapping sessions")
        print("=" * 70)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        # Run the four main tests
        test1_result = self.test_time_display_10am()
        test2_result = self.test_business_hours_validation()
        test3_result = self.test_session_end_time_validation()
        test4_result = self.test_double_booking_prevention()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Targeted Review Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 REVIEW REQUIREMENTS STATUS:")
        print(f"   🕐 Time Display Verification: {'✅ PASS' if test1_result else '❌ FAIL'}")
        print(f"   🕘 Business Hours Validation: {'✅ PASS' if test2_result else '❌ FAIL'}")
        print(f"   🕕 Session End Time Validation: {'✅ PASS' if test3_result else '❌ FAIL'}")
        print(f"   📅 Double Booking Prevention: {'✅ PASS' if test4_result else '❌ FAIL'}")
        
        all_tests_passed = test1_result and test2_result and test3_result and test4_result
        
        if all_tests_passed:
            print("\n🎉 ALL REVIEW REQUIREMENTS VERIFIED!")
            print("✅ Time display and booking validation fixes are working correctly")
            return True
        else:
            print("\n⚠️ SOME REVIEW REQUIREMENTS FAILED")
            print("❌ Issues found that need to be addressed")
            return False

def main():
    tester = TargetedReviewTester()
    success = tester.run_targeted_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open("/app/targeted_review_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: /app/targeted_review_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())