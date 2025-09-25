#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class DurationCalculationTester:
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
        test_email = f"duration_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Duration Test User",
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

    def test_service_removal(self):
        """Test that 'chart-tarot-combo' service is no longer available"""
        success, response = self.make_request('GET', 'services', None, 200)
        
        if success and 'services' in response:
            services = response['services']
            service_ids = [service['id'] for service in services]
            
            # Check that chart-tarot-combo is NOT in the services
            if 'chart-tarot-combo' not in service_ids:
                self.log_test("Service Removal - chart-tarot-combo", True, 
                             f"chart-tarot-combo service successfully removed. Available services: {service_ids}")
                return True
            else:
                self.log_test("Service Removal - chart-tarot-combo", False, 
                             f"chart-tarot-combo service still exists in services list: {service_ids}")
                return False
        else:
            self.log_test("Service Removal - chart-tarot-combo", False, 
                         "Failed to retrieve services", response)
            return False

    def test_general_purpose_reading_duration(self):
        """Test that general-purpose-reading has correct 45-minute duration"""
        success, response = self.make_request('GET', 'services', None, 200)
        
        if success and 'services' in response:
            services = response['services']
            
            # Find general-purpose-reading service
            general_service = None
            for service in services:
                if service['id'] == 'general-purpose-reading':
                    general_service = service
                    break
            
            if general_service:
                duration = general_service.get('duration', 0)
                price = general_service.get('price', 0)
                
                if duration == 45 and price == 65.0:
                    self.log_test("General Purpose Reading Service", True, 
                                 f"Service correctly configured: 45 minutes, $65")
                    return True
                else:
                    self.log_test("General Purpose Reading Service", False, 
                                 f"Incorrect configuration: {duration} minutes, ${price} (expected 45 min, $65)")
                    return False
            else:
                self.log_test("General Purpose Reading Service", False, 
                             "general-purpose-reading service not found in services list")
                return False
        else:
            self.log_test("General Purpose Reading Service", False, 
                         "Failed to retrieve services", response)
            return False

    def test_duration_calculation_fix(self):
        """Test that 45-minute session starting at 10:00 AM ends at 10:45 AM (not 3:45 PM)"""
        # Create a session starting at 10:00 AM tomorrow
        tomorrow = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # For 45-minute service, end time should be 10:45 AM
        expected_end_time = tomorrow + timedelta(minutes=45)
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": tomorrow.isoformat(),
            "end_at": expected_end_time.isoformat(),
            "client_message": "Testing duration calculation fix"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            start_at = datetime.fromisoformat(response['start_at'].replace('Z', '+00:00'))
            end_at = datetime.fromisoformat(response['end_at'].replace('Z', '+00:00'))
            
            # Calculate actual duration in minutes
            duration_delta = end_at - start_at
            duration_minutes = int(duration_delta.total_seconds() / 60)
            
            # Check if duration is correct (45 minutes)
            if duration_minutes == 45:
                # Check if end time is correct (10:45 AM, not 3:45 PM)
                if end_at.hour == 10 and end_at.minute == 45:
                    self.log_test("Duration Calculation Fix", True, 
                                 f"Correct calculation: 10:00 AM + 45 min = 10:45 AM (duration: {duration_minutes} min)")
                    return True
                else:
                    self.log_test("Duration Calculation Fix", False, 
                                 f"Wrong end time: expected 10:45 AM, got {end_at.strftime('%I:%M %p')} (duration: {duration_minutes} min)")
                    return False
            else:
                self.log_test("Duration Calculation Fix", False, 
                             f"Wrong duration: expected 45 minutes, got {duration_minutes} minutes")
                return False
        else:
            self.log_test("Duration Calculation Fix", False, 
                         "Failed to create session for duration test", response)
            return False

    def test_all_service_durations(self):
        """Test session creation with different services to ensure duration calculations work for all"""
        success, response = self.make_request('GET', 'services', None, 200)
        
        if not success or 'services' not in response:
            self.log_test("All Service Durations", False, "Failed to retrieve services", response)
            return False
        
        services = response['services']
        all_passed = True
        
        for service in services:
            service_id = service['id']
            expected_duration = service['duration']
            
            # Create session for this service
            tomorrow = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0) + timedelta(days=1)
            expected_end_time = tomorrow + timedelta(minutes=expected_duration)
            
            session_data = {
                "service_type": service_id,
                "start_at": tomorrow.isoformat(),
                "end_at": expected_end_time.isoformat(),
                "client_message": f"Testing {service_id} duration"
            }
            
            success_session, response_session = self.make_request('POST', 'sessions', session_data, 200)
            
            if success_session and 'id' in response_session:
                start_at = datetime.fromisoformat(response_session['start_at'].replace('Z', '+00:00'))
                end_at = datetime.fromisoformat(response_session['end_at'].replace('Z', '+00:00'))
                
                # Calculate actual duration
                duration_delta = end_at - start_at
                actual_duration = int(duration_delta.total_seconds() / 60)
                
                if actual_duration == expected_duration:
                    self.log_test(f"Duration Test - {service_id}", True, 
                                 f"Correct duration: {actual_duration} minutes")
                else:
                    self.log_test(f"Duration Test - {service_id}", False, 
                                 f"Wrong duration: expected {expected_duration}, got {actual_duration}")
                    all_passed = False
            else:
                self.log_test(f"Duration Test - {service_id}", False, 
                             f"Failed to create session for {service_id}", response_session)
                all_passed = False
        
        return all_passed

    def test_business_hours_validation(self):
        """Test that business hours validation still works correctly"""
        # Test session ending after 6 PM (should fail)
        tomorrow = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0) + timedelta(days=1)
        end_time = tomorrow + timedelta(minutes=45)  # Would end at 6:15 PM
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": tomorrow.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing business hours validation"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        # This should fail because it ends after 6 PM
        if not success and ('6:00 PM' in str(response) or 'business hours' in str(response).lower()):
            self.log_test("Business Hours Validation", True, 
                         "Correctly rejected session ending after 6:00 PM")
            return True
        else:
            self.log_test("Business Hours Validation", False, 
                         "Failed to reject session ending after 6:00 PM", response)
            return False

    def run_duration_tests(self):
        """Run all duration calculation and service removal tests"""
        print("🕐 Starting Duration Calculation & Service Removal Tests...")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        print("\n🔧 Testing Review Requirements:")
        
        # Test 1: Service removal
        print("\n1️⃣ Testing Service Removal:")
        self.test_service_removal()
        
        # Test 2: General purpose reading duration
        print("\n2️⃣ Testing General Purpose Reading Configuration:")
        self.test_general_purpose_reading_duration()
        
        # Test 3: Duration calculation fix
        print("\n3️⃣ Testing Duration Calculation Fix:")
        self.test_duration_calculation_fix()
        
        # Test 4: All service durations
        print("\n4️⃣ Testing All Service Durations:")
        self.test_all_service_durations()
        
        # Test 5: Business hours validation still works
        print("\n5️⃣ Testing Business Hours Validation:")
        self.test_business_hours_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All duration tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

def main():
    tester = DurationCalculationTester()
    success = tester.run_duration_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())