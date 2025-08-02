#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

# Test sorting dashboard visibility after the fix
print("=== Testing Sorting Dashboard After Fix ===")

# Get all BMRs
all_bmrs = BMR.objects.all()

# Simulate what the sorting operator sees
print(f"\n=== Sorting Operator Dashboard View ===")
my_phases = []

for bmr in all_bmrs:
    # Get phases for sorting operator role
    user_phases = WorkflowService.get_phases_for_user_role(bmr, 'sorting_operator')
    my_phases.extend(user_phases)

print(f"Total phases visible to sorting operator: {len(my_phases)}")

for phase in my_phases:
    status_icon = {
        'completed': '✅',
        'in_progress': '🔄',
        'pending': '⏳',
        'not_ready': '⚫',
        'failed': '❌',
        'skipped': '⏭️'
    }.get(phase.status, '❓')
    
    print(f"  {status_icon} BMR {phase.bmr.batch_number}: {phase.phase.phase_name} - {phase.status}")

# Count by status
pending_count = len([p for p in my_phases if p.status == 'pending'])
skipped_count = len([p for p in my_phases if p.status == 'skipped'])
completed_count = len([p for p in my_phases if p.status == 'completed'])

print(f"\n=== Summary ===")
print(f"Pending phases: {pending_count}")
print(f"Skipped phases: {skipped_count}")
print(f"Completed phases: {completed_count}")

if pending_count == 0:
    print(f"✅ No orphaned sorting phases - fix successful!")
else:
    print(f"⚠️ Still has pending phases - may need attention")

# Test packing dashboard as well
print(f"\n=== Packing Operator Dashboard View ===")
packing_phases = []

for bmr in all_bmrs:
    user_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
    packing_phases.extend(user_phases)

print(f"Total phases visible to packing operator: {len(packing_phases)}")

for phase in packing_phases:
    status_icon = {
        'completed': '✅',
        'in_progress': '🔄',
        'pending': '⏳',
        'not_ready': '⚫',
        'failed': '❌',
        'skipped': '⏭️'
    }.get(phase.status, '❓')
    
    print(f"  {status_icon} BMR {phase.bmr.batch_number}: {phase.phase.phase_name} - {phase.status}")

packing_pending = len([p for p in packing_phases if p.status == 'pending'])
print(f"\nPacking phases pending: {packing_pending}")

if packing_pending > 0:
    print(f"✅ Packing phases are now available after packaging material release!")
else:
    print(f"ℹ️ No packing phases currently pending")

print(f"\n=== Test Complete ===")
