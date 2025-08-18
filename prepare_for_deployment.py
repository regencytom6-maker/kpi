"""
This script prepares the KPI system for deployment by:
1. Collecting static files
2. Running migrations
3. Creating a superuser if needed
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.core.management import call_command

def prepare_for_deployment():
    print("Preparing KPI system for deployment...")
    
    # Collect static files
    print("\n1. Collecting static files...")
    call_command('collectstatic', interactive=False)
    
    # Run migrations
    print("\n2. Running database migrations...")
    call_command('migrate')
    
    # Create a superuser if none exists
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("\n3. No superuser found. Creating a new superuser...")
        username = input("Enter username (default: admin): ") or "admin"
        email = input("Enter email: ")
        password = input("Enter password: ")
        
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully!")
    else:
        print("\n3. Superuser already exists. Skipping creation.")
    
    # Setup product phases if needed
    try:
        print("\n4. Setting up production phases...")
        call_command('setup_phases')
        print("Production phases set up successfully!")
    except:
        print("Note: 'setup_phases' command not found or failed. You may need to run it manually.")
    
    print("\nDeployment preparation completed successfully!")
    print("\nNext steps:")
    print("1. Update kampala_pharma/production_settings.py with your deployment details")
    print("2. Follow the instructions in DEPLOYMENT_GUIDE_PYTHONANYWHERE.md")
    print("3. Deploy your application")

if __name__ == "__main__":
    prepare_for_deployment()
