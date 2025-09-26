#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class DoubleBookingTester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues_found = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def log_issue(self, issue_type: str, description: str, data: Any = None):
        """Log critical issue found"""
        issue = {
            "type": issue_type,
            "description": description,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.issues_found.append(issue)
        print(f"🚨 CRITICAL ISSUE - {issue_type}: {description}")

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
        """Get next weekday (Monday-Friday) for testing"""
        current = datetime.now()
        for i in range(days_ahead, days_ahead + 7):
            test_date = current + timedelta(days=i)
            if test_date.weekday() < 5:  # Monday=0, Friday=4
                return test_date
        return current + timedelta(days=days_ahead)

    def setup_test_user(self):
        """Setup test user for testing"""
        test_email = f"double_booking_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Double Booking Test User",
            "email": test_email,
            "password": "DoubleTest123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', register_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log_test("Test User Setup", True, f"Created test user: {test_email}")
            return True
        else:
            self.log_test("Test User Setup", False, "Failed to create test user")
            return False

    def test_double_booking_same_user(self):
        """Test if the same user can create overlapping sessions"""
        print("\n📅 DOUBLE BOOKING TEST: Same User, Same Time Slot")
        
        # Get next weekday
        test_date = self.get_next_weekday(1)
        start_time = test_date.replace(hour=11, minute=0, second=0, microsecond=0)  # 11:00 AM
        end_time = start_time + timedelta(hours=1)  # 12:00 PM
        
        print(f"📅 Testing on {test_date.strftime('%A, %Y-%m-%d')} from 11:00 AM to 12:00 PM")
        
        # Create first session
        session_data = {
            "service_type": "astrological-tarot-session",  # 60 minutes
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "First session - should succeed"
        }
        
        print("🔄 Creating first session...")
        success1, response1 = self.make_request('POST', 'sessions', session_data, 200)
        
        if success1 and 'id' in response1:
            first_session_id = response1['id']
            print(f"✅ First session created: {first_session_id}")
            print(f"   Status: {response1.get('status')}")
            print(f"   Payment Status: {response1.get('payment_status')}")
            
            # Complete payment to confirm the session
            print("💳 Completing payment for first session...")
            success_payment, payment_response = self.make_request('POST', f'sessions/{first_session_id}/payment/complete', None, 200)
            
            if success_payment:
                print("✅ First session payment completed - time slot should now be blocked")
                
                # Try to create second session with exact same time
                print("🔄 Attempting to create overlapping session...")
                overlapping_data = {
                    "service_type": "general-purpose-reading",  # 45 minutes
                    "start_at": start_time.isoformat(),  # Same start time
                    "end_at": (start_time + timedelta(minutes=45)).isoformat(),  # Overlaps
                    "client_message": "Second session - should be rejected due to overlap"
                }
                
                success2, response2 = self.make_request('POST', 'sessions', overlapping_data, 200)
                
                if not success2:
                    error_message = str(response2).lower()
                    print(f"❌ Second session rejected: {response2}")
                    
                    if 'not available' in error_message or 'conflict' in error_message or 'slot' in error_message:
                        self.log_test("Double Booking Prevention (Same User)", True, 
                                     "Successfully prevented overlapping booking for same user")
                        return True
                    else:
                        self.log_test("Double Booking Prevention (Same User)", False, 
                                     f"Session rejected but not for time conflict: {response2}")
                        return False
                else:
                    # This is the critical issue
                    second_session_id = response2.get('id')
                    self.log_issue("CRITICAL_DOUBLE_BOOKING_SAME_USER", 
                                 f"Same user was able to create overlapping sessions! Second session: {second_session_id}")
                    self.log_test("Double Booking Prevention (Same User)", False, 
                                 "CRITICAL: Same user created overlapping sessions")
                    return False
            else:
                self.log_test("Payment Completion", False, 
                             f"Failed to complete payment: {payment_response}")
                return False
        else:
            self.log_test("First Session Creation", False, 
                         f"Failed to create first session: {response1}")
            return False

    def test_double_booking_different_users(self):
        """Test if different users can create overlapping sessions"""
        print("\n👥 DOUBLE BOOKING TEST: Different Users, Same Time Slot")
        
        # Create second user
        test_email2 = f"double_booking_test2_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data2 = {
            "name": "Second Test User",
            "email": test_email2,
            "password": "DoubleTest123!",
            "role": "client"
        }
        
        success_reg, response_reg = self.make_request('POST', 'auth/register', register_data2, 200)
        
        if not success_reg:
            self.log_test("Second User Registration", False, "Failed to create second user")
            return False
        
        second_token = response_reg['access_token']
        print(f"✅ Created second user: {test_email2}")
        
        # Get next weekday
        test_date = self.get_next_weekday(2)
        start_time = test_date.replace(hour=13, minute=0, second=0, microsecond=0)  # 1:00 PM
        end_time = start_time + timedelta(hours=1)  # 2:00 PM
        
        print(f"📅 Testing on {test_date.strftime('%A, %Y-%m-%d')} from 1:00 PM to 2:00 PM")
        
        # First user creates session
        session_data = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "First user session"
        }
        
        print("🔄 First user creating session...")
        success1, response1 = self.make_request('POST', 'sessions', session_data, 200)
        
        if success1 and 'id' in response1:
            first_session_id = response1['id']
            print(f"✅ First user session created: {first_session_id}")
            
            # Complete payment
            success_payment, _ = self.make_request('POST', f'sessions/{first_session_id}/payment/complete', None, 200)
            
            if success_payment:
                print("✅ First user payment completed")
                
                # Switch to second user token
                original_token = self.token
                self.token = second_token
                
                # Second user tries to create overlapping session
                print("🔄 Second user attempting overlapping session...")
                overlapping_data = {
                    "service_type": "general-purpose-reading",
                    "start_at": start_time.isoformat(),  # Same time
                    "end_at": (start_time + timedelta(minutes=45)).isoformat(),
                    "client_message": "Second user overlapping session - should be rejected"
                }
                
                success2, response2 = self.make_request('POST', 'sessions', overlapping_data, 200)
                
                # Restore original token
                self.token = original_token
                
                if not success2:
                    error_message = str(response2).lower()
                    print(f"❌ Second user session rejected: {response2}")
                    
                    if 'not available' in error_message or 'conflict' in error_message:
                        self.log_test("Double Booking Prevention (Different Users)", True, 
                                     "Successfully prevented overlapping booking between different users")
                        return True
                    else:
                        self.log_test("Double Booking Prevention (Different Users)", False, 
                                     f"Session rejected but not for time conflict: {response2}")
                        return False
                else:
                    # Critical issue - different users can double book
                    second_session_id = response2.get('id')
                    self.log_issue("CRITICAL_DOUBLE_BOOKING_DIFFERENT_USERS", 
                                 f"Different users created overlapping sessions! Second session: {second_session_id}")
                    self.log_test("Double Booking Prevention (Different Users)", False, 
                                 "CRITICAL: Different users created overlapping sessions")
                    return False
            else:
                self.log_test("First User Payment", False, "Failed to complete first user payment")
                return False
        else:
            self.log_test("First User Session Creation", False, 
                         f"Failed to create first user session: {response1}")
            return False

    def test_partial_overlap_scenarios(self):
        """Test various partial overlap scenarios"""
        print("\n⏰ PARTIAL OVERLAP SCENARIOS TEST")
        
        test_date = self.get_next_weekday(3)
        base_start = test_date.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        base_end = base_start + timedelta(hours=1)  # 3:00 PM
        
        # Create base session
        base_session_data = {
            "service_type": "astrological-tarot-session",
            "start_at": base_start.isoformat(),
            "end_at": base_end.isoformat(),
            "client_message": "Base session: 2:00 PM - 3:00 PM"
        }
        
        print(f"📅 Creating base session: {base_start.strftime('%I:%M %p')} - {base_end.strftime('%I:%M %p')}")
        success_base, response_base = self.make_request('POST', 'sessions', base_session_data, 200)
        
        if not success_base:
            self.log_test("Base Session Creation", False, "Failed to create base session")
            return False
        
        base_session_id = response_base['id']
        print(f"✅ Base session created: {base_session_id}")
        
        # Complete payment
        self.make_request('POST', f'sessions/{base_session_id}/payment/complete', None, 200)
        print("✅ Base session payment completed")
        
        # Test various overlap scenarios
        overlap_scenarios = [
            # (start_offset_minutes, duration_minutes, description, should_be_rejected)
            (-30, 45, "1:30 PM - 2:15 PM (overlaps start)", True),
            (15, 45, "2:15 PM - 3:00 PM (overlaps middle)", True),
            (45, 45, "2:45 PM - 3:30 PM (overlaps end)", True),
            (-60, 180, "1:00 PM - 4:00 PM (completely contains)", True),
            (60, 45, "3:00 PM - 3:45 PM (starts when base ends)", False),  # Should be allowed
            (-60, 60, "1:00 PM - 2:00 PM (ends when base starts)", False),  # Should be allowed
        ]
        
        overlap_errors = 0
        
        for start_offset, duration, description, should_be_rejected in overlap_scenarios:
            test_start = base_start + timedelta(minutes=start_offset)
            test_end = test_start + timedelta(minutes=duration)
            
            print(f"\n🔍 Testing: {description}")
            print(f"   Time: {test_start.strftime('%I:%M %p')} - {test_end.strftime('%I:%M %p')}")
            print(f"   Expected: {'REJECTION' if should_be_rejected else 'ACCEPTANCE'}")
            
            overlap_session_data = {
                "service_type": "general-purpose-reading",
                "start_at": test_start.isoformat(),
                "end_at": test_end.isoformat(),
                "client_message": f"Testing overlap: {description}"
            }
            
            success, response = self.make_request('POST', 'sessions', overlap_session_data, 200)
            
            if should_be_rejected:
                if not success:
                    print(f"   ✅ Correctly rejected")
                else:
                    overlap_errors += 1
                    self.log_issue("OVERLAP_FALSE_ACCEPTANCE", 
                                 f"Overlapping session incorrectly allowed: {description}")
                    print(f"   ❌ Incorrectly allowed")
            else:
                if success:
                    print(f"   ✅ Correctly allowed")
                else:
                    overlap_errors += 1
                    print(f"   ❌ Incorrectly rejected: {response}")
        
        if overlap_errors == 0:
            self.log_test("Partial Overlap Scenarios", True, 
                         "All overlap scenarios handled correctly")
            return True
        else:
            self.log_test("Partial Overlap Scenarios", False, 
                         f"Found {overlap_errors} overlap handling errors")
            return False

    def run_double_booking_tests(self):
        """Run all double booking tests"""
        print("📅 Starting Double Booking Investigation...")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user - stopping investigation")
            return False
        
        # Run tests
        print("\n" + "=" * 60)
        self.test_double_booking_same_user()
        
        print("\n" + "=" * 60)
        self.test_double_booking_different_users()
        
        print("\n" + "=" * 60)
        self.test_partial_overlap_scenarios()
        
        # Summary
        print("\n" + "=" * 60)
        print("🔍 DOUBLE BOOKING INVESTIGATION SUMMARY")
        print("=" * 60)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"🚨 Critical Issues Found: {len(self.issues_found)}")
        
        if self.issues_found:
            print("\n🚨 CRITICAL DOUBLE BOOKING ISSUES:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue['type']}: {issue['description']}")
        else:
            print("\n✅ No double booking issues found")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return len(self.issues_found) == 0

def main():
    tester = DoubleBookingTester()
    success = tester.run_double_booking_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())