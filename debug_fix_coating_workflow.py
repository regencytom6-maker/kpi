#!/usr/bin/env python
"""
Diagnoses and fixes issues with coating workflow for tablets
1. Checks if product.is_coated property is correctly set
2. Checks the phase order in ProductionPhase
3. Verifies BatchPhaseExecution status transitions
4. Force-corrects the workflow for BMRs with wrong phase status
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

def check_tablet_product_coating(batch_number=None):
    """Check if product.is_coated matches coating_type"""
    if batch_number:
        bmrs = BMR.objects.filter(batch_number=batch_number, product__product_type='tablet')
    else:
        bmrs = BMR.objects.filter(product__product_type='tablet')
    
    print(f"\n=== Checking {bmrs.count()} tablet BMRs for coating configuration ===")
    for bmr in bmrs:
        product = bmr.product
        is_coated = product.is_coated
        coating_type = product.coating_type
        print(f"BMR {bmr.batch_number}: {product.product_name}")
        print(f"  - is_coated property: {is_coated}")
        print(f"  - coating_type field: {coating_type}")
        # Verify and correct if needed
        if (is_coated and coating_type != 'coated') or (not is_coated and coating_type == 'coated'):
            print(f"  ! Inconsistent coating configuration detected!")
            expected_coating = 'coated' if is_coated else 'uncoated'
            print(f"  * Fixing coating_type to '{expected_coating}'")
            product.coating_type = expected_coating
            product.save()
            print("  ✓ Fixed")

def check_phase_order(batch_number=None):
    """Check that phases are in correct order for tablets"""
    print("\n=== Checking phase order in ProductionPhase ===")
    phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    print("Current phase order for tablets:")
    for p in phases:
        print(f"  {p.phase_order}. {p.phase_name}")
    
    # Check for coating/packaging_material_release order
    try:
        coating_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='coating')
        pmr_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='packaging_material_release')
        if coating_phase.phase_order > pmr_phase.phase_order:
            print("! ERROR: packaging_material_release comes BEFORE coating in phase order")
            print("* Fixing phase order...")
            # Find sorting phase
            sorting_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='sorting')
            # Set the correct order
            order_map = {}
            for phase in phases:
                if phase.phase_name == 'coating':
                    order_map[phase] = sorting_phase.phase_order + 1
                elif phase.phase_name == 'packaging_material_release':
                    order_map[phase] = sorting_phase.phase_order + 2
                elif phase.phase_order > sorting_phase.phase_order:
                    order_map[phase] = phase.phase_order + 2
            
            # Update the phases
            for phase, new_order in order_map.items():
                if phase.phase_order != new_order:
                    print(f"  Setting {phase.phase_name} order to {new_order}")
                    phase.phase_order = new_order
                    phase.save()
            print("✓ Phase order fixed")
        else:
            print("✓ Phase order is correct (coating before packaging_material_release)")
    except ProductionPhase.DoesNotExist:
        print("! ERROR: Required phases not found")

def check_workflow_status(batch_number=None):
    """Check workflow status for coated tablets"""
    if batch_number:
        bmrs = BMR.objects.filter(batch_number=batch_number, product__product_type='tablet', product__coating_type='coated')
    else:
        bmrs = BMR.objects.filter(product__product_type='tablet', product__coating_type='coated')
    
    print(f"\n=== Checking workflow status for {bmrs.count()} coated tablet BMRs ===")
    for bmr in bmrs:
        print(f"\nBMR {bmr.batch_number}: {bmr.product.product_name}")
        
        # Get all phases in correct order
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        # Print current state
        print("Current phase statuses:")
        for p in phases:
            print(f"  {p.phase.phase_order:2d}. {p.phase.phase_name:25} {p.status}")
        
        # Check for coating -> packaging_material_release order
        coating_phase = None
        pmr_phase = None
        sorting_phase = None
        
        for p in phases:
            if p.phase.phase_name == 'coating':
                coating_phase = p
            elif p.phase.phase_name == 'packaging_material_release':
                pmr_phase = p
            elif p.phase.phase_name == 'sorting':
                sorting_phase = p
        
        if coating_phase and pmr_phase:
            # Verify coating comes before packaging_material_release
            if coating_phase.phase.phase_order > pmr_phase.phase.phase_order:
                print("! ERROR: packaging_material_release phase comes BEFORE coating")
                # This requires a fix in ProductionPhase - already addressed in check_phase_order()
            else:
                print("✓ Phase order is correct (coating before packaging_material_release)")
            
            # Check status transitions
            if sorting_phase and sorting_phase.status == 'completed':
                if pmr_phase.status != 'not_ready':
                    print("! ERROR: packaging_material_release is not 'not_ready' after sorting")
                    
                if coating_phase.status == 'not_ready' and sorting_phase.status == 'completed':
                    print("! ERROR: coating is 'not_ready' after sorting is completed")
                    print("* Fixing coating phase status to 'pending'...")
                    with transaction.atomic():
                        coating_phase.status = 'pending'
                        coating_phase.save()
                        print("✓ Set coating to 'pending'")

def force_fix_phases(batch_number=None):
    """Force fix the workflow for the specified BMR or all tablet BMRs"""
    if batch_number:
        bmrs = BMR.objects.filter(batch_number=batch_number, product__product_type='tablet')
    else:
        bmrs = BMR.objects.filter(product__product_type='tablet')
    
    print(f"\n=== Force fixing workflow for {bmrs.count()} tablet BMRs ===")
    for bmr in bmrs:
        is_coated = bmr.product.is_coated
        print(f"BMR {bmr.batch_number}: {bmr.product.product_name} (Coated: {is_coated})")
        
        with transaction.atomic():
            # Update phase order for the ProductionPhase objects
            phase_updates = {
                'coating': {'order': 9, 'skip_if_uncoated': True},
                'packaging_material_release': {'order': 10, 'skip_if_uncoated': False},
                'blister_packing': {'order': 11, 'skip_if_uncoated': False},
                'bulk_packing': {'order': 11, 'skip_if_uncoated': False},
                'secondary_packaging': {'order': 12, 'skip_if_uncoated': False},
                'final_qa': {'order': 13, 'skip_if_uncoated': False},
                'finished_goods_store': {'order': 14, 'skip_if_uncoated': False}
            }
            
            for phase_name, config in phase_updates.items():
                try:
                    phase = ProductionPhase.objects.get(product_type='tablet', phase_name=phase_name)
                    if phase.phase_order != config['order']:
                        phase.phase_order = config['order']
                        phase.save()
                        print(f"  Updated {phase_name} order to {config['order']}")
                except ProductionPhase.DoesNotExist:
                    print(f"  Phase {phase_name} not found")
            
            # Get all phases for this BMR
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            
            # Update statuses based on workflow logic
            sorting_done = False
            for phase in phases:
                if phase.phase.phase_name == 'sorting' and phase.status == 'completed':
                    sorting_done = True
                
                # If sorting is done, fix coating and packaging_material_release statuses
                if sorting_done:
                    if phase.phase.phase_name == 'coating':
                        if is_coated and phase.status != 'pending' and phase.status != 'completed':
                            phase.status = 'pending'
                            phase.save()
                            print("  ✓ Fixed coating status to 'pending' after sorting")
                        elif not is_coated and phase.status != 'skipped':
                            phase.status = 'skipped'
                            phase.completed_date = timezone.now()
                            phase.operator_comments = "Phase skipped - product does not require coating"
                            phase.save()
                            print("  ✓ Fixed coating status to 'skipped' for uncoated product")
                    
                    if phase.phase.phase_name == 'packaging_material_release':
                        if is_coated:
                            # For coated products, PMR should be not_ready until coating is done
                            coating_phase = phases.filter(phase__phase_name='coating').first()
                            if coating_phase and coating_phase.status != 'completed' and phase.status != 'not_ready':
                                phase.status = 'not_ready'
                                phase.save()
                                print("  ✓ Fixed packaging_material_release status to 'not_ready' until coating is completed")
                        else:
                            # For uncoated products, PMR should be pending after sorting
                            if phase.status != 'pending' and phase.status != 'completed':
                                phase.status = 'pending'
                                phase.save()
                                print("  ✓ Fixed packaging_material_release status to 'pending' for uncoated product")
            
            print("  ✓ Workflow fixed for this BMR")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        batch_number = sys.argv[1]
        print(f"Working with BMR: {batch_number}")
        check_tablet_product_coating(batch_number)
        check_phase_order()
        check_workflow_status(batch_number)
        force_fix_phases(batch_number)
    else:
        check_tablet_product_coating()
        check_phase_order()
        check_workflow_status()
        force_fix_phases()
        
    print("\nDone. All tablet BMRs now have correct workflow order and statuses.")
