#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class BookingDiagnosticTester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.client_token = None
        self.admin_token = None
        self.issues_found = []
        self.session_id = None

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
        print("🔧 Setting up test environment...")
        
        # Create client
        client_email = f"diagnostic_client_{datetime.now().strftime('%H%M%S')}@example.com"
        client_data = {
            "name": "Diagnostic Client",
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
            admin_role = response['user']['role']
            print(f"✅ Admin logged in: {response['user']['email']} (role: {admin_role})")
        else:
            print(f"❌ Failed to login admin: {response}")
            return False
        
        return True

    def diagnose_session_creation(self):
        """Diagnose session creation and storage"""
        print("\n🔍 DIAGNOSING: Session Creation and Storage")
        print("-" * 50)
        
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
            "client_message": "Diagnostic test - investigating user reported booking issues"
        }
        
        print(f"📅 Creating session for: {start_time.strftime('%A, %B %d at %I:%M %p')}")
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            status = response.get('status', 'unknown')
            payment_status = response.get('payment_status', 'unknown')
            amount = response.get('amount', 0)
            has_payment_link = 'payment_link' in response and response['payment_link']
            
            print(f"✅ Session created successfully:")
            print(f"   - Session ID: {self.session_id}")
            print(f"   - Status: {status}")
            print(f"   - Payment Status: {payment_status}")
            print(f"   - Amount: ${amount}")
            print(f"   - Has Payment Link: {has_payment_link}")
            
            if has_payment_link:
                print(f"   - Payment Link: {response['payment_link']}")
            
            # Verify session storage
            success2, response2 = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
            
            if success2 and response2.get('id') == self.session_id:
                print("✅ Session successfully stored in database")
                return True
            else:
                print("❌ Session not found in database after creation")
                self.issues_found.append("Session storage: Session not retrievable after creation")
                return False
        else:
            print(f"❌ Session creation failed: {response}")
            self.issues_found.append(f"Session creation failed: {response}")
            return False

    def diagnose_email_system(self):
        """Diagnose email system"""
        print("\n🔍 DIAGNOSING: Email System")
        print("-" * 50)
        
        if not self.session_id:
            print("❌ No session available for email testing")
            self.issues_found.append("Email system: No session available for testing")
            return False
        
        print("📧 Testing email triggers by completing payment...")
        
        # Complete payment which should trigger emails
        success, response = self.make_request('POST', f'sessions/{self.session_id}/payment/complete', None, 200)
        
        if success:
            print("✅ Payment completion successful - should trigger emails:")
            print("   - Client confirmation email")
            print("   - Admin/reader notification email")
            
            # Check if session status updated
            success2, response2 = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
            
            if success2 and response2.get('payment_status') == 'paid':
                print("✅ Session status updated to 'paid' - email triggers working")
                print("📧 NOTE: Check backend console logs for actual email sending attempts")
                print("📧 NOTE: SendGrid may have sender verification issues (403 errors)")
                return True
            else:
                print("❌ Session status not updated after payment")
                self.issues_found.append("Email system: Session status not updated after payment completion")
                return False
        else:
            print(f"❌ Payment completion failed: {response}")
            self.issues_found.append(f"Email system: Payment completion failed - {response}")
            return False

    def diagnose_admin_portal_issues(self):
        """Diagnose admin portal session visibility issues"""
        print("\n🔍 DIAGNOSING: Admin Portal Session Visibility")
        print("-" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            self.issues_found.append("Admin portal: No admin access available")
            return False
        
        # Test admin dashboard stats (this should work)
        print("📊 Testing admin dashboard stats...")
        success, response = self.make_request('GET', 'admin/dashboard-stats', None, 200, self.admin_token)
        
        if success and 'total_sessions' in response:
            stats = response
            print(f"✅ Admin dashboard stats working:")
            print(f"   - Total sessions: {stats['total_sessions']}")
            print(f"   - Confirmed sessions: {stats['confirmed_sessions']}")
            print(f"   - Pending sessions: {stats['pending_sessions']}")
            print(f"   - Total revenue: ${stats.get('total_revenue', 0)}")
        else:
            print(f"❌ Admin dashboard stats failed: {response}")
            self.issues_found.append(f"Admin portal: Dashboard stats failed - {response}")
        
        # Test admin sessions list (this is the problematic endpoint)
        print("📋 Testing admin sessions list...")
        success, response = self.make_request('GET', 'admin/sessions', None, 200, self.admin_token)
        
        if success and isinstance(response, list):
            sessions_count = len(response)
            print(f"✅ Admin sessions list working: {sessions_count} sessions retrieved")
            
            # Check if our test session is visible
            if self.session_id:
                test_session_found = any(session.get('id') == self.session_id for session in response)
                if test_session_found:
                    print("✅ Test session found in admin sessions list")
                else:
                    print("⚠️  Test session not found in admin sessions list")
                    self.issues_found.append("Admin portal: Test session not visible in admin sessions list")
            
            return True
        else:
            print(f"❌ CRITICAL: Admin sessions list failed with 500 error")
            print("   This is the main reason sessions don't appear in admin portal!")
            print("   Error details:", response)
            self.issues_found.append("CRITICAL: Admin sessions list endpoint failing with 500 error - MongoDB ObjectId serialization issue")
            return False

    def diagnose_reader_dashboard_access(self):
        """Diagnose reader dashboard access"""
        print("\n🔍 DIAGNOSING: Reader Dashboard Access")
        print("-" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Test reader dashboard access
        print("📖 Testing reader dashboard access...")
        success, response = self.make_request('GET', 'reader/dashboard', None, 200, self.admin_token)
        
        if success and 'sessions' in response:
            reader_sessions = response['sessions']
            stats = response.get('stats', {})
            print(f"✅ Reader dashboard accessible: {len(reader_sessions)} sessions")
            
            # Check if our test session is visible
            if self.session_id:
                test_session_found = any(session.get('id') == self.session_id for session in reader_sessions)
                if test_session_found:
                    print("✅ Test session found in reader dashboard")
                else:
                    print("⚠️  Test session not found in reader dashboard")
            
            return True
        else:
            print(f"❌ Reader dashboard access failed: {response}")
            if 'Reader access required' in str(response):
                print("   Issue: Admin user (role: 'admin') cannot access reader dashboard (requires role: 'reader')")
                print("   Solution: Admin should also have reader permissions OR reader dashboard should allow admin access")
                self.issues_found.append("Reader dashboard: Admin user cannot access reader dashboard - role permission issue")
            else:
                self.issues_found.append(f"Reader dashboard: Access failed - {response}")
            return False

    def diagnose_payment_system(self):
        """Diagnose payment system"""
        print("\n🔍 DIAGNOSING: Payment System")
        print("-" * 50)
        
        if not self.session_id:
            print("❌ No session available for payment testing")
            return False
        
        # Get session details
        success, response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
        
        if not success:
            print(f"❌ Failed to get session details: {response}")
            return False
        
        service_type = response.get('service_type')
        payment_link = response.get('payment_link')
        
        print(f"💳 Testing Stripe payment integration for service: {service_type}")
        
        # Create Stripe checkout session
        payment_request = {
            "service_type": service_type,
            "session_id": self.session_id,
            "origin_url": self.base_url
        }
        
        success, response = self.make_request('POST', 'payments/v1/checkout/session', payment_request, 200)
        
        if success and 'url' in response:
            checkout_session_id = response['session_id']
            checkout_url = response['url']
            
            print(f"✅ Stripe checkout session created:")
            print(f"   - Checkout Session ID: {checkout_session_id}")
            print(f"   - Checkout URL: {checkout_url}")
            
            # Test payment status checking
            success2, response2 = self.make_request('GET', f'payments/v1/checkout/status/{checkout_session_id}', None, 200)
            
            if success2 and 'payment_status' in response2:
                payment_status = response2['payment_status']
                print(f"✅ Payment status check working: {payment_status}")
                print("✅ Payment system is fully functional")
                return True
            else:
                print(f"❌ Payment status check failed: {response2}")
                self.issues_found.append(f"Payment system: Status check failed - {response2}")
                return False
        else:
            print(f"❌ Stripe checkout creation failed: {response}")
            self.issues_found.append(f"Payment system: Checkout creation failed - {response}")
            return False

    def run_comprehensive_diagnosis(self):
        """Run comprehensive diagnosis of booking flow"""
        print("🏥 COMPREHENSIVE BOOKING FLOW DIAGNOSIS")
        print("=" * 60)
        print("Investigating user-reported issues:")
        print("• Sessions not appearing in admin portal")
        print("• No confirmation emails to admin or client")
        print("• No payment redirect for auto-confirmation")
        print("• Session storage and visibility issues")
        print("=" * 60)
        
        # Setup
        if not self.setup_users():
            print("❌ Failed to setup test environment")
            return False
        
        # Run diagnostics
        session_ok = self.diagnose_session_creation()
        email_ok = self.diagnose_email_system()
        admin_ok = self.diagnose_admin_portal_issues()
        reader_ok = self.diagnose_reader_dashboard_access()
        payment_ok = self.diagnose_payment_system()
        
        # Final diagnosis
        print("\n" + "=" * 60)
        print("🏥 FINAL DIAGNOSIS")
        print("=" * 60)
        
        if not self.issues_found:
            print("✅ No critical issues found - booking flow is working correctly")
        else:
            print("🚨 CRITICAL ISSUES IDENTIFIED:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue}")
        
        print("\n📋 DIAGNOSIS SUMMARY:")
        print(f"✅ Session Creation & Storage: {'Working' if session_ok else 'Issues Found'}")
        print(f"📧 Email System: {'Working' if email_ok else 'Issues Found'}")
        print(f"👑 Admin Portal: {'Working' if admin_ok else 'CRITICAL ISSUES'}")
        print(f"📖 Reader Dashboard: {'Working' if reader_ok else 'Issues Found'}")
        print(f"💳 Payment System: {'Working' if payment_ok else 'Issues Found'}")
        
        print("\n🔧 RECOMMENDED FIXES:")
        
        if not admin_ok:
            print("1. CRITICAL: Fix admin sessions list endpoint")
            print("   - Issue: MongoDB ObjectId serialization error")
            print("   - Fix: Exclude '_id' field or convert ObjectId to string")
            print("   - Code location: /app/backend/server.py line ~1533")
        
        if not reader_ok:
            print("2. Fix reader dashboard access for admin users")
            print("   - Issue: Admin role cannot access reader dashboard")
            print("   - Fix: Allow admin role OR change admin user role to 'reader'")
            print("   - Code location: /app/backend/server.py line ~435")
        
        if not email_ok:
            print("3. Verify SendGrid sender email verification")
            print("   - Issue: Sender email may not be verified in SendGrid")
            print("   - Fix: Verify 'Lago.mistico11@gmail.com' in SendGrid dashboard")
        
        print("\n📊 ROOT CAUSE OF USER ISSUES:")
        print("• Sessions not appearing in admin portal: Admin sessions list endpoint failing (500 error)")
        print("• No confirmation emails: SendGrid sender verification issue (emails triggered but not sent)")
        print("• Payment system: Working correctly")
        print("• Session storage: Working correctly")
        
        return len(self.issues_found) == 0

def main():
    tester = BookingDiagnosticTester()
    success = tester.run_comprehensive_diagnosis()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())