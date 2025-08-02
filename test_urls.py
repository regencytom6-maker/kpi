"""
Test script to verify URL patterns and view functions
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from dashboards.views import dashboard_home

print("Testing URL configuration...")

# Test URL patterns
try:
    home_url = reverse('home')
    print(f"✅ Home URL: {home_url}")
except Exception as e:
    print(f"❌ Home URL error: {e}")

try:
    admin_url = reverse('admin:index')
    print(f"✅ Admin URL: {admin_url}")
except Exception as e:
    print(f"❌ Admin URL error: {e}")

# Test view function
try:
    factory = RequestFactory()
    
    # Test anonymous user
    request = factory.get('/')
    request.user = type('MockUser', (), {'is_authenticated': False})()
    
    response = dashboard_home(request)
    print(f"✅ Anonymous user response status: {response.status_code}")
    
except Exception as e:
    print(f"❌ View function error: {e}")

print("\nURL configuration test complete!")
print("Try accessing: http://127.0.0.1:8000/")
print("Admin panel: http://127.0.0.1:8000/admin/")
