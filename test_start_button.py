#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from bmr.models import BMR

# Check specific phase from debug output
phase_execution = BatchPhaseExecution.objects.get(id=156)
print(f'Phase: {phase_execution.phase}')
print(f'Status: {phase_execution.status}')
print(f'Phase name: {phase_execution.phase.phase_name}')

# Check BMR workflow context
bmr = phase_execution.bmr
print(f'\nBMR: {bmr.batch_number}')
print(f'Product: {bmr.product.product_name}')
print(f'Product type: {bmr.product.product_type}')

# Test can_start_phase method exactly as dashboard calls it
can_start_result = WorkflowService.can_start_phase(bmr, phase_execution.phase.phase_name)
print(f'\nWorkflowService.can_start_phase result: {can_start_result}')

# Check previous phases that might be blocking this
prerequisite_phases = BatchPhaseExecution.objects.filter(
    bmr=bmr,
    phase__phase_order__lt=phase_execution.phase.phase_order
)
print(f'\nPrerequisite phases:')
for prereq in prerequisite_phases:
    print(f'  {prereq.phase.phase_order}. {prereq.phase} - {prereq.status}')

# Check if any prerequisite is not completed/skipped
blocking_phases = prerequisite_phases.exclude(status__in=['completed', 'skipped'])
if blocking_phases.exists():
    print(f'\nBlocking phases (not completed/skipped):')
    for block in blocking_phases:
        print(f'  {block.phase.phase_order}. {block.phase} - {block.status}')
else:
    print('\nNo blocking phases found - should be able to start!')

# Test the dashboard POST logic
from django.utils import timezone
print(f'\nSimulating dashboard start action...')

# Check if status is pending
if phase_execution.status == 'pending':
    if can_start_result:
        print('✅ Phase can be started!')
        print('Updating phase status...')
        
        # Simulate what the dashboard does
        phase_execution.status = 'in_progress'
        phase_execution.started_date = timezone.now()
        print(f'Phase status changed to: {phase_execution.status}')
        print('Would save to database if this was real action')
    else:
        print('❌ Phase cannot be started due to prerequisites')
else:
    print(f'❌ Phase status is {phase_execution.status}, not pending')
