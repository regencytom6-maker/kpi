#!/usr/bin/env python
"""
Fix workflow phase orders after correcting the workflow sequence
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

def fix_workflow_order():
    """Fix the workflow phase order for existing BMRs after updating the workflow sequence"""
    
    print("Fixing workflow phase orders...")
    
    # Get all BMRs that need fixing
    bmrs = BMR.objects.all()
    
    for bmr in bmrs:
        print(f"\nProcessing BMR: {bmr.batch_number}")
        
        # Re-initialize the workflow for this BMR with correct order
        try:
            # Delete existing phases that are not yet started
            not_started_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                status='not_ready',
                started_by__isnull=True
            )
            
            print(f"  Deleting {not_started_phases.count()} not-started phases")
            not_started_phases.delete()
            
            # Re-initialize workflow with correct order
            WorkflowService.initialize_workflow_for_bmr(bmr)
            print(f"  Re-initialized workflow for {bmr.batch_number}")
            
            # Check the phases after fixing
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
            print(f"  Current phases:")
            for phase in phases:
                print(f"    - {phase.phase.phase_name}: {phase.status}")
                
        except Exception as e:
            print(f"  Error processing {bmr.batch_number}: {e}")

if __name__ == "__main__":
    fix_workflow_order()
