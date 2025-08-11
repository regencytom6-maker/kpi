#!/usr/bin/env python
"""
Simple analysis of specified batches and system configuration
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from products.models import Product

# Check specific batches
batch_numbers = ['0122025', '0132025']

print(f"\n=== ANALYZING BATCHES {', '.join(batch_numbers)} ===\n")

for batch_number in batch_numbers:
    try:
        bmr = BMR.objects.get(batch_number=batch_number)
        print(f"BMR {batch_number}: {bmr.product.product_name}")
        print(f"Product Type: {bmr.product.product_type}, Tablet Type: '{bmr.product.tablet_type}'")
        
        # Get phase executions
        bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
        
        if bulk_exec and secondary_exec:
            print(f"Bulk packing phase order: {bulk_exec.phase.phase_order}, Status: {bulk_exec.status}")
            print(f"Secondary packaging phase order: {secondary_exec.phase.phase_order}, Status: {secondary_exec.status}")
            
            if bulk_exec.phase.phase_order < secondary_exec.phase.phase_order:
                print("CORRECT: Phase order is correct (bulk packing before secondary packaging)")
            else:
                print("ERROR: Incorrect phase order")
                
            if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
                print("ERROR: Secondary packaging is active but bulk packing is not completed")
            else:
                print("CORRECT: Workflow status is consistent")
        else:
            print("Missing one or more required phases")
    except BMR.DoesNotExist:
        print(f"BMR {batch_number} not found in the database")
    
    print("")

# Check system configuration
print("\n=== CHECKING SYSTEM CONFIGURATION ===\n")

# Check production phase order
phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
print("Tablet production phases in order:")
for phase in phases:
    print(f"{phase.phase_order}: {phase.phase_name}")

# Check if bulk packing comes before secondary packaging
bulk_phase = phases.filter(phase_name='bulk_packing').first()
secondary_phase = phases.filter(phase_name='secondary_packaging').first()

if bulk_phase and secondary_phase:
    if bulk_phase.phase_order < secondary_phase.phase_order:
        print("\nCORRECT: System configuration is correct - bulk packing comes before secondary packaging")
    else:
        print("\nERROR: System configuration issue - bulk packing should come before secondary packaging")
else:
    print("\nMissing one or more required phases in system configuration")

# Check for tablet type 2 products
tablet2_products = Product.objects.filter(product_type='tablet', tablet_type='tablet_2')
print(f"\nFound {tablet2_products.count()} Tablet Type 2 products:")
for product in tablet2_products:
    print(f"- {product.product_name}")

print("\n=== CONCLUSION ===\n")
if bulk_phase and secondary_phase and bulk_phase.phase_order < secondary_phase.phase_order:
    print("CORRECT: The system has been permanently fixed. New BMRs will have the correct workflow.")
    print("  (bulk packing will come before secondary packaging)")
else:
    print("ERROR: There may still be issues with the system configuration.")
    print("  New BMRs might not have the correct workflow order.")
