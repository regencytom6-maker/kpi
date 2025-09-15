# Fix database references to deleted BMRs
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR
from django.db import connection

def clean_inconsistent_bmr_references():
    print("\n--- Cleaning inconsistent BMR references ---")
    
    # Check for any QC phases referencing non-existent BMRs
    with connection.cursor() as cursor:
        # This query finds BatchPhaseExecution records where bmr_id doesn't exist in BMR table
        cursor.execute("""
            SELECT bpe.id, bpe.bmr_id, pp.phase_name, bpe.status 
            FROM workflow_batchphaseexecution bpe
            JOIN workflow_productionphase pp ON bpe.phase_id = pp.id
            LEFT JOIN bmr_bmr bmr ON bpe.bmr_id = bmr.id
            WHERE bmr.id IS NULL
        """)
        
        orphaned_phases = cursor.fetchall()
        
    if orphaned_phases:
        print(f"Found {len(orphaned_phases)} phase executions referencing deleted BMRs:")
        for phase in orphaned_phases:
            print(f"  - Phase ID: {phase[0]}, Referenced BMR ID: {phase[1]}, Phase: {phase[2]}, Status: {phase[3]}")
        
        confirmation = input("\nDo you want to delete these orphaned phase executions? (y/n): ")
        if confirmation.lower() == 'y':
            for phase in orphaned_phases:
                BatchPhaseExecution.objects.filter(id=phase[0]).delete()
            print(f"Deleted {len(orphaned_phases)} orphaned phase executions.")
        else:
            print("No changes made.")
    else:
        print("No orphaned phase executions found.")
    
    # Check for phases referencing a specific BMR number
    bmr_number_to_check = "BMR20250001"
    print(f"\nChecking for phases referencing {bmr_number_to_check}...")
    
    try:
        # Try to find BMR with this number
        bmr = BMR.objects.filter(bmr_number=bmr_number_to_check).first()
        if bmr:
            print(f"BMR found in database: {bmr.bmr_number} (ID: {bmr.id}, Batch: {bmr.batch_number})")
            
            # Check phases for this BMR
            phases = BatchPhaseExecution.objects.filter(bmr=bmr)
            print(f"Found {phases.count()} phases for this BMR:")
            for phase in phases:
                print(f"  - {phase.phase.phase_name}: {phase.status}")
                
            confirmation = input(f"\nDo you want to delete BMR {bmr_number_to_check} and all its phases? (y/n): ")
            if confirmation.lower() == 'y':
                # First delete all phases
                phases.delete()
                # Then delete the BMR
                bmr.delete()
                print(f"Deleted BMR {bmr_number_to_check} and all its phases.")
            else:
                print("No changes made.")
        else:
            print(f"No BMR with number {bmr_number_to_check} found in database.")
            
            # Check if any phases reference this BMR by name in logs
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT bpe.id, bpe.bmr_id, pp.phase_name, bpe.status, bpe.operator_comments 
                    FROM workflow_batchphaseexecution bpe
                    JOIN workflow_productionphase pp ON bpe.phase_id = pp.id
                    WHERE bpe.operator_comments LIKE %s
                """, [f'%{bmr_number_to_check}%'])
                
                phases = cursor.fetchall()
                
            if phases:
                print(f"Found {len(phases)} phases referencing {bmr_number_to_check} in comments:")
                for phase in phases:
                    print(f"  - Phase ID: {phase[0]}, BMR ID: {phase[1]}, Phase: {phase[2]}, Status: {phase[3]}")
                    print(f"    Comments: {phase[4]}")
                    
                confirmation = input("\nDo you want to delete these phases? (y/n): ")
                if confirmation.lower() == 'y':
                    for phase in phases:
                        BatchPhaseExecution.objects.filter(id=phase[0]).delete()
                    print(f"Deleted {len(phases)} phases.")
                else:
                    print("No changes made.")
            else:
                print(f"No phases found referencing {bmr_number_to_check} in comments.")
            
    except Exception as e:
        print(f"Error checking BMR {bmr_number_to_check}: {e}")

if __name__ == "__main__":
    clean_inconsistent_bmr_references()