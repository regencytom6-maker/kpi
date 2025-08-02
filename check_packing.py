#!/usr/bin/env python
"""
Simple check of packing operator phases
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.services import WorkflowService

def check_packing_operator():
    """Check what phases packing operator can see"""
    
    bmrs = BMR.objects.all()
    print(f"Total BMRs: {bmrs.count()}")
    
    total_packing_phases = 0
    
    for bmr in bmrs:
        packing_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
        if packing_phases.exists():
            print(f"\nBMR {bmr.batch_number} - Packing phases available:")
            for phase in packing_phases:
                print(f"  - {phase.phase.phase_name}: {phase.status}")
                total_packing_phases += 1
        else:
            print(f"\nBMR {bmr.batch_number} - No packing phases available")
    
    print(f"\nTotal packing phases available: {total_packing_phases}")

if __name__ == "__main__":
    check_packing_operator()
