#!/usr/bin/env python
"""
Debug prerequisite checking for packaging material release
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

def debug_packaging_prerequisites():
    """Debug prerequisites for packaging material release"""
    
    # Get BMR 0022025 that's having issues
    bmr = BMR.objects.filter(batch_number='0022025').first()
    if not bmr:
        print("BMR 0022025 not found")
        return
    
    print(f"=== Debug BMR {bmr.batch_number} ===")
    print(f"Product: {bmr.product.product_name}")
    print(f"Product type: {bmr.product.product_type}")
    print(f"Coating type: {bmr.product.coating_type}")
    print(f"Tablet type: {bmr.product.tablet_type}")
    
    # Get packaging material release phase
    pkg_release = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='packaging_material_release'
    ).first()
    
    if not pkg_release:
        print("Packaging material release phase not found")
        return
    
    print(f"\nPackaging material release:")
    print(f"  Status: {pkg_release.status}")
    print(f"  Phase order: {pkg_release.phase.phase_order}")
    
    # Get all prerequisite phases (lower order)
    prerequisite_phases = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_order__lt=pkg_release.phase.phase_order
    ).order_by('phase__phase_order')
    
    print(f"\nPrerequisite phases (order < {pkg_release.phase.phase_order}):")
    all_completed = True
    for prereq in prerequisite_phases:
        status_icon = "✅" if prereq.status == 'completed' else "❌"
        print(f"  {status_icon} {prereq.phase.phase_name}: {prereq.status} (order: {prereq.phase.phase_order})")
        if prereq.status != 'completed':
            all_completed = False
    
    print(f"\nAll prerequisites completed: {all_completed}")
    
    # Check specifically for coating phase
    coating_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='coating'
    ).first()
    
    if coating_phase:
        print(f"\nCoating phase found:")
        print(f"  Status: {coating_phase.status}")
        print(f"  Order: {coating_phase.phase.phase_order}")
        print(f"  Should be skipped for uncoated tablets: {bmr.product.coating_type != 'coated'}")
    else:
        print(f"\nNo coating phase found (properly skipped for uncoated tablet)")
    
    # Test can_start_phase logic
    can_start = WorkflowService.can_start_phase(bmr, 'packaging_material_release')
    print(f"\nWorkflowService.can_start_phase result: {can_start}")

if __name__ == "__main__":
    debug_packaging_prerequisites()
