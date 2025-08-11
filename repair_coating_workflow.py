"""
Repair script for tablet coated products workflow.

This script ensures that all coated tablet batches have the correct workflow sequence:
1. Ensures coating phase follows sorting phase for coated tablets
2. Ensures packaging phase follows coating phase for coated tablets
3. Fixes any incorrect phase statuses based on product type
4. Reports a full status of all tablet BMRs and their phase sequences
"""

import os
import django
import sys
from django.utils import timezone

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from products.models import Product

print("TABLET WORKFLOW REPAIR UTILITY")
print("==============================")

# Get all tablet BMRs
tablet_bmrs = BMR.objects.filter(product__product_type='tablet')
print(f"Found {tablet_bmrs.count()} tablet BMRs")

fixed_count = 0
coated_count = 0
uncoated_count = 0

for bmr in tablet_bmrs:
    print(f"\nProcessing BMR {bmr.batch_number} - {bmr.product.product_name}")
    print(f"Is Coated: {bmr.product.is_coated}")
    
    # Get relevant phases
    sorting_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr, 
        phase__phase_name='sorting'
    ).first()
    
    coating_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr, 
        phase__phase_name='coating'
    ).first()
    
    packaging_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='packaging_material_release'
    ).first()
    
    if not (sorting_phase and coating_phase and packaging_phase):
        print(f"  ERROR: Missing required phases for BMR {bmr.batch_number}")
        continue
    
    print(f"  Current phase statuses:")
    print(f"  - Sorting: {sorting_phase.status}")
    print(f"  - Coating: {coating_phase.status}")
    print(f"  - Packaging: {packaging_phase.status}")
    
    needs_fixing = False
    
    # Check if this is a coated tablet
    if bmr.product.is_coated:
        coated_count += 1
        
        # If sorting is completed but coating is not pending/completed/skipped
        if sorting_phase.status == 'completed' and coating_phase.status == 'not_ready':
            print(f"  ISSUE: Sorting completed but coating not activated")
            coating_phase.status = 'pending'
            coating_phase.save()
            needs_fixing = True
            
        # If coating is completed but packaging is not pending/completed
        if coating_phase.status == 'completed' and packaging_phase.status == 'not_ready':
            print(f"  ISSUE: Coating completed but packaging not activated")
            packaging_phase.status = 'pending'
            packaging_phase.save()
            needs_fixing = True
            
        # If coating was skipped for a coated product
        if coating_phase.status == 'skipped' and sorting_phase.status == 'completed':
            print(f"  ISSUE: Coating was incorrectly skipped for a coated product")
            # If packaging is not started, reset coating to pending
            if packaging_phase.status in ['not_ready', 'pending']:
                coating_phase.status = 'pending'
                coating_phase.operator_comments = "Phase reset - product requires coating"
                coating_phase.completed_date = None
                coating_phase.save()
                needs_fixing = True
    else:
        uncoated_count += 1
        
        # If sorting is completed and coating is not skipped for uncoated
        if sorting_phase.status == 'completed' and coating_phase.status != 'skipped':
            print(f"  ISSUE: Sorting completed but coating not skipped for uncoated product")
            coating_phase.status = 'skipped'
            coating_phase.completed_date = timezone.now()
            coating_phase.operator_comments = "Phase skipped - product does not require coating"
            coating_phase.save()
            needs_fixing = True
            
        # If sorting is completed but packaging not activated for uncoated
        if sorting_phase.status == 'completed' and packaging_phase.status == 'not_ready':
            print(f"  ISSUE: Sorting completed but packaging not activated for uncoated product")
            packaging_phase.status = 'pending'
            packaging_phase.save()
            needs_fixing = True
    
    if needs_fixing:
        print("  ✅ Fixed workflow issues")
        fixed_count += 1
    else:
        print("  ✓ No issues found")

print("\nREPAIR SUMMARY")
print("==============")
print(f"Total tablet BMRs processed: {tablet_bmrs.count()}")
print(f"Coated tablet BMRs: {coated_count}")
print(f"Uncoated tablet BMRs: {uncoated_count}")
print(f"BMRs with fixed workflow: {fixed_count}")
print("\nWorkflow repair complete.")
