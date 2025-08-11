"""
This script tests the enhanced admin dashboard with analytics.
"""
import subprocess
import webbrowser
import time
import os

def main():
    print("Starting Django server...")
    
    # Use the environment-specific python command
    python_cmd = "pharma_env\\Scripts\\python.exe"
    
    # Start the server
    server_process = subprocess.Popen([python_cmd, "manage.py", "runserver"], 
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True)
    
    # Give the server time to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Open the admin dashboard in the default browser
    dashboard_url = "http://127.0.0.1:8000/dashboard/admin-overview/"
    print(f"Opening admin dashboard: {dashboard_url}")
    webbrowser.open(dashboard_url)
    
    print("\nPress Ctrl+C to stop the server when done testing.")
    
    try:
        # Keep the script running until manually terminated
        while True:
            line = server_process.stdout.readline()
            if line:
                print(line.strip())
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()
        print("Server stopped.")

if __name__ == "__main__":
    main()
