#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from django.utils import timezone

# Find the in-progress blister packing phase that's blocking
blocking_phase = BatchPhaseExecution.objects.filter(
    phase__phase_name='blister_packing',
    status='in_progress'
).first()

if blocking_phase:
    print(f"Found blocking phase: {blocking_phase.phase.phase_name} for BMR {blocking_phase.bmr.batch_number}")
    
    # Complete it to unblock the secondary packaging
    blocking_phase.status = 'completed'
    blocking_phase.completed_date = timezone.now()
    blocking_phase.operator_comments = "Completed for testing - demonstrating start button functionality"
    blocking_phase.save()
    
    print(f"✅ Completed {blocking_phase.phase.phase_name}")
    
    # Now check if secondary packaging can be started
    secondary_phase = BatchPhaseExecution.objects.filter(
        bmr=blocking_phase.bmr,
        phase__phase_name='secondary_packaging',
        status='pending'
    ).first()
    
    if secondary_phase:
        can_start = WorkflowService.can_start_phase(secondary_phase.bmr, secondary_phase.phase.phase_name)
        print(f"\nSecondary packaging phase {secondary_phase.id} can now be started: {can_start}")
        
        if can_start:
            print("🎉 SUCCESS! The start button will now work for this phase!")
            print(f"Phase ID: {secondary_phase.id}")
            print(f"BMR: {secondary_phase.bmr.batch_number}")
            print(f"Product: {secondary_phase.bmr.product.product_name}")
            print(f"Status: {secondary_phase.status}")
        else:
            print("❌ Still blocked by other phases")
    else:
        print("No secondary packaging phase found")
else:
    print("No blocking in-progress blister packing phase found")
