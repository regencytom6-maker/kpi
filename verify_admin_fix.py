"""
Test script to verify the admin dashboard loads correctly after fixing the import error
"""
import requests
import time
import sys

def test_admin_dashboard():
    dashboard_url = "http://127.0.0.1:8000/dashboard/admin-overview/"
    
    print(f"Testing dashboard URL: {dashboard_url}")
    print("Waiting for server to be fully ready...")
    time.sleep(2)
    
    try:
        response = requests.get(dashboard_url)
        
        if response.status_code == 200:
            print("✅ SUCCESS: Admin dashboard loaded successfully!")
            print(f"Status code: {response.status_code}")
            print(f"Response size: {len(response.text)} bytes")
            print("\nThe import error has been fixed. The admin dashboard is working correctly.")
        else:
            print(f"❌ ERROR: Failed to load admin dashboard.")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ ERROR: Exception occurred while testing: {str(e)}")
        
    print("\nMake sure to manually check that all admin dashboard features are working.")

if __name__ == "__main__":
    test_admin_dashboard()
