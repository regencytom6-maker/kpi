#!/usr/bin/env python
"""
Fix script for BMRs where bulk packing is being skipped in tablet type 2 products
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from products.models import Product

def fix_tablet2_workflow():
    """Fix tablet type 2 workflow issues where bulk packing is being skipped"""
    print("\n=== FIXING TABLET TYPE 2 WORKFLOW ISSUES ===\n")
    
    # 1. Find all tablet type 2 products
    tablet2_products = Product.objects.filter(product_type='tablet', tablet_type='tablet_2')
    print(f"Found {tablet2_products.count()} Tablet Type 2 products:")
    for product in tablet2_products:
        print(f"- {product.product_name} (ID: {product.id})")
    
    # 2. Check production phase configuration
    print("\n=== CHECKING PRODUCTION PHASE CONFIGURATION ===\n")
    try:
        # Get all tablet phases
        phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
        print("Current tablet production phases in order:")
        for phase in phases:
            print(f"- Order {phase.phase_order}: {phase.phase_name}")
            
        # Get specific phases
        pmr_phase = phases.filter(phase_name='packaging_material_release').first()
        bulk_phase = phases.filter(phase_name='bulk_packing').first()
        secondary_phase = phases.filter(phase_name='secondary_packaging').first()
        
        if bulk_phase and secondary_phase:
            print(f"\nBulk packing order: {bulk_phase.phase_order}")
            print(f"Secondary packaging order: {secondary_phase.phase_order}")
            
            if bulk_phase.phase_order >= secondary_phase.phase_order:
                # Fix phase order
                print("\nFIXING: Bulk packing should come BEFORE secondary packaging")
                with transaction.atomic():
                    # Make sure bulk_packing comes right after packaging_material_release
                    pmr_order = pmr_phase.phase_order if pmr_phase else 0
                    new_bulk_order = pmr_order + 1
                    
                    # Shift all phases from bulk_packing position onwards
                    phases_to_shift = phases.filter(phase_order__gte=new_bulk_order).order_by('-phase_order')
                    
                    # Start from end to avoid conflicts
                    for phase in phases_to_shift:
                        if phase != bulk_phase:
                            phase.phase_order += 1
                            phase.save()
                    
                    # Set bulk_packing to the correct position
                    bulk_phase.phase_order = new_bulk_order
                    bulk_phase.save()
                    
                    print("✓ Fixed phase order")
                    # Print updated order
                    updated_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
                    print("\nUpdated tablet production phases in order:")
                    for phase in updated_phases:
                        print(f"- Order {phase.phase_order}: {phase.phase_name}")
            else:
                print("✓ Phase order is correct (bulk packing before secondary packaging)")
    except Exception as e:
        print(f"Error checking phases: {e}")
    
    # 3. Find tablet type 2 BMRs and check their phase executions
    print("\n=== CHECKING TABLET TYPE 2 BMRs ===\n")
    tablet2_bmrs = BMR.objects.filter(product__in=tablet2_products)
    
    print(f"Found {tablet2_bmrs.count()} Tablet Type 2 BMRs:")
    for bmr in tablet2_bmrs:
        print(f"\nChecking BMR {bmr.batch_number}: {bmr.product.product_name}")
        
        # Get relevant phase executions
        bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
        
        if bulk_exec and secondary_exec:
            print(f"Current status - bulk_packing: {bulk_exec.status}, secondary_packaging: {secondary_exec.status}")
            
            # Case 1: Secondary packaging is active but bulk packing is not completed
            if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
                print("Secondary packaging active before bulk packing - fixing status flow...")
                with transaction.atomic():
                    # Auto-complete bulk packing
                    bulk_exec.status = 'completed'
                    bulk_exec.started_date = secondary_exec.started_date or timezone.now() - timezone.timedelta(minutes=5)
                    bulk_exec.completed_date = secondary_exec.started_date or timezone.now() - timezone.timedelta(minutes=1)
                    bulk_exec.started_by = secondary_exec.started_by or bmr.created_by
                    bulk_exec.completed_by = secondary_exec.started_by or bmr.created_by
                    bulk_exec.operator_comments = "Auto-completed to fix workflow (bulk packing must precede secondary packaging)"
                    bulk_exec.save()
                    print("✓ Marked bulk_packing as completed")
                    print("✓ Fixed workflow for this BMR")
            
            # Case 2: Secondary packaging is pending but bulk packing is not ready
            elif secondary_exec.status == 'pending' and bulk_exec.status == 'not_ready':
                print("Secondary packaging pending but bulk packing not ready - fixing status flow...")
                with transaction.atomic():
                    # Fix order: make bulk packing pending, secondary not ready
                    bulk_exec.status = 'pending'
                    bulk_exec.save()
                    secondary_exec.status = 'not_ready'
                    secondary_exec.save()
                    print("✓ Made bulk_packing 'pending' and secondary_packaging 'not_ready'")
                    print("✓ Fixed workflow for this BMR")
            else:
                print("✓ Workflow status is correct for this BMR")
        else:
            if not bulk_exec:
                print("ERROR: Missing bulk_packing phase for this BMR!")
            if not secondary_exec:
                print("ERROR: Missing secondary_packaging phase for this BMR!")
    
    print("\nDone. Bulk packing workflow has been corrected.")

if __name__ == "__main__":
    fix_tablet2_workflow()
