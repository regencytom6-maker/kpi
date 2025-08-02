#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

# Debug capsule BMR sorting issue
bmr = BMR.objects.get(batch_number='0012025')  # Amoxicillin Capsules
print(f"=== Debugging Capsule Sorting Issue for {bmr.batch_number} ===")
print(f"Product: {bmr.product.product_name}")
print(f"Product type: {bmr.product.product_type}")

# Get all phases for this BMR
phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')

print(f"\n=== Current Phase Status ===")
for phase in phases:
    status_icon = {
        'completed': '✅',
        'in_progress': '🔄',
        'pending': '⏳',
        'not_ready': '⚫',
        'failed': '❌'
    }.get(phase.status, '❓')
    
    print(f"  {status_icon} {phase.phase.phase_name} (order {phase.phase.phase_order}): {phase.status}")

# Focus on sorting phase
try:
    sorting_phase = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='sorting')
    print(f"\n=== Sorting Phase Details ===")
    print(f"Status: {sorting_phase.status}")
    print(f"Phase order: {sorting_phase.phase.phase_order}")
    print(f"Started by: {sorting_phase.started_by}")
    print(f"Started date: {sorting_phase.started_date}")
    print(f"Completed by: {sorting_phase.completed_by}")
    print(f"Completed date: {sorting_phase.completed_date}")
    print(f"Notes: {sorting_phase.operator_comments}")
    
    # Check if sorting can be started
    workflow_service = WorkflowService()
    can_start = workflow_service.can_start_phase(bmr, 'sorting')
    print(f"Can start sorting: {can_start}")
    
    # Check prerequisites
    print(f"\n=== Sorting Prerequisites ===")
    print(f"Sorting phase order: {sorting_phase.phase.phase_order}")
    
    prerequisite_phases = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_order__lt=sorting_phase.phase.phase_order
    ).select_related('phase').order_by('phase__phase_order')
    
    all_completed = True
    for prereq in prerequisite_phases:
        is_completed = prereq.status == 'completed'
        if not is_completed:
            all_completed = False
        status_icon = '✅' if is_completed else '❌'
        print(f"  {status_icon} {prereq.phase.phase_name}: {prereq.status}")
    
    print(f"All prerequisites completed: {all_completed}")
    
    # Check what happens when we try to start sorting
    if sorting_phase.status == 'pending' and can_start:
        print(f"\n=== Testing Sorting Phase Start ===")
        print("Sorting phase should be startable. Testing...")
        
        # Check the workflow logic
        expected_workflow = WorkflowService.PRODUCT_WORKFLOWS.get('capsule', [])
        print(f"Expected capsule workflow: {expected_workflow}")
        
        sorting_index = expected_workflow.index('sorting') if 'sorting' in expected_workflow else -1
        packaging_index = expected_workflow.index('packaging_material_release') if 'packaging_material_release' in expected_workflow else -1
        
        print(f"Sorting index in workflow: {sorting_index}")
        print(f"Packaging material release index: {packaging_index}")
        
        if sorting_index < packaging_index:
            print("✅ Sorting should come BEFORE packaging material release")
        else:
            print("❌ Workflow order issue detected!")
    
except BatchPhaseExecution.DoesNotExist:
    print("❌ Sorting phase not found for this BMR!")

# Check packaging material release status
try:
    packaging_phase = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='packaging_material_release')
    print(f"\n=== Packaging Material Release Status ===")
    print(f"Status: {packaging_phase.status}")
    print(f"Phase order: {packaging_phase.phase.phase_order}")
    
    if packaging_phase.status == 'completed':
        print("⚠️  Packaging material already released - this may have bypassed sorting!")
        
except BatchPhaseExecution.DoesNotExist:
    print("❌ Packaging material release phase not found!")
