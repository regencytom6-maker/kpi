"""
Test script to check if the admin dashboard loads correctly after fixing the WorkflowPhase import.
"""
import subprocess
import webbrowser
import time
import sys

def main():
    print("Testing admin dashboard after fixing analytics import...")
    
    # Start the Django development server
    python_cmd = "pharma_env\\Scripts\\python.exe"
    
    try:
        # Start the Django server
        process = subprocess.Popen(
            [python_cmd, "manage.py", "runserver"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give the server time to start
        print("Starting server...")
        time.sleep(3)
        
        # Open the admin dashboard in the default browser
        dashboard_url = "http://127.0.0.1:8000/dashboard/admin-overview/"
        print(f"Opening admin dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        print("\nPress Ctrl+C to stop the server when done testing.")
        
        # Monitor for errors
        while True:
            output = process.stdout.readline()
            if output:
                print(output.strip())
            
            error = process.stderr.readline()
            if error:
                print(f"ERROR: {error.strip()}", file=sys.stderr)
            
            if process.poll() is not None:
                break
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nStopping server...")
        process.terminate()
        print("Test completed.")

if __name__ == "__main__":
    main()
