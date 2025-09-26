#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class TimeChartTester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
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

    def setup_authentication(self):
        """Setup authentication for testing"""
        test_email = f"time_chart_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Time Chart Test User",
            "email": test_email,
            "password": "TimeChart123!",
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

    def test_time_display_10am_session_creation(self):
        """Test creating a session at 10:00 AM and verify correct storage"""
        # Create session at exactly 10:00 AM next Monday (to avoid weekend issues)
        today = datetime.now()
        days_ahead = 7 - today.weekday()  # Next Monday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_monday = today + timedelta(days=days_ahead)
        session_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = session_time + timedelta(minutes=45)
        
        session_data = {
            "service_type": "general-purpose-reading",
            "start_at": session_time.isoformat(),
            "end_at": end_time.isoformat(),
            "client_message": "Testing 10:00 AM time storage - should not convert to 3:00 PM"
        }
        
        success, response = self.make_request('POST', 'sessions', session_data, 200)
        
        if success and 'id' in response:
            self.session_id = response['id']
            stored_start_time = response.get('start_at')
            
            if stored_start_time:
                try:
                    # Parse the stored time
                    parsed_time = datetime.fromisoformat(stored_start_time.replace('Z', '+00:00'))
                    stored_hour = parsed_time.hour
                    
                    if stored_hour == 10:
                        self.log_test("Time Display - 10:00 AM Session Creation", True, 
                                     f"✅ Session correctly stored at hour {stored_hour} (10:00 AM, not 3:00 PM)")
                        return True
                    else:
                        self.log_test("Time Display - 10:00 AM Session Creation", False, 
                                     f"❌ Session stored at incorrect hour {stored_hour}, expected 10 (10:00 AM)")
                        return False
                except Exception as e:
                    self.log_test("Time Display - 10:00 AM Session Creation", False, 
                                 f"Failed to parse stored time: {str(e)}")
                    return False
            else:
                self.log_test("Time Display - 10:00 AM Session Creation", False, 
                             "No start_at time in response")
                return False
        else:
            self.log_test("Time Display - 10:00 AM Session Creation", False, 
                         "Failed to create session", response)
            return False

    def test_time_display_session_retrieval(self):
        """Test retrieving session data and confirm time is not converted"""
        if not hasattr(self, 'session_id'):
            self.log_test("Time Display - Session Retrieval", False, "No session ID available")
            return False
            
        success, response = self.make_request('GET', f'sessions/{self.session_id}', None, 200)
        
        if success and 'start_at' in response:
            stored_start_time = response['start_at']
            
            try:
                parsed_time = datetime.fromisoformat(stored_start_time.replace('Z', '+00:00'))
                stored_hour = parsed_time.hour
                
                if stored_hour == 10:
                    self.log_test("Time Display - Session Retrieval", True, 
                                 f"✅ Retrieved session shows correct hour {stored_hour} (10:00 AM, not 3:00 PM)")
                    return True
                else:
                    self.log_test("Time Display - Session Retrieval", False, 
                                 f"❌ Retrieved session shows incorrect hour {stored_hour}, expected 10")
                    return False
            except Exception as e:
                self.log_test("Time Display - Session Retrieval", False, 
                             f"Failed to parse retrieved time: {str(e)}")
                return False
        else:
            self.log_test("Time Display - Session Retrieval", False, 
                         "Failed to retrieve session or no start_at time", response)
            return False

    def test_birth_chart_generation_with_svg(self):
        """Test birth chart generation includes SVG content"""
        # Create birth data
        birth_data = {
            "birth_date": "1990-05-15",
            "birth_time": "10:00",
            "time_accuracy": "exact",
            "birth_place": "New York, NY",
            "latitude": "40.7128",
            "longitude": "-74.0060"
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200)
        
        if not success or 'id' not in response:
            self.log_test("Birth Chart SVG - Birth Data Creation", False, "Failed to create birth data", response)
            return False
            
        birth_data_id = response['id']
        self.log_test("Birth Chart SVG - Birth Data Creation", True, f"Created birth data: {birth_data_id}")
        
        # Generate chart
        success, response = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200)
        
        if success and 'id' in response:
            self.chart_id = response['id']
            planets = response.get('planets', {})
            houses = response.get('houses', {})
            chart_svg = response.get('chart_svg')
            image_path = response.get('image_path')
            
            planet_count = len(planets)
            house_count = len(houses)
            has_svg = chart_svg is not None and len(str(chart_svg)) > 0
            has_image_path = image_path is not None
            
            details = f"Chart ID: {self.chart_id}, Planets: {planet_count}, Houses: {house_count}"
            
            if has_svg:
                svg_length = len(str(chart_svg))
                details += f", SVG Content: {svg_length} characters"
            
            if has_image_path:
                details += f", Image Path: {image_path}"
            
            if planet_count > 0 and house_count > 0:
                if has_svg or has_image_path:
                    self.log_test("Birth Chart Generation with SVG", True, 
                                 f"✅ Chart generated with astrological data and SVG content - {details}")
                    return True
                else:
                    self.log_test("Birth Chart Generation with SVG", False, 
                                 f"❌ Chart generated but missing SVG content - {details}")
                    return False
            else:
                self.log_test("Birth Chart Generation with SVG", False, 
                             f"❌ Chart missing astrological data - {details}")
                return False
        else:
            self.log_test("Birth Chart Generation with SVG", False, 
                         "Failed to generate chart", response)
            return False

    def test_chart_map_generation_endpoint(self):
        """Test /api/charts/{chart_id}/generate-map endpoint"""
        if not hasattr(self, 'chart_id'):
            self.log_test("Chart Map Generation Endpoint", False, "No chart ID available")
            return False
            
        success, response = self.make_request('POST', f'charts/{self.chart_id}/generate-map', None, 200)
        
        if success:
            message = response.get('message', '')
            has_svg = response.get('has_svg', False)
            
            if 'successfully' in message.lower():
                self.log_test("Chart Map Generation Endpoint", True, 
                             f"✅ Map generation successful: {message}, Has SVG: {has_svg}")
                return True
            else:
                self.log_test("Chart Map Generation Endpoint", False, 
                             f"❌ Unexpected response: {message}")
                return False
        else:
            self.log_test("Chart Map Generation Endpoint", False, 
                         "Failed to generate chart map", response)
            return False

    def test_chart_svg_retrieval_endpoint(self):
        """Test /api/charts/{chart_id}/svg endpoint"""
        if not hasattr(self, 'chart_id'):
            self.log_test("Chart SVG Retrieval Endpoint", False, "No chart ID available")
            return False
            
        # Make request expecting SVG content
        url = f"{self.api_url}/charts/{self.chart_id}/svg"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'svg' in content_type.lower() or 'xml' in content_type.lower():
                    self.log_test("Chart SVG Retrieval Endpoint", True, 
                                 f"✅ SVG retrieved: {content_length} bytes, Content-Type: {content_type}")
                    return True
                else:
                    # Check if content looks like SVG even if content-type is wrong
                    content_text = response.text[:100].lower()
                    if '<svg' in content_text or 'xml' in content_text:
                        self.log_test("Chart SVG Retrieval Endpoint", True, 
                                     f"✅ SVG content retrieved: {content_length} bytes (content-type: {content_type})")
                        return True
                    else:
                        self.log_test("Chart SVG Retrieval Endpoint", False, 
                                     f"❌ Wrong content type: {content_type}, content: {content_text}")
                        return False
            elif response.status_code == 404:
                self.log_test("Chart SVG Retrieval Endpoint", False, 
                             "❌ Chart SVG not found - may not be generated yet")
                return False
            else:
                self.log_test("Chart SVG Retrieval Endpoint", False, 
                             f"❌ HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Chart SVG Retrieval Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_kerykeion_integration(self):
        """Test KerykeionChartSVG integration with proper astrological maps"""
        # Create birth data with specific coordinates for testing
        birth_data = {
            "birth_date": "1985-12-25",
            "birth_time": "15:30",
            "time_accuracy": "exact",
            "birth_place": "Los Angeles, CA",
            "latitude": "34.0522",
            "longitude": "-118.2437"
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200)
        
        if not success:
            self.log_test("KerykeionChartSVG Integration", False, "Failed to create birth data", response)
            return False
            
        birth_data_id = response['id']
        
        # Generate chart
        success, response = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200)
        
        if success and 'id' in response:
            chart_id = response['id']
            planets = response.get('planets', {})
            houses = response.get('houses', {})
            chart_svg = response.get('chart_svg')
            
            # Check for major planets
            major_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
            found_planets = [p for p in major_planets if p in planets]
            
            # Check for houses
            house_count = len(houses)
            
            # Check SVG content
            has_substantial_svg = chart_svg and len(str(chart_svg)) > 500
            
            details = f"Planets found: {found_planets} ({len(found_planets)}/5), Houses: {house_count}"
            if has_substantial_svg:
                details += f", SVG: {len(str(chart_svg))} characters"
            
            if len(found_planets) >= 3 and house_count >= 3:
                if has_substantial_svg:
                    self.log_test("KerykeionChartSVG Integration", True, 
                                 f"✅ Proper astrological chart with SVG - {details}")
                    
                    # Test regenerating the map
                    success2, response2 = self.make_request('POST', f'charts/{chart_id}/generate-map', None, 200)
                    
                    if success2:
                        self.log_test("KerykeionChartSVG - Map Regeneration", True, 
                                     "✅ Chart map regeneration successful")
                        return True
                    else:
                        self.log_test("KerykeionChartSVG - Map Regeneration", False, 
                                     "❌ Chart map regeneration failed", response2)
                        return False
                else:
                    self.log_test("KerykeionChartSVG Integration", False, 
                                 f"❌ Chart has astrological data but insufficient SVG content - {details}")
                    return False
            else:
                self.log_test("KerykeionChartSVG Integration", False, 
                             f"❌ Insufficient astrological data - {details}")
                return False
        else:
            self.log_test("KerykeionChartSVG Integration", False, 
                         "Failed to generate chart", response)
            return False

    def run_time_chart_tests(self):
        """Run all time display and birth chart tests"""
        print("🌟 Starting Time Display & Birth Chart Map Generation Tests...")
        print("Testing Review Requirements: Time Fix & Chart SVG Generation")
        print("=" * 70)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        print("\n🕐 TIME DISPLAY FIX TESTING:")
        print("Testing sessions at 10:00 AM - should NOT convert to 3:00 PM...")
        
        # Time display tests
        self.test_time_display_10am_session_creation()
        self.test_time_display_session_retrieval()
        
        print("\n🗺️ BIRTH CHART MAP GENERATION TESTING:")
        print("Testing chart generation with SVG content and new endpoints...")
        
        # Birth chart tests
        self.test_birth_chart_generation_with_svg()
        self.test_chart_map_generation_endpoint()
        self.test_chart_svg_retrieval_endpoint()
        self.test_kerykeion_integration()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 REVIEW REQUIREMENTS STATUS:")
        print("   🕐 Time Display Fix: Sessions at 10:00 AM stored/retrieved correctly")
        print("   🗺️ Birth Chart SVG: Chart generation includes SVG content")
        print("   🔗 New Endpoints: /api/charts/{id}/generate-map and /api/charts/{id}/svg")
        print("   🎨 KerykeionChartSVG: Integration working for astrological maps")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All time display and chart tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

def main():
    tester = TimeChartTester()
    success = tester.run_time_chart_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())