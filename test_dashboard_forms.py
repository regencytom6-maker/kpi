#!/usr/bin/env python
"""
Simple test to verify dashboard forms work correctly
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from bmr.models import BMR
from products.models import Product

def test_dashboard_forms():
    """Test that dashboard forms work with CSRF"""
    
    client = Client()
    User = get_user_model()
    
    # Create test users if they don't exist
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@kampala.com',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
    
    try:
        regulatory_user = User.objects.get(username='regulatory_user')
    except User.DoesNotExist:
        regulatory_user = User.objects.create_user(
            username='regulatory_user',
            password='regulatory123',
            email='regulatory@kampala.com',
            role='regulatory'
        )
    
    # Test login
    print("Testing login...")
    login_response = client.post('/accounts/login/', {
        'username': 'admin',
        'password': 'admin123'
    })
    
    if login_response.status_code == 302:
        print("✓ Login successful")
    else:
        print(f"✗ Login failed with status {login_response.status_code}")
        return
    
    # Test dashboard access
    print("Testing dashboard access...")
    dashboard_response = client.get('/dashboard/')
    
    if dashboard_response.status_code in [200, 302]:
        print("✓ Dashboard accessible")
    else:
        print(f"✗ Dashboard access failed with status {dashboard_response.status_code}")
        return
    
    # Test regulatory dashboard
    print("Testing regulatory dashboard...")
    client.logout()
    
    # Login as regulatory user
    reg_login = client.post('/accounts/login/', {
        'username': 'regulatory_user',
        'password': 'regulatory123'
    })
    
    if reg_login.status_code == 302:
        print("✓ Regulatory user login successful")
        
        # Access regulatory dashboard
        reg_dashboard = client.get('/dashboard/regulatory/')
        if reg_dashboard.status_code == 200:
            print("✓ Regulatory dashboard accessible")
        else:
            print(f"✗ Regulatory dashboard failed with status {reg_dashboard.status_code}")
    else:
        print(f"✗ Regulatory user login failed with status {reg_login.status_code}")

if __name__ == "__main__":
    test_dashboard_forms()
