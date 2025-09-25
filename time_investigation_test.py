#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

class TimeInvestigationTester:
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

    def setup_test_user(self):
        """Setup test user for testing"""
        test_email = f"time_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Time Test User",
            "email": test_email,
            "password": "TimeTest123!",
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

    def test_time_storage_investigation(self):
        """Test 1: Investigate how session times are stored vs displayed"""
        print("\n🕐 INVESTIGATION 1: Time Storage vs Display")
        
        # Create a session with specific time (10:00 AM)
        target_date = datetime.now() + timedelta(days=1)
        # Set to exactly 10:00 AM
        start_time = target_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=45)  # 45-minute session
        
        print(f"📅 Creating session for: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (10:00 AM)")
        print(f"📅 Expected end time: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (10:45 AM)")
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing time storage - should be 10:00 AM"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            stored_start = response.get('start_at')
            stored_end = response.get('end_at')
            
            print(f"✅ Session created: {session_id}")
            print(f"📊 Stored start_at: {stored_start}")
            print(f"📊 Stored end_at: {stored_end}")
            
            # Parse stored times to check for discrepancies
            try:
                if stored_start:
                    parsed_start = datetime.fromisoformat(stored_start.replace('Z', '+00:00'))
                    print(f"🔍 Parsed start time: {parsed_start}")
                    
                    # Check if there's a timezone issue
                    if parsed_start.hour != 10:
                        self.log_issue("TIME_DISPLAY_MISMATCH", 
                                     f"Session scheduled for 10:00 AM but stored as {parsed_start.hour}:00")
                        
                if stored_end:
                    parsed_end = datetime.fromisoformat(stored_end.replace('Z', '+00:00'))
                    print(f"🔍 Parsed end time: {parsed_end}")
                    
                    # Check if end time is correct (should be 10:45 AM, not 3:45 PM)
                    if parsed_end.hour == 15:  # 3 PM
                        self.log_issue("TIME_CALCULATION_ERROR", 
                                     f"45-minute session ending at 3:00 PM instead of 10:45 AM")
                        
            except Exception as e:
                self.log_issue("TIME_PARSING_ERROR", f"Failed to parse stored times: {str(e)}")
            
            # Retrieve the session to see how it's returned
            success2, response2 = self.make_request('GET', f'sessions/{session_id}', None, 200)
            
            if success2:
                retrieved_start = response2.get('start_at')
                retrieved_end = response2.get('end_at')
                
                print(f"🔄 Retrieved start_at: {retrieved_start}")
                print(f"🔄 Retrieved end_at: {retrieved_end}")
                
                # Compare original vs retrieved
                if stored_start != retrieved_start:
                    self.log_issue("TIME_RETRIEVAL_MISMATCH", 
                                 f"Stored time differs from retrieved time")
                
                self.log_test("Time Storage Investigation", True, 
                             f"Session times stored and retrieved - check console for discrepancies")
                return session_id
            else:
                self.log_test("Time Storage Investigation", False, 
                             "Failed to retrieve session", response2)
                return None
        else:
            self.log_test("Time Storage Investigation", False, 
                         "Failed to create session", response)
            return None

    def test_double_booking_prevention(self):
        """Test 2: Verify calendar blocking system prevents double bookings"""
        print("\n📅 INVESTIGATION 2: Double Booking Prevention")
        
        # Create first session
        target_date = datetime.now() + timedelta(days=2)
        start_time = target_date.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        end_time = start_time + timedelta(hours=1)  # 3:00 PM
        
        print(f"📅 Testing double booking for: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        session_data = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "First session - should succeed"
        }
        
        # Create first session
        success1, response1 = self.make_request('POST', 'sessions', session_data, 200)
        
        if success1 and 'id' in response1:
            first_session_id = response1['id']
            print(f"✅ First session created: {first_session_id}")
            
            # Complete payment to confirm the session (this should block the time slot)
            success_payment, payment_response = self.make_request('POST', f'sessions/{first_session_id}/payment/complete', None, 200)
            
            if success_payment:
                print("✅ First session payment completed - time slot should now be blocked")
                
                # Try to create overlapping session (should fail)
                overlapping_session_data = {
                    "service_type": "general-purpose-reading",
                    "start_at": start_time.isoformat(),  # Same start time
                    "end_at": end_time.isoformat(),      # Same end time
                    "client_message": "Overlapping session - should fail"
                }
                
                success2, response2 = self.make_request('POST', 'sessions', overlapping_session_data, 200)
                
                if not success2:
                    if 'not available' in str(response2).lower() or 'conflict' in str(response2).lower():
                        self.log_test("Double Booking Prevention", True, 
                                     "Successfully prevented overlapping booking")
                        return True
                    else:
                        self.log_issue("DOUBLE_BOOKING_ALLOWED", 
                                     f"Session creation failed but not due to time conflict: {response2}")
                        self.log_test("Double Booking Prevention", False, 
                                     "Failed for wrong reason", response2)
                        return False
                else:
                    # This is a critical issue - double booking was allowed
                    second_session_id = response2.get('id')
                    self.log_issue("CRITICAL_DOUBLE_BOOKING", 
                                 f"Double booking allowed! Second session created: {second_session_id}")
                    self.log_test("Double Booking Prevention", False, 
                                 "Double booking was allowed - CRITICAL ISSUE", response2)
                    return False
            else:
                self.log_test("Payment Completion for Blocking", False, 
                             "Failed to complete payment", payment_response)
                return False
        else:
            self.log_test("First Session Creation", False, 
                         "Failed to create first session", response1)
            return False

    def test_session_time_retrieval(self):
        """Test 3: Check if session times are converted incorrectly when retrieved"""
        print("\n🔄 INVESTIGATION 3: Session Time Retrieval Accuracy")
        
        # Create multiple sessions at different times to test retrieval
        test_times = [
            (10, 0, "10:00 AM"),  # Morning
            (14, 30, "2:30 PM"),  # Afternoon  
            (16, 0, "4:00 PM"),   # Late afternoon
        ]
        
        created_sessions = []
        
        for hour, minute, description in test_times:
            target_date = datetime.now() + timedelta(days=3)
            start_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end_time = start_time + timedelta(minutes=45)
            
            print(f"📅 Creating session for {description}: {start_time.isoformat()}")
            
            session_data = {
                "service_type": "general-purpose-reading",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": f"Testing retrieval for {description}"
            }
            
            success, response = self.make_request('POST', 'sessions', session_data, 200)
            
            if success and 'id' in response:
                created_sessions.append({
                    'id': response['id'],
                    'expected_hour': hour,
                    'expected_minute': minute,
                    'description': description,
                    'original_start': start_time.isoformat(),
                    'stored_start': response.get('start_at'),
                    'stored_end': response.get('end_at')
                })
                print(f"✅ Session created: {response['id']}")
            else:
                print(f"❌ Failed to create session for {description}")
        
        # Now retrieve all sessions and check for time discrepancies
        success, response = self.make_request('GET', 'sessions', None, 200)
        
        if success and isinstance(response, list):
            print(f"🔄 Retrieved {len(response)} total sessions")
            
            discrepancies_found = 0
            
            for created_session in created_sessions:
                # Find this session in the retrieved list
                retrieved_session = None
                for session in response:
                    if session.get('id') == created_session['id']:
                        retrieved_session = session
                        break
                
                if retrieved_session:
                    retrieved_start = retrieved_session.get('start_at')
                    retrieved_end = retrieved_session.get('end_at')
                    
                    print(f"\n🔍 Checking {created_session['description']}:")
                    print(f"   Original: {created_session['original_start']}")
                    print(f"   Stored:   {created_session['stored_start']}")
                    print(f"   Retrieved: {retrieved_start}")
                    
                    # Parse and compare times
                    try:
                        if retrieved_start:
                            parsed_retrieved = datetime.fromisoformat(retrieved_start.replace('Z', '+00:00'))
                            
                            if parsed_retrieved.hour != created_session['expected_hour']:
                                discrepancies_found += 1
                                self.log_issue("TIME_RETRIEVAL_DISCREPANCY", 
                                             f"{created_session['description']} - Expected {created_session['expected_hour']}:00, got {parsed_retrieved.hour}:00")
                            
                            # Check for the specific 10 AM -> 3 PM issue
                            if created_session['expected_hour'] == 10 and parsed_retrieved.hour == 15:
                                self.log_issue("SPECIFIC_10AM_3PM_BUG", 
                                             "Found the reported bug: 10 AM session displaying as 3 PM")
                                
                    except Exception as e:
                        self.log_issue("TIME_PARSING_ERROR", 
                                     f"Failed to parse retrieved time for {created_session['description']}: {str(e)}")
                        discrepancies_found += 1
                else:
                    print(f"❌ Could not find retrieved session for {created_session['description']}")
                    discrepancies_found += 1
            
            if discrepancies_found == 0:
                self.log_test("Session Time Retrieval", True, 
                             "All session times retrieved correctly")
                return True
            else:
                self.log_test("Session Time Retrieval", False, 
                             f"Found {discrepancies_found} time discrepancies")
                return False
        else:
            self.log_test("Session Time Retrieval", False, 
                         "Failed to retrieve sessions", response)
            return False

    def test_timezone_conversion_issues(self):
        """Test 4: Check for timezone conversion problems"""
        print("\n🌍 INVESTIGATION 4: Timezone Conversion Issues")
        
        # Test with explicit timezone information
        target_date = datetime.now() + timedelta(days=4)
        
        # Create session with UTC time
        utc_start = target_date.replace(hour=10, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        utc_end = utc_start + timedelta(minutes=60)
        
        print(f"🌍 Creating session with UTC time: {utc_start.isoformat()}")
        
        session_data = {
            "service_type": "astrological-tarot-session",
            "start_at": utc_start.isoformat(),
            "end_at": utc_end.isoformat(),
            "client_message": "Testing timezone handling with UTC"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            stored_start = response.get('start_at')
            stored_end = response.get('end_at')
            
            print(f"✅ UTC session created: {session_id}")
            print(f"📊 Stored start: {stored_start}")
            print(f"📊 Stored end: {stored_end}")
            
            # Now create session with local time (no timezone info)
            local_start = target_date.replace(hour=11, minute=0, second=0, microsecond=0)
            local_end = local_start + timedelta(minutes=60)
            
            print(f"🏠 Creating session with local time: {local_start.isoformat()}")
            
            local_session_data = {
                "service_type": "general-purpose-reading",
                "start_at": local_start.isoformat(),
                "end_at": local_end.isoformat(),
                "client_message": "Testing timezone handling with local time"
            }
            
            success2, response2 = self.make_request('POST', 'sessions', local_session_data, 200)
            
            if success2 and 'id' in response2:
                local_session_id = response2['id']
                local_stored_start = response2.get('start_at')
                local_stored_end = response2.get('end_at')
                
                print(f"✅ Local session created: {local_session_id}")
                print(f"📊 Stored start: {local_stored_start}")
                print(f"📊 Stored end: {local_stored_end}")
                
                # Compare how UTC vs local times are handled
                try:
                    if stored_start and local_stored_start:
                        utc_parsed = datetime.fromisoformat(stored_start.replace('Z', '+00:00'))
                        local_parsed = datetime.fromisoformat(local_stored_start.replace('Z', '+00:00'))
                        
                        print(f"🔍 UTC parsed: {utc_parsed}")
                        print(f"🔍 Local parsed: {local_parsed}")
                        
                        # Check for unexpected timezone conversions
                        hour_diff = abs(utc_parsed.hour - local_parsed.hour)
                        if hour_diff > 1:  # More than 1 hour difference is suspicious
                            self.log_issue("TIMEZONE_CONVERSION_ERROR", 
                                         f"Unexpected time difference between UTC and local: {hour_diff} hours")
                        
                        # Check for the specific 10 AM -> 3 PM issue (5 hour difference suggests timezone problem)
                        if hour_diff == 5:
                            self.log_issue("TIMEZONE_5_HOUR_SHIFT", 
                                         "Found 5-hour time shift - likely timezone conversion bug")
                        
                        self.log_test("Timezone Conversion Test", True, 
                                     f"Timezone handling tested - {hour_diff} hour difference found")
                        return True
                        
                except Exception as e:
                    self.log_issue("TIMEZONE_PARSING_ERROR", 
                                 f"Failed to parse timezone data: {str(e)}")
                    self.log_test("Timezone Conversion Test", False, 
                                 "Failed to parse timezone data", str(e))
                    return False
            else:
                self.log_test("Local Time Session Creation", False, 
                             "Failed to create local time session", response2)
                return False
        else:
            self.log_test("UTC Time Session Creation", False, 
                         "Failed to create UTC time session", response)
            return False

    def run_time_investigation(self):
        """Run all time-related investigations"""
        print("🕐 Starting Time Display and Double Booking Investigation...")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user - stopping investigation")
            return False
        
        # Run investigations
        print("\n" + "=" * 70)
        self.test_time_storage_investigation()
        
        print("\n" + "=" * 70)
        self.test_double_booking_prevention()
        
        print("\n" + "=" * 70)
        self.test_session_time_retrieval()
        
        print("\n" + "=" * 70)
        self.test_timezone_conversion_issues()
        
        # Summary
        print("\n" + "=" * 70)
        print("🔍 INVESTIGATION SUMMARY")
        print("=" * 70)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"🚨 Critical Issues Found: {len(self.issues_found)}")
        
        if self.issues_found:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue['type']}: {issue['description']}")
        else:
            print("\n✅ No critical issues found in time handling")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return len(self.issues_found) == 0

    def save_investigation_results(self, filename: str = "/app/time_investigation_results.json"):
        """Save investigation results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "investigation_focus": "Time Display and Double Booking Issues",
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "critical_issues_found": len(self.issues_found),
            "issues": self.issues_found,
            "test_details": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Investigation results saved to: {filename}")

def main():
    tester = TimeInvestigationTester()
    success = tester.run_time_investigation()
    tester.save_investigation_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())