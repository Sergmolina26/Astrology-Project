#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AdminCRUDTester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.admin_user_id = None
        self.client_token = None
        self.client_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.test_session_id = None
        self.test_client_id = None
        self.test_chart_id = None

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

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200, use_admin_token: bool = True) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Choose token based on parameter
        token = self.admin_token if use_admin_token else self.client_token
        if token:
            headers['Authorization'] = f'Bearer {token}'

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

    def test_admin_login(self):
        """Test admin user login"""
        login_data = {
            "email": "lago.mistico11@gmail.com",
            "password": "CelestiaAdmin2024!"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200, use_admin_token=False)
        
        if success and 'access_token' in response and response.get('user', {}).get('role') == 'admin':
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            self.log_test("Admin Login", True, f"Admin logged in: {response['user']['email']}")
            return True
        else:
            self.log_test("Admin Login", False, "Failed to login as admin", response)
            return False

    def test_create_test_client(self):
        """Create a test client for CRUD operations"""
        test_email = f"test_client_{datetime.now().strftime('%H%M%S')}@celestia.com"
        client_data = {
            "name": "Test Client for CRUD",
            "email": test_email,
            "password": "TestClient123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', client_data, 200, use_admin_token=False)
        
        if success and 'access_token' in response:
            self.client_token = response['access_token']
            self.client_user_id = response['user']['id']
            self.log_test("Create Test Client", True, f"Test client created: {test_email}")
            return True
        else:
            self.log_test("Create Test Client", False, "Failed to create test client", response)
            return False

    def test_create_test_data(self):
        """Create test data (session, birth chart) for CRUD operations"""
        # Create birth data first
        birth_data = {
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "time_accuracy": "exact",
            "birth_place": "New York, NY",
            "latitude": "40.7128",
            "longitude": "-74.0060"
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200, use_admin_token=False)
        
        if success and 'id' in response:
            birth_data_id = response['id']
            
            # Generate astrology chart
            success2, response2 = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200, use_admin_token=False)
            
            if success2 and 'id' in response2:
                self.test_chart_id = response2['id']
                self.log_test("Create Test Chart", True, f"Test chart created: {self.test_chart_id}")
            else:
                self.log_test("Create Test Chart", False, "Failed to create test chart", response2)
            
            # Create session using admin
            start_time = datetime.now() + timedelta(days=1)
            end_time = start_time + timedelta(hours=1)
            
            session_data = {
                "service_type": "general-purpose-reading",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": "Test session for CRUD operations",
                "client_email": "test_client_" + datetime.now().strftime('%H%M%S') + "@celestia.com"
            }
            
            # First create the session as client
            session_data_client = {
                "service_type": "general-purpose-reading",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": "Test session for CRUD operations"
            }
            
            success3, response3 = self.make_request('POST', 'sessions', session_data_client, 200, use_admin_token=False)
            
            if success3 and 'id' in response3:
                self.test_session_id = response3['id']
                self.log_test("Create Test Session", True, f"Test session created: {self.test_session_id}")
                return True
            else:
                self.log_test("Create Test Session", False, "Failed to create test session", response3)
                return False
        else:
            self.log_test("Create Test Birth Data", False, "Failed to create test birth data", response)
            return False

    # ==================== SESSION CRUD TESTS ====================
    
    def test_admin_get_sessions(self):
        """Test GET /api/admin/sessions"""
        success, response = self.make_request('GET', 'admin/sessions', None, 200)
        
        if success and isinstance(response, list):
            session_count = len(response)
            self.log_test("Admin Get All Sessions", True, f"Retrieved {session_count} sessions")
            
            # Verify session structure
            if session_count > 0:
                session = response[0]
                required_fields = ['id', 'client_id', 'service_type', 'start_at', 'status']
                has_required_fields = all(field in session for field in required_fields)
                
                if has_required_fields:
                    self.log_test("Session Data Structure", True, "Sessions have required fields")
                else:
                    missing_fields = [field for field in required_fields if field not in session]
                    self.log_test("Session Data Structure", False, f"Missing fields: {missing_fields}")
            
            return True
        else:
            self.log_test("Admin Get All Sessions", False, "Failed to retrieve sessions", response)
            return False

    def test_admin_create_session(self):
        """Test POST /api/admin/sessions"""
        if not self.client_user_id:
            self.log_test("Admin Create Session", False, "No test client available")
            return False
            
        # Get client email
        success_client, client_response = self.make_request('GET', 'auth/me', None, 200, use_admin_token=False)
        if not success_client:
            self.log_test("Admin Create Session - Get Client", False, "Failed to get client info")
            return False
            
        client_email = client_response['email']
        
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            "service_type": "astrological-tarot-session",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Admin created session",
            "client_email": client_email,
            "status": "confirmed"
        }
        
        success, response = self.make_request('POST', 'admin/sessions', session_data, 200)
        
        if success and 'id' in response:
            admin_created_session_id = response['id']
            self.log_test("Admin Create Session", True, f"Admin created session: {admin_created_session_id}")
            
            # Verify session was created with correct data
            if response.get('service_type') == 'astrological-tarot-session' and response.get('status') == 'confirmed':
                self.log_test("Admin Session Data Verification", True, "Session created with correct data")
            else:
                self.log_test("Admin Session Data Verification", False, "Session data mismatch")
            
            return True
        else:
            self.log_test("Admin Create Session", False, "Failed to create session", response)
            return False

    def test_admin_update_session(self):
        """Test PUT /api/admin/sessions/{session_id}"""
        if not self.test_session_id:
            self.log_test("Admin Update Session", False, "No test session available")
            return False
            
        update_data = {
            "status": "confirmed",
            "client_message": "Updated by admin",
            "notes": "Admin updated this session"
        }
        
        success, response = self.make_request('PUT', f'admin/sessions/{self.test_session_id}', update_data, 200)
        
        if success and 'id' in response:
            # Verify updates were applied
            if response.get('status') == 'confirmed' and response.get('notes') == 'Admin updated this session':
                self.log_test("Admin Update Session", True, f"Session updated successfully: {self.test_session_id}")
                return True
            else:
                self.log_test("Admin Update Session", False, "Session update data mismatch", response)
                return False
        else:
            self.log_test("Admin Update Session", False, "Failed to update session", response)
            return False

    def test_admin_delete_session(self):
        """Test DELETE /api/admin/sessions/{session_id}"""
        # Create a session specifically for deletion
        start_time = datetime.now() + timedelta(days=3)
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            "service_type": "follow-up",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Session to be deleted"
        }
        
        success_create, create_response = self.make_request('POST', 'sessions', session_data, 200, use_admin_token=False)
        
        if not success_create:
            self.log_test("Admin Delete Session - Create", False, "Failed to create session for deletion")
            return False
            
        delete_session_id = create_response['id']
        
        # Now delete it as admin
        success, response = self.make_request('DELETE', f'admin/sessions/{delete_session_id}', None, 200)
        
        if success and 'message' in response:
            self.log_test("Admin Delete Session", True, f"Session deleted: {delete_session_id}")
            
            # Verify session is actually deleted
            success_verify, verify_response = self.make_request('GET', f'sessions/{delete_session_id}', None, 404, use_admin_token=False)
            
            if success_verify:  # 404 is expected
                self.log_test("Admin Delete Verification", True, "Session successfully deleted from database")
            else:
                self.log_test("Admin Delete Verification", False, "Session still exists after deletion")
            
            return True
        else:
            self.log_test("Admin Delete Session", False, "Failed to delete session", response)
            return False

    # ==================== CLIENT CRUD TESTS ====================
    
    def test_admin_get_clients(self):
        """Test GET /api/admin/clients"""
        success, response = self.make_request('GET', 'admin/clients', None, 200)
        
        if success and isinstance(response, list):
            client_count = len(response)
            self.log_test("Admin Get All Clients", True, f"Retrieved {client_count} clients")
            
            # Verify client structure
            if client_count > 0:
                client = response[0]
                required_fields = ['id', 'email', 'name', 'role']
                has_required_fields = all(field in client for field in required_fields)
                
                # Verify sensitive data is not included
                has_no_password = 'hashed_password' not in client
                
                if has_required_fields and has_no_password:
                    self.log_test("Client Data Structure", True, "Clients have required fields, no sensitive data")
                else:
                    issues = []
                    if not has_required_fields:
                        missing_fields = [field for field in required_fields if field not in client]
                        issues.append(f"Missing fields: {missing_fields}")
                    if not has_no_password:
                        issues.append("Contains sensitive password data")
                    self.log_test("Client Data Structure", False, "; ".join(issues))
            
            return True
        else:
            self.log_test("Admin Get All Clients", False, "Failed to retrieve clients", response)
            return False

    def test_admin_create_client(self):
        """Test POST /api/admin/clients"""
        test_email = f"admin_created_client_{datetime.now().strftime('%H%M%S')}@celestia.com"
        client_data = {
            "name": "Admin Created Client",
            "email": test_email,
            "password": "AdminClient123!",
            "phone": "+1234567890",
            "timezone": "America/New_York"
        }
        
        success, response = self.make_request('POST', 'admin/clients', client_data, 200)
        
        if success and 'id' in response:
            self.test_client_id = response['id']
            self.log_test("Admin Create Client", True, f"Admin created client: {test_email}")
            
            # Verify client data
            if response.get('role') == 'client' and response.get('email') == test_email:
                self.log_test("Admin Client Data Verification", True, "Client created with correct data")
            else:
                self.log_test("Admin Client Data Verification", False, "Client data mismatch")
            
            return True
        else:
            self.log_test("Admin Create Client", False, "Failed to create client", response)
            return False

    def test_admin_update_client(self):
        """Test PUT /api/admin/clients/{client_id}"""
        if not self.test_client_id:
            self.log_test("Admin Update Client", False, "No test client available")
            return False
            
        update_data = {
            "name": "Updated Client Name",
            "phone": "+9876543210",
            "timezone": "America/Los_Angeles"
        }
        
        success, response = self.make_request('PUT', f'admin/clients/{self.test_client_id}', update_data, 200)
        
        if success and 'id' in response:
            # Verify updates were applied
            if (response.get('name') == 'Updated Client Name' and 
                response.get('phone') == '+9876543210' and
                response.get('timezone') == 'America/Los_Angeles'):
                self.log_test("Admin Update Client", True, f"Client updated successfully: {self.test_client_id}")
                return True
            else:
                self.log_test("Admin Update Client", False, "Client update data mismatch", response)
                return False
        else:
            self.log_test("Admin Update Client", False, "Failed to update client", response)
            return False

    def test_admin_delete_client(self):
        """Test DELETE /api/admin/clients/{client_id}"""
        # Create a client specifically for deletion (without sessions)
        test_email = f"delete_client_{datetime.now().strftime('%H%M%S')}@celestia.com"
        client_data = {
            "name": "Client To Delete",
            "email": test_email,
            "password": "DeleteMe123!"
        }
        
        success_create, create_response = self.make_request('POST', 'admin/clients', client_data, 200)
        
        if not success_create:
            self.log_test("Admin Delete Client - Create", False, "Failed to create client for deletion")
            return False
            
        delete_client_id = create_response['id']
        
        # Delete the client
        success, response = self.make_request('DELETE', f'admin/clients/{delete_client_id}', None, 200)
        
        if success and 'message' in response:
            self.log_test("Admin Delete Client", True, f"Client deleted: {delete_client_id}")
            
            # Verify client is actually deleted by trying to get all clients
            success_verify, verify_response = self.make_request('GET', 'admin/clients', None, 200)
            
            if success_verify:
                client_exists = any(client['id'] == delete_client_id for client in verify_response)
                if not client_exists:
                    self.log_test("Admin Delete Client Verification", True, "Client successfully deleted from database")
                else:
                    self.log_test("Admin Delete Client Verification", False, "Client still exists after deletion")
            
            return True
        else:
            self.log_test("Admin Delete Client", False, "Failed to delete client", response)
            return False

    # ==================== BIRTH CHART CRUD TESTS ====================
    
    def test_admin_get_charts(self):
        """Test GET /api/admin/charts"""
        success, response = self.make_request('GET', 'admin/charts', None, 200)
        
        if success and isinstance(response, list):
            chart_count = len(response)
            self.log_test("Admin Get All Charts", True, f"Retrieved {chart_count} charts")
            
            # Verify chart structure
            if chart_count > 0:
                chart = response[0]
                required_fields = ['id', 'client_id', 'chart_type', 'birth_data']
                has_required_fields = all(field in chart for field in required_fields)
                
                if has_required_fields:
                    self.log_test("Chart Data Structure", True, "Charts have required fields")
                else:
                    missing_fields = [field for field in required_fields if field not in chart]
                    self.log_test("Chart Data Structure", False, f"Missing fields: {missing_fields}")
            
            return True
        else:
            self.log_test("Admin Get All Charts", False, "Failed to retrieve charts", response)
            return False

    def test_admin_update_chart(self):
        """Test PUT /api/admin/charts/{chart_id}"""
        if not self.test_chart_id:
            self.log_test("Admin Update Chart", False, "No test chart available")
            return False
            
        update_data = {
            "chart_type": "transit",
            "notes": "Updated by admin for testing"
        }
        
        success, response = self.make_request('PUT', f'admin/charts/{self.test_chart_id}', update_data, 200)
        
        if success and 'id' in response:
            # Verify updates were applied
            if response.get('chart_type') == 'transit':
                self.log_test("Admin Update Chart", True, f"Chart updated successfully: {self.test_chart_id}")
                return True
            else:
                self.log_test("Admin Update Chart", False, "Chart update data mismatch", response)
                return False
        else:
            self.log_test("Admin Update Chart", False, "Failed to update chart", response)
            return False

    def test_admin_delete_chart(self):
        """Test DELETE /api/admin/charts/{chart_id}"""
        # Create a chart specifically for deletion
        birth_data = {
            "birth_date": "1985-12-25",
            "birth_time": "10:00",
            "time_accuracy": "exact",
            "birth_place": "Los Angeles, CA",
            "latitude": "34.0522",
            "longitude": "-118.2437"
        }
        
        success_birth, birth_response = self.make_request('POST', 'birth-data', birth_data, 200, use_admin_token=False)
        
        if not success_birth:
            self.log_test("Admin Delete Chart - Create Birth Data", False, "Failed to create birth data")
            return False
            
        birth_data_id = birth_response['id']
        
        # Generate chart
        success_chart, chart_response = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200, use_admin_token=False)
        
        if not success_chart:
            self.log_test("Admin Delete Chart - Create Chart", False, "Failed to create chart for deletion")
            return False
            
        delete_chart_id = chart_response['id']
        
        # Delete the chart as admin
        success, response = self.make_request('DELETE', f'admin/charts/{delete_chart_id}', None, 200)
        
        if success and 'message' in response:
            self.log_test("Admin Delete Chart", True, f"Chart deleted: {delete_chart_id}")
            
            # Verify chart is actually deleted
            success_verify, verify_response = self.make_request('GET', 'admin/charts', None, 200)
            
            if success_verify:
                chart_exists = any(chart['id'] == delete_chart_id for chart in verify_response)
                if not chart_exists:
                    self.log_test("Admin Delete Chart Verification", True, "Chart successfully deleted from database")
                else:
                    self.log_test("Admin Delete Chart Verification", False, "Chart still exists after deletion")
            
            return True
        else:
            self.log_test("Admin Delete Chart", False, "Failed to delete chart", response)
            return False

    # ==================== ACCESS CONTROL TESTS ====================
    
    def test_access_control_non_admin(self):
        """Test that non-admin users cannot access admin endpoints"""
        if not self.client_token:
            self.log_test("Access Control Test", False, "No client token available")
            return False
            
        # Test various admin endpoints with client token
        admin_endpoints = [
            ('GET', 'admin/sessions'),
            ('GET', 'admin/clients'),
            ('GET', 'admin/charts'),
            ('POST', 'admin/sessions'),
            ('POST', 'admin/clients')
        ]
        
        access_denied_count = 0
        
        for method, endpoint in admin_endpoints:
            success, response = self.make_request(method, endpoint, {}, 403, use_admin_token=False)
            
            if success:  # 403 is expected
                access_denied_count += 1
            else:
                print(f"    ⚠️ {method} {endpoint} did not return 403: {response}")
        
        if access_denied_count == len(admin_endpoints):
            self.log_test("Access Control - Non-Admin Denied", True, f"All {access_denied_count} admin endpoints properly denied non-admin access")
            return True
        else:
            self.log_test("Access Control - Non-Admin Denied", False, f"Only {access_denied_count}/{len(admin_endpoints)} endpoints denied access")
            return False

    def test_access_control_admin_allowed(self):
        """Test that admin users can access admin endpoints"""
        if not self.admin_token:
            self.log_test("Access Control Admin Test", False, "No admin token available")
            return False
            
        # Test key admin endpoints with admin token
        admin_endpoints = [
            ('GET', 'admin/sessions'),
            ('GET', 'admin/clients'),
            ('GET', 'admin/charts')
        ]
        
        access_allowed_count = 0
        
        for method, endpoint in admin_endpoints:
            success, response = self.make_request(method, endpoint, None, 200, use_admin_token=True)
            
            if success:
                access_allowed_count += 1
            else:
                print(f"    ⚠️ {method} {endpoint} failed for admin: {response}")
        
        if access_allowed_count == len(admin_endpoints):
            self.log_test("Access Control - Admin Allowed", True, f"All {access_allowed_count} admin endpoints accessible to admin")
            return True
        else:
            self.log_test("Access Control - Admin Allowed", False, f"Only {access_allowed_count}/{len(admin_endpoints)} endpoints accessible")
            return False

    def run_all_tests(self):
        """Run all admin CRUD tests"""
        print("🔧 Starting Admin CRUD Operations Testing...")
        print("=" * 60)
        
        # Setup
        print("\n🔐 Authentication Setup:")
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return False
            
        if not self.test_create_test_client():
            print("❌ Test client creation failed - stopping tests")
            return False
            
        if not self.test_create_test_data():
            print("❌ Test data creation failed - some tests may fail")
        
        # Session CRUD Tests
        print("\n📅 SESSION CRUD OPERATIONS:")
        self.test_admin_get_sessions()
        self.test_admin_create_session()
        self.test_admin_update_session()
        self.test_admin_delete_session()
        
        # Client CRUD Tests
        print("\n👥 CLIENT CRUD OPERATIONS:")
        self.test_admin_get_clients()
        self.test_admin_create_client()
        self.test_admin_update_client()
        self.test_admin_delete_client()
        
        # Birth Chart CRUD Tests
        print("\n⭐ BIRTH CHART CRUD OPERATIONS:")
        self.test_admin_get_charts()
        self.test_admin_update_chart()
        self.test_admin_delete_chart()
        
        # Access Control Tests
        print("\n🔒 ACCESS CONTROL TESTS:")
        self.test_access_control_non_admin()
        self.test_access_control_admin_allowed()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All admin CRUD tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

    def save_results(self, filename: str = "/app/admin_crud_test_results.json"):
        """Save test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_details": self.test_results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Test results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to save results: {e}")

def main():
    tester = AdminCRUDTester()
    success = tester.run_all_tests()
    tester.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())