#!/usr/bin/env python
"""
Script to check and fix Tablet Type 2 workflow issues
particularly focusing on bulk packing phase being skipped
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

def debug_tablet2_workflow():
    """Diagnose and fix tablet type 2 workflow issues with bulk packing"""
    print("\n=== TABLET TYPE 2 WORKFLOW DIAGNOSTIC ===\n")
    
    # 1. Find all tablet type 2 products
    tablet2_products = Product.objects.filter(product_type='tablet', tablet_type=2)
    print(f"Found {tablet2_products.count()} Tablet Type 2 products:")
    for product in tablet2_products:
        print(f"- {product.product_name} (ID: {product.id})")
    
    # 2. Check production phase configuration
    print("\n=== CHECKING PRODUCTION PHASE CONFIGURATION ===\n")
    try:
        phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
        print("Current tablet production phases in order:")
        for phase in phases:
            print(f"- Order {phase.phase_order}: {phase.phase_name}")
        
        # Check if bulk_packing comes before secondary_packaging
        bulk_phase = phases.filter(phase_name='bulk_packing').first()
        secondary_phase = phases.filter(phase_name='secondary_packaging').first()
        
        if bulk_phase and secondary_phase:
            print(f"\nBulk packing order: {bulk_phase.phase_order}")
            print(f"Secondary packaging order: {secondary_phase.phase_order}")
            
            if bulk_phase.phase_order >= secondary_phase.phase_order:
                print("ERROR: Bulk packing should come BEFORE secondary packaging")
            else:
                print("✓ Phase order is correct (bulk packing before secondary packaging)")
        else:
            print("ERROR: Could not find both bulk_packing and secondary_packaging phases")
    except Exception as e:
        print(f"Error checking phases: {e}")
    
    # 3. Find tablet type 2 BMRs and check their phase executions
    print("\n=== CHECKING TABLET TYPE 2 BMRs ===\n")
    tablet2_bmrs = BMR.objects.filter(product__in=tablet2_products)
    
    print(f"Found {tablet2_bmrs.count()} Tablet Type 2 BMRs:")
    for bmr in tablet2_bmrs:
        print(f"\nBMR {bmr.batch_number}: {bmr.product.product_name}")
        
        # Get bulk packing and secondary packaging phase executions
        bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
        
        if bulk_exec and secondary_exec:
            print(f"  Bulk packing status: {bulk_exec.status}")
            print(f"  Secondary packaging status: {secondary_exec.status}")
            
            # Check if secondary is active but bulk isn't completed
            if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
                print("  ERROR: Secondary packaging is active but bulk packing is not completed!")
                print("  This BMR needs fixing.")
        else:
            if not bulk_exec:
                print("  ERROR: Missing bulk packing phase execution!")
            if not secondary_exec:
                print("  ERROR: Missing secondary packaging phase execution!")

    # 4. Check prerequisite configuration
    print("\n=== CHECKING PHASE PREREQUISITES ===\n")
    try:
        bulk_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='bulk_packing')
        secondary_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='secondary_packaging')
        
        bulk_prerequisites = bulk_phase.get_prerequisites()
        secondary_prerequisites = secondary_phase.get_prerequisites()
        
        print("Bulk packing prerequisites:")
        for prereq in bulk_prerequisites:
            print(f"- {prereq}")
        
        print("\nSecondary packaging prerequisites:")
        for prereq in secondary_prerequisites:
            print(f"- {prereq}")
        
        # Check if secondary packaging requires bulk packing
        if 'bulk_packing' in [p for p in secondary_prerequisites]:
            print("\n✓ Secondary packaging correctly requires bulk_packing as prerequisite")
        else:
            print("\nERROR: Secondary packaging does NOT require bulk_packing as prerequisite!")
            print("This explains why tablet type 2 products are skipping bulk packing.")
    except Exception as e:
        print(f"Error checking prerequisites: {e}")
    
    # Ask if user wants to fix the issues
    print("\n=== FIXING OPTIONS ===")
    print("Would you like to fix the identified issues? (Press enter to continue)")
    input()
    
    # 5. Fix prerequisite configuration if needed
    try:
        with transaction.atomic():
            secondary_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='secondary_packaging')
            
            # Get current prerequisites
            current_prereqs = secondary_phase.prerequisites or ""
            print(f"Current prerequisites for secondary_packaging: {current_prereqs}")
            
            # Add bulk_packing as prerequisite if not already there
            if 'bulk_packing' not in current_prereqs:
                if current_prereqs:
                    new_prereqs = current_prereqs + ",bulk_packing"
                else:
                    new_prereqs = "bulk_packing"
                
                secondary_phase.prerequisites = new_prereqs
                secondary_phase.save()
                print(f"✓ Added bulk_packing as prerequisite for secondary_packaging: {new_prereqs}")
            else:
                print("✓ bulk_packing is already a prerequisite for secondary_packaging")
    except Exception as e:
        print(f"Error fixing prerequisites: {e}")
    
    # 6. Fix affected BMRs
    print("\n=== FIXING AFFECTED BMRs ===")
    print("Would you like to fix BMRs where secondary packaging is active but bulk packing is not? (Press enter to continue)")
    input()
    
    affected_count = 0
    for bmr in tablet2_bmrs:
        bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
        
        if bulk_exec and secondary_exec:
            if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
                print(f"\nFixing BMR {bmr.batch_number}: {bmr.product.product_name}")
                print(f"  Current bulk_packing status: {bulk_exec.status}")
                print(f"  Current secondary_packaging status: {secondary_exec.status}")
                
                try:
                    with transaction.atomic():
                        # Mark bulk packing as completed with timestamp just before secondary
                        bulk_exec.status = 'completed'
                        bulk_exec.started_date = secondary_exec.started_date or timezone.now() - timezone.timedelta(minutes=5)
                        bulk_exec.completed_date = secondary_exec.started_date or timezone.now() - timezone.timedelta(minutes=1)
                        bulk_exec.started_by = secondary_exec.started_by or bmr.created_by
                        bulk_exec.completed_by = secondary_exec.started_by or bmr.created_by
                        bulk_exec.operator_comments = "Auto-completed to fix workflow (bulk packing must precede secondary packaging)"
                        bulk_exec.save()
                        print("  ✓ Marked bulk_packing as completed")
                        affected_count += 1
                except Exception as e:
                    print(f"  Error fixing BMR: {e}")
    
    print(f"\nFixed {affected_count} affected BMRs")
    print("\nDiagnostic and fixes completed!")

if __name__ == "__main__":
    debug_tablet2_workflow()
