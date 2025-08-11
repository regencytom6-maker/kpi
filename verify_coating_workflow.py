"""
Test script to verify the coating workflow fixes.

This script creates a new BMR for a coated tablet product and follows the workflow to
ensure that after sorting, the coating phase is correctly activated.
"""

import os
import django
from django.utils import timezone

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from products.models import Product
from accounts.models import CustomUser

print("COATING WORKFLOW VERIFICATION")
print("============================")

# 1. Find a coated tablet product
coated_tablet = Product.objects.filter(
    product_type='tablet', 
    coating_type='coated'
).first()

if not coated_tablet:
    print("ERROR: No coated tablet products found in database!")
    exit(1)

print(f"Using product: {coated_tablet.product_name}")
print(f"Is coated: {coated_tablet.is_coated}")

# 2. Create a test BMR
batch_number = f"TEST{timezone.now().strftime('%d%m%y%H%M')}"
test_user = CustomUser.objects.first()  # Get any user for test purposes

print(f"Creating test BMR with batch number: {batch_number}")

test_bmr = BMR.objects.create(
    batch_number=batch_number,
    bmr_number=f"BMR-{batch_number}",
    product=coated_tablet,
    batch_size=1000,
    batch_size_unit="tablets",
    created_by=test_user
)

# 3. Initialize workflow
print("Initializing workflow...")
WorkflowService.initialize_workflow_for_bmr(test_bmr)

# 4. Verify all phases are created
print("\nVerifying phase sequence...")
all_phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')

if not all_phases:
    print("ERROR: No phases were created!")
    exit(1)

print("Initial phase statuses:")
for p in all_phases:
    print(f"  {p.phase.phase_order:2d}. {p.phase.phase_name:25} {p.status}")

# 5. Complete the sorting phase
print("\nCompleting the sorting phase...")
sorting_phase = BatchPhaseExecution.objects.filter(
    bmr=test_bmr, 
    phase__phase_name='sorting'
).first()

if not sorting_phase:
    print("ERROR: Sorting phase not found!")
    exit(1)

sorting_phase.status = 'completed'
sorting_phase.completed_date = timezone.now()
sorting_phase.save()

# 6. Trigger next phase after sorting
print("Triggering next phase after sorting...")
WorkflowService.trigger_next_phase(test_bmr, sorting_phase.phase)

# 7. Check if coating is now pending
print("\nVerifying phase statuses after sorting completion:")
all_phases_updated = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
for p in all_phases_updated:
    print(f"  {p.phase.phase_order:2d}. {p.phase.phase_name:25} {p.status}")

coating_phase = BatchPhaseExecution.objects.filter(
    bmr=test_bmr, 
    phase__phase_name='coating'
).first()

packaging_phase = BatchPhaseExecution.objects.filter(
    bmr=test_bmr,
    phase__phase_name='packaging_material_release'
).first()

print("\nVERIFICATION RESULTS")
print("===================")
if coating_phase and coating_phase.status == 'pending':
    print("✅ SUCCESS: Coating phase correctly activated after sorting")
else:
    print("❌ FAILURE: Coating phase not activated after sorting!")
    if coating_phase:
        print(f"  Coating phase status: {coating_phase.status}")
    else:
        print("  Coating phase not found!")

if packaging_phase and packaging_phase.status == 'not_ready':
    print("✅ SUCCESS: Packaging phase correctly NOT activated (should wait for coating)")
else:
    print("❌ FAILURE: Packaging phase incorrectly activated or in wrong status!")
    if packaging_phase:
        print(f"  Packaging phase status: {packaging_phase.status}")
    else:
        print("  Packaging phase not found!")

# 8. Clean up (optional, comment out to keep the test BMR for manual inspection)
# print("\nCleaning up test data...")
# BatchPhaseExecution.objects.filter(bmr=test_bmr).delete()
# test_bmr.delete()
# print("Test data removed.")

print("\nWorkflow verification complete.")
