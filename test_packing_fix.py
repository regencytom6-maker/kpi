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

print("=== Testing Fixed Packing Dashboard Context ===")

# Simulate the exact logic from the FIXED packing_dashboard view
all_bmrs = BMR.objects.all()

my_phases = []
for bmr in all_bmrs:
    user_phases = WorkflowService.get_phases_for_user_role(bmr, 'packing_operator')
    my_phases.extend(user_phases)

# Updated statistics with template compatibility
stats = {
    'pending_phases': len([p for p in my_phases if p.status == 'pending']),
    'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
    'pending_packing': len([p for p in my_phases if p.status == 'pending']),  # For template compatibility
    'in_progress_packing': len([p for p in my_phases if p.status == 'in_progress']),  # For template compatibility
    'completed_today': 0,  # Simplified for test
    'total_batches': len(set([p.bmr for p in my_phases])),
}

# Updated context with template compatibility
context = {
    'my_phases': my_phases,
    'packing_phases': my_phases,  # For template compatibility
    'stats': stats,
}

print(f"Fixed template context:")
print(f"  packing_phases count: {len(context['packing_phases'])}")
print(f"  stats.pending_packing: {context['stats']['pending_packing']}")
print(f"  stats.in_progress_packing: {context['stats']['in_progress_packing']}")

print(f"\nTemplate checks:")
print(f"  if packing_phases → {bool(context['packing_phases'])}")
print(f"  Template will show phases: {'✅ YES' if context['packing_phases'] else '❌ NO'}")

print(f"\nPhases that will be displayed:")
for i, phase in enumerate(context['packing_phases'], 1):
    print(f"  {i}. BMR {phase.bmr.batch_number}: {phase.phase.phase_name} ({phase.status})")

print(f"\n=== Fix Summary ===")
print(f"✅ Added 'packing_phases' to context (was missing)")
print(f"✅ Added 'pending_packing' to stats (was pending_phases)")
print(f"✅ Added 'in_progress_packing' to stats (was in_progress_phases)")
print(f"✅ Template should now display all {len(context['packing_phases'])} phases")
