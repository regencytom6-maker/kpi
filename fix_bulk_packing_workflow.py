#!/usr/bin/env python
"""
Diagnoses and fixes issues with bulk packing workflow
1. Checks phase order in ProductionPhase
2. Verifies BatchPhaseExecution status transitions
3. Force-corrects the workflow for BMRs with wrong phase statuses
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

def check_packing_phases_order():
    """Check the order of packing phases for all product types"""
    print("\n=== Checking packing phase order across product types ===")
    
    for product_type in ['tablet', 'capsule', 'ointment', 'liquid']:
        phases = ProductionPhase.objects.filter(product_type=product_type).order_by('phase_order')
        
        print(f"\nProduct Type: {product_type}")
        print("Current phase order:")
        for p in phases:
            print(f"  {p.phase_order:2d}. {p.phase_name}")
        
        # Check for bulk_packing and secondary_packaging order
        try:
            bulk_packing = phases.filter(phase_name='bulk_packing').first()
            secondary_packaging = phases.filter(phase_name='secondary_packaging').first()
            
            if bulk_packing and secondary_packaging:
                if bulk_packing.phase_order > secondary_packaging.phase_order:
                    print(f"! ERROR: secondary_packaging (order {secondary_packaging.phase_order}) "
                          f"comes BEFORE bulk_packing (order {bulk_packing.phase_order})")
                else:
                    print(f"✓ Phase order is correct (bulk_packing before secondary_packaging)")
        except:
            print("! Could not check phase order - phases may be missing")

def identify_affected_bmrs():
    """Identify BMRs with incorrect packing workflow"""
    print("\n=== Identifying BMRs with incorrect packing workflow ===")
    
    affected_bmrs = []
    all_bmrs = BMR.objects.all()
    
    for bmr in all_bmrs:
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        # Get relevant phases
        bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
        secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
        
        if bulk_packing and secondary_packaging:
            if bulk_packing.phase.phase_order > secondary_packaging.phase.phase_order:
                affected_bmrs.append(bmr)
                print(f"BMR {bmr.batch_number}: {bmr.product.product_name} - Incorrect phase order")
            elif secondary_packaging.status not in ['not_ready', 'skipped'] and bulk_packing.status in ['not_ready', 'pending']:
                affected_bmrs.append(bmr)
                print(f"BMR {bmr.batch_number}: {bmr.product.product_name} - Secondary packaging active before bulk packing")
    
    print(f"\nTotal affected BMRs: {len(affected_bmrs)}")
    return affected_bmrs

def fix_packing_phase_order():
    """Fix the order of packing phases for all product types"""
    print("\n=== Fixing packing phase order ===")
    
    for product_type in ['tablet', 'capsule', 'ointment', 'liquid']:
        with transaction.atomic():
            try:
                # Get packaging phases
                bulk_packing = ProductionPhase.objects.filter(
                    product_type=product_type, phase_name='bulk_packing').first()
                secondary_packaging = ProductionPhase.objects.filter(
                    product_type=product_type, phase_name='secondary_packaging').first()
                
                if bulk_packing and secondary_packaging:
                    if bulk_packing.phase_order > secondary_packaging.phase_order:
                        print(f"Fixing {product_type} packing order:")
                        
                        # Determine proper order
                        pmr_phase = ProductionPhase.objects.filter(
                            product_type=product_type, phase_name='packaging_material_release').first()
                        
                        if pmr_phase:
                            base_order = pmr_phase.phase_order
                            
                            # Set blister_packing and bulk_packing to the same order level
                            blister_packing = ProductionPhase.objects.filter(
                                product_type=product_type, phase_name='blister_packing').first()
                            
                            packing_order = base_order + 1
                            secondary_order = base_order + 2
                            
                            if blister_packing:
                                blister_packing.phase_order = packing_order
                                blister_packing.save()
                                print(f"  Updated blister_packing order to {packing_order}")
                            
                            bulk_packing.phase_order = packing_order
                            bulk_packing.save()
                            print(f"  Updated bulk_packing order to {packing_order}")
                            
                            secondary_packaging.phase_order = secondary_order
                            secondary_packaging.save()
                            print(f"  Updated secondary_packaging order to {secondary_order}")
                            
                            # Update subsequent phases
                            next_phases = ProductionPhase.objects.filter(
                                product_type=product_type,
                                phase_order__gt=secondary_packaging.phase_order
                            ).order_by('phase_order')
                            
                            current_order = secondary_order + 1
                            for phase in next_phases:
                                phase.phase_order = current_order
                                phase.save()
                                print(f"  Updated {phase.phase_name} order to {current_order}")
                                current_order += 1
                        else:
                            print(f"  Could not find packaging_material_release phase for {product_type}")
            except Exception as e:
                print(f"Error fixing {product_type} packing order: {str(e)}")

def fix_affected_bmrs(batch_number=None):
    """Fix workflow for affected BMRs"""
    print("\n=== Fixing affected BMRs ===")
    
    if batch_number:
        bmrs = BMR.objects.filter(batch_number=batch_number)
    else:
        bmrs = identify_affected_bmrs()
    
    for bmr in bmrs:
        print(f"\nFixing BMR {bmr.batch_number}: {bmr.product.product_name}")
        
        with transaction.atomic():
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            
            # Get relevant phases
            bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
            secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
            
            if bulk_packing and secondary_packaging:
                # Fix phase execution order first (unlikely but possible)
                if bulk_packing.phase.phase_order > secondary_packaging.phase.phase_order:
                    print("  Fixing phase execution order...")
                    # Use the global ordering we've set
                    bulk_packing_phase = ProductionPhase.objects.get(
                        product_type=bmr.product.product_type, phase_name='bulk_packing')
                    secondary_packaging_phase = ProductionPhase.objects.get(
                        product_type=bmr.product.product_type, phase_name='secondary_packaging')
                    
                    bulk_packing.phase = bulk_packing_phase
                    secondary_packaging.phase = secondary_packaging_phase
                    bulk_packing.save()
                    secondary_packaging.save()
                
                # Now fix the status flow if secondary_packaging is already started
                if secondary_packaging.status not in ['not_ready', 'skipped'] and bulk_packing.status in ['not_ready', 'pending']:
                    print("  Secondary packaging active before bulk packing - fixing status flow...")
                    
                    # If secondary packaging is in progress or completed
                    if secondary_packaging.status in ['in_progress', 'completed']:
                        # Mark bulk packing as completed too
                        if bulk_packing.status != 'completed':
                            bulk_packing.status = 'completed'
                            bulk_packing.started_date = secondary_packaging.started_date or timezone.now()
                            bulk_packing.completed_date = secondary_packaging.started_date or timezone.now()
                            bulk_packing.started_by = secondary_packaging.started_by
                            bulk_packing.completed_by = secondary_packaging.started_by
                            bulk_packing.operator_comments = "Auto-completed by system due to workflow fix"
                            bulk_packing.save()
                            print("  ✓ Marked bulk_packing as completed")
                    
                    # If secondary packaging is pending but bulk packing is not
                    elif secondary_packaging.status == 'pending' and bulk_packing.status == 'not_ready':
                        # Set bulk packing to pending too
                        bulk_packing.status = 'pending'
                        bulk_packing.save()
                        print("  ✓ Set bulk_packing to pending status")
                
                print("  ✓ Fixed workflow for this BMR")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        batch_number = sys.argv[1]
        print(f"Working with specific BMR: {batch_number}")
        check_packing_phases_order()
        fix_packing_phase_order()
        fix_affected_bmrs(batch_number)
    else:
        check_packing_phases_order()
        fix_packing_phase_order()
        fix_affected_bmrs()
        
    print("\nDone. Bulk packing workflow has been corrected.")
