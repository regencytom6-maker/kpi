# Verify BMR numbers in database against logs

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR

def verify_bmrs():
    print("\n--- Verifying BMRs in Database ---")
    
    # Get all BMRs
    bmrs = BMR.objects.all()
    print(f"Total BMRs in database: {bmrs.count()}")
    
    # Print BMR details
    print("\nBMR Details:")
    for bmr in bmrs:
        print(f"BMR Number: {bmr.bmr_number}, Batch Number: {bmr.batch_number}")
        
        # Check phase executions for this BMR
        phases = BatchPhaseExecution.objects.filter(bmr=bmr)
        print(f"  Phases: {phases.count()}")
        for phase in phases:
            print(f"    - {phase.phase.phase_name}: {phase.status}")
    
    # Check for phases with specific BMR numbers from logs
    problematic_bmrs = ["BMR20250001", "BMR20250002"]
    
    for bmr_number in problematic_bmrs:
        print(f"\nChecking for BMR {bmr_number}...")
        bmr = BMR.objects.filter(bmr_number=bmr_number).first()
        
        if bmr:
            print(f"  Found in database: {bmr.bmr_number} (Batch: {bmr.batch_number})")
            phases = BatchPhaseExecution.objects.filter(bmr=bmr)
            print(f"  Has {phases.count()} phases")
        else:
            print(f"  Not found in database")
            
            # Look for phases referencing a BMR with this number in comments
            comments_phases = BatchPhaseExecution.objects.filter(operator_comments__contains=bmr_number)
            if comments_phases.exists():
                print(f"  Found {comments_phases.count()} phases referencing this BMR in comments")
                for phase in comments_phases:
                    print(f"    - Phase ID: {phase.id}, BMR: {phase.bmr.bmr_number if phase.bmr else 'None'}, Phase: {phase.phase.phase_name}, Status: {phase.status}")

if __name__ == "__main__":
    verify_bmrs()