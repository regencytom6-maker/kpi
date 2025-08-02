#!/usr/bin/env python
"""
Test coating skip logic for all BMRs
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution

def test_coating_logic():
    """Test coating skip logic for all BMRs"""
    
    bmrs = BMR.objects.all()
    
    for bmr in bmrs:
        print(f"\n=== BMR {bmr.batch_number} - {bmr.product.product_name} ===")
        print(f"Product type: {bmr.product.product_type}")
        
        if bmr.product.product_type == 'tablet':
            print(f"Coating type: {bmr.product.coating_type}")
            print(f"Tablet type: {bmr.product.tablet_type}")
            
            # Check if coating phase exists
            coating_phase = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='coating'
            ).first()
            
            should_have_coating = bmr.product.coating_type == 'coated'
            has_coating = coating_phase is not None
            
            if should_have_coating and has_coating:
                print(f"✅ Coated tablet has coating phase: {coating_phase.status}")
            elif not should_have_coating and not has_coating:
                print(f"✅ Uncoated tablet correctly skips coating phase")
            elif should_have_coating and not has_coating:
                print(f"❌ Coated tablet missing coating phase!")
            else:
                print(f"❌ Uncoated tablet has coating phase: {coating_phase.status}")
            
            # Check packing type
            blister_packing = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='blister_packing'
            ).first()
            
            bulk_packing = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='bulk_packing'
            ).first()
            
            if bmr.product.tablet_type == 'tablet_2':
                if bulk_packing and not blister_packing:
                    print(f"✅ Tablet Type 2 correctly has bulk_packing: {bulk_packing.status}")
                else:
                    print(f"❌ Tablet Type 2 should have bulk_packing, not blister_packing")
            else:
                if blister_packing and not bulk_packing:
                    print(f"✅ Normal tablet correctly has blister_packing: {blister_packing.status}")
                else:
                    print(f"❌ Normal tablet should have blister_packing, not bulk_packing")
        
        # Show phase progression
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        print("Phase progression:")
        for phase in phases:
            status_icon = "✅" if phase.status == 'completed' else "⏳" if phase.status == 'pending' else "⚫"
            print(f"  {status_icon} {phase.phase.phase_name} (order {phase.phase.phase_order}): {phase.status}")

if __name__ == "__main__":
    test_coating_logic()
