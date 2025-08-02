#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

# Test starting packaging material release for BMR 0022025
bmr = BMR.objects.get(batch_number='0022025')
print(f"=== Testing Packaging Material Release Start for {bmr.batch_number} ===")

# Get the packaging material release phase
try:
    packaging_phase = BatchPhaseExecution.objects.get(
        bmr=bmr, 
        phase__name='packaging_material_release'
    )
    print(f"Found packaging phase: {packaging_phase.phase.name}")
    print(f"Current status: {packaging_phase.status}")
    print(f"Phase order: {packaging_phase.phase_order}")
    
    # Check if it can be started
    workflow_service = WorkflowService()
    can_start = workflow_service.can_start_phase(bmr, packaging_phase.phase.name)
    print(f"Can start phase: {can_start}")
    
    if can_start and packaging_phase.status == 'pending':
        print("\n🚀 Starting packaging material release phase...")
        
        # Start the phase
        packaging_phase.status = 'in_progress'
        packaging_phase.started_at = django.utils.timezone.now()
        packaging_phase.save()
        
        print("✅ Phase started successfully!")
        print(f"New status: {packaging_phase.status}")
        print(f"Started at: {packaging_phase.started_at}")
        
        # Check what packing phases are now visible
        print("\n=== Checking Packing Phases Visibility ===")
        bulk_packing = BatchPhaseExecution.objects.get(bmr=bmr, phase__name='bulk_packing')
        secondary = BatchPhaseExecution.objects.get(bmr=bmr, phase__name='secondary_packaging')
        
        print(f"Bulk packing status: {bulk_packing.status}")
        print(f"Secondary packaging status: {secondary.status}")
        
        # Test if bulk packing can now be started (after packaging material release is completed)
        print("\n=== Simulating Packaging Material Release Completion ===")
        packaging_phase.status = 'completed'
        packaging_phase.completed_at = django.utils.timezone.now()
        packaging_phase.save()
        
        print("✅ Packaging material release marked as completed")
        
        # Trigger next phases
        workflow_service.trigger_next_phase(bmr)
        
        # Check packing phases again
        bulk_packing.refresh_from_db()
        secondary.refresh_from_db()
        
        print(f"After completion - Bulk packing status: {bulk_packing.status}")
        print(f"After completion - Secondary packaging status: {secondary.status}")
        
        can_start_bulk = workflow_service.can_start_phase(bmr, 'bulk_packing')
        print(f"Can start bulk packing: {can_start_bulk}")
        
    else:
        print(f"❌ Cannot start phase. Can start: {can_start}, Status: {packaging_phase.status}")
        
except BatchPhaseExecution.DoesNotExist:
    print("❌ Packaging material release phase not found!")
