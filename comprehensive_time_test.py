#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

class ComprehensiveTimeTester:
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
        if not success and response_data:
            print(f"    Response: {response_data}")

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
        if data:
            print(f"    Data: {data}")

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
        """Get next weekday (Monday-Friday) for testing"""
        current = datetime.now()
        for i in range(days_ahead, days_ahead + 7):
            test_date = current + timedelta(days=i)
            if test_date.weekday() < 5:  # Monday=0, Friday=4
                return test_date
        return current + timedelta(days=days_ahead)

    def setup_test_user(self):
        """Setup test user for testing"""
        test_email = f"comprehensive_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Comprehensive Test User",
            "email": test_email,
            "password": "CompTest123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', register_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log_test("Test User Setup", True, f"Created test user: {test_email}")
            return True
        else:
            self.log_test("Test User Setup", False, "Failed to create test user", response)
            return False

    def test_specific_10am_3pm_issue(self):
        """Test the specific reported issue: 10 AM sessions showing as 3:00 PM"""
        print("\n🕐 SPECIFIC ISSUE TEST: 10 AM → 3:00 PM Bug")
        
        # Get next weekday
        test_date = self.get_next_weekday(1)
        start_time = test_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=45)  # 45-minute session
        
        print(f"📅 Creating 45-minute session starting at 10:00 AM on {test_date.strftime('%A, %Y-%m-%d')}")
        print(f"📅 Expected end time: 10:45 AM")
        
        session_data = {
            "service_type": "general-purpose-reading",  # 45 minutes, $65
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing the 10 AM → 3 PM bug specifically"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            stored_start = response.get('start_at')
            stored_end = response.get('end_at')
            
            print(f"✅ Session created: {session_id}")
            print(f"📊 Backend returned start_at: {stored_start}")
            print(f"📊 Backend returned end_at: {stored_end}")
            
            # Parse the times to check for the specific bug
            try:
                if stored_start:
                    parsed_start = datetime.fromisoformat(stored_start.replace('Z', '+00:00'))
                    print(f"🔍 Parsed start time: {parsed_start.strftime('%I:%M %p')} ({parsed_start.hour}:00)")
                    
                if stored_end:
                    parsed_end = datetime.fromisoformat(stored_end.replace('Z', '+00:00'))
                    print(f"🔍 Parsed end time: {parsed_end.strftime('%I:%M %p')} ({parsed_end.hour}:{parsed_end.minute:02d})")
                    
                    # Check for the specific bug: 10:45 AM showing as 3:45 PM
                    if parsed_end.hour == 15 and parsed_end.minute == 45:  # 3:45 PM
                        self.log_issue("CONFIRMED_10AM_3PM_BUG", 
                                     f"CONFIRMED: 45-minute session starting at 10:00 AM shows end time as 3:45 PM instead of 10:45 AM")
                        self.log_test("10 AM → 3 PM Bug Test", False, 
                                     "Bug confirmed: 10:45 AM displaying as 3:45 PM")
                        return False
                    elif parsed_end.hour == 10 and parsed_end.minute == 45:  # Correct: 10:45 AM
                        self.log_test("10 AM → 3 PM Bug Test", True, 
                                     "Time calculation working correctly: 10:00 AM + 45 min = 10:45 AM")
                        return True
                    else:
                        self.log_issue("UNEXPECTED_TIME_CALCULATION", 
                                     f"Unexpected end time: {parsed_end.strftime('%I:%M %p')} for 45-minute session starting at 10:00 AM")
                        self.log_test("10 AM → 3 PM Bug Test", False, 
                                     f"Unexpected time calculation result: {parsed_end.strftime('%I:%M %p')}")
                        return False
                        
            except Exception as e:
                self.log_issue("TIME_PARSING_ERROR", f"Failed to parse session times: {str(e)}")
                self.log_test("10 AM → 3 PM Bug Test", False, "Failed to parse times", str(e))
                return False
        else:
            self.log_test("10 AM → 3 PM Bug Test", False, "Failed to create test session", response)
            return False

    def test_double_booking_on_weekday(self):
        """Test double booking prevention on a valid weekday"""
        print("\n📅 DOUBLE BOOKING TEST: Weekday Business Hours")
        
        # Get next weekday
        test_date = self.get_next_weekday(2)
        start_time = test_date.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        end_time = start_time + timedelta(hours=1)  # 3:00 PM
        
        print(f"📅 Testing double booking on {test_date.strftime('%A, %Y-%m-%d')} from 2:00 PM to 3:00 PM")
        
        # Create first session
        session_data = {
            "service_type": "astrological-tarot-session",  # 60 minutes
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "First session - should succeed and block time slot"
        }
        
        success1, response1 = self.make_request('POST', 'sessions', session_data, 200)
        
        if success1 and 'id' in response1:
            first_session_id = response1['id']
            print(f"✅ First session created: {first_session_id}")
            
            # Complete payment to confirm and block the time slot
            success_payment, payment_response = self.make_request('POST', f'sessions/{first_session_id}/payment/complete', None, 200)
            
            if success_payment:
                print("✅ First session payment completed - time slot should now be blocked")
                
                # Try to create overlapping session
                overlapping_data = {
                    "service_type": "general-purpose-reading",  # 45 minutes
                    "start_at": start_time.isoformat(),  # Same start time
                    "end_at": (start_time + timedelta(minutes=45)).isoformat(),  # Overlaps with first session
                    "client_message": "Overlapping session - should be rejected"
                }
                
                success2, response2 = self.make_request('POST', 'sessions', overlapping_data, 200)
                
                if not success2:
                    error_message = str(response2).lower()
                    if 'not available' in error_message or 'conflict' in error_message or 'slot' in error_message:
                        self.log_test("Double Booking Prevention", True, 
                                     "Successfully prevented overlapping booking")
                        return True
                    else:
                        self.log_test("Double Booking Prevention", False, 
                                     f"Session rejected but not for time conflict: {response2}")
                        return False
                else:
                    # Critical issue - double booking allowed
                    second_session_id = response2.get('id')
                    self.log_issue("CRITICAL_DOUBLE_BOOKING_ALLOWED", 
                                 f"Double booking allowed! Second session created: {second_session_id}")
                    self.log_test("Double Booking Prevention", False, 
                                 "CRITICAL: Double booking was allowed", response2)
                    return False
            else:
                self.log_test("Payment Completion", False, 
                             "Failed to complete payment for first session", payment_response)
                return False
        else:
            self.log_test("First Session Creation", False, 
                         "Failed to create first session", response1)
            return False

    def test_session_duration_calculations(self):
        """Test various session durations to identify calculation issues"""
        print("\n⏱️  SESSION DURATION CALCULATIONS TEST")
        
        test_date = self.get_next_weekday(3)
        
        # Test different service types with their expected durations
        test_cases = [
            ("general-purpose-reading", 45, "45-minute General Reading"),
            ("astrological-tarot-session", 60, "60-minute Astrological Tarot"),
            ("birth-chart-reading", 90, "90-minute Birth Chart Reading"),
            ("follow-up", 30, "30-minute Follow-up Session")
        ]
        
        calculation_errors = 0
        
        for service_type, expected_minutes, description in test_cases:
            start_time = test_date.replace(hour=11, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(minutes=expected_minutes)
            
            print(f"\n🔍 Testing {description}")
            print(f"   Expected: {start_time.strftime('%I:%M %p')} → {end_time.strftime('%I:%M %p')} ({expected_minutes} min)")
            
            session_data = {
                "service_type": service_type,
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": f"Testing {description} duration calculation"
            }
            
            success, response = self.make_request('POST', 'sessions', session_data, 200)
            
            if success and 'id' in response:
                stored_start = response.get('start_at')
                stored_end = response.get('end_at')
                
                try:
                    if stored_start and stored_end:
                        parsed_start = datetime.fromisoformat(stored_start.replace('Z', '+00:00'))
                        parsed_end = datetime.fromisoformat(stored_end.replace('Z', '+00:00'))
                        
                        actual_duration = (parsed_end - parsed_start).total_seconds() / 60
                        
                        print(f"   Stored: {parsed_start.strftime('%I:%M %p')} → {parsed_end.strftime('%I:%M %p')} ({actual_duration:.0f} min)")
                        
                        if abs(actual_duration - expected_minutes) > 1:  # Allow 1 minute tolerance
                            calculation_errors += 1
                            self.log_issue("DURATION_CALCULATION_ERROR", 
                                         f"{description}: Expected {expected_minutes} min, got {actual_duration:.0f} min")
                        else:
                            print(f"   ✅ Duration calculation correct")
                            
                except Exception as e:
                    calculation_errors += 1
                    self.log_issue("DURATION_PARSING_ERROR", 
                                 f"Failed to parse duration for {description}: {str(e)}")
            else:
                calculation_errors += 1
                print(f"   ❌ Failed to create session for {description}")
            
            # Move to next hour for next test
            test_date = test_date.replace(hour=test_date.hour + 2)
        
        if calculation_errors == 0:
            self.log_test("Session Duration Calculations", True, 
                         "All duration calculations working correctly")
            return True
        else:
            self.log_test("Session Duration Calculations", False, 
                         f"Found {calculation_errors} duration calculation errors")
            return False

    def test_business_hours_edge_cases(self):
        """Test edge cases around business hours (6 PM cutoff)"""
        print("\n🕕 BUSINESS HOURS EDGE CASES TEST")
        
        test_date = self.get_next_weekday(4)
        
        # Test cases around 6 PM cutoff
        test_cases = [
            (17, 0, 45, "5:00 PM + 45 min = 5:45 PM", True),   # Should succeed (ends before 6 PM)
            (17, 15, 45, "5:15 PM + 45 min = 6:00 PM", True),  # Should succeed (ends exactly at 6 PM)
            (17, 16, 45, "5:16 PM + 45 min = 6:01 PM", False), # Should fail (ends after 6 PM)
            (17, 30, 60, "5:30 PM + 60 min = 6:30 PM", False), # Should fail (ends after 6 PM)
        ]
        
        edge_case_errors = 0
        
        for hour, minute, duration, description, should_succeed in test_cases:
            start_time = test_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end_time = start_time + timedelta(minutes=duration)
            
            print(f"\n🔍 Testing: {description}")
            print(f"   Expected result: {'SUCCESS' if should_succeed else 'REJECTION'}")
            
            session_data = {
                "service_type": "general-purpose-reading",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": f"Testing business hours: {description}"
            }
            
            success, response = self.make_request('POST', 'sessions', session_data, 200)
            
            if should_succeed:
                if success:
                    print(f"   ✅ Correctly allowed session ending at {end_time.strftime('%I:%M %p')}")
                else:
                    edge_case_errors += 1
                    self.log_issue("BUSINESS_HOURS_FALSE_REJECTION", 
                                 f"Session incorrectly rejected: {description}")
                    print(f"   ❌ Incorrectly rejected: {response}")
            else:
                if not success:
                    error_message = str(response).lower()
                    if '6' in error_message or 'business' in error_message or 'hour' in error_message:
                        print(f"   ✅ Correctly rejected session ending at {end_time.strftime('%I:%M %p')}")
                    else:
                        edge_case_errors += 1
                        print(f"   ⚠️  Rejected but wrong reason: {response}")
                else:
                    edge_case_errors += 1
                    self.log_issue("BUSINESS_HOURS_FALSE_ACCEPTANCE", 
                                 f"Session incorrectly allowed: {description}")
                    print(f"   ❌ Incorrectly allowed session ending at {end_time.strftime('%I:%M %p')}")
        
        if edge_case_errors == 0:
            self.log_test("Business Hours Edge Cases", True, 
                         "All business hours validations working correctly")
            return True
        else:
            self.log_test("Business Hours Edge Cases", False, 
                         f"Found {edge_case_errors} business hours validation errors")
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive time-related tests"""
        print("🕐 Starting Comprehensive Time Display and Double Booking Investigation...")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user - stopping investigation")
            return False
        
        # Run specific tests for reported issues
        print("\n" + "=" * 80)
        self.test_specific_10am_3pm_issue()
        
        print("\n" + "=" * 80)
        self.test_double_booking_on_weekday()
        
        print("\n" + "=" * 80)
        self.test_session_duration_calculations()
        
        print("\n" + "=" * 80)
        self.test_business_hours_edge_cases()
        
        # Summary
        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE INVESTIGATION SUMMARY")
        print("=" * 80)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"🚨 Critical Issues Found: {len(self.issues_found)}")
        
        if self.issues_found:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue['type']}: {issue['description']}")
        else:
            print("\n✅ No critical issues found")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return len(self.issues_found) == 0

    def save_results(self, filename: str = "/app/comprehensive_time_test_results.json"):
        """Save test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "investigation_focus": "Comprehensive Time Display and Double Booking Issues",
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "critical_issues_found": len(self.issues_found),
            "issues": self.issues_found,
            "test_details": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Test results saved to: {filename}")

def main():
    tester = ComprehensiveTimeTester()
    success = tester.run_comprehensive_tests()
    tester.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())