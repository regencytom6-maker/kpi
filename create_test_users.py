#!/usr/bin/env python
"""
Script to create test users for all roles in Kampala Pharmaceutical Industries
Run this script to create users with known passwords for testing
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from accounts.models import CustomUser

def create_test_users():
    """Create test users for all pharmaceutical roles"""
    
    # Define test users with their roles and passwords
    test_users = [
        # Management Roles
        {'username': 'qa_officer', 'email': 'qa@kampala-pharma.com', 'role': 'qa', 'password': 'qa123'},
        {'username': 'regulatory_officer', 'email': 'regulatory@kampala-pharma.com', 'role': 'regulatory', 'password': 'reg123'},
        {'username': 'store_manager', 'email': 'store@kampala-pharma.com', 'role': 'store_manager', 'password': 'store123'},
        {'username': 'qc_officer', 'email': 'qc@kampala-pharma.com', 'role': 'qc', 'password': 'qc123'},
        
        # Production Operators
        {'username': 'mixing_op', 'email': 'mixing@kampala-pharma.com', 'role': 'mixing_operator', 'password': 'mix123'},
        {'username': 'granulation_op', 'email': 'granulation@kampala-pharma.com', 'role': 'granulation_operator', 'password': 'gran123'},
        {'username': 'blending_op', 'email': 'blending@kampala-pharma.com', 'role': 'blending_operator', 'password': 'blend123'},
        {'username': 'compression_op', 'email': 'compression@kampala-pharma.com', 'role': 'compression_operator', 'password': 'comp123'},
        {'username': 'coating_op', 'email': 'coating@kampala-pharma.com', 'role': 'coating_operator', 'password': 'coat123'},
        {'username': 'drying_op', 'email': 'drying@kampala-pharma.com', 'role': 'drying_operator', 'password': 'dry123'},
        {'username': 'filling_op', 'email': 'filling@kampala-pharma.com', 'role': 'filling_operator', 'password': 'fill123'},
        {'username': 'tube_filling_op', 'email': 'tube_filling@kampala-pharma.com', 'role': 'tube_filling_operator', 'password': 'tube123'},
        {'username': 'packing_op', 'email': 'packing@kampala-pharma.com', 'role': 'packing_operator', 'password': 'pack123'},
        {'username': 'sorting_op', 'email': 'sorting@kampala-pharma.com', 'role': 'sorting_operator', 'password': 'sort123'},
    ]
    
    created_users = []
    existing_users = []
    
    print("Creating test users for Kampala Pharmaceutical Industries...")
    print("=" * 60)
    
    for user_data in test_users:
        username = user_data['username']
        
        # Check if user already exists
        if CustomUser.objects.filter(username=username).exists():
            existing_users.append(username)
            print(f"❌ User '{username}' already exists")
            continue
        
        # Create new user
        try:
            user = CustomUser.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                role=user_data['role'],
                first_name=user_data['role'].replace('_', ' ').title(),
                last_name="Operator" if "operator" in user_data['role'] else "Officer"
            )
            created_users.append({
                'username': username,
                'password': user_data['password'],
                'role': user_data['role']
            })
            print(f"✅ Created user '{username}' with role '{user_data['role']}'")
            
        except Exception as e:
            print(f"❌ Error creating user '{username}': {e}")
    
    print("\n" + "=" * 60)
    print("USER CREATION SUMMARY")
    print("=" * 60)
    
    if created_users:
        print(f"\n✅ Successfully created {len(created_users)} users:")
        print("-" * 40)
        for user in created_users:
            print(f"Username: {user['username']:<15} | Password: {user['password']:<8} | Role: {user['role']}")
    
    if existing_users:
        print(f"\n⚠️  {len(existing_users)} users already existed:")
        print("-" * 40)
        for username in existing_users:
            print(f"Username: {username}")
    
    print("\n" + "=" * 60)
    print("LOGIN INSTRUCTIONS")
    print("=" * 60)
    print("1. Start the server: .\\start_server.ps1")
    print("2. Go to: http://127.0.0.1:8000/accounts/login/")
    print("3. Use any username/password combination above")
    print("4. Admin access: admin/admin123")
    print("\nEach user will be redirected to their role-specific dashboard!")

if __name__ == "__main__":
    create_test_users()
