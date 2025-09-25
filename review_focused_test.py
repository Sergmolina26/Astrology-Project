#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ReviewFocusedTester:
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

    def setup_auth(self):
        """Setup authentication for testing"""
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
            self.log_test("Authentication Setup", True, f"Registered user: {test_email}")
            return True
        else:
            self.log_test("Authentication Setup", False, "Failed to register user", response)
            return False

    def test_new_services_api(self):
        """Test the new /api/services endpoint to verify updated service list with correct pricing"""
        success, response = self.make_request('GET', 'services', None, 200)
        
        if success and 'services' in response:
            services = response['services']
            
            # Check if we have the expected new services
            service_ids = [service['id'] for service in services]
            expected_services = ['general-purpose-reading', 'astrological-tarot-session']
            
            found_services = []
            missing_services = []
            
            for expected_service in expected_services:
                if expected_service in service_ids:
                    found_services.append(expected_service)
                else:
                    missing_services.append(expected_service)
            
            # Check pricing for the new services
            pricing_correct = True
            pricing_details = []
            
            for service in services:
                if service['id'] == 'general-purpose-reading':
                    if service['price'] == 65.0 and service['duration'] == 45:
                        pricing_details.append(f"✅ General Purpose Reading: ${service['price']}, {service['duration']}min")
                    else:
                        pricing_correct = False
                        pricing_details.append(f"❌ General Purpose Reading: Expected $65/45min, got ${service['price']}/{service['duration']}min")
                
                elif service['id'] == 'astrological-tarot-session':
                    if service['price'] == 85.0 and service['duration'] == 60:
                        pricing_details.append(f"✅ Astrological Tarot Session: ${service['price']}, {service['duration']}min")
                    else:
                        pricing_correct = False
                        pricing_details.append(f"❌ Astrological Tarot Session: Expected $85/60min, got ${service['price']}/{service['duration']}min")
            
            if len(found_services) == len(expected_services) and pricing_correct:
                details = f"Found all new services with correct pricing: {', '.join(pricing_details)}"
                self.log_test("New Services API", True, details)
                return True
            else:
                details = f"Issues found - Missing: {missing_services}, Pricing: {', '.join(pricing_details)}"
                self.log_test("New Services API", False, details, response)
                return False
        else:
            self.log_test("New Services API", False, "Failed to retrieve services", response)
            return False

    def test_business_hours_validation_6pm_exact(self):
        """Test that sessions can end exactly at 6:00 PM but are rejected if they end after 6:00 PM"""
        
        # Test 1: Session ending exactly at 6:00 PM (should be REJECTED based on user feedback)
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        # Skip weekends
        while tomorrow.weekday() > 4:  # Saturday=5, Sunday=6
            tomorrow += timedelta(days=1)
        
        start_time_6pm = tomorrow.replace(hour=17, minute=0)  # 5:00 PM
        end_time_6pm = tomorrow.replace(hour=18, minute=0)    # 6:00 PM exactly
        
        session_data_6pm = {
            "service_type": "general-purpose-reading",
            "start_at": start_time_6pm.isoformat(),
            "end_at": end_time_6pm.isoformat(),
            "client_message": "Testing 6:00 PM exact end time"
        }
        
        success_6pm, response_6pm = self.make_request('POST', 'sessions', session_data_6pm, 400)  # Expecting 400 error
        
        if not success_6pm and "6:00 PM" in str(response_6pm):
            self.log_test("Business Hours - 6:00 PM Exact (Should Reject)", True, 
                         "Correctly rejected session ending exactly at 6:00 PM")
        else:
            self.log_test("Business Hours - 6:00 PM Exact (Should Reject)", False, 
                         "Failed to reject session ending at 6:00 PM", response_6pm)
        
        # Test 2: Session ending after 6:00 PM (6:01 PM - should be rejected)
        start_time_601pm = tomorrow.replace(hour=17, minute=1)  # 5:01 PM
        end_time_601pm = tomorrow.replace(hour=18, minute=1)    # 6:01 PM
        
        session_data_601pm = {
            "service_type": "general-purpose-reading",
            "start_at": start_time_601pm.isoformat(),
            "end_at": end_time_601pm.isoformat(),
            "client_message": "Testing 6:01 PM end time"
        }
        
        success_601pm, response_601pm = self.make_request('POST', 'sessions', session_data_601pm, 400)  # Expecting 400 error
        
        if success_601pm and "6:00 PM" in str(response_601pm):
            self.log_test("Business Hours - 6:01 PM (Should Reject)", True, 
                         "Correctly rejected session ending at 6:01 PM")
        else:
            self.log_test("Business Hours - 6:01 PM (Should Reject)", False, 
                         "Failed to reject session ending at 6:01 PM", response_601pm)
        
        # Test 3: Session ending after 6:00 PM (6:30 PM - should be rejected)
        start_time_630pm = tomorrow.replace(hour=17, minute=30)  # 5:30 PM
        end_time_630pm = tomorrow.replace(hour=18, minute=30)    # 6:30 PM
        
        session_data_630pm = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time_630pm.isoformat(),
            "end_at": end_time_630pm.isoformat(),
            "client_message": "Testing 6:30 PM end time"
        }
        
        success_630pm, response_630pm = self.make_request('POST', 'sessions', session_data_630pm, 400)  # Expecting 400 error
        
        if not success_630pm and "6:00 PM" in str(response_630pm):
            self.log_test("Business Hours - 6:30 PM (Should Reject)", True, 
                         "Correctly rejected session ending at 6:30 PM")
        else:
            self.log_test("Business Hours - 6:30 PM (Should Reject)", False, 
                         "Failed to reject session ending at 6:30 PM", response_630pm)
        
        # Test 4: Session ending before 6:00 PM (5:59 PM - should be accepted)
        start_time_559pm = tomorrow.replace(hour=16, minute=14)  # 4:14 PM
        end_time_559pm = tomorrow.replace(hour=17, minute=59)    # 5:59 PM
        
        session_data_559pm = {
            "service_type": "general-purpose-reading",
            "start_at": start_time_559pm.isoformat(),
            "end_at": end_time_559pm.isoformat(),
            "client_message": "Testing 5:59 PM end time"
        }
        
        success_559pm, response_559pm = self.make_request('POST', 'sessions', session_data_559pm, 200)  # Expecting success
        
        if success_559pm and 'id' in response_559pm:
            self.log_test("Business Hours - 5:59 PM (Should Accept)", True, 
                         "Correctly accepted session ending at 5:59 PM")
            return True
        else:
            self.log_test("Business Hours - 5:59 PM (Should Accept)", False, 
                         "Failed to accept session ending at 5:59 PM", response_559pm)
            return False

    def test_service_pricing_new_services(self):
        """Test session creation with new service types to verify pricing is correct"""
        
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        # Skip weekends
        while tomorrow.weekday() > 4:
            tomorrow += timedelta(days=1)
        
        # Test 1: General Purpose Reading ($65, 45min)
        start_time_general = tomorrow.replace(hour=14, minute=0)  # 2:00 PM
        end_time_general = start_time_general + timedelta(minutes=45)  # 2:45 PM
        
        session_data_general = {
            "service_type": "general-purpose-reading",
            "start_at": start_time_general.isoformat(),
            "end_at": end_time_general.isoformat(),
            "client_message": "Testing general purpose reading pricing"
        }
        
        success_general, response_general = self.make_request('POST', 'sessions', session_data_general, 200)
        
        if success_general and response_general.get('amount') == 65.0:
            self.log_test("Service Pricing - General Purpose Reading", True, 
                         f"Correct pricing: ${response_general['amount']}")
        else:
            self.log_test("Service Pricing - General Purpose Reading", False, 
                         f"Incorrect pricing: expected $65, got ${response_general.get('amount', 'N/A')}", response_general)
        
        # Test 2: Astrological Tarot Session ($85, 60min)
        start_time_astro = tomorrow.replace(hour=15, minute=0)  # 3:00 PM
        end_time_astro = start_time_astro + timedelta(minutes=60)  # 4:00 PM
        
        session_data_astro = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time_astro.isoformat(),
            "end_at": end_time_astro.isoformat(),
            "client_message": "Testing astrological tarot session pricing"
        }
        
        success_astro, response_astro = self.make_request('POST', 'sessions', session_data_astro, 200)
        
        if success_astro and response_astro.get('amount') == 85.0:
            self.log_test("Service Pricing - Astrological Tarot Session", True, 
                         f"Correct pricing: ${response_astro['amount']}")
            return True
        else:
            self.log_test("Service Pricing - Astrological Tarot Session", False, 
                         f"Incorrect pricing: expected $85, got ${response_astro.get('amount', 'N/A')}", response_astro)
            return False

    def test_duration_calculation_new_services(self):
        """Verify that backend duration calculation is working correctly for the new services"""
        
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)
        # Skip weekends
        while tomorrow.weekday() > 4:
            tomorrow += timedelta(days=1)
        
        # Test 1: Create a 45-minute general purpose reading
        start_time = tomorrow.replace(hour=11, minute=0)  # 11:00 AM
        end_time = start_time + timedelta(minutes=45)     # 11:45 AM
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing duration calculation for 45-minute session"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            
            # Get the session details to check duration calculation
            success2, session_response = self.make_request('GET', f'sessions/{session_id}', None, 200)
            
            if success2:
                # Calculate duration from start_at and end_at
                start_at = datetime.fromisoformat(session_response['start_at'].replace('Z', '+00:00'))
                end_at = datetime.fromisoformat(session_response['end_at'].replace('Z', '+00:00'))
                duration_minutes = int((end_at - start_at).total_seconds() / 60)
                
                if duration_minutes == 45:
                    self.log_test("Duration Calculation - 45 Minutes", True, 
                                 f"Correct duration calculated: {duration_minutes} minutes")
                else:
                    self.log_test("Duration Calculation - 45 Minutes", False, 
                                 f"Incorrect duration: expected 45 minutes, got {duration_minutes} minutes")
            else:
                self.log_test("Duration Calculation - Session Retrieval", False, 
                             "Failed to retrieve session for duration check", session_response)
        else:
            self.log_test("Duration Calculation - Session Creation", False, 
                         "Failed to create session for duration test", response)
        
        # Test 2: Create a 60-minute astrological tarot session
        start_time_60 = tomorrow.replace(hour=13, minute=0)  # 1:00 PM
        end_time_60 = start_time_60 + timedelta(minutes=60)  # 2:00 PM
        
        session_data_60 = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time_60.isoformat(),
            "end_at": end_time_60.isoformat(),
            "client_message": "Testing duration calculation for 60-minute session"
        }
        
        success_60, response_60 = self.make_request('POST', 'sessions', session_data_60, 200)
        
        if success_60 and 'id' in response_60:
            session_id_60 = response_60['id']
            
            # Get the session details to check duration calculation
            success2_60, session_response_60 = self.make_request('GET', f'sessions/{session_id_60}', None, 200)
            
            if success2_60:
                # Calculate duration from start_at and end_at
                start_at_60 = datetime.fromisoformat(session_response_60['start_at'].replace('Z', '+00:00'))
                end_at_60 = datetime.fromisoformat(session_response_60['end_at'].replace('Z', '+00:00'))
                duration_minutes_60 = int((end_at_60 - start_at_60).total_seconds() / 60)
                
                if duration_minutes_60 == 60:
                    self.log_test("Duration Calculation - 60 Minutes", True, 
                                 f"Correct duration calculated: {duration_minutes_60} minutes")
                    return True
                else:
                    self.log_test("Duration Calculation - 60 Minutes", False, 
                                 f"Incorrect duration: expected 60 minutes, got {duration_minutes_60} minutes")
                    return False
            else:
                self.log_test("Duration Calculation - Session Retrieval 60min", False, 
                             "Failed to retrieve 60-minute session for duration check", session_response_60)
                return False
        else:
            self.log_test("Duration Calculation - Session Creation 60min", False, 
                         "Failed to create 60-minute session for duration test", response_60)
            return False

    def run_review_tests(self):
        """Run all review-focused tests"""
        print("🔍 Starting Review-Focused Tests...")
        print("Testing: Business Hours Validation, New Services API, Service Pricing, Duration Calculation")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        print("\n🆕 Testing New Services API:")
        self.test_new_services_api()
        
        print("\n⏰ Testing Business Hours Validation (6:00 PM Rules):")
        self.test_business_hours_validation_6pm_exact()
        
        print("\n💰 Testing Service Pricing for New Services:")
        self.test_service_pricing_new_services()
        
        print("\n⏱️ Testing Duration Calculation:")
        self.test_duration_calculation_new_services()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Review Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All review tests passed!")
            return True
        else:
            print("⚠️ Some review tests failed - check details above")
            return False

def main():
    tester = ReviewFocusedTester()
    success = tester.run_review_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())