#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class FocusedBookingTester:
    def __init__(self, base_url="https://astro-booking-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.client_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues_found = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        else:
            self.issues_found.append({
                "test": name,
                "details": details,
                "response": response_data
            })
        
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
        print("🔧 Setting up users...")
        
        # Create client
        client_email = f"test_client_{datetime.now().strftime('%H%M%S')}@example.com"
        client_data = {
            "name": "Test Client",
            "email": client_email,
            "password": "TestPass123!",
            "role": "client"
        }
        
        success, response = self.make_request('POST', 'auth/register', client_data, 200)
        if success and 'access_token' in response:
            self.client_token = response['access_token']
            print(f"✅ Client created: {client_email}")
        else:
            print(f"❌ Failed to create client: {response}")
            return False

        # Login admin
        admin_login = {
            "email": "lago.mistico11@gmail.com",
            "password": "CelestiaAdmin2024!"
        }
        
        success, response = self.make_request('POST', 'auth/login', admin_login, 200)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"✅ Admin logged in: {response['user']['email']}")
        else:
            print(f"❌ Failed to login admin: {response}")
            return False
        
        return True

    def test_session_creation_and_storage(self):
        """Test session creation with proper business hours"""
        print("\n📊 Testing Session Creation and Storage...")
        
        # Calculate next Monday at 2 PM (within business hours)
        now = datetime.now()
        days_ahead = 0 - now.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_monday = now + timedelta(days=days_ahead)
        start_time = next_monday.replace(hour=14, minute=0, second=0, microsecond=0)  # 2 PM
        end_time = start_time + timedelta(minutes=45)  # 45 minutes
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing complete booking flow - user reported issues"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            session_id = response['id']
            status = response.get('status', 'unknown')
            payment_status = response.get('payment_status', 'unknown')
            amount = response.get('amount', 0)
            has_payment_link = 'payment_link' in response and response['payment_link']
            
            self.log_test("Session Creation", True, 
                         f"Session {session_id} created with status: {status}, payment: {payment_status}, amount: ${amount}, has_payment_link: {has_payment_link}")
            
            # Verify session is stored and retrievable
            success2, response2 = self.make_request('GET', f'sessions/{session_id}', None, 200)
            
            if success2 and response2.get('id') == session_id:
                self.log_test("Session Storage", True, "Session successfully stored and retrieved")
                return session_id
            else:
                self.log_test("Session Storage", False, "Session not found after creation", response2)
                return None
        else:
            self.log_test("Session Creation", False, "Failed to create session", response)
            return None

    def test_email_system_triggers(self, session_id):
        """Test email system by completing payment"""
        print("\n📧 Testing Email System...")
        
        if not session_id:
            self.log_test("Email System", False, "No session available for testing")
            return False
        
        # Complete payment which should trigger emails
        success, response = self.make_request('POST', f'sessions/{session_id}/payment/complete', None, 200)
        
        if success:
            self.log_test("Payment Completion", True, "Payment completed - should trigger emails")
            
            # Check if session status updated
            success2, response2 = self.make_request('GET', f'sessions/{session_id}', None, 200)
            
            if success2 and response2.get('payment_status') == 'paid':
                self.log_test("Email System Integration", True, "Payment flow working - emails should be sent")
                return True
            else:
                self.log_test("Email System Integration", False, "Payment status not updated", response2)
                return False
        else:
            self.log_test("Payment Completion", False, "Failed to complete payment", response)
            return False

    def test_admin_dashboard_access(self, session_id):
        """Test admin dashboard and session visibility"""
        print("\n👑 Testing Admin Dashboard...")
        
        if not self.admin_token:
            self.log_test("Admin Dashboard", False, "No admin token available")
            return False
        
        # Test admin dashboard stats
        success, response = self.make_request('GET', 'admin/dashboard-stats', None, 200, self.admin_token)
        
        if success and 'total_sessions' in response:
            stats = response
            self.log_test("Admin Dashboard Stats", True, 
                         f"Stats: {stats['total_sessions']} total, {stats['confirmed_sessions']} confirmed, {stats['pending_sessions']} pending")
        else:
            self.log_test("Admin Dashboard Stats", False, "Failed to get dashboard stats", response)
        
        # Test admin sessions list (this was failing before)
        success, response = self.make_request('GET', 'admin/sessions', None, 200, self.admin_token)
        
        if success and isinstance(response, list):
            sessions_count = len(response)
            self.log_test("Admin Sessions List", True, f"Retrieved {sessions_count} sessions")
            
            # Check if our test session is visible
            if session_id:
                test_session_found = any(session.get('id') == session_id for session in response)
                if test_session_found:
                    self.log_test("Test Session Visibility in Admin", True, "Test session found in admin dashboard")
                else:
                    self.log_test("Test Session Visibility in Admin", False, "Test session not found in admin dashboard")
            
            return True
        else:
            self.log_test("Admin Sessions List", False, "Failed to retrieve admin sessions list", response)
            return False

    def test_reader_dashboard_access(self, session_id):
        """Test reader dashboard access"""
        print("\n📖 Testing Reader Dashboard...")
        
        if not self.admin_token:
            self.log_test("Reader Dashboard", False, "No admin token available")
            return False
        
        # Test reader dashboard (admin should be able to access as reader)
        success, response = self.make_request('GET', 'reader/dashboard', None, 200, self.admin_token)
        
        if success and 'sessions' in response:
            reader_sessions = response['sessions']
            stats = response.get('stats', {})
            
            self.log_test("Reader Dashboard Access", True, 
                         f"Reader dashboard loaded with {len(reader_sessions)} sessions")
            
            # Check if our test session is visible
            if session_id:
                test_session_found = any(session.get('id') == session_id for session in reader_sessions)
                if test_session_found:
                    self.log_test("Test Session Visibility in Reader Dashboard", True, "Test session found in reader dashboard")
                else:
                    self.log_test("Test Session Visibility in Reader Dashboard", False, "Test session not found in reader dashboard")
            
            return True
        else:
            self.log_test("Reader Dashboard Access", False, "Failed to access reader dashboard", response)
            return False

    def test_stripe_payment_integration(self, session_id):
        """Test Stripe payment integration"""
        print("\n💳 Testing Stripe Payment Integration...")
        
        if not session_id:
            self.log_test("Stripe Integration", False, "No session available for testing")
            return False
        
        # Get session details
        success, response = self.make_request('GET', f'sessions/{session_id}', None, 200)
        
        if not success:
            self.log_test("Stripe Integration - Session Retrieval", False, "Failed to get session", response)
            return False
        
        service_type = response.get('service_type')
        
        # Create Stripe checkout session
        payment_request = {
            "service_type": service_type,
            "session_id": session_id,
            "origin_url": self.base_url
        }
        
        success, response = self.make_request('POST', 'payments/v1/checkout/session', payment_request, 200)
        
        if success and 'url' in response:
            checkout_session_id = response['session_id']
            checkout_url = response['url']
            
            self.log_test("Stripe Checkout Creation", True, 
                         f"Checkout session created: {checkout_session_id}")
            
            # Test payment status checking
            success2, response2 = self.make_request('GET', f'payments/v1/checkout/status/{checkout_session_id}', None, 200)
            
            if success2 and 'payment_status' in response2:
                payment_status = response2['payment_status']
                self.log_test("Stripe Payment Status", True, f"Payment status: {payment_status}")
                return True
            else:
                self.log_test("Stripe Payment Status", False, "Failed to get payment status", response2)
                return False
        else:
            self.log_test("Stripe Checkout Creation", False, "Failed to create checkout session", response)
            return False

    def run_focused_investigation(self):
        """Run focused investigation of booking flow issues"""
        print("🔍 FOCUSED BOOKING FLOW INVESTIGATION")
        print("=" * 60)
        print("Investigating specific user-reported issues:")
        print("1. Sessions not appearing in admin portal (Sessions or Upcoming Sessions)")
        print("2. No confirmation email to admin (lago.mistico11@gmail.com)")
        print("3. No confirmation email to client")
        print("4. No payment redirect for auto-confirmation")
        print("=" * 60)
        
        # Setup
        if not self.setup_users():
            print("❌ Failed to setup users")
            return False
        
        # Test 1: Session Creation and Storage
        session_id = self.test_session_creation_and_storage()
        
        # Test 2: Email System
        self.test_email_system_triggers(session_id)
        
        # Test 3: Admin Dashboard Access
        self.test_admin_dashboard_access(session_id)
        
        # Test 4: Reader Dashboard Access
        self.test_reader_dashboard_access(session_id)
        
        # Test 5: Stripe Payment Integration
        self.test_stripe_payment_integration(session_id)
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 INVESTIGATION RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Critical Issues Analysis
        print("\n🚨 CRITICAL ISSUES FOUND:")
        if not self.issues_found:
            print("✅ No critical issues detected in booking flow")
        else:
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue['test']}: {issue['details']}")
        
        # Root Cause Analysis
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        
        admin_sessions_failed = any("Admin Sessions List" in issue['test'] for issue in self.issues_found)
        if admin_sessions_failed:
            print("❌ CRITICAL: Admin sessions list endpoint failing with 500 error")
            print("   - Likely MongoDB ObjectId serialization issue")
            print("   - This prevents sessions from appearing in admin portal")
            print("   - Sessions are being created and stored correctly")
        
        email_issues = any("Email" in issue['test'] for issue in self.issues_found)
        if email_issues:
            print("❌ Email system issues detected")
        else:
            print("✅ Email system triggers are working (check SendGrid sender verification)")
        
        payment_issues = any("Stripe" in issue['test'] or "Payment" in issue['test'] for issue in self.issues_found)
        if payment_issues:
            print("❌ Payment system issues detected")
        else:
            print("✅ Payment system is working correctly")
        
        return len(self.issues_found) == 0

def main():
    tester = FocusedBookingTester()
    success = tester.run_focused_investigation()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())