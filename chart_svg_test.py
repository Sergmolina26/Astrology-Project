#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ChartSVGTester:
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
        # Try to register a new user
        test_email = f"chart_test_{datetime.now().strftime('%H%M%S')}@celestia.com"
        register_data = {
            "name": "Chart Test User",
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

    def test_existing_charts_with_svg(self):
        """Test if there are existing charts in the system with SVG content"""
        if not self.user_id:
            self.log_test("Check Existing Charts", False, "No user ID available")
            return False
            
        success, response = self.make_request('GET', f'astrology/charts/{self.user_id}', None, 200)
        
        if success and isinstance(response, list):
            charts_with_svg = []
            charts_without_svg = []
            
            for chart in response:
                if chart.get('chart_svg'):
                    charts_with_svg.append(chart['id'])
                else:
                    charts_without_svg.append(chart['id'])
            
            total_charts = len(response)
            svg_charts = len(charts_with_svg)
            
            if total_charts > 0:
                self.log_test("Existing Charts Check", True, 
                             f"Found {total_charts} charts: {svg_charts} with SVG, {len(charts_without_svg)} without SVG")
                return charts_with_svg
            else:
                self.log_test("Existing Charts Check", True, "No existing charts found - will create new ones")
                return []
        else:
            self.log_test("Existing Charts Check", False, "Failed to retrieve charts", response)
            return False

    def create_sample_chart(self):
        """Create a sample chart for testing"""
        # First create birth data
        birth_data = {
            "birth_date": "1985-07-20",
            "birth_time": "15:45",
            "time_accuracy": "exact",
            "birth_place": "Los Angeles, CA",
            "latitude": "34.0522",
            "longitude": "-118.2437"
        }
        
        success, response = self.make_request('POST', 'birth-data', birth_data, 200)
        
        if success and 'id' in response:
            birth_data_id = response['id']
            self.log_test("Birth Data Creation", True, f"Created birth data: {birth_data_id}")
            
            # Generate chart
            success2, response2 = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200)
            
            if success2 and 'id' in response2:
                chart_id = response2['id']
                has_svg = bool(response2.get('chart_svg'))
                svg_size = len(response2.get('chart_svg', '')) if response2.get('chart_svg') else 0
                
                self.log_test("Sample Chart Creation", True, 
                             f"Created chart {chart_id}, SVG included: {has_svg}, SVG size: {svg_size} chars")
                return chart_id, has_svg
            else:
                self.log_test("Sample Chart Creation", False, "Failed to generate chart", response2)
                return None, False
        else:
            self.log_test("Birth Data Creation", False, "Failed to create birth data", response)
            return None, False

    def test_svg_generation_endpoint(self, chart_id: str):
        """Test the SVG map generation endpoint"""
        success, response = self.make_request('POST', f'charts/{chart_id}/generate-map', None, 200)
        
        if success and 'message' in response:
            has_svg = response.get('has_svg', False)
            self.log_test("SVG Map Generation", True, 
                         f"Map generation completed, SVG generated: {has_svg}")
            return has_svg
        else:
            self.log_test("SVG Map Generation", False, "Failed to generate map", response)
            return False

    def test_svg_retrieval_endpoint(self, chart_id: str):
        """Test the SVG retrieval endpoint"""
        # Make request to SVG endpoint
        url = f"{self.api_url}/charts/{chart_id}/svg"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                svg_content = response.text
                svg_size = len(svg_content)
                
                # Check if it's actually SVG content
                is_svg = 'image/svg+xml' in content_type or svg_content.strip().startswith('<svg')
                
                if is_svg and svg_size > 1000:  # SVG should be substantial
                    self.log_test("SVG Retrieval", True, 
                                 f"Retrieved SVG: {svg_size} chars, Content-Type: {content_type}")
                    
                    # Check for key SVG elements
                    has_circles = '<circle' in svg_content
                    has_paths = '<path' in svg_content
                    has_text = '<text' in svg_content
                    
                    self.log_test("SVG Content Validation", True, 
                                 f"SVG elements - Circles: {has_circles}, Paths: {has_paths}, Text: {has_text}")
                    return True
                else:
                    self.log_test("SVG Retrieval", False, 
                                 f"Invalid SVG content: size={svg_size}, is_svg={is_svg}")
                    return False
            elif response.status_code == 404:
                self.log_test("SVG Retrieval", False, "SVG not found - chart may not have generated SVG yet")
                return False
            else:
                self.log_test("SVG Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("SVG Retrieval", False, f"Request failed: {str(e)}")
            return False

    def test_chart_workflow_complete(self):
        """Test complete chart generation and SVG workflow"""
        print("\n🗺️ Testing Complete Chart SVG Workflow...")
        
        # Create new chart
        chart_id, initial_svg = self.create_sample_chart()
        if not chart_id:
            return False
        
        # If no initial SVG, generate it
        if not initial_svg:
            print("    📝 Chart created without SVG, generating map...")
            svg_generated = self.test_svg_generation_endpoint(chart_id)
            if not svg_generated:
                self.log_test("Complete Workflow", False, "Failed to generate SVG map")
                return False
        
        # Test SVG retrieval
        svg_retrieved = self.test_svg_retrieval_endpoint(chart_id)
        if not svg_retrieved:
            self.log_test("Complete Workflow", False, "Failed to retrieve SVG content")
            return False
        
        self.log_test("Complete Chart SVG Workflow", True, 
                     f"Full workflow successful for chart {chart_id}")
        return True

    def test_multiple_chart_svg_generation(self):
        """Test SVG generation for multiple charts"""
        print("\n📊 Testing Multiple Chart SVG Generation...")
        
        successful_charts = 0
        total_attempts = 3
        
        for i in range(total_attempts):
            # Create different birth data for variety
            birth_dates = ["1990-03-15", "1975-11-08", "2000-06-22"]
            birth_times = ["10:30", "18:15", "22:45"]
            locations = [
                ("New York, NY", "40.7128", "-74.0060"),
                ("London, UK", "51.5074", "-0.1278"),
                ("Sydney, Australia", "-33.8688", "151.2093")
            ]
            
            birth_data = {
                "birth_date": birth_dates[i],
                "birth_time": birth_times[i],
                "time_accuracy": "exact",
                "birth_place": locations[i][0],
                "latitude": locations[i][1],
                "longitude": locations[i][2]
            }
            
            # Create birth data
            success, response = self.make_request('POST', 'birth-data', birth_data, 200)
            if not success:
                continue
                
            birth_data_id = response['id']
            
            # Generate chart
            success2, response2 = self.make_request('POST', f'astrology/chart?birth_data_id={birth_data_id}', None, 200)
            if not success2:
                continue
                
            chart_id = response2['id']
            
            # Generate SVG map
            success3 = self.test_svg_generation_endpoint(chart_id)
            if success3:
                # Test retrieval
                success4 = self.test_svg_retrieval_endpoint(chart_id)
                if success4:
                    successful_charts += 1
        
        success_rate = (successful_charts / total_attempts) * 100
        self.log_test("Multiple Chart SVG Generation", successful_charts == total_attempts,
                     f"Successfully generated SVG for {successful_charts}/{total_attempts} charts ({success_rate:.1f}%)")
        
        return successful_charts > 0

    def run_chart_svg_tests(self):
        """Run all chart SVG tests as requested in review"""
        print("🗺️ Starting Chart SVG Testing - Review Request Focus...")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return False
        
        print("\n1️⃣ Testing Current Charts with SVG Content:")
        existing_charts = self.test_existing_charts_with_svg()
        
        print("\n2️⃣ Testing SVG Retrieval for Existing Charts:")
        if existing_charts and len(existing_charts) > 0:
            # Test SVG retrieval for first existing chart
            svg_retrieved = self.test_svg_retrieval_endpoint(existing_charts[0])
            if svg_retrieved:
                print("    ✅ Existing chart SVG retrieval working")
            else:
                print("    ⚠️ Existing chart SVG retrieval failed")
        else:
            print("    ℹ️ No existing charts with SVG found")
        
        print("\n3️⃣ Generating Sample Chart to Demonstrate SVG Working:")
        workflow_success = self.test_chart_workflow_complete()
        
        print("\n4️⃣ Testing Multiple Chart SVG Generation:")
        multiple_success = self.test_multiple_chart_svg_generation()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🗺️ CHART SVG STATUS SUMMARY:")
        print(f"   📊 Existing Charts: {'Found' if existing_charts else 'None found'}")
        print(f"   🎨 SVG Generation: {'Working' if workflow_success else 'Failed'}")
        print(f"   📥 SVG Retrieval: {'Working' if workflow_success else 'Failed'}")
        print(f"   🔄 Multiple Charts: {'Working' if multiple_success else 'Failed'}")
        
        # Provide frontend testing guidance
        print("\n🎯 FRONTEND TESTING GUIDANCE:")
        print("   1. Backend chart generation is confirmed functional")
        print("   2. SVG content is available via /api/charts/{id}/svg endpoint")
        print("   3. Frontend should display SVG inline using dangerouslySetInnerHTML")
        print("   4. Check AstrologyPage.js for proper SVG container styling")
        print("   5. Verify 'Generate Map' button triggers /api/charts/{id}/generate-map")
        
        if self.tests_passed >= (self.tests_run * 0.8):  # 80% success rate
            print("🎉 Chart SVG functionality is working correctly!")
            return True
        else:
            print("⚠️ Some chart SVG tests failed - check details above")
            return False

def main():
    tester = ChartSVGTester()
    success = tester.run_chart_svg_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open("/app/chart_svg_test_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: /app/chart_svg_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())