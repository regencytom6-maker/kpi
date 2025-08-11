"""
This script runs the repair_coating_workflow directly without shell redirection
which is causing issues in Windows PowerShell
"""
import os
import traceback

print("Starting Coating Workflow Repair")
print("===============================")
print("Setting up Django environment...")

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')

    import django
    django.setup()
    print("Django environment ready.")

    # Now run the repair functionality 
    print("Loading repair script...")
    with open('repair_coating_workflow.py', 'r') as f:
        repair_code = f.read()
        print("Executing repair code...")
        exec(repair_code)
    
    print("Repair process completed successfully!")
except Exception as e:
    print(f"ERROR: {str(e)}")
    print("Detailed traceback:")
    traceback.print_exc()
    print("Repair process failed.")
