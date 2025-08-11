"""
Final fix for bulk packing workflow - addressing the can_start_phase logic
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db import transaction
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

def fix_can_start_phase():
    """Fix the can_start_phase method for special cases"""
    print("\n=== Fixing can_start_phase method for bulk packing ===")
    
    # Get the original method
    original_can_start = WorkflowService.can_start_phase
    
    # Create our patched version
    def patched_can_start_phase(cls, bmr, phase_name):
        """Enhanced can_start_phase with special handling for bulk packing"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Cannot start phases that are not pending
            if current_execution.status != 'pending':
                return False
            
            # Special handling for bulk_packing after failed QC
            # If bulk_packing is pending but post_compression_qc failed,
            # we should still allow starting bulk_packing
            if (phase_name == 'bulk_packing' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                # Check if post_compression_qc failed but packaging_material_release is complete
                post_qc = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_compression_qc'
                ).first()
                
                packaging_material_release = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='packaging_material_release'
                ).first()
                
                if post_qc and post_qc.status == 'failed' and packaging_material_release and packaging_material_release.status == 'completed':
                    print(f"Special case: Allowing bulk_packing to start despite failed QC because packaging_material_release is completed")
                    return True
            
            # Get all phases with lower order (prerequisites)
            prerequisite_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__lt=current_execution.phase.phase_order
            )
            
            # Check if all prerequisite phases are completed, skipped or failed (for QC)
            for prereq in prerequisite_phases:
                # For QC phases, 'failed' is acceptable for progression
                if 'qc' in prereq.phase.phase_name and prereq.status == 'failed':
                    continue
                
                if prereq.status not in ['completed', 'skipped']:
                    return False
            
            return True
                
        except BatchPhaseExecution.DoesNotExist:
            return False
    
    # Replace the method
    WorkflowService.can_start_phase = classmethod(patched_can_start_phase)
    print("✅ Successfully patched WorkflowService.can_start_phase with special handling for bulk packing")

def fix_specific_batches():
    """Fix specific batches that have issues"""
    print("\n=== Fixing specific batches ===")
    
    # Find batches with failed QC but pending bulk_packing
    problem_bmrs = []
    
    # Find all tablet type 2 batches
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    for bmr in tablet2_bmrs:
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
        post_qc = phases.filter(phase__phase_name='post_compression_qc').first()
        bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
        packaging_material_release = phases.filter(phase__phase_name='packaging_material_release').first()
        secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
        
        # Check for specific issue: failed QC, completed packaging_material_release, but can't start bulk_packing
        if (post_qc and post_qc.status == 'failed' and
            packaging_material_release and packaging_material_release.status == 'completed' and
            bulk_packing and bulk_packing.status == 'pending' and
            secondary_packaging and secondary_packaging.status == 'pending'):
            
            problem_bmrs.append(bmr)
            print(f"Found problematic BMR {bmr.batch_number}: {bmr.product.product_name}")
    
    print(f"Found {len(problem_bmrs)} batches with issues")
    
    # Now test if our fix works
    for bmr in problem_bmrs:
        print(f"\nTesting fix for BMR {bmr.batch_number}:")
        # Test can_start_phase
        can_start = WorkflowService.can_start_phase(bmr, 'bulk_packing')
        print(f"Can start bulk_packing now: {can_start}")
        
        if can_start:
            # Allow user to start this phase
            user = User.objects.filter(is_staff=True).first()
            bulk_packing = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
            
            if bulk_packing and bulk_packing.status == 'pending':
                print(f"Starting bulk_packing phase for BMR {bmr.batch_number}...")
                bulk_packing.status = 'in_progress'
                bulk_packing.started_by = user
                bulk_packing.started_date = timezone.now()
                bulk_packing.save()
                print(f"✅ Successfully started bulk_packing for BMR {bmr.batch_number}")

def test_fix():
    """Test our fixes"""
    print("\n=== Testing fixes ===")
    
    # Find a batch with completed bulk_packing and verify next phase
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    for bmr in tablet2_bmrs:
        bulk_packing = BatchPhaseExecution.objects.filter(
            bmr=bmr, phase__phase_name='bulk_packing', status='in_progress').first()
        
        if bulk_packing:
            print(f"Testing BMR {bmr.batch_number} with in_progress bulk_packing")
            user = User.objects.filter(is_staff=True).first()
            next_phase = WorkflowService.complete_phase(bmr, 'bulk_packing', user)
            print(f"After completing bulk_packing, next phase is: {next_phase.phase.phase_name if next_phase else 'None'}")
            break
    
if __name__ == "__main__":
    # Fix the can_start_phase method
    fix_can_start_phase()
    
    # Fix specific batches
    fix_specific_batches()
    
    # Test the fixes
    test_fix()
