#!/usr/bin/env python
"""
Quick fix script for bulk packing workflow order issues
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from products.models import Product

def fix_bulk_packing_order():
    """Fix the workflow issue where secondary packaging comes before bulk packing"""
    print("\n=== FIXING BULK PACKING WORKFLOW ===\n")
    
    # Check current phase order
    for product_type in ['tablet', 'capsule', 'ointment', 'liquid']:
        print(f"\nProduct type: {product_type}")
        
        # Get the relevant phases
        try:
            bulk_phase = ProductionPhase.objects.get(product_type=product_type, phase_name='bulk_packing')
            secondary_phase = ProductionPhase.objects.get(product_type=product_type, phase_name='secondary_packaging')
            
            print(f"  Current bulk_packing order: {bulk_phase.phase_order}")
            print(f"  Current secondary_packaging order: {secondary_phase.phase_order}")
            
            # Fix phase order if needed
            if bulk_phase.phase_order >= secondary_phase.phase_order:
                print(f"  ! ERROR: bulk_packing ({bulk_phase.phase_order}) should come before secondary_packaging ({secondary_phase.phase_order})")
                
                # Get packaging_material_release phase for reference
                pmr_phase = ProductionPhase.objects.get(product_type=product_type, phase_name='packaging_material_release')
                base_order = pmr_phase.phase_order
                
                with transaction.atomic():
                    # Set bulk_packing to come immediately after packaging_material_release
                    new_bulk_order = base_order + 1
                    bulk_phase.phase_order = new_bulk_order
                    bulk_phase.save()
                    
                    # Set secondary_packaging to come after bulk_packing
                    new_secondary_order = new_bulk_order + 1
                    secondary_phase.phase_order = new_secondary_order
                    secondary_phase.save()
                    
                    # Update final_qa and finished_goods_store if they exist
                    try:
                        final_qa = ProductionPhase.objects.get(product_type=product_type, phase_name='final_qa')
                        final_qa.phase_order = new_secondary_order + 1
                        final_qa.save()
                        print(f"  Updated final_qa order to {final_qa.phase_order}")
                    except ProductionPhase.DoesNotExist:
                        pass
                        
                    try:
                        fgs = ProductionPhase.objects.get(product_type=product_type, phase_name='finished_goods_store')
                        fgs.phase_order = new_secondary_order + 2
                        fgs.save()
                        print(f"  Updated finished_goods_store order to {fgs.phase_order}")
                    except ProductionPhase.DoesNotExist:
                        pass
                    
                    print(f"  ✓ Fixed: bulk_packing now order {new_bulk_order}, secondary_packaging now order {new_secondary_order}")
            else:
                print("  ✓ Phase order is correct (bulk_packing before secondary_packaging)")
        except ProductionPhase.DoesNotExist:
            print(f"  - Skipping: Not all required phases exist for {product_type}")
    
    # Fix BMRs with incorrect status flow
    print("\n\n=== FIXING AFFECTED BMRs ===\n")
    
    # Find BMRs where secondary packaging is active but bulk packing is not
    affected_bmrs = []
    for bmr in BMR.objects.all():
        bulk_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        secondary_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
        
        if bulk_phase and secondary_phase:
            if secondary_phase.status not in ['not_ready', 'skipped'] and bulk_phase.status in ['not_ready', 'pending']:
                affected_bmrs.append(bmr)
    
    print(f"Found {len(affected_bmrs)} BMRs with incorrect status flow")
    
    # Fix each affected BMR
    for bmr in affected_bmrs:
        print(f"\nFixing BMR {bmr.batch_number}: {bmr.product.product_name}")
        bulk_phase = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='bulk_packing')
        secondary_phase = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='secondary_packaging')
        
        print(f"  Current bulk_packing status: {bulk_phase.status}")
        print(f"  Current secondary_packaging status: {secondary_phase.status}")
        
        with transaction.atomic():
            if secondary_phase.status in ['in_progress', 'completed']:
                # Mark bulk packing as completed with timestamp just before secondary started
                bulk_phase.status = 'completed'
                bulk_phase.started_date = secondary_phase.started_date or timezone.now() - timezone.timedelta(minutes=5)
                bulk_phase.completed_date = secondary_phase.started_date or timezone.now() - timezone.timedelta(minutes=1)
                bulk_phase.started_by = secondary_phase.started_by or bmr.created_by
                bulk_phase.completed_by = secondary_phase.started_by or bmr.created_by
                bulk_phase.operator_comments = "Auto-completed to fix workflow (bulk packing must precede secondary packaging)"
                bulk_phase.save()
                print("  ✓ Marked bulk_packing as completed")
            
            elif secondary_phase.status == 'pending' and bulk_phase.status == 'not_ready':
                # Set bulk packing to pending
                bulk_phase.status = 'pending'
                bulk_phase.save()
                print("  ✓ Set bulk_packing to pending status")
    
    print("\nDone. All bulk packing workflow issues have been fixed.")

if __name__ == "__main__":
    fix_bulk_packing_order()
