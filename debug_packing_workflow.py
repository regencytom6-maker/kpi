#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

print("=== Testing Packing Workflow Logic ===")

# Check each BMR and its packing workflow
for bmr in BMR.objects.all():
    print(f"\n--- BMR {bmr.batch_number} ({bmr.product.product_name}) ---")
    print(f"Product type: {bmr.product.product_type}")
    
    # Check product-specific attributes
    if hasattr(bmr.product, 'tablet_type'):
        print(f"Tablet type: {bmr.product.tablet_type}")
    if hasattr(bmr.product, 'requires_coating'):
        print(f"Requires coating: {bmr.product.requires_coating}")
    if hasattr(bmr.product, 'packing_type'):
        print(f"Packing type: {bmr.product.packing_type}")
    
    # Get packing phases for this BMR
    packing_phases = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name__in=['blister_packing', 'bulk_packing', 'secondary_packaging']
    ).order_by('phase__phase_order')
    
    print(f"Packing phases:")
    for phase in packing_phases:
        can_start = WorkflowService.can_start_phase(bmr, phase.phase.phase_name)
        status_icon = "✅" if can_start else "❌"
        print(f"  {status_icon} {phase.phase.phase_name} (order {phase.phase.phase_order}): {phase.status}")
        
        if not can_start and phase.status == 'pending':
            # Debug why it can't be started
            print(f"    Debug: Checking prerequisites for {phase.phase.phase_name}")
            
            prerequisite_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__lt=phase.phase.phase_order
            ).order_by('phase__phase_order')
            
            print(f"    Prerequisites:")
            for prereq in prerequisite_phases:
                prereq_ok = prereq.status in ['completed', 'skipped']
                prereq_icon = "✅" if prereq_ok else "❌"
                print(f"      {prereq_icon} {prereq.phase.phase_name}: {prereq.status}")

print(f"\n=== Checking Expected Packing Logic ===")

print(f"Expected workflows:")
print(f"• Tablet (Normal): Blister Packing → Secondary Packaging")
print(f"• Tablet Type 2: Bulk Packing → Secondary Packaging") 
print(f"• Ointment: Secondary Packaging only")
print(f"• Capsule: Blister Packing → Secondary Packaging")

print(f"\n=== Workflow Verification ===")
workflows = WorkflowService.PRODUCT_WORKFLOWS

for product_type, workflow in workflows.items():
    print(f"\n{product_type.title()} workflow:")
    packing_phases_in_workflow = []
    for i, phase_name in enumerate(workflow):
        if 'packing' in phase_name:
            packing_phases_in_workflow.append(f"{i+1}. {phase_name}")
    
    if packing_phases_in_workflow:
        for phase in packing_phases_in_workflow:
            print(f"  {phase}")
    else:
        print(f"  No packing phases found")

print(f"\n=== Testing Start Button Issue ===")
# Find a pending packing phase to test
test_phase = BatchPhaseExecution.objects.filter(
    phase__phase_name__in=['blister_packing', 'bulk_packing', 'secondary_packaging'],
    status='pending'
).first()

if test_phase:
    print(f"Testing phase: {test_phase.phase.phase_name} for BMR {test_phase.bmr.batch_number}")
    print(f"Phase ID: {test_phase.id}")
    print(f"Current status: {test_phase.status}")
    can_start = WorkflowService.can_start_phase(test_phase.bmr, test_phase.phase.phase_name)
    print(f"Can be started: {can_start}")
    
    if not can_start:
        print(f"Reason: Prerequisites not met")
    else:
        print(f"✅ Should be able to start this phase")
else:
    print(f"No pending packing phases found for testing")
