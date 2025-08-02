#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from django.utils import timezone

print("=== Simulating Packing Dashboard Context ===")

# Simulate the exact logic from packing_dashboard view
all_bmrs = BMR.objects.all()

my_phases = []
for bmr in all_bmrs:
    user_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
    my_phases.extend(user_phases)

print(f"Total phases found: {len(my_phases)}")
print(f"Phases list:")
for i, phase in enumerate(my_phases):
    print(f"  {i+1}. BMR {phase.bmr.batch_number}: {phase.phase.phase_name} - {phase.status}")

# Calculate statistics exactly like the view does
stats = {
    'pending_phases': len([p for p in my_phases if p.status == 'pending']),
    'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
    'completed_today': BatchPhaseExecution.objects.filter(
        completed_by=None,  # No user specified in debug
        completed_date__date=timezone.now().date()
    ).count(),
    'total_batches': len(set([p.bmr for p in my_phases])),
}

print(f"\nStatistics:")
print(f"  Pending phases: {stats['pending_phases']}")
print(f"  In progress phases: {stats['in_progress_phases']}")
print(f"  Completed today: {stats['completed_today']}")
print(f"  Total batches: {stats['total_batches']}")

# Check if all phases can be started
print(f"\nPhase startability check:")
for phase in my_phases:
    can_start = WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)
    status_icon = "✅" if can_start else "❌"
    print(f"  {status_icon} BMR {phase.bmr.batch_number}: {phase.phase.phase_name} ({phase.status}) - Can start: {can_start}")

print(f"\n=== Template Context Check ===")
# This is what gets passed to the template
template_context = {
    'my_phases': my_phases,
    'stats': stats,
}

print(f"Template will receive:")
print(f"  my_phases count: {len(template_context['my_phases'])}")
print(f"  pending count: {template_context['stats']['pending_phases']}")

if len(my_phases) == 0:
    print("❌ No phases found - template will show 'No Pending Packing Operations'")
elif stats['pending_phases'] == 0:
    print("❌ No pending phases - template may show 'No Pending Packing Operations'")
else:
    print("✅ Phases should be visible in template")

print(f"\n=== Check Template Logic ===")
print("The template likely checks either:")
print(f"1. if my_phases - Result: {bool(my_phases)}")
print(f"2. if stats.pending_phases - Result: {bool(stats['pending_phases'])}")
print(f"3. Both conditions must be satisfied for phases to show")
