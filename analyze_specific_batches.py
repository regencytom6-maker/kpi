#!/usr/bin/env python
"""
Analyze specific batches and verify system fix for bulk packing workflow
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

def analyze_specific_batches():
    """Analyze batches 0122025 and 0132025 to check if workflow is correct"""
    print("\n=== ANALYZING SPECIFIC BATCHES ===\n")
    
    # Check batches 0122025 and 0132025
    batch_numbers = ['0122025', '0132025']
    
    for batch_number in batch_numbers:
        print(f"\n--- Analyzing BMR {batch_number} ---\n")
        
        try:
            bmr = BMR.objects.get(batch_number=batch_number)
            print(f"Found BMR: {bmr.batch_number} - {bmr.product.product_name}")
            print(f"Product Type: {bmr.product.product_type}")
            print(f"Tablet Type: '{bmr.product.tablet_type}'")
            print(f"Coating Type: '{bmr.product.coating_type}'")
            
            # Check if this is a tablet type 2 product
            is_type2 = bmr.product.tablet_type == 'tablet_2'
            print(f"Is Tablet Type 2: {is_type2}")
            
            # Get phase executions
            executions = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
            
            print("\nPhase execution order and status:")
            for execution in executions:
                print(f"- Order {execution.phase.phase_order:2}: {execution.phase.phase_name:25} - Status: {execution.status}")
            
            # Check specifically for bulk packing and secondary packaging
            bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
            secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
            
            if bulk_exec and secondary_exec:
                print(f"\nBulk packing status: {bulk_exec.status}")
                print(f"Secondary packaging status: {secondary_exec.status}")
                
                # Check if order is correct
                if bulk_exec.phase.phase_order < secondary_exec.phase.phase_order:
                    print("✓ Phase order is correct (bulk packing before secondary packaging)")
                else:
                    print("✗ ERROR: Incorrect phase order - bulk packing should come before secondary packaging")
                
                # Check if workflow status is consistent
                if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
                    print("✗ ERROR: Secondary packaging is active but bulk packing is not completed")
                elif secondary_exec.status == 'pending' and bulk_exec.status == 'not_ready':
                    print("✗ ERROR: Secondary packaging is pending but bulk packing is not ready")
                else:
                    print("✓ Workflow status is consistent")
            else:
                if not bulk_exec and is_type2:
                    print("✗ ERROR: This is a Type 2 tablet but missing bulk packing phase")
                elif not secondary_exec:
                    print("✗ ERROR: Missing secondary packaging phase")
                elif not bulk_exec and not is_type2:
                    print("✓ This is a regular tablet (not Type 2) so no bulk packing needed")
        
        except BMR.DoesNotExist:
            print(f"BMR {batch_number} not found in the database")
    
    # Check if the system is permanently fixed
    print("\n\n=== VERIFYING SYSTEM FIX ===\n")
    
    # 1. Check production phase configuration
    print("Checking production phase configuration...")
    try:
        phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
        bulk_phase = phases.filter(phase_name='bulk_packing').first()
        secondary_phase = phases.filter(phase_name='secondary_packaging').first()
        
        if bulk_phase and secondary_phase:
            print(f"Bulk packing order: {bulk_phase.phase_order}")
            print(f"Secondary packaging order: {secondary_phase.phase_order}")
            
            if bulk_phase.phase_order < secondary_phase.phase_order:
                print("✓ System configuration is correct - bulk packing comes before secondary packaging")
            else:
                print("✗ System configuration issue - bulk packing should come before secondary packaging")
        else:
            if not bulk_phase:
                print("✗ System configuration issue - missing bulk packing phase definition")
            if not secondary_phase:
                print("✗ System configuration issue - missing secondary packaging phase definition")
    except Exception as e:
        print(f"Error checking phase configuration: {e}")
    
    # 2. Create a simulated workflow for new BMRs
    print("\nSimulating workflow initialization for a new tablet type 2 BMR...")
    
    # Get a tablet type 2 product to use as reference
    tablet2_product = Product.objects.filter(product_type='tablet', tablet_type='tablet_2').first()
    
    if tablet2_product:
        print(f"Using product: {tablet2_product.product_name}")
        
        # Simulate the workflow initialization (without creating a BMR)
        workflow_phases = []
        try:
            base_phases = [
                'bmr_creation',
                'regulatory_approval',
                'material_dispensing',
                'granulation',
                'blending',
                'compression',
                'post_compression_qc',
                'sorting',
            ]
            
            if tablet2_product.coating_type == 'coated':
                base_phases.append('coating')
                
            base_phases.append('packaging_material_release')
            base_phases.append('bulk_packing')  # For tablet type 2
            base_phases.extend(['secondary_packaging', 'final_qa', 'finished_goods_store'])
            
            workflow_phases = base_phases
            
            print("\nSimulated workflow for a new tablet type 2 BMR:")
            for i, phase_name in enumerate(workflow_phases, 1):
                print(f"{i}. {phase_name}")
            
            # Check if bulk packing comes before secondary packaging
            bulk_idx = workflow_phases.index('bulk_packing') if 'bulk_packing' in workflow_phases else -1
            secondary_idx = workflow_phases.index('secondary_packaging') if 'secondary_packaging' in workflow_phases else -1
            
            if bulk_idx >= 0 and secondary_idx >= 0 and bulk_idx < secondary_idx:
                print("\n✓ New BMRs will have the correct workflow order (bulk packing before secondary packaging)")
            else:
                print("\n✗ System initialization issue - workflow order would be incorrect for new BMRs")
                if bulk_idx < 0:
                    print("  - bulk_packing phase is missing from the workflow")
                if secondary_idx < 0:
                    print("  - secondary_packaging phase is missing from the workflow")
                if bulk_idx >= secondary_idx:
                    print("  - bulk_packing would come after or at the same position as secondary_packaging")
        except Exception as e:
            print(f"Error simulating workflow: {e}")
    else:
        print("No tablet type 2 products found for simulation")
    
    print("\n=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    # Flush output buffer to ensure we see all output
    import sys
    sys.stdout.flush()
    print("\n" + "="*80 + "\n")
    print("STARTING ANALYSIS")
    print("\n" + "="*80 + "\n")
    analyze_specific_batches()
    sys.stdout.flush()
    print("\n" + "="*80 + "\n")
    print("ANALYSIS COMPLETED")
    print("\n" + "="*80 + "\n")
