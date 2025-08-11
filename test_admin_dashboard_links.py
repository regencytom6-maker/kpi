import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

def test_admin_dashboard_links():
    # Create a client and log in as admin
    client = Client()
    
    # Get or create a superuser for testing
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    
    client.force_login(user)
    
    # List of URLs to test
    urls_to_test = [
        ('dashboards:admin_dashboard', [], 'Admin Dashboard'),
        ('dashboards:admin_timeline', [], 'Admin Timeline'),
        ('dashboards:admin_fgs_monitor', [], 'FGS Monitor'),
        ('bmr:list', [], 'BMR List'),
        ('bmr:create', [], 'BMR Creation'),
        ('admin:index', [], 'Django Admin'),
    ]
    
    # Test each URL
    for url_name, args, description in urls_to_test:
        try:
            url = reverse(url_name, args=args)
            response = client.get(url)
            status = response.status_code
            print(f"✓ {description} ({url_name}): URL {url} - Status {status}")
        except Exception as e:
            print(f"✗ {description} ({url_name}): ERROR - {str(e)}")

if __name__ == "__main__":
    test_admin_dashboard_links()
