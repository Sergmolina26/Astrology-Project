#!/usr/bin/env python3

import requests
import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ChartMapDebugTester:
    def __init__(self, base_url="https://astro-reader-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.chart_id = None
        self.birth_data_id = None

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
        test_email = f"chart_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Chart Test User",
            "email": test_email,
            "password": "ChartTest123!",
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

    def create_birth_data(self):
        """Create birth data for chart generation"""
        birth_data = {
            "birth_date": "1985-07-20",
            "birth_time": "10:30",
            "time_accuracy": "exact",
            "birth_place": "Los Angeles, CA",
            "latitude": "34.0522",
            "longitude": "-118.2437"
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200)
        
        if success and 'id' in response:
            self.birth_data_id = response['id']
            self.log_test("Birth Data Creation", True, f"Created birth data: {response['id']}")
            return True
        else:
            self.log_test("Birth Data Creation", False, "Failed to create birth data", response)
            return False

    def test_chart_generation_with_svg(self):
        """Test generating astrology chart with SVG content"""
        if not self.birth_data_id:
            self.log_test("Chart Generation with SVG", False, "No birth data available")
            return False
            
        success, response = self.make_request('POST', f'astrology/chart?birth_data_id={self.birth_data_id}', None, 200)
        
        if success and 'id' in response:
            self.chart_id = response['id']
            
            # Check if chart has SVG content
            has_svg = 'chart_svg' in response and response['chart_svg'] is not None
            has_planets = 'planets' in response and len(response['planets']) > 0
            has_houses = 'houses' in response and len(response['houses']) > 0
            
            details = f"Chart ID: {self.chart_id}"
            details += f", Planets: {len(response.get('planets', {}))}"
            details += f", Houses: {len(response.get('houses', {}))}"
            details += f", Has SVG: {has_svg}"
            
            if has_svg:
                svg_length = len(response['chart_svg'])
                details += f", SVG Length: {svg_length} chars"
                
                # Check if SVG contains expected astrological elements
                svg_content = response['chart_svg']
                has_circle = '<circle' in svg_content
                has_path = '<path' in svg_content
                has_text = '<text' in svg_content
                
                details += f", SVG Elements: circle={has_circle}, path={has_path}, text={has_text}"
                
                if svg_length > 1000 and has_circle and has_path:
                    self.log_test("Chart Generation with SVG", True, details)
                    return True
                else:
                    self.log_test("Chart Generation with SVG", False, f"SVG content appears incomplete: {details}")
                    return False
            else:
                self.log_test("Chart Generation with SVG", False, f"No SVG content generated: {details}")
                return False
        else:
            self.log_test("Chart Generation with SVG", False, "Failed to generate chart", response)
            return False

    def test_chart_map_generation_endpoint(self):
        """Test the /api/charts/{chart_id}/generate-map endpoint"""
        if not self.chart_id:
            self.log_test("Chart Map Generation Endpoint", False, "No chart ID available")
            return False
        
        success, response = self.make_request('POST', f'charts/{self.chart_id}/generate-map', None, 200)
        
        if success and 'message' in response:
            has_svg = response.get('has_svg', False)
            details = f"Message: {response['message']}, Has SVG: {has_svg}"
            
            if has_svg:
                self.log_test("Chart Map Generation Endpoint", True, details)
                return True
            else:
                self.log_test("Chart Map Generation Endpoint", False, f"Map generation failed: {details}")
                return False
        else:
            self.log_test("Chart Map Generation Endpoint", False, "Failed to generate map", response)
            return False

    def test_svg_retrieval_endpoint(self):
        """Test the /api/charts/{chart_id}/svg endpoint"""
        if not self.chart_id:
            self.log_test("SVG Retrieval Endpoint", False, "No chart ID available")
            return False
        
        # Make request expecting SVG content (not JSON)
        url = f"{self.api_url}/charts/{self.chart_id}/svg"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                svg_content = response.text
                
                # Check if it's SVG content
                is_svg = 'image/svg+xml' in content_type or svg_content.strip().startswith('<svg')
                svg_length = len(svg_content)
                
                details = f"Content-Type: {content_type}, Length: {svg_length}, Is SVG: {is_svg}"
                
                if is_svg and svg_length > 100:
                    # Check for astrological elements in SVG
                    has_circle = '<circle' in svg_content
                    has_path = '<path' in svg_content
                    has_text = '<text' in svg_content
                    
                    details += f", Elements: circle={has_circle}, path={has_path}, text={has_text}"
                    
                    if has_circle and has_path:
                        self.log_test("SVG Retrieval Endpoint", True, details)
                        return True
                    else:
                        self.log_test("SVG Retrieval Endpoint", False, f"SVG missing key elements: {details}")
                        return False
                else:
                    self.log_test("SVG Retrieval Endpoint", False, f"Invalid SVG content: {details}")
                    return False
            else:
                error_details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("SVG Retrieval Endpoint", False, error_details)
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("SVG Retrieval Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_kerykeion_svg_file_generation(self):
        """Test if KerykeionChartSVG is properly generating files"""
        # This test checks if the SVG generation process creates files
        # We'll create a new chart and check the generation process
        
        if not self.birth_data_id:
            self.log_test("KerykeionChartSVG File Generation", False, "No birth data available")
            return False
        
        # Generate a new chart to test file creation
        success, response = self.make_request('POST', f'astrology/chart?birth_data_id={self.birth_data_id}', None, 200)
        
        if success and 'id' in response:
            new_chart_id = response['id']
            
            # Check if chart was created with SVG content
            has_initial_svg = 'chart_svg' in response and response['chart_svg'] is not None
            
            # Now test the map generation endpoint
            success2, response2 = self.make_request('POST', f'charts/{new_chart_id}/generate-map', None, 200)
            
            if success2:
                has_regenerated_svg = response2.get('has_svg', False)
                
                details = f"Initial SVG: {has_initial_svg}, Regenerated SVG: {has_regenerated_svg}"
                
                if has_initial_svg or has_regenerated_svg:
                    self.log_test("KerykeionChartSVG File Generation", True, details)
                    return True
                else:
                    self.log_test("KerykeionChartSVG File Generation", False, f"No SVG generated: {details}")
                    return False
            else:
                self.log_test("KerykeionChartSVG File Generation", False, "Map generation failed", response2)
                return False
        else:
            self.log_test("KerykeionChartSVG File Generation", False, "Failed to create test chart", response)
            return False

    def test_svg_file_path_issues(self):
        """Test for SVG file path and permission issues"""
        # This test will check if there are any file system issues
        
        if not self.chart_id:
            self.log_test("SVG File Path Issues", False, "No chart ID available")
            return False
        
        # Try to regenerate the map and check for errors
        success, response = self.make_request('POST', f'charts/{self.chart_id}/generate-map', None, 200)
        
        if success:
            has_svg = response.get('has_svg', False)
            message = response.get('message', '')
            
            # Check if the response indicates file system issues
            file_error_indicators = ['permission', 'path', 'file not found', 'directory']
            has_file_error = any(indicator in message.lower() for indicator in file_error_indicators)
            
            details = f"Message: {message}, Has SVG: {has_svg}, File Error Detected: {has_file_error}"
            
            if has_svg and not has_file_error:
                self.log_test("SVG File Path Issues", True, f"No file path issues detected: {details}")
                return True
            else:
                self.log_test("SVG File Path Issues", False, f"Potential file path issues: {details}")
                return False
        else:
            error_msg = str(response)
            self.log_test("SVG File Path Issues", False, f"Map generation failed: {error_msg}")
            return False

    def test_chart_data_integrity(self):
        """Test if chart data is properly structured for map generation"""
        if not self.chart_id:
            self.log_test("Chart Data Integrity", False, "No chart ID available")
            return False
        
        # Get the chart data
        success, response = self.make_request('GET', f'astrology/charts/{self.user_id}', None, 200)
        
        if success and isinstance(response, list) and len(response) > 0:
            # Find our chart
            chart = None
            for c in response:
                if c['id'] == self.chart_id:
                    chart = c
                    break
            
            if chart:
                # Check chart data structure
                has_birth_data = 'birth_data' in chart and chart['birth_data'] is not None
                has_planets = 'planets' in chart and len(chart['planets']) > 0
                has_houses = 'houses' in chart and len(chart['houses']) > 0
                
                birth_data_complete = False
                if has_birth_data:
                    bd = chart['birth_data']
                    birth_data_complete = all(key in bd for key in ['birth_date', 'birth_place', 'latitude', 'longitude'])
                
                details = f"Birth Data: {has_birth_data}, Complete: {birth_data_complete}, Planets: {len(chart.get('planets', {}))}, Houses: {len(chart.get('houses', {}))}"
                
                if has_birth_data and birth_data_complete and has_planets and has_houses:
                    self.log_test("Chart Data Integrity", True, details)
                    return True
                else:
                    self.log_test("Chart Data Integrity", False, f"Incomplete chart data: {details}")
                    return False
            else:
                self.log_test("Chart Data Integrity", False, "Chart not found in user's charts")
                return False
        else:
            self.log_test("Chart Data Integrity", False, "Failed to retrieve charts", response)
            return False

    def test_error_investigation(self):
        """Investigate specific errors in the chart generation process"""
        print("\n🔍 DETAILED ERROR INVESTIGATION:")
        
        # Test with invalid chart ID
        success, response = self.make_request('POST', 'charts/invalid-id/generate-map', None, 200)
        if not success:
            error_msg = str(response)
            print(f"    Invalid Chart ID Error: {error_msg}")
        
        # Test SVG endpoint with invalid ID
        success, response = self.make_request('GET', 'charts/invalid-id/svg', None, 200)
        if not success:
            error_msg = str(response)
            print(f"    Invalid SVG Request Error: {error_msg}")
        
        # Test with missing authentication
        original_token = self.token
        self.token = None
        success, response = self.make_request('POST', f'charts/{self.chart_id}/generate-map', None, 200)
        self.token = original_token
        
        if not success:
            error_msg = str(response)
            print(f"    Authentication Error: {error_msg}")
        
        self.log_test("Error Investigation", True, "Completed error investigation - check console output above")
        return True

    def run_chart_map_debug_tests(self):
        """Run all chart map debugging tests"""
        print("🗺️  Starting Chart Map Generation Debug Tests...")
        print("=" * 60)
        
        # Setup
        print("\n🔧 Setup:")
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        if not self.create_birth_data():
            print("❌ Birth data creation failed - stopping tests")
            return False
        
        # Core chart generation tests
        print("\n⭐ Chart Generation Tests:")
        self.test_chart_generation_with_svg()
        
        # Map generation endpoint tests
        print("\n🗺️  Map Generation Endpoint Tests:")
        self.test_chart_map_generation_endpoint()
        
        # SVG retrieval tests
        print("\n🖼️  SVG Retrieval Tests:")
        self.test_svg_retrieval_endpoint()
        
        # KerykeionChartSVG integration tests
        print("\n🔮 KerykeionChartSVG Integration Tests:")
        self.test_kerykeion_svg_file_generation()
        
        # File system tests
        print("\n📁 File System Tests:")
        self.test_svg_file_path_issues()
        
        # Data integrity tests
        print("\n📊 Data Integrity Tests:")
        self.test_chart_data_integrity()
        
        # Error investigation
        print("\n🚨 Error Investigation:")
        self.test_error_investigation()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Debug Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed findings
        print("\n🔍 KEY FINDINGS:")
        failed_tests = [result for result in self.test_results if not result['success']]
        
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['details']}")
        else:
            print("✅ All chart map generation tests passed!")
        
        return len(failed_tests) == 0

    def save_debug_results(self, filename: str = "/app/chart_map_debug_results.json"):
        """Save debug test results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "chart_map_debug",
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "chart_id": self.chart_id,
            "birth_data_id": self.birth_data_id,
            "test_details": self.test_results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Debug results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")

def main():
    tester = ChartMapDebugTester()
    success = tester.run_chart_map_debug_tests()
    tester.save_debug_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())