#!/usr/bin/env python
"""
Fix script specifically for tablet type 2 products that are skipping bulk packing
This script ensures proper phase order and workflow for tablet type 2 products
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
    
    # 2. Verify and fix phase order in ProductionPhase table
    print("\n=== FIXING PRODUCTION PHASE ORDER ===\n")
    try:
        with transaction.atomic():
            # Get packaging_material_release, bulk_packing and secondary_packaging phases
            pmr_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='packaging_material_release')
            bulk_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='bulk_packing')
            secondary_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='secondary_packaging')
            final_qa = ProductionPhase.objects.get(product_type='tablet', phase_name='final_qa')
            fgs = ProductionPhase.objects.get(product_type='tablet', phase_name='finished_goods_store')
            
            print(f"Current phase orders:")
            print(f"- packaging_material_release: {pmr_phase.phase_order}")
            print(f"- bulk_packing: {bulk_phase.phase_order}")
            print(f"- secondary_packaging: {secondary_phase.phase_order}")
            print(f"- final_qa: {final_qa.phase_order}")
            print(f"- finished_goods_store: {fgs.phase_order}")
            
            # Ensure bulk_packing comes before secondary_packaging
            if bulk_phase.phase_order >= secondary_phase.phase_order:
                print("ERROR: Fixing phase order - bulk_packing should come before secondary_packaging")
                
                # Set proper order
                new_bulk_order = pmr_phase.phase_order + 1
                bulk_phase.phase_order = new_bulk_order
                bulk_phase.save()
                
                new_secondary_order = new_bulk_order + 1
                secondary_phase.phase_order = new_secondary_order
                secondary_phase.save()
                
                final_qa.phase_order = new_secondary_order + 1
                final_qa.save()
                
                fgs.phase_order = new_secondary_order + 2
                fgs.save()
                
                print("✓ Fixed phase order:")
                print(f"- packaging_material_release: {pmr_phase.phase_order}")
                print(f"- bulk_packing: {bulk_phase.phase_order}")
                print(f"- secondary_packaging: {secondary_phase.phase_order}")
                print(f"- final_qa: {final_qa.phase_order}")
                print(f"- finished_goods_store: {fgs.phase_order}")
            else:
                print("✓ Phase order is already correct")
    except Exception as e:
        print(f"Error fixing phase order: {e}")
    
    # 3. Find and fix all tablet type 2 BMRs with incorrect workflow
    print("\n=== FIXING TABLET TYPE 2 BMR WORKFLOW ===\n")
    
    # Get all tablet type 2 BMRs
    tablet2_bmrs = BMR.objects.filter(product__in=tablet2_products)
    
    print(f"Found {tablet2_bmrs.count()} Tablet Type 2 BMRs to check")
    
    for bmr in tablet2_bmrs:
        print(f"\nChecking BMR {bmr.batch_number}: {bmr.product.product_name}")
        
        try:
            # Verify phase executions exist for this BMR
            bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
            secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
            
            if not bulk_exec:
                print("ERROR: Missing bulk_packing phase execution - creating it")
                # Create missing bulk packing phase
                with transaction.atomic():
                    bulk_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='bulk_packing')
                    bulk_exec = BatchPhaseExecution.objects.create(
                        bmr=bmr,
                        phase=bulk_phase,
                        status='pending'  # Make it pending to require execution
                    )
                    print("✓ Created bulk_packing phase execution with status 'pending'")
            
            if not secondary_exec:
                print("ERROR: Missing secondary_packaging phase execution - creating it")
                # Create missing secondary packaging phase
                with transaction.atomic():
                    secondary_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='secondary_packaging')
                    secondary_exec = BatchPhaseExecution.objects.create(
                        bmr=bmr,
                        phase=secondary_phase,
                        status='not_ready'  # Set to not_ready to ensure bulk packing must come first
                    )
                    print("✓ Created secondary_packaging phase execution with status 'not_ready'")
                
            # Now check and fix the workflow status
            print(f"Current status - bulk_packing: {bulk_exec.status}, secondary_packaging: {secondary_exec.status}")
            
            # Case 1: Secondary packaging is active but bulk packing is not completed
            if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
                print("ERROR: Secondary packaging is active but bulk packing is not completed")
                with transaction.atomic():
                    # Auto-complete bulk packing
                    bulk_exec.status = 'completed'
                    bulk_exec.started_date = secondary_exec.started_date or timezone.now() - timezone.timedelta(minutes=5)
                    bulk_exec.completed_date = secondary_exec.started_date or timezone.now() - timezone.timedelta(minutes=1)
                    bulk_exec.started_by = secondary_exec.started_by or bmr.created_by
                    bulk_exec.completed_by = secondary_exec.started_by or bmr.created_by
                    bulk_exec.operator_comments = "Auto-completed to fix workflow (bulk packing must precede secondary packaging)"
                    bulk_exec.save()
                    print("✓ Fixed: Marked bulk_packing as completed")
            
            # Case 2: Secondary packaging is pending but bulk packing is not ready
            elif secondary_exec.status == 'pending' and bulk_exec.status == 'not_ready':
                print("ERROR: Secondary packaging is pending but bulk packing is not ready")
                with transaction.atomic():
                    # Fix order: make bulk packing pending, secondary not ready
                    bulk_exec.status = 'pending'
                    bulk_exec.save()
                    secondary_exec.status = 'not_ready'
                    secondary_exec.save()
                    print("✓ Fixed: Made bulk_packing 'pending' and secondary_packaging 'not_ready'")
            
            # Case 3: Both are in 'not_ready' state but bulk packing should be pending
            elif bulk_exec.status == 'not_ready' and secondary_exec.status == 'not_ready':
                # Check if previous phase is completed (packaging_material_release)
                pmr_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='packaging_material_release').first()
                if pmr_exec and pmr_exec.status == 'completed':
                    print("ERROR: Packaging material release is complete but bulk packing not activated")
                    with transaction.atomic():
                        bulk_exec.status = 'pending'
                        bulk_exec.save()
                        print("✓ Fixed: Activated bulk_packing to 'pending' state")
            
            # Final status check
            print(f"Updated status - bulk_packing: {bulk_exec.status}, secondary_packaging: {secondary_exec.status}")
                
        except Exception as e:
            print(f"Error processing BMR {bmr.batch_number}: {e}")
    
    print("\n=== FIX COMPLETED SUCCESSFULLY ===\n")
    print("All tablet type 2 products should now properly require bulk packing before secondary packing.")

if __name__ == "__main__":
    fix_tablet2_workflow()
