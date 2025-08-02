#!/usr/bin/env python
"""
Fix phase orders for BMR 0022025
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

def fix_phase_orders():
    """Fix phase orders for BMR 0022025"""
    
    bmr = BMR.objects.filter(batch_number='0022025').first()
    if not bmr:
        print("BMR 0022025 not found")
        return
    
    print(f"Fixing phase orders for BMR {bmr.batch_number}")
    
    # The correct workflow order for tablet type 2 (uncoated) should be:
    correct_workflow = [
        'bmr_creation',           # 1
        'regulatory_approval',    # 2  
        'material_dispensing',    # 3
        'granulation',           # 4
        'blending',              # 5
        'compression',           # 6
        'post_compression_qc',   # 7
        'sorting',               # 8
        # coating skipped for uncoated
        'packaging_material_release',  # 9
        'bulk_packing',          # 10
        'secondary_packaging',   # 11
        'final_qa',              # 12
        'finished_goods_store'   # 13
    ]
    
    print("Current phases:")
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    for phase in phases:
        print(f"  {phase.phase.phase_name}: order {phase.phase.phase_order}, status: {phase.status}")
    
    print("\nUpdating phase orders...")
    
    # Update the phase orders to match correct workflow
    for new_order, phase_name in enumerate(correct_workflow, 1):
        try:
            # Update the ProductionPhase definition
            production_phase = ProductionPhase.objects.filter(
                product_type='tablet',
                phase_name=phase_name
            ).first()
            
            if production_phase:
                production_phase.phase_order = new_order
                production_phase.save()
                print(f"  Updated {phase_name} to order {new_order}")
            else:
                print(f"  ProductionPhase not found for {phase_name}")
                
        except Exception as e:
            print(f"  Error updating {phase_name}: {e}")
    
    print("\nAfter fix:")
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    for phase in phases:
        print(f"  {phase.phase.phase_name}: order {phase.phase.phase_order}, status: {phase.status}")
    
    # Test can_start_phase again
    can_start = WorkflowService.can_start_phase(bmr, 'packaging_material_release')
    print(f"\nCan start packaging_material_release now: {can_start}")

if __name__ == "__main__":
    fix_phase_orders()
