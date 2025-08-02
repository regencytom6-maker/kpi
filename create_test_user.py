#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from accounts.models import CustomUser

def create_test_user():
    """Create a test user for login testing"""
    username = 'testuser'
    
    if CustomUser.objects.filter(username=username).exists():
        print(f"User {username} already exists")
        user = CustomUser.objects.get(username=username)
    else:
        user = CustomUser.objects.create_user(
            username=username,
            password='test123',
            email='test@kampala.com',
            first_name='Test',
            last_name='User',
            role='qa',
            employee_id='TEST001',
            department='QA'
        )
        print(f"Created user: {user.username}")
    
    print(f"Login with: {username} / test123")
    return user

if __name__ == '__main__':
    create_test_user()
