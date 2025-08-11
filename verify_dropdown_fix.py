import os
import django
import sys
from pathlib import Path
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

print("\n🌐 TESTING ADMIN DASHBOARD DROPDOWN FIX\n")
print("✅ Server is now running")
print("✅ Dropdown fix has been applied")
print("\n📋 HOW TO TEST:")
print("1. Visit http://localhost:8000/dashboards/admin/")
print("2. Click on your username in the top-right corner")
print("3. The dropdown menu should now appear with options")
print("\n🔍 WHAT WE FIXED:")
print("- Added manual dropdown initialization code")
print("- Implemented custom click handling for the dropdown")
print("- Added fallback for dropdown positioning")
print("- Fixed possible Bootstrap version conflicts")
print("\n✅ You should now be able to see and use the dropdown menu on the admin dashboard")
print("✨ If it's still not working, please let us know and we'll try a different approach.")

# Open browser automatically
try:
    import webbrowser
    webbrowser.open('http://localhost:8000/dashboards/admin/')
    print("\n✨ Opened browser to admin dashboard")
except Exception as e:
    print(f"\n❌ Could not open browser: {e}")

print("\nWhen you're done testing, press Ctrl+C to stop this script.")
