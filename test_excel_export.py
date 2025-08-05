#!/usr/bin/env python
"""
Test the timeline Excel export functionality
"""
import os
import sys
import requests
import webbrowser
from pathlib import Path
import tempfile

# Initialize Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')

import django
django.setup()

def test_excel_export():
    """Test the Excel export functionality"""
    print("\n=== Testing Timeline Excel Export ===\n")
    
    try:
        # Start server in background if not already running
        try:
            response = requests.get('http://127.0.0.1:8000/', timeout=1)
            print("Django server is already running")
        except (requests.ConnectionError, requests.Timeout):
            print("Starting Django server in background...")
            os.system('start cmd /c "cd /d %CD% && .\\pharma_env\\Scripts\\python.exe manage.py runserver"')
            import time
            time.sleep(5)  # Wait for server to start
        
        # Test Excel export
        print("\nDownloading Excel export...")
        export_url = 'http://127.0.0.1:8000/dashboard/admin/export-timeline/?format=excel'
        response = requests.get(export_url)
        
        if response.status_code == 200:
            print("✅ Excel export successful!")
            
            # Save the Excel file
            temp_dir = tempfile.gettempdir()
            excel_path = os.path.join(temp_dir, "bmr_timeline_export.xlsx")
            
            with open(excel_path, 'wb') as f:
                f.write(response.content)
                
            print(f"Excel file saved to: {excel_path}")
            print("Opening Excel file...")
            webbrowser.open(excel_path)
        else:
            print(f"❌ Excel export failed with status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    test_excel_export()
