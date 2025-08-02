#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

print("=== Debugging Packing Dashboard Phase Visibility ===")

# Check what phases should be visible to packing operator
all_bmrs = BMR.objects.all()
print(f"Total BMRs: {all_bmrs.count()}")

total_packing_phases = 0
for bmr in all_bmrs:
    print(f"\n--- BMR {bmr.batch_number} ---")
    
    # Get phases for packing operator role
    user_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
    print(f"Phases for packing operator: {len(user_phases)}")
    
    for phase in user_phases:
        print(f"  - {phase.phase.phase_name}: {phase.status}")
        total_packing_phases += 1
    
    # Also check all packing-related phases directly
    packing_phases = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name__in=['blister_packing', 'bulk_packing', 'secondary_packaging']
    )
    
    print(f"Direct packing phases: {packing_phases.count()}")
    for phase in packing_phases:
        print(f"  - {phase.phase.phase_name}: {phase.status}")

print(f"\n=== Summary ===")
print(f"Total packing phases found via get_phases_for_user_role: {total_packing_phases}")

# Test the get_phases_for_user_role method specifically
print(f"\n=== Testing get_phases_for_user_role method ===")
if all_bmrs.exists():
    test_bmr = all_bmrs.first()
    print(f"Testing with BMR: {test_bmr.batch_number}")
    
    try:
        test_phases = WorkflowService.get_phases_for_user_role(test_bmr, 'packing_operator')
        print(f"Method returned {len(test_phases)} phases")
        for phase in test_phases:
            print(f"  - {phase.phase.phase_name}: {phase.status}")
    except Exception as e:
        print(f"Error calling get_phases_for_user_role: {e}")

# Check if the method exists
print(f"\n=== Method Check ===")
if hasattr(WorkflowService, 'get_phases_for_user_role'):
    print("✅ get_phases_for_user_role method exists")
else:
    print("❌ get_phases_for_user_role method not found!")
    
    # List available methods
    methods = [method for method in dir(WorkflowService) if not method.startswith('_')]
    print(f"Available methods: {methods}")
