#!/usr/bin/env python
"""
Debug script to check packing operator phases
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from accounts.models import CustomUser

def debug_packing_phases():
    """Debug what phases are available for packing operator"""
    
    # Get all BMRs
    bmrs = BMR.objects.all()
    print(f"Total BMRs: {bmrs.count()}")
    
    for bmr in bmrs:
        print(f"\n=== BMR: {bmr.batch_number} ({bmr.product.product_name}) ===")
        
        # Check all phases for this BMR
        all_phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        print("All phases for this BMR:")
        for phase in all_phases:
            print(f"  - {phase.phase.phase_name}: {phase.status}")
        
        # Check phases available for packing operator
        packing_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
        print(f"\nPacking operator phases (pending/in_progress): {packing_phases.count()}")
        
        for phase in packing_phases:
            print(f"  - {phase.phase.phase_name}: {phase.status}")
        
        # Check if packaging_material_release is completed
        packaging_release = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='packaging_material_release'
        ).first()
        
        if packaging_release:
            print(f"\nPackaging material release status: {packaging_release.status}")
        else:
            print("\nNo packaging material release phase found")
        
        # Check what packing phases exist
        packing_phase_names = ['blister_packing', 'bulk_packing', 'secondary_packaging']
        for phase_name in packing_phase_names:
            phase_exec = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name=phase_name
            ).first()
            if phase_exec:
                print(f"  {phase_name}: {phase_exec.status}")
            else:
                print(f"  {phase_name}: NOT FOUND")

if __name__ == "__main__":
    debug_packing_phases()
