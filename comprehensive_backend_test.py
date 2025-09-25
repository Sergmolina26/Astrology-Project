#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://astro-booking-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.client_token = None
        self.admin_token = None
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

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200, token: str = None) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        auth_token = token or self.client_token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

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

    def setup_users(self):
        """Setup test users"""
        # Register client
        client_email = f"comprehensive_client_{datetime.now().strftime('%H%M%S')}@celestia.com"
        client_data = {
            "name": "Comprehensive Test Client",
            "email": client_email,
            "password": "ClientPass123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', client_data, 200)
        if success and 'access_token' in response:
            self.client_token = response['access_token']
            self.client_user_id = response['user']['id']
            self.log_test("Client Setup", True, f"Client registered: {client_email}")
        else:
            self.log_test("Client Setup", False, "Failed to register client", response)
            return False

        # Login admin
        admin_login_data = {
            "email": "lago.mistico11@gmail.com",
            "password": "CelestiaAdmin2024!"
        }
        
        success, response = self.make_request('POST', 'auth/login', admin_login_data, 200)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            self.log_test("Admin Setup", True, "Admin logged in")
        else:
            self.log_test("Admin Setup", False, "Failed to login admin", response)
            return False
        
        return True

    def test_services_endpoint(self):
        """Test services endpoint returns correct data"""
        success, response = self.make_request('GET', 'services', None, 200)
        
        if success and 'services' in response:
            services = response['services']
            expected_services = ['general-purpose-reading', 'astrological-tarot-session', 'birth-chart-reading', 'follow-up']
            
            service_ids = [service['id'] for service in services]
            missing_services = [svc for svc in expected_services if svc not in service_ids]
            
            if not missing_services:
                # Check pricing
                pricing_correct = True
                pricing_details = []
                for service in services:
                    if service['id'] == 'general-purpose-reading' and service['price'] != 65.0:
                        pricing_correct = False
                    elif service['id'] == 'astrological-tarot-session' and service['price'] != 85.0:
                        pricing_correct = False
                    pricing_details.append(f"{service['id']}: ${service['price']}")
                
                if pricing_correct:
                    self.log_test("Services Endpoint", True, f"All services available with correct pricing: {', '.join(pricing_details)}")
                else:
                    self.log_test("Services Endpoint", False, f"Incorrect pricing: {', '.join(pricing_details)}")
            else:
                self.log_test("Services Endpoint", False, f"Missing services: {missing_services}")
        else:
            self.log_test("Services Endpoint", False, "Failed to get services", response)

    def test_business_hours_validation(self):
        """Test business hours validation"""
        # Test session ending after 6 PM (should fail)
        tomorrow = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0) + timedelta(days=1)
        end_time = tomorrow + timedelta(hours=1)  # Ends at 6:30 PM
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": tomorrow.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing business hours validation"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if not success and 'must conclude by 6:00 PM' in str(response):
            self.log_test("Business Hours Validation (After 6 PM)", True, "Correctly rejected session ending after 6 PM")
        else:
            self.log_test("Business Hours Validation (After 6 PM)", False, "Failed to reject session ending after 6 PM", response)
        
        # Test session ending exactly at 6 PM (should succeed)
        tomorrow_6pm = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end_time_6pm = tomorrow_6pm + timedelta(hours=1)  # Ends at 6:00 PM
        
        session_data_6pm = {
            "service_type": "general-purpose-reading",
            "start_at": tomorrow_6pm.isoformat(),
            "end_at": end_time_6pm.isoformat(),
            "client_message": "Testing 6 PM boundary"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data_6pm, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            self.log_test("Business Hours Validation (At 6 PM)", True, "Correctly accepted session ending at 6 PM")
        else:
            self.log_test("Business Hours Validation (At 6 PM)", False, "Failed to accept session ending at 6 PM", response)

    def test_session_duration_calculation(self):
        """Test session duration calculations for different services"""
        # Test 45-minute service
        start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=2)
        end_time = start_time + timedelta(minutes=45)
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 45-minute duration"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success:
            stored_start = datetime.fromisoformat(response['start_at'].replace('Z', '+00:00'))
            stored_end = datetime.fromisoformat(response['end_at'].replace('Z', '+00:00'))
            duration_minutes = (stored_end - stored_start).total_seconds() / 60
            
            if duration_minutes == 45:
                self.log_test("Duration Calculation (45 min)", True, f"Correct 45-minute duration calculated")
            else:
                self.log_test("Duration Calculation (45 min)", False, f"Incorrect duration: {duration_minutes} minutes")
        else:
            self.log_test("Duration Calculation (45 min)", False, "Failed to create 45-minute session", response)

    def test_admin_sessions_list(self):
        """Test admin sessions list endpoint"""
        if not self.admin_token:
            self.log_test("Admin Sessions List", False, "No admin token available")
            return
        
        success, response = self.make_request('GET', 'admin/sessions', None, 200, self.admin_token)
        
        if success and isinstance(response, list):
            # Check if sessions have required fields and no ObjectId issues
            if response:
                first_session = response[0]
                required_fields = ['id', 'start_at', 'end_at', 'service_type', 'status']
                missing_fields = [field for field in required_fields if field not in first_session]
                
                if not missing_fields:
                    self.log_test("Admin Sessions List", True, f"Retrieved {len(response)} sessions with all required fields")
                else:
                    self.log_test("Admin Sessions List", False, f"Sessions missing fields: {missing_fields}")
            else:
                self.log_test("Admin Sessions List", True, "Admin sessions endpoint working (no sessions found)")
        else:
            self.log_test("Admin Sessions List", False, "Failed to retrieve admin sessions", response)

    def test_reader_dashboard_access(self):
        """Test reader dashboard access for admin users"""
        if not self.admin_token:
            self.log_test("Reader Dashboard Access", False, "No admin token available")
            return
        
        success, response = self.make_request('GET', 'reader/dashboard', None, 200, self.admin_token)
        
        if success and 'stats' in response and 'sessions' in response:
            stats = response['stats']
            sessions = response['sessions']
            
            # Check if sessions are properly serialized (no ObjectId issues)
            if sessions and isinstance(sessions, list):
                first_session = sessions[0]
                if '_id' not in first_session:
                    self.log_test("Reader Dashboard Access", True, f"Admin can access reader dashboard with {len(sessions)} sessions")
                else:
                    self.log_test("Reader Dashboard Access", False, "Sessions contain MongoDB _id field")
            else:
                self.log_test("Reader Dashboard Access", True, "Admin can access reader dashboard (no sessions)")
        else:
            self.log_test("Reader Dashboard Access", False, "Failed to access reader dashboard", response)

    def test_time_storage_consistency(self):
        """Test time storage and retrieval consistency"""
        if not hasattr(self, 'session_id'):
            self.log_test("Time Storage Consistency", False, "No session available for testing")
            return
        
        # Get the session we created earlier
        success, response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
        
        if success:
            start_time = response.get('start_at')
            end_time = response.get('end_at')
            
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # Check if times are consistent (end time should be after start time)
                if end_dt > start_dt:
                    duration = (end_dt - start_dt).total_seconds() / 60
                    self.log_test("Time Storage Consistency", True, f"Times consistent: {duration} minute duration")
                else:
                    self.log_test("Time Storage Consistency", False, "End time is not after start time")
            else:
                self.log_test("Time Storage Consistency", False, "Missing time fields in session")
        else:
            self.log_test("Time Storage Consistency", False, "Failed to retrieve session for time test", response)

    def run_comprehensive_tests(self):
        """Run comprehensive backend tests"""
        print("🌟 Starting Comprehensive Backend Tests...")
        print("=" * 60)
        
        # Setup
        if not self.setup_users():
            print("❌ User setup failed - stopping tests")
            return False
        
        print("\n🔧 Core API Tests:")
        self.test_services_endpoint()
        
        print("\n⏰ Business Logic Tests:")
        self.test_business_hours_validation()
        self.test_session_duration_calculation()
        self.test_time_storage_consistency()
        
        print("\n👑 Admin Features Tests:")
        self.test_admin_sessions_list()
        self.test_reader_dashboard_access()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Specific findings
        print("\n🔍 FINDINGS:")
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test['details']}")
        else:
            print("✅ All comprehensive tests passed!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/comprehensive_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: /app/comprehensive_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())