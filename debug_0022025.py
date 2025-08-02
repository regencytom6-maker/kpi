#!/usr/bin/env python
"""
Debug BMR 0022025 specifically
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

def debug_bmr_0022025():
    """Debug BMR 0022025 specifically"""
    
    bmr = BMR.objects.filter(batch_number='0022025').first()
    if not bmr:
        print("BMR 0022025 not found")
        return
    
    print(f"BMR: {bmr.batch_number} - {bmr.product.product_name}")
    print(f"Product type: {bmr.product.product_type}")
    
    # Check all phases
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    print("\nAll phases:")
    for phase in phases:
        print(f"  {phase.phase.phase_name}: {phase.status}")
    
    # Check specifically for packing phases
    packing_phase_names = ['blister_packing', 'bulk_packing', 'secondary_packaging', 'packaging_material_release']
    print("\nPacking-related phases:")
    for phase_name in packing_phase_names:
        phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name=phase_name).first()
        if phase:
            print(f"  {phase_name}: {phase.status}")
        else:
            print(f"  {phase_name}: NOT FOUND")
    
    # Check what packing operator can see
    packing_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
    print(f"\nPacking operator can see ({packing_phases.count()} phases):")
    for phase in packing_phases:
        print(f"  - {phase.phase.phase_name}: {phase.status}")
    
    # Check the packaging_material_release status
    pkg_release = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='packaging_material_release').first()
    if pkg_release:
        print(f"\nPackaging material release: {pkg_release.status}")
        if pkg_release.status == 'pending':
            print("  ^ This needs to be completed before packing phases become available")

if __name__ == "__main__":
    debug_bmr_0022025()
