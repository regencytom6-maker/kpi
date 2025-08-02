#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR

# Check the specific BMR mentioned in the logs
bmr = BMR.objects.get(batch_number='0042025')
print(f"BMR: {bmr.batch_number} - {bmr.product.product_name}")
print(f"Product type: {bmr.product.product_type}")

# Get all phases for this BMR
phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')

print(f"\nAll phases for BMR {bmr.batch_number}:")
for phase in phases:
    print(f"  {phase.phase.phase_order}. {phase.phase.phase_name} - {phase.status}")

# Check what phases are in 'not_ready' status
not_ready = phases.filter(status='not_ready')
print(f"\nPhases in 'not_ready' status: {not_ready.count()}")
for phase in not_ready:
    print(f"  {phase.phase.phase_order}. {phase.phase.phase_name}")

# Check what's the last completed phase
completed = phases.filter(status='completed').order_by('-phase__phase_order')
if completed.exists():
    last_completed = completed.first()
    print(f"\nLast completed phase: {last_completed.phase.phase_name}")
    
    # Check what should be the next phase
    next_phases = phases.filter(
        phase__phase_order__gt=last_completed.phase.phase_order,
        status='not_ready'
    ).order_by('phase__phase_order')
    
    if next_phases.exists():
        print(f"Next phase that should be triggered: {next_phases.first().phase.phase_name}")
    else:
        print("No 'not_ready' phases found after the last completed phase")
        
        # Check all phases after last completed
        all_next = phases.filter(
            phase__phase_order__gt=last_completed.phase.phase_order
        ).order_by('phase__phase_order')
        print("All phases after last completed:")
        for phase in all_next:
            print(f"  {phase.phase.phase_order}. {phase.phase.phase_name} - {phase.status}")
else:
    print("No completed phases found")
