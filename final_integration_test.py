#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

def test_integrations():
    base_url = 'https://astro-reader-1.preview.emergentagent.com'
    api_url = f'{base_url}/api'

    # Create user
    test_email = f'final_test_{datetime.now().strftime("%H%M%S")}@celestia.com'
    register_data = {
        'name': 'Final Test User',
        'email': test_email,
        'password': 'TestPass123!',
        'role': 'client'
    }

    response = requests.post(f'{api_url}/auth/register', json=register_data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        token = result['access_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        print('✅ User created successfully')
        
        # Test SendGrid with a far future time slot
        start_time = datetime.now() + timedelta(days=30, hours=9)  # 30 days from now at 9 AM
        end_time = start_time + timedelta(hours=1)
        
        session_data = {
            'service_type': 'tarot-reading',
            'start_at': start_time.isoformat(),
            'end_at': end_time.isoformat(),
            'client_message': 'Testing SendGrid integration with far future date'
        }
        
        session_response = requests.post(f'{api_url}/sessions', json=session_data, headers=headers, timeout=30)
        
        if session_response.status_code == 200:
            session_result = session_response.json()
            session_id = session_result['id']
            print(f'✅ SendGrid Test Session Created: {session_id}')
            print('📧 Should trigger SendGrid emails (check backend logs for 403 errors)')
            
            # Test Stripe integration
            payment_request = {
                'service_type': 'tarot-reading',
                'session_id': session_id,
                'origin_url': base_url
            }
            
            stripe_response = requests.post(f'{api_url}/payments/v1/checkout/session', json=payment_request, headers=headers, timeout=30)
            
            if stripe_response.status_code == 200:
                stripe_result = stripe_response.json()
                checkout_session_id = stripe_result['session_id']
                checkout_url = stripe_result['url']
                
                print(f'✅ Stripe Checkout Session: {checkout_session_id}')
                print(f'💳 Checkout URL: {checkout_url[:60]}...')
                
                # Check payment status
                status_response = requests.get(f'{api_url}/payments/v1/checkout/status/{checkout_session_id}', headers=headers, timeout=30)
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f'✅ Payment Status: {status_result["payment_status"]}')
                    print(f'💰 Amount: ${status_result["amount"]} {status_result["currency"]}')
                    print('🎉 STRIPE INTEGRATION FULLY WORKING!')
                    return True
                else:
                    print(f'❌ Payment status check failed: {status_response.status_code}')
            else:
                print(f'❌ Stripe checkout failed: {stripe_response.status_code}')
                print(f'Response: {stripe_response.text}')
        else:
            print(f'❌ Session creation failed: {session_response.status_code}')
            print(f'Response: {session_response.text}')
    else:
        print(f'❌ User creation failed: {response.status_code}')
    
    return False

if __name__ == "__main__":
    test_integrations()