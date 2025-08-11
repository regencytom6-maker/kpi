import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

# Restart Django server to load new template filters
print("Restarting server to load new template filters...")
