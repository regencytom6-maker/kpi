#!/usr/bin/env python
"""
Test script to check if CSRF protection is working correctly
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.test import RequestFactory, Client
from django.middleware.csrf import get_token
from django.contrib.auth import get_user_model

def test_csrf_token():
    """Test CSRF token generation"""
    client = Client()
    
    # Get login page
    response = client.get('/accounts/login/')
    print(f"Login page status: {response.status_code}")
    
    # Check if CSRF token is in the response
    if 'csrfmiddlewaretoken' in response.content.decode():
        print("✓ CSRF token found in login page")
    else:
        print("✗ CSRF token NOT found in login page")
    
    # Extract CSRF token from cookies
    csrf_token = None
    if hasattr(response, 'cookies') and 'csrftoken' in response.cookies:
        csrf_token = response.cookies['csrftoken'].value
    
    if csrf_token:
        print(f"✓ CSRF token in cookies: {csrf_token[:20]}...")
    else:
        print("✗ No CSRF token in cookies")
        # Try to extract from form
        content = response.content.decode()
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
        if match:
            csrf_token = match.group(1)
            print(f"✓ CSRF token found in form: {csrf_token[:20]}...")
        else:
            print("✗ Could not extract CSRF token from form")
    
    # Test login with CSRF token
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    # Make sure to include the CSRF token in the request
    login_response = client.post('/accounts/login/', data=login_data)
    print(f"Login POST status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("✓ Login successful (redirected)")
    elif login_response.status_code == 403:
        print("✗ Login failed with 403 - CSRF verification failed")
    else:
        print(f"Login response: {login_response.status_code}")

if __name__ == "__main__":
    test_csrf_token()
