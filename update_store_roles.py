#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from accounts.models import CustomUser

def update_user_roles():
    """Update user roles to reflect the new store separation"""
    print("Updating user roles for store separation...")
    
    # Example: Update any existing store managers that should be packaging store
    # You can adjust these based on your specific users
    
    # Show current users
    store_users = CustomUser.objects.filter(role__in=['store_manager'])
    print(f"Found {store_users.count()} store users:")
    for user in store_users:
        print(f"  - {user.username}: {user.get_role_display()}")
    
    print("\nNew role choices available:")
    print("  - store_manager: Material Dispensing")
    print("  - packaging_store: Packaging Material Release")  
    print("  - finished_goods_store: Finished Goods Storage")
    
    print("\nYou can update user roles in the admin panel at /admin/accounts/customuser/")

if __name__ == '__main__':
    update_user_roles()
