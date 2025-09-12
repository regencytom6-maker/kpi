"""
Script to apply the raw_materials field changes and sync existing data.
This will:
1. Make and apply migrations
2. Run the sync script to populate raw_materials
"""
import os
import sys
import subprocess
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def main():
    print("Step 1: Making migrations for the raw_materials field...")
    result = subprocess.run(["pharma_env\\Scripts\\python.exe", "manage.py", "makemigrations"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error making migrations: {result.stderr}")
        return

    print("\nStep 2: Applying migrations...")
    result = subprocess.run(["pharma_env\\Scripts\\python.exe", "manage.py", "migrate"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error applying migrations: {result.stderr}")
        return

    print("\nStep 3: Syncing ProductMaterial data to raw_materials field...")
    from sync_product_materials import run
    run()

    print("\nCompleted successfully!")

if __name__ == "__main__":
    main()
