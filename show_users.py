#!/usr/bin/env python
"""
Script to show existing user passwords and reset them if needed
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from accounts.models import CustomUser

def show_existing_users():
    """Show all existing users and their roles"""
    
    print("EXISTING USERS IN KAMPALA PHARMACEUTICAL SYSTEM")
    print("=" * 60)
    
    users = CustomUser.objects.all().order_by('role', 'username')
    
    if not users.exists():
        print("No users found in the system.")
        return
    
    # Default passwords for existing users (these were set during creation)
    default_passwords = {
        'admin': 'admin123',
        'qa_officer': 'qa123',
        'store_manager': 'store123',
        # Add more as needed
    }
    
    print(f"{'Username':<20} | {'Role':<20} | {'Email':<30} | {'Status'}")
    print("-" * 80)
    
    for user in users:
        status = "Active" if user.is_active else "Inactive"
        email = user.email or "No email"
        print(f"{user.username:<20} | {user.role:<20} | {email:<30} | {status}")
    
    print("\n" + "=" * 60)
    print("DEFAULT PASSWORDS FOR EXISTING USERS")
    print("=" * 60)
    
    for username, password in default_passwords.items():
        if CustomUser.objects.filter(username=username).exists():
            print(f"Username: {username:<15} | Password: {password}")
    
    print("\nNote: If you need to reset passwords, use the admin panel reset feature.")

if __name__ == "__main__":
    show_existing_users()
