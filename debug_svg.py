#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_svg_debug():
    base_url = "https://astro-booking-3.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Register user
    test_email = f"svg_debug_{datetime.now().strftime('%H%M%S')}@celestia.com"
    register_data = {
        "name": "SVG Debug User",
        "email": test_email,
        "password": "SvgDebug123!",
        "role": "client"
    }
    
    response = requests.post(f"{api_url}/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.text}")
        return
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Create birth data
    birth_data = {
        "birth_date": "1990-05-15",
        "birth_time": "10:00",
        "time_accuracy": "exact",
        "birth_place": "New York, NY",
        "latitude": "40.7128",
        "longitude": "-74.0060"
    }
    
    response = requests.post(f"{api_url}/birth-data", json=birth_data, headers=headers)
    if response.status_code != 200:
        print(f"Birth data creation failed: {response.text}")
        return
    
    birth_data_id = response.json()['id']
    print(f"Created birth data: {birth_data_id}")
    
    # Generate chart
    response = requests.post(f"{api_url}/astrology/chart?birth_data_id={birth_data_id}", headers=headers)
    if response.status_code != 200:
        print(f"Chart generation failed: {response.text}")
        return
    
    chart_data = response.json()
    chart_id = chart_data['id']
    chart_svg = chart_data.get('chart_svg')
    
    print(f"Chart ID: {chart_id}")
    print(f"Chart SVG length: {len(str(chart_svg)) if chart_svg else 0}")
    print(f"Chart SVG type: {type(chart_svg)}")
    
    if chart_svg:
        print(f"Chart SVG preview (first 200 chars): {str(chart_svg)[:200]}")
    
    # Test generate-map endpoint
    response = requests.post(f"{api_url}/charts/{chart_id}/generate-map", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"Generate map result: {result}")
    else:
        print(f"Generate map failed: {response.text}")
    
    # Test SVG retrieval endpoint
    response = requests.get(f"{api_url}/charts/{chart_id}/svg", headers=headers)
    print(f"SVG retrieval status: {response.status_code}")
    if response.status_code == 200:
        print(f"SVG content length: {len(response.content)}")
        print(f"SVG content type: {response.headers.get('content-type')}")
        print(f"SVG preview: {response.text[:200]}")
    else:
        print(f"SVG retrieval failed: {response.text}")

if __name__ == "__main__":
    test_svg_debug()