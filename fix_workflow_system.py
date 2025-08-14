#!/usr/bin/env python
"""
Fix the workflow system for approved BMRs that are missing raw_material_release phases
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

def fix_approved_bmrs():
    """Add missing raw_material_release phases to approved BMRs"""
    print("=== Fixing Approved BMRs Workflow ===")
    
    # Get all approved BMRs
    approved_bmrs = BMR.objects.filter(status='approved')
    print(f"Found {approved_bmrs.count()} approved BMRs")
    
    for bmr in approved_bmrs:
        print(f"\nProcessing BMR {bmr.bmr_number}...")
        
        # Check if raw_material_release phase exists
        raw_material_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='raw_material_release'
        ).first()
        
        if not raw_material_phase:
            print(f"  Missing raw_material_release phase - creating...")
            
            # Get or create the production phase definition
            phase_def, created = ProductionPhase.objects.get_or_create(
                product_type=bmr.product.product_type,
                phase_name='raw_material_release',
                defaults={
                    'phase_order': 2,  # After regulatory approval (order 1)
                    'is_mandatory': True,
                    'requires_approval': False
                }
            )
            
            if created:
                print(f"  Created ProductionPhase definition for raw_material_release")
            
            # Create the batch phase execution
            BatchPhaseExecution.objects.create(
                bmr=bmr,
                phase=phase_def,
                status='pending'  # Ready to be worked on by store manager
            )
            print(f"  Created raw_material_release phase execution (status: pending)")
            
        else:
            print(f"  Raw material release phase exists (status: {raw_material_phase.status})")
            # If it exists but is not_ready, make it pending
            if raw_material_phase.status == 'not_ready':
                raw_material_phase.status = 'pending'
                raw_material_phase.save()
                print(f"  Updated status from not_ready to pending")

def verify_fix():
    """Verify that the fix worked"""
    print("\n=== Verification ===")
    
    approved_bmrs = BMR.objects.filter(status='approved')
    
    for bmr in approved_bmrs:
        raw_material_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='raw_material_release'
        ).first()
        
        if raw_material_phase:
            print(f"BMR {bmr.bmr_number}: raw_material_release = {raw_material_phase.status}")
        else:
            print(f"BMR {bmr.bmr_number}: NO raw_material_release phase!")

if __name__ == '__main__':
    fix_approved_bmrs()
    verify_fix()
    print("\n=== Fix Complete ===")
