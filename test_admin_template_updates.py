#!/usr/bin/env python
"""
Test script to verify the admin dashboard and timeline template updates.
This script:
1. Loads the admin dashboard to check the sidebar implementation
2. Loads the admin timeline to check the tabular view implementation
"""
import os
import sys
import django
import requests
from time import sleep

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse

User = get_user_model()

def get_admin_user():
    """Get an admin user for testing."""
    # Try to find a superuser
    admin_users = User.objects.filter(is_superuser=True)
    if admin_users.exists():
        return admin_users.first()
    
    # If no superuser, try staff user
    staff_users = User.objects.filter(is_staff=True)
    if staff_users.exists():
        return staff_users.first()
    
    # If no staff, get any user with 'admin' in username
    admin_users = User.objects.filter(username__icontains='admin')
    if admin_users.exists():
        return admin_users.first()
    
    return None

def check_template_rendering():
    """Check that both admin dashboard and timeline templates render correctly."""
    admin_user = get_admin_user()
    
    if not admin_user:
        print("ERROR: No admin user found. Cannot test templates.")
        return
    
    print(f"Using user {admin_user.username} for testing.")
    
    # Create test client and log in
    client = Client()
    client.force_login(admin_user)
    
    # Test admin dashboard
    print("\nChecking admin dashboard with sidebar...")
    response = client.get(reverse('dashboards:admin_dashboard'))
    if response.status_code == 200:
        print("✅ Admin dashboard loaded successfully (status 200)")
        # Check for sidebar elements
        if 'sidebar' in response.content.decode('utf-8'):
            print("✅ Sidebar found in admin dashboard template")
        else:
            print("❌ Sidebar NOT found in admin dashboard template")
    else:
        print(f"❌ Admin dashboard failed to load (status {response.status_code})")

    # Test if the admin_timeline_table.html template exists
    print("\nChecking if admin_timeline_table.html exists...")
    try:
        with open('templates/dashboards/admin_timeline_table.html', 'r') as f:
            print("✅ admin_timeline_table.html file exists")
    except FileNotFoundError:
        print("❌ admin_timeline_table.html file NOT found")

    # Test if the server is running and if we can access the admin timeline
    print("\nChecking if server is running and admin timeline is accessible...")
    try:
        response = requests.get('http://localhost:8000/dashboards/admin/timeline/', timeout=2)
        if response.status_code == 200:
            print("✅ Server is running and admin timeline is accessible")
        else:
            print(f"❌ Admin timeline returned status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running.")
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Server might be slow or not responding.")

if __name__ == '__main__':
    check_template_rendering()
    print("\nDone!")
