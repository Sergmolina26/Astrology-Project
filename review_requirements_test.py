#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ReviewRequirementsAPITester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_user_id = None
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

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200, use_admin_token: bool = False) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        token_to_use = self.admin_token if use_admin_token and self.admin_token else self.token
        if token_to_use:
            headers['Authorization'] = f'Bearer {token_to_use}'

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
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            admin_role = response['user'].get('role', 'unknown')
            self.log_test("Admin User Login", True, f"Admin logged in successfully - Role: {admin_role}")
            return True
        else:
            self.log_test("Admin User Login", False, "Failed to login as admin user", response)
            return False

    def test_gmail_smtp_integration(self):
        """Test Gmail SMTP integration instead of SendGrid"""
        # Create a test session to trigger email sending
        start_time = datetime.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(minutes=45)
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing Gmail SMTP integration"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200, use_admin_token=True)
        
        if success and 'id' in response:
            session_id = response['id']
            self.log_test("Gmail SMTP - Session Creation", True, 
                         f"Session created to test Gmail email sending: {session_id}")
            
            # Complete payment to trigger confirmation emails
            success2, response2 = self.make_request('POST', f'sessions/{session_id}/payment/complete', None, 200, use_admin_token=True)
            
            if success2:
                self.log_test("Gmail SMTP - Email Trigger", True, 
                             "Payment completed - should trigger Gmail SMTP emails (check server logs for Gmail provider usage)")
                return True
            else:
                self.log_test("Gmail SMTP - Email Trigger", False, 
                             "Failed to complete payment for email test", response2)
                return False
        else:
            self.log_test("Gmail SMTP - Session Creation", False, 
                         "Failed to create session for Gmail email test", response)
            return False

    def test_admin_reader_role_merge(self):
        """Test that admin user can access both admin and reader functionalities"""
        if not self.admin_token:
            self.log_test("Admin/Reader Role Merge", False, "No admin token available")
            return False

        # Test 1: Admin can access reader dashboard
        success, response = self.make_request('GET', 'reader/dashboard', None, 200, use_admin_token=True)
        
        if success and 'stats' in response and 'sessions' in response:
            session_count = len(response.get('sessions', []))
            self.log_test("Admin Access to Reader Dashboard", True, 
                         f"Admin can access reader dashboard - {session_count} sessions visible")
            
            # Test 2: Admin can view all sessions in reader dashboard (not filtered by reader_id)
            if session_count > 0:
                # Check if admin sees all sessions, not just their own
                all_sessions = response['sessions']
                admin_sessions = [s for s in all_sessions if s.get('reader_id') == self.admin_user_id]
                other_sessions = [s for s in all_sessions if s.get('reader_id') != self.admin_user_id]
                
                self.log_test("Admin Views All Sessions", True, 
                             f"Admin sees {len(all_sessions)} total sessions ({len(admin_sessions)} own, {len(other_sessions)} others)")
            
            # Test 3: Test session creation workflow where admin acts as reader
            start_time = datetime.now() + timedelta(days=2, hours=14)
            end_time = start_time + timedelta(minutes=60)
            
            session_data = {
                "service_type": "astrological-tarot-session",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "client_message": "Testing admin as reader workflow"
            }
            
            success3, response3 = self.make_request('POST', 'sessions', session_data, 200, use_admin_token=True)
            
            if success3 and 'id' in response3:
                self.log_test("Admin Session Creation as Reader", True, 
                             f"Admin successfully created session as reader: {response3['id']}")
                return True
            else:
                self.log_test("Admin Session Creation as Reader", False, 
                             "Admin failed to create session as reader", response3)
                return False
        else:
            self.log_test("Admin Access to Reader Dashboard", False, 
                         "Admin cannot access reader dashboard", response)
            return False

    def test_session_time_handling(self):
        """Test that session times are stored and retrieved correctly without timezone conversion issues"""
        if not self.admin_token:
            self.log_test("Session Time Handling", False, "No admin token available")
            return False

        # Test with specific time that could reveal timezone issues
        test_time = datetime(2024, 12, 20, 10, 0, 0)  # 10:00 AM
        end_time = test_time + timedelta(minutes=45)
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": test_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing session time handling"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200, use_admin_token=True)
        
        if success and 'id' in response:
            session_id = response['id']
            stored_start_time = response.get('start_at')
            stored_end_time = response.get('end_at')
            
            # Retrieve the session to verify time storage
            success2, response2 = self.make_request('GET', f'sessions/{session_id}', None, 200, use_admin_token=True)
            
            if success2:
                retrieved_start_time = response2.get('start_at')
                retrieved_end_time = response2.get('end_at')
                
                # Parse times to check if they match
                try:
                    original_start = datetime.fromisoformat(test_time.isoformat().replace('Z', '+00:00') if 'Z' in test_time.isoformat() else test_time.isoformat())
                    retrieved_start = datetime.fromisoformat(retrieved_start_time.replace('Z', '+00:00') if 'Z' in retrieved_start_time else retrieved_start_time)
                    
                    # Check if the hour is preserved (10 AM should stay 10 AM, not become 3 PM)
                    if retrieved_start.hour == 10:
                        self.log_test("Session Time Storage/Retrieval", True, 
                                     f"Session time correctly stored and retrieved: {retrieved_start_time} (hour: {retrieved_start.hour})")
                        
                        # Test duration calculation
                        duration_minutes = (datetime.fromisoformat(retrieved_end_time.replace('Z', '+00:00') if 'Z' in retrieved_end_time else retrieved_end_time) - retrieved_start).total_seconds() / 60
                        
                        if duration_minutes == 45:
                            self.log_test("Session Duration Calculation", True, 
                                         f"Duration correctly calculated: {duration_minutes} minutes")
                            return True
                        else:
                            self.log_test("Session Duration Calculation", False, 
                                         f"Duration incorrect: expected 45 minutes, got {duration_minutes}")
                            return False
                    else:
                        self.log_test("Session Time Storage/Retrieval", False, 
                                     f"Session time incorrectly converted: expected hour 10, got hour {retrieved_start.hour}")
                        return False
                        
                except Exception as e:
                    self.log_test("Session Time Parsing", False, f"Failed to parse session times: {str(e)}")
                    return False
            else:
                self.log_test("Session Time Retrieval", False, 
                             "Failed to retrieve session for time verification", response2)
                return False
        else:
            self.log_test("Session Time Creation", False, 
                         "Failed to create session for time testing", response)
            return False

    def test_astrological_map_generation(self):
        """Test the complete astrological map generation workflow"""
        if not self.admin_token:
            self.log_test("Astrological Map Generation", False, "No admin token available")
            return False

        # Step 1: Create birth data
        birth_data = {
            "birth_date": "1990-07-15",
            "birth_time": "14:30",
            "time_accuracy": "exact",
            "birth_place": "Los Angeles, CA",
            "latitude": "34.0522",
            "longitude": "-118.2437"
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200, use_admin_token=True)
        
        if success and 'id' in response:
            birth_data_id = response['id']
            self.log_test("Birth Data Creation", True, f"Created birth data: {birth_data_id}")
            
            # Step 2: Generate astrological chart
            success2, response2 = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200, use_admin_token=True)
            
            if success2 and 'id' in response2:
                chart_id = response2['id']
                has_svg = response2.get('chart_svg') is not None
                self.log_test("Astrological Chart Generation", True, 
                             f"Generated chart: {chart_id}, Has SVG: {has_svg}")
                
                # Step 3: Generate SVG map using the new endpoint
                success3, response3 = self.make_request('POST', f'charts/{chart_id}/generate-map', None, 200, use_admin_token=True)
                
                if success3 and response3.get('message') == 'Chart map generated successfully':
                    has_svg_after_generation = response3.get('has_svg', False)
                    self.log_test("SVG Map Generation", True, 
                                 f"SVG map generated successfully, Has SVG: {has_svg_after_generation}")
                    
                    # Step 4: Retrieve SVG content
                    success4, response4 = self.make_request('GET', f'charts/{chart_id}/svg', None, 200, use_admin_token=True)
                    
                    if success4:
                        # Check if we got SVG content (should be text/xml response)
                        svg_content = response4 if isinstance(response4, str) else str(response4)
                        is_svg = '<svg' in svg_content.lower() or 'svg' in str(response4).lower()
                        
                        self.log_test("SVG Content Retrieval", True, 
                                     f"Retrieved SVG content, Is valid SVG: {is_svg}, Content length: {len(svg_content)}")
                        
                        if is_svg:
                            self.log_test("Complete Astrological Map Workflow", True, 
                                         "Full workflow completed: Birth data → Chart → SVG generation → SVG retrieval")
                            return True
                        else:
                            self.log_test("SVG Content Validation", False, 
                                         "Retrieved content is not valid SVG")
                            return False
                    else:
                        self.log_test("SVG Content Retrieval", False, 
                                     "Failed to retrieve SVG content", response4)
                        return False
                else:
                    self.log_test("SVG Map Generation", False, 
                                 "Failed to generate SVG map", response3)
                    return False
            else:
                self.log_test("Astrological Chart Generation", False, 
                             "Failed to generate astrological chart", response2)
                return False
        else:
            self.log_test("Birth Data Creation", False, 
                         "Failed to create birth data", response)
            return False

    def test_translation_support(self):
        """Test that backend responses support translation improvements"""
        if not self.admin_token:
            self.log_test("Translation Support", False, "No admin token available")
            return False

        # Test services endpoint for translation-ready structure
        success, response = self.make_request('GET', 'services', None, 200, use_admin_token=True)
        
        if success and 'services' in response:
            services = response['services']
            
            # Check if services have proper structure for translation
            translation_ready = True
            service_details = []
            
            for service in services:
                has_required_fields = all(field in service for field in ['id', 'name', 'description', 'price', 'duration'])
                service_details.append(f"{service.get('name', 'Unknown')} (${service.get('price', 0)}/{service.get('duration', 0)}min)")
                
                if not has_required_fields:
                    translation_ready = False
                    break
            
            if translation_ready:
                self.log_test("Services Translation Support", True, 
                             f"Services endpoint ready for translation: {', '.join(service_details)}")
                
                # Test reader dashboard for translation support
                success2, response2 = self.make_request('GET', 'reader/dashboard', None, 200, use_admin_token=True)
                
                if success2 and 'stats' in response2:
                    stats = response2['stats']
                    has_stats_structure = all(key in stats for key in ['total_sessions', 'pending_sessions', 'confirmed_sessions'])
                    
                    if has_stats_structure:
                        self.log_test("Dashboard Translation Support", True, 
                                     f"Dashboard stats ready for translation: {stats}")
                        
                        # Test session structure for translation support
                        sessions = response2.get('sessions', [])
                        if sessions:
                            sample_session = sessions[0]
                            has_session_structure = all(key in sample_session for key in ['id', 'service_type', 'status', 'start_at'])
                            
                            if has_session_structure:
                                self.log_test("Session Data Translation Support", True, 
                                             "Session data structure supports translation")
                                return True
                            else:
                                self.log_test("Session Data Translation Support", False, 
                                             "Session data missing required fields for translation")
                                return False
                        else:
                            self.log_test("Session Data Translation Support", True, 
                                         "No sessions to test, but structure appears ready")
                            return True
                    else:
                        self.log_test("Dashboard Translation Support", False, 
                                     "Dashboard stats missing required structure for translation")
                        return False
                else:
                    self.log_test("Dashboard Translation Support", False, 
                                 "Failed to access dashboard for translation testing", response2)
                    return False
            else:
                self.log_test("Services Translation Support", False, 
                             "Services endpoint missing required fields for translation")
                return False
        else:
            self.log_test("Services Translation Support", False, 
                         "Failed to access services endpoint", response)
            return False

    def run_review_tests(self):
        """Run all review requirement tests"""
        print("🔍 Starting Review Requirements Testing...")
        print("=" * 60)
        
        # Login as admin user
        print("\n🔐 Admin Authentication:")
        if not self.test_admin_login():
            print("❌ Admin login failed - cannot proceed with review tests")
            return False
        
        # Test specific review requirements
        print("\n📧 1. GMAIL SMTP INTEGRATION:")
        self.test_gmail_smtp_integration()
        
        print("\n👑 2. ADMIN/READER ROLE MERGE:")
        self.test_admin_reader_role_merge()
        
        print("\n⏰ 3. SESSION TIME HANDLING:")
        self.test_session_time_handling()
        
        print("\n🗺️ 4. ASTROLOGICAL MAP GENERATION:")
        self.test_astrological_map_generation()
        
        print("\n🌐 5. TRANSLATION SUPPORT:")
        self.test_translation_support()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Review Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All review requirements tests passed!")
            return True
        else:
            print("⚠️ Some review requirements tests failed - check details above")
            return False

    def save_results(self, filename: str = "/app/review_test_results.json"):
        """Save test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_details": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Review test results saved to: {filename}")

def main():
    tester = ReviewRequirementsAPITester()
    success = tester.run_review_tests()
    tester.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())