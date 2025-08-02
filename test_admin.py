"""
Test script to verify admin registration
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.contrib import admin
from accounts.models import CustomUser

print("Checking admin registration...")
print(f"CustomUser model registered: {CustomUser in admin.site._registry}")
print(f"All registered models: {list(admin.site._registry.keys())}")

# Check if users exist
users = CustomUser.objects.all()
print(f"Total users in database: {users.count()}")
for user in users:
    print(f"- {user.username} ({user.get_role_display()})")
