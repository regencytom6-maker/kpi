#!/usr/bin/env python
"""
Manually fix the specific workflow issues
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

def fix_specific_issues():
    """Fix specific workflow issues"""
    
    print("Fixing specific workflow issues...")
    
    # Fix BMR 0022025 - packaging_material_release should be before bulk_packing
    bmr_0022025 = BMR.objects.filter(batch_number='0022025').first()
    if bmr_0022025:
        print(f"\nFixing BMR {bmr_0022025.batch_number}:")
        
        # Make packaging_material_release pending (it should come before bulk_packing)
        packaging_release = BatchPhaseExecution.objects.filter(
            bmr=bmr_0022025,
            phase__phase_name='packaging_material_release'
        ).first()
        
        if packaging_release and packaging_release.status == 'pending':
            print("  packaging_material_release is already pending - this is correct for the new workflow order")
        
        # Bulk packing should wait for packaging material release
        bulk_packing = BatchPhaseExecution.objects.filter(
            bmr=bmr_0022025,
            phase__phase_name='bulk_packing'
        ).first()
        
        if bulk_packing and bulk_packing.status == 'pending':
            # This is wrong - bulk_packing should wait for packaging material release
            bulk_packing.status = 'not_ready'
            bulk_packing.save()
            print("  Set bulk_packing to not_ready (will be triggered after packaging material release)")
        
        # Secondary packaging should also wait
        secondary_packaging = BatchPhaseExecution.objects.filter(
            bmr=bmr_0022025,
            phase__phase_name='secondary_packaging'
        ).first()
        
        if secondary_packaging and secondary_packaging.status == 'pending':
            secondary_packaging.status = 'not_ready'
            secondary_packaging.save()
            print("  Set secondary_packaging to not_ready")
    
    # Fix BMR 0012025 - sorting should be pending after filling
    bmr_0012025 = BMR.objects.filter(batch_number='0012025').first()
    if bmr_0012025:
        print(f"\nFixing BMR {bmr_0012025.batch_number}:")
        
        # Check if filling is completed
        filling = BatchPhaseExecution.objects.filter(
            bmr=bmr_0012025,
            phase__phase_name='filling'
        ).first()
        
        if filling and filling.status == 'completed':
            # Make sorting pending
            sorting = BatchPhaseExecution.objects.filter(
                bmr=bmr_0012025,
                phase__phase_name='sorting'
            ).first()
            
            if sorting and sorting.status == 'not_ready':
                sorting.status = 'pending'
                sorting.save()
                print("  Set sorting to pending (filling is completed)")
    
    print("\nAfter fixes:")
    
    # Check the results
    for batch_number in ['0022025', '0012025']:
        bmr = BMR.objects.filter(batch_number=batch_number).first()
        if bmr:
            print(f"\n=== BMR: {batch_number} ===")
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
            for phase in phases:
                print(f"  - {phase.phase.phase_name}: {phase.status}")
            
            # Check packing operator phases
            packing_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
            print(f"  Packing operator can see: {[p.phase.phase_name for p in packing_phases]}")

if __name__ == "__main__":
    fix_specific_issues()
