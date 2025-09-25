#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class SessionNotesAPITester:
    def __init__(self, base_url="https://astro-booking-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.client_token = None
        self.admin_token = None
        self.client_user_id = None
        self.admin_user_id = None
        self.session_id = None
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
        
        # Use provided token or default client token
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

    def setup_test_users(self):
        """Setup client and admin users for testing"""
        print("🔧 Setting up test users...")
        
        # Register client user
        client_email = f"client_notes_{datetime.now().strftime('%H%M%S')}@celestia.com"
        client_data = {
            "name": "Notes Test Client",
            "email": client_email,
            "password": "ClientPass123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', client_data, 200)
        if success and 'access_token' in response:
            self.client_token = response['access_token']
            self.client_user_id = response['user']['id']
            self.log_test("Client User Setup", True, f"Client registered: {client_email}")
        else:
            self.log_test("Client User Setup", False, "Failed to register client", response)
            return False

        # Try to get admin user (should already exist)
        admin_login_data = {
            "email": "lago.mistico11@gmail.com",
            "password": "CelestiaAdmin2024!"
        }
        
        success, response = self.make_request('POST', 'auth/login', admin_login_data, 200)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            self.log_test("Admin User Setup", True, f"Admin logged in: {response['user']['email']}")
        else:
            # Try to create admin if login fails
            success, response = self.make_request('POST', 'admin/create-admin', None, 200)
            if success:
                # Try login again
                success, response = self.make_request('POST', 'auth/login', admin_login_data, 200)
                if success and 'access_token' in response:
                    self.admin_token = response['access_token']
                    self.admin_user_id = response['user']['id']
                    self.log_test("Admin User Setup", True, f"Admin created and logged in")
                else:
                    self.log_test("Admin User Setup", False, "Failed to login after admin creation", response)
                    return False
            else:
                self.log_test("Admin User Setup", False, "Failed to create admin", response)
                return False
        
        return True

    def test_session_creation_with_exact_time(self):
        """Test creating session at exactly 10:00 AM and verify time storage"""
        print("\n⏰ Testing Session Creation with Exact Time (10:00 AM)...")
        
        # Create session at exactly 10:00 AM tomorrow
        tomorrow = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end_time = tomorrow + timedelta(minutes=45)  # 45-minute session
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": tomorrow.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing exact 10:00 AM time storage"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            stored_start_time = response.get('start_at')
            stored_end_time = response.get('end_at')
            
            # Parse stored time and check if it matches 10:00 AM
            if stored_start_time:
                stored_datetime = datetime.fromisoformat(stored_start_time.replace('Z', '+00:00'))
                stored_hour = stored_datetime.hour
                stored_minute = stored_datetime.minute
                
                if stored_hour == 10 and stored_minute == 0:
                    self.log_test("Session Time Storage (10:00 AM)", True, 
                                f"Time correctly stored as 10:00 AM (hour: {stored_hour}, minute: {stored_minute})")
                else:
                    self.log_test("Session Time Storage (10:00 AM)", False, 
                                f"Time incorrectly stored - expected 10:00, got {stored_hour:02d}:{stored_minute:02d}")
            else:
                self.log_test("Session Time Storage (10:00 AM)", False, "No start_at time in response")
            
            # Verify session details include all required fields
            required_fields = ['id', 'start_at', 'end_at', 'service_type', 'amount', 'status', 'client_id']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_test("Session Required Fields", True, 
                            f"All required fields present: {', '.join(required_fields)}")
            else:
                self.log_test("Session Required Fields", False, 
                            f"Missing fields: {', '.join(missing_fields)}")
            
            return True
        else:
            self.log_test("Session Creation (10:00 AM)", False, "Failed to create session", response)
            return False

    def test_session_retrieval_time_display(self):
        """Test retrieving session and verify time is still 10:00 AM (not 3:00 PM)"""
        if not self.session_id:
            self.log_test("Session Time Retrieval", False, "No session ID available")
            return False
        
        print("\n🔍 Testing Session Time Retrieval...")
        
        success, response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
        
        if success and 'start_at' in response:
            stored_start_time = response['start_at']
            stored_datetime = datetime.fromisoformat(stored_start_time.replace('Z', '+00:00'))
            stored_hour = stored_datetime.hour
            stored_minute = stored_datetime.minute
            
            # Check if time is still 10:00 AM (not 3:00 PM which would be hour 15)
            if stored_hour == 10 and stored_minute == 0:
                self.log_test("Session Time Retrieval (10:00 AM)", True, 
                            f"Time correctly retrieved as 10:00 AM (not 3:00 PM)")
            elif stored_hour == 15:  # 3:00 PM
                self.log_test("Session Time Retrieval (10:00 AM)", False, 
                            f"❌ BUG CONFIRMED: Time showing as 3:00 PM instead of 10:00 AM")
            else:
                self.log_test("Session Time Retrieval (10:00 AM)", False, 
                            f"Unexpected time: {stored_hour:02d}:{stored_minute:02d}")
            
            return True
        else:
            self.log_test("Session Time Retrieval", False, "Failed to retrieve session", response)
            return False

    def test_personal_notes_creation(self):
        """Test creating personal notes for a session"""
        if not self.session_id:
            self.log_test("Personal Notes Creation", False, "No session ID available")
            return False
        
        print("\n📝 Testing Personal Notes Creation...")
        
        # Create personal note as client - note_content is a query parameter
        note_content = "This is my personal note about the upcoming session. I'm looking forward to insights about my career path."
        
        success, response = self.make_request('POST', f'sessions/{self.session_id}/personal-notes?note_content={note_content}', 
                                            None, 200)
        
        if success and 'message' in response:
            self.log_test("Personal Notes Creation", True, 
                        f"Personal note created successfully: {response['message']}")
            return True
        else:
            self.log_test("Personal Notes Creation", False, "Failed to create personal note", response)
            return False

    def test_mistica_notes_creation(self):
        """Test creating Mistica notes for admin users"""
        if not self.session_id or not self.admin_token:
            self.log_test("Mistica Notes Creation", False, "No session ID or admin token available")
            return False
        
        print("\n🔮 Testing Mistica Notes Creation (Admin)...")
        
        # Create Mistica note as admin - parameters are query parameters
        note_content = "Mistica's insights: The client's energy suggests a strong focus on career transformation. Recommend exploring Jupiter transits in their 10th house."
        
        success, response = self.make_request('POST', f'sessions/{self.session_id}/mistica-notes?note_content={note_content}&is_visible_to_client=true', 
                                            None, 200, self.admin_token)
        
        if success and 'message' in response:
            self.log_test("Mistica Notes Creation (Admin)", True, 
                        f"Mistica note created successfully: {response['message']}")
            
            # Test creating private Mistica note (not visible to client)
            private_note_content = "Private admin note: Client seems anxious about career change. Approach with gentle guidance."
            
            success2, response2 = self.make_request('POST', f'sessions/{self.session_id}/mistica-notes?note_content={private_note_content}&is_visible_to_client=false', 
                                                  None, 200, self.admin_token)
            
            if success2:
                self.log_test("Mistica Private Notes Creation", True, "Private Mistica note created")
            else:
                self.log_test("Mistica Private Notes Creation", False, "Failed to create private note", response2)
            
            return True
        else:
            self.log_test("Mistica Notes Creation (Admin)", False, "Failed to create Mistica note", response)
            return False

    def test_session_notes_retrieval_client(self):
        """Test retrieving session notes as client"""
        if not self.session_id:
            self.log_test("Session Notes Retrieval (Client)", False, "No session ID available")
            return False
        
        print("\n👤 Testing Session Notes Retrieval (Client View)...")
        
        success, response = self.make_request('GET', f'sessions/{self.session_id}/notes', None, 200)
        
        if success:
            personal_notes = response.get('personal_notes', [])
            mistica_notes = response.get('mistica_notes', [])
            
            # Check if personal notes are visible
            if personal_notes:
                self.log_test("Personal Notes Visibility (Client)", True, 
                            f"Client can see {len(personal_notes)} personal note(s)")
            else:
                self.log_test("Personal Notes Visibility (Client)", False, 
                            "Client cannot see personal notes")
            
            # Check if Mistica notes are visible (only public ones)
            visible_mistica_notes = [note for note in mistica_notes if note.get('is_visible_to_client', True)]
            private_mistica_notes = [note for note in mistica_notes if not note.get('is_visible_to_client', True)]
            
            if visible_mistica_notes:
                self.log_test("Mistica Notes Visibility (Client)", True, 
                            f"Client can see {len(visible_mistica_notes)} Mistica note(s)")
            else:
                self.log_test("Mistica Notes Visibility (Client)", False, 
                            "Client cannot see any Mistica notes")
            
            # Verify client cannot see private Mistica notes
            if not private_mistica_notes:
                self.log_test("Mistica Private Notes Security", True, 
                            "Client correctly cannot see private Mistica notes")
            else:
                self.log_test("Mistica Private Notes Security", False, 
                            f"❌ SECURITY ISSUE: Client can see {len(private_mistica_notes)} private note(s)")
            
            return True
        else:
            self.log_test("Session Notes Retrieval (Client)", False, "Failed to retrieve session notes", response)
            return False

    def test_session_notes_retrieval_admin(self):
        """Test retrieving session notes as admin"""
        if not self.session_id or not self.admin_token:
            self.log_test("Session Notes Retrieval (Admin)", False, "No session ID or admin token available")
            return False
        
        print("\n👑 Testing Session Notes Retrieval (Admin View)...")
        
        success, response = self.make_request('GET', f'sessions/{self.session_id}/notes', None, 200, self.admin_token)
        
        if success:
            personal_notes = response.get('personal_notes', [])
            mistica_notes = response.get('mistica_notes', [])
            
            # Admin should see all notes
            if personal_notes:
                self.log_test("Personal Notes Visibility (Admin)", True, 
                            f"Admin can see {len(personal_notes)} personal note(s)")
            else:
                self.log_test("Personal Notes Visibility (Admin)", False, 
                            "Admin cannot see personal notes")
            
            if mistica_notes:
                # Count public and private notes
                public_notes = [note for note in mistica_notes if note.get('is_visible_to_client', True)]
                private_notes = [note for note in mistica_notes if not note.get('is_visible_to_client', True)]
                
                self.log_test("Mistica Notes Visibility (Admin)", True, 
                            f"Admin can see {len(mistica_notes)} total Mistica notes ({len(public_notes)} public, {len(private_notes)} private)")
            else:
                self.log_test("Mistica Notes Visibility (Admin)", False, 
                            "Admin cannot see Mistica notes")
            
            return True
        else:
            self.log_test("Session Notes Retrieval (Admin)", False, "Failed to retrieve session notes as admin", response)
            return False

    def test_session_notes_api_endpoint(self):
        """Test the specific /sessions/{session_id}/notes endpoint functionality"""
        if not self.session_id:
            self.log_test("Session Notes API Endpoint", False, "No session ID available")
            return False
        
        print("\n🔗 Testing Session Notes API Endpoint...")
        
        # Test endpoint exists and returns proper structure
        success, response = self.make_request('GET', f'sessions/{self.session_id}/notes', None, 200)
        
        if success:
            # Check response structure
            required_keys = ['personal_notes', 'mistica_notes']
            missing_keys = [key for key in required_keys if key not in response]
            
            if not missing_keys:
                self.log_test("Session Notes API Structure", True, 
                            "API returns correct structure with personal_notes and mistica_notes")
                
                # Check if notes are properly formatted
                personal_notes = response.get('personal_notes', [])
                mistica_notes = response.get('mistica_notes', [])
                
                # Validate personal notes structure
                if personal_notes:
                    first_personal = personal_notes[0]
                    personal_required = ['id', 'session_id', 'user_id', 'note_content', 'created_at']
                    personal_missing = [field for field in personal_required if field not in first_personal]
                    
                    if not personal_missing:
                        self.log_test("Personal Notes Structure", True, 
                                    "Personal notes have all required fields")
                    else:
                        self.log_test("Personal Notes Structure", False, 
                                    f"Personal notes missing fields: {personal_missing}")
                
                # Validate Mistica notes structure
                if mistica_notes:
                    first_mistica = mistica_notes[0]
                    mistica_required = ['id', 'session_id', 'client_id', 'admin_id', 'note_content', 'is_visible_to_client', 'created_at']
                    mistica_missing = [field for field in mistica_required if field not in first_mistica]
                    
                    if not mistica_missing:
                        self.log_test("Mistica Notes Structure", True, 
                                    "Mistica notes have all required fields")
                    else:
                        self.log_test("Mistica Notes Structure", False, 
                                    f"Mistica notes missing fields: {mistica_missing}")
                
                return True
            else:
                self.log_test("Session Notes API Structure", False, 
                            f"API response missing keys: {missing_keys}")
                return False
        else:
            self.log_test("Session Notes API Endpoint", False, "Session notes endpoint not working", response)
            return False

    def test_dashboard_stats_clickable(self):
        """Test if dashboard stats are properly returned for clickable functionality"""
        if not self.admin_token:
            self.log_test("Dashboard Stats (Admin)", False, "No admin token available")
            return False
        
        print("\n📊 Testing Dashboard Stats for Clickable Functionality...")
        
        # Test admin dashboard stats
        success, response = self.make_request('GET', 'admin/dashboard-stats', None, 200, self.admin_token)
        
        if success:
            required_stats = ['total_users', 'total_clients', 'total_sessions', 'confirmed_sessions', 'pending_sessions', 'total_revenue']
            missing_stats = [stat for stat in required_stats if stat not in response]
            
            if not missing_stats:
                stats_summary = {key: response[key] for key in required_stats}
                self.log_test("Admin Dashboard Stats", True, 
                            f"All dashboard stats available: {stats_summary}")
            else:
                self.log_test("Admin Dashboard Stats", False, 
                            f"Missing dashboard stats: {missing_stats}")
            
            return True
        else:
            self.log_test("Admin Dashboard Stats", False, "Failed to retrieve dashboard stats", response)
            return False

    def run_session_notes_tests(self):
        """Run all session notes and time display tests"""
        print("🌟 Starting Session Notes & Time Display Tests...")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_users():
            print("❌ User setup failed - stopping tests")
            return False
        
        # Core tests based on review request
        print("\n⏰ Time Display Tests:")
        self.test_session_creation_with_exact_time()
        self.test_session_retrieval_time_display()
        
        print("\n📝 Session Notes System Tests:")
        self.test_personal_notes_creation()
        self.test_mistica_notes_creation()
        self.test_session_notes_retrieval_client()
        self.test_session_notes_retrieval_admin()
        self.test_session_notes_api_endpoint()
        
        print("\n📊 Dashboard Tests:")
        self.test_dashboard_stats_clickable()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Specific findings
        print("\n🔍 SPECIFIC FINDINGS:")
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test['details']}")
        else:
            print("✅ All tests passed!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SessionNotesAPITester()
    success = tester.run_session_notes_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/session_notes_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: /app/session_notes_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())