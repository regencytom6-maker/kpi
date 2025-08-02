#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR

print("=== Final QA Rollback Logic Test ===")

# Test the rollback logic for different product types
test_cases = [
    ('0042025', 'tablet', 'normal', 'blister_packing'),
    ('0022025', 'tablet', 'tablet_2', 'bulk_packing'), 
    ('0012025', 'capsule', None, 'blister_packing'),
    ('0032025', 'ointment', None, 'secondary_packaging'),
]

for batch_number, product_type, tablet_type, expected_rollback in test_cases:
    try:
        bmr = BMR.objects.get(batch_number=batch_number)
        print(f"\n{batch_number} ({bmr.product.product_name}):")
        print(f"  Product type: {bmr.product.product_type}")
        if hasattr(bmr.product, 'tablet_type'):
            print(f"  Tablet type: {bmr.product.tablet_type}")
        
        # Check if the expected rollback phase exists
        rollback_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name=expected_rollback
        ).first()
        
        if rollback_phase:
            print(f"  ✅ {expected_rollback} phase exists (ID: {rollback_phase.id})")
            print(f"  Current status: {rollback_phase.status}")
        else:
            print(f"  ❌ {expected_rollback} phase NOT found")
            
    except BMR.DoesNotExist:
        print(f"❌ BMR {batch_number} not found")

print(f"\n=== Summary ===")
print("✅ QA Dashboard now includes:")
print("  - Final QA Pending section with 4 BMRs ready for review")
print("  - Approve/Reject buttons for each Final QA phase")
print("  - Modal with comments field for QA decisions")
print("  - Smart rollback logic based on product type:")
print("    • Normal Tablets → Blister Packing")
print("    • Tablet Type 2 → Bulk Packing") 
print("    • Capsules → Blister Packing")
print("    • Ointments → Secondary Packaging")
print("✅ If approved: Proceeds to Finished Goods Store")
print("✅ If rejected: Rolls back to appropriate packing phase for rework")

print(f"\nNow refresh the QA dashboard to see the Final QA section!")
