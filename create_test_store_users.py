#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from accounts.models import CustomUser

def create_test_users():
    """Create test users for different store roles"""
    print("Creating test users for store roles...")
    
    # Create packaging store user
    if not CustomUser.objects.filter(username='packaging_user').exists():
        user = CustomUser.objects.create_user(
            username='packaging_user',
            password='test123',
            email='packaging@kampala.com',
            first_name='Packaging',
            last_name='Store',
            role='packaging_store',
            employee_id='PKG001',
            department='Packaging Store'
        )
        print(f"Created packaging store user: {user.username}")
    
    # Create finished goods store user
    if not CustomUser.objects.filter(username='finished_goods_user').exists():
        user = CustomUser.objects.create_user(
            username='finished_goods_user',
            password='test123',
            email='finished@kampala.com',
            first_name='Finished',
            last_name='Goods',
            role='finished_goods_store',
            employee_id='FGS001',
            department='Finished Goods Store'
        )
        print(f"Created finished goods store user: {user.username}")
    
    # Create regular store manager
    if not CustomUser.objects.filter(username='store_manager').exists():
        user = CustomUser.objects.create_user(
            username='store_manager',
            password='test123',
            email='store@kampala.com',
            first_name='Store',
            last_name='Manager',
            role='store_manager',
            employee_id='STR001',
            department='Store'
        )
        print(f"Created store manager user: {user.username}")
    
    print("\nTest users created! You can now login with:")
    print("- packaging_user / test123 (Packaging Store)")
    print("- finished_goods_user / test123 (Finished Goods Store)")
    print("- store_manager / test123 (Store Manager)")

if __name__ == '__main__':
    create_test_users()
