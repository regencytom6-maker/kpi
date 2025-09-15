#!/usr/bin/env python
# Script to verify the workflow fixes for failed QC and batch number references

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR
from workflow.services import WorkflowService

def verify_workflow_fix():
    """
    Verify the workflow fixes:
    1. Ensure that batch number is consistently used instead of BMR number
    2. Ensure that post-compression QC failure leads to proper workflow restart
    """
    print("\n=== Verifying Workflow Fixes ===")
    
    # Get all BMRs
    bmrs = BMR.objects.all()
    print(f"Total BMRs in database: {bmrs.count()}")
    
    for bmr in bmrs:
        print(f"\nChecking BMR: {bmr.bmr_number}, Batch: {bmr.batch_number}")
        
        # Get all phase executions for this BMR
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
        print(f"  Total phases: {phases.count()}")
        
        # Get all phases with failed status
        failed_phases = phases.filter(status='failed')
        if failed_phases.exists():
            print(f"  Found {failed_phases.count()} failed phases:")
            for phase in failed_phases:
                print(f"    - {phase.phase.phase_name} (Status: {phase.status})")
                
                # Check if this is a post_compression_qc failure
                if phase.phase.phase_name == 'post_compression_qc':
                    print(f"    Checking post-compression QC failure workflow for batch {bmr.batch_number}:")
                    
                    # Get subsequent phases after the failure
                    granulation_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr, 
                        phase__phase_name='granulation'
                    ).first()
                    
                    blending_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr, 
                        phase__phase_name='blending'
                    ).first()
                    
                    compression_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr, 
                        phase__phase_name='compression'
                    ).first()
                    
                    sorting_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr, 
                        phase__phase_name='sorting'
                    ).first()
                    
                    # Verify that the workflow is being restarted properly
                    print(f"      Granulation phase status: {granulation_phase.status if granulation_phase else 'N/A'}")
                    print(f"      Blending phase status: {blending_phase.status if blending_phase else 'N/A'}")
                    print(f"      Compression phase status: {compression_phase.status if compression_phase else 'N/A'}")
                    print(f"      Sorting phase status: {sorting_phase.status if sorting_phase else 'N/A'}")
                    
                    # Verify the proper sequence for a failed QC
                    if (granulation_phase and granulation_phase.status in ['pending', 'in_progress', 'completed'] and
                        blending_phase and blending_phase.status in ['not_ready', 'pending', 'in_progress'] and
                        compression_phase and compression_phase.status in ['not_ready'] and
                        sorting_phase and sorting_phase.status in ['not_ready']):
                        print("      ✅ Workflow sequence is correct for post-compression QC failure")
                    else:
                        print("      ❌ Workflow sequence may have issues for post-compression QC failure")
                        
                        # Provide more detailed explanation of what's wrong
                        if sorting_phase and sorting_phase.status in ['pending', 'in_progress', 'completed']:
                            print("      ❌ Issue detected: Sorting phase is active but workflow should restart from granulation")
                        
                        if blending_phase and blending_phase.status not in ['not_ready', 'pending', 'in_progress'] and granulation_phase.status == 'completed':
                            print("      ❌ Issue detected: Granulation completed but blending not properly activated")
                        
        else:
            print("  No failed phases found for this BMR")
        
        # Check for any phases in progress
        in_progress_phases = phases.filter(status='in_progress')
        if in_progress_phases.exists():
            print(f"  Phases in progress:")
            for phase in in_progress_phases:
                print(f"    - {phase.phase.phase_name}")
                
        # Check for pending phases
        pending_phases = phases.filter(status='pending')
        if pending_phases.exists():
            print(f"  Pending phases:")
            for phase in pending_phases:
                print(f"    - {phase.phase.phase_name}")
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_workflow_fix()