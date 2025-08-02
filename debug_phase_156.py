#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR

# Check specific phase from debug output
phase = BatchPhaseExecution.objects.get(id=156)
print(f'Phase: {phase.phase}')
print(f'Status: {phase.status}')
print(f'Phase order: {phase.phase.phase_order}')

# Check BMR workflow context
bmr = phase.bmr
print(f'\nBMR: {bmr.batch_number}')
print(f'Product: {bmr.product.name}')
print(f'Product type: {bmr.product.product_type}')

# Check previous phases
prev_phases = BatchPhaseExecution.objects.filter(
    bmr=bmr, 
    phase__phase_order__lt=phase.phase.phase_order
).order_by('phase__phase_order')
print(f'\nPrevious phases status:')
for p in prev_phases:
    print(f'  {p.phase.phase_order}. {p.phase} - {p.status}')

# Check if there's a specific issue with the start logic
from workflow.services import WorkflowService
service = WorkflowService()
can_start_result = service.can_start_phase(phase)
print(f'\nWorkflow service can_start_phase result: {can_start_result}')

# Check what happens when we try to start
print(f'\nTesting phase start...')
try:
    result = service.start_phase(phase.id, bmr.created_by)
    print(f'Start result: {result}')
except Exception as e:
    print(f'Start failed: {e}')
    import traceback
    traceback.print_exc()
