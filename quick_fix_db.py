# One-line command to remove references to deleted BMR
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from django.db import connection

def clean_specific_bmr():
    # Target BMR number
    bmr_number = "BMR20250001"
    
    # This query deletes BatchPhaseExecution records where operator_comments contains the BMR number
    # and the BMR doesn't exist in the database
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM workflow_batchphaseexecution
            WHERE operator_comments LIKE %s
            AND bmr_id NOT IN (SELECT id FROM bmr_bmr)
        """, [f'%{bmr_number}%'])
        
        deleted_count = cursor.rowcount
    
    print(f"Removed {deleted_count} phantom references to {bmr_number}")
    
    # This query looks for other references to this BMR
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM workflow_batchphaseexecution
            WHERE bmr_id NOT IN (SELECT id FROM bmr_bmr)
        """)
        
        deleted_count = cursor.rowcount
    
    print(f"Removed {deleted_count} orphaned phase executions")

if __name__ == "__main__":
    clean_specific_bmr()