"""
Test script to verify the bulk packing workflow is working correctly
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.utils import timezone
from django.db.models import Q
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from django.contrib.auth import get_user_model

User = get_user_model()

def test_bulk_workflow():
    """Test the workflow for a tablet type 2 product"""
    print("=== Testing Bulk Packing Workflow ===")
    
    # Try to find a BMR with tablet type 2 that's at the right stage
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    print(f"Found {tablet2_bmrs.count()} tablet type 2 BMRs")
    
    test_bmr = None
    test_pmr = None
    test_bulk = None
    
    # Find a BMR with packaging_material_release completed and bulk_packing pending
    for bmr in tablet2_bmrs:
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
        pmr = phases.filter(phase__phase_name='packaging_material_release').first()
        bulk = phases.filter(phase__phase_name='bulk_packing').first()
        
        if pmr and bulk and pmr.status == 'completed' and bulk.status == 'pending':
            test_bmr = bmr
            test_pmr = pmr
            test_bulk = bulk
            break
    
    if not test_bmr:
        print("No suitable BMR found for testing.")
        print("Creating test workflow...")
        
        # Let's create a test scenario
        # Find a BMR with packaging_material_release that's not yet completed
        for bmr in tablet2_bmrs:
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            pmr = phases.filter(phase__phase_name='packaging_material_release').first()
            bulk = phases.filter(phase__phase_name='bulk_packing').first()
            
            if pmr and bulk and pmr.status != 'completed':
                test_bmr = bmr
                test_pmr = pmr
                test_bulk = bulk
                
                # Get phases up to packaging_material_release
                previous_phases = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_order__lt=pmr.phase.phase_order
                ).order_by('phase__phase_order')
                
                # Make sure all previous phases are completed
                user = User.objects.filter(is_staff=True).first()
                
                for phase in previous_phases:
                    if phase.status != 'completed':
                        if phase.status == 'not_ready':
                            phase.status = 'pending'
                            phase.save()
                        
                        if phase.status == 'pending':
                            phase.status = 'in_progress'
                            phase.started_by = user
                            phase.started_date = timezone.now() - timezone.timedelta(hours=1)
                            phase.save()
                        
                        if phase.status == 'in_progress':
                            phase.status = 'completed'
                            phase.completed_by = user
                            phase.completed_date = timezone.now()
                            phase.save()
                
                # Set packaging_material_release to in_progress
                if pmr.status == 'not_ready':
                    pmr.status = 'pending'
                    pmr.save()
                
                if pmr.status == 'pending':
                    pmr.status = 'in_progress'
                    pmr.started_by = user
                    pmr.started_date = timezone.now()
                    pmr.save()
                
                test_pmr = pmr
                break
    
    if not test_bmr:
        print("Could not find or create a test scenario. Exiting.")
        return
    
    print(f"\nUsing BMR {test_bmr.batch_number}: {test_bmr.product.product_name}")
    print(f"Product Type: {test_bmr.product.product_type}")
    print(f"Tablet Type: {test_bmr.product.tablet_type}")
    
    # Check phase status before
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    print("\nPhases BEFORE:")
    for phase in phases:
        print(f"  {phase.phase.phase_name}: {phase.status}")
    
    # Get key phases
    pmr_phase = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_phase = phases.filter(phase__phase_name='secondary_packaging').first()
    
    # 1. Test completing packaging_material_release
    if pmr_phase and pmr_phase.status == 'in_progress':
        user = User.objects.filter(is_staff=True).first()
        print(f"\nCompleting packaging_material_release phase...")
        
        # Use WorkflowService to complete the phase
        next_phase = WorkflowService.complete_phase(test_bmr, 'packaging_material_release', user)
        print(f"Next phase returned: {next_phase.phase.phase_name if next_phase else 'None'}")
    
    # Refresh phases
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    # Get key phases again
    pmr_phase = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_phase = phases.filter(phase__phase_name='secondary_packaging').first()
    
    print("\nPhases AFTER completing packaging_material_release:")
    for phase in phases:
        print(f"  {phase.phase.phase_name}: {phase.status}")
    
    # 2. Test starting bulk_packing
    if bulk_phase and bulk_phase.status == 'pending':
        user = User.objects.filter(is_staff=True).first()
        print(f"\nStarting bulk_packing phase...")
        
        # Check if we can start bulk_packing
        can_start = WorkflowService.can_start_phase(test_bmr, 'bulk_packing')
        print(f"Can start bulk_packing: {can_start}")
        
        if can_start:
            # Use WorkflowService to start the phase
            started_phase = WorkflowService.start_phase(test_bmr, 'bulk_packing', user)
            print(f"Started phase: {started_phase.phase.phase_name if started_phase else 'None'}")
    
    # Refresh phases
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    # Get key phases again
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    
    print("\nPhases AFTER starting bulk_packing:")
    for phase in phases:
        print(f"  {phase.phase.phase_name}: {phase.status}")
    
    # 3. Test completing bulk_packing
    if bulk_phase and bulk_phase.status == 'in_progress':
        user = User.objects.filter(is_staff=True).first()
        print(f"\nCompleting bulk_packing phase...")
        
        # Use WorkflowService to complete the phase
        next_phase = WorkflowService.complete_phase(test_bmr, 'bulk_packing', user)
        print(f"Next phase returned: {next_phase.phase.phase_name if next_phase else 'None'}")
    
    # Refresh phases
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    print("\nPhases AFTER completing bulk_packing:")
    for phase in phases:
        print(f"  {phase.phase.phase_name}: {phase.status}")
    
    # Final verification
    pmr_phase = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_phase = phases.filter(phase__phase_name='secondary_packaging').first()
    
    print("\nVerifying workflow progression:")
    if pmr_phase.status == 'completed':
        print("✅ packaging_material_release is completed")
    else:
        print(f"❌ packaging_material_release should be completed but is {pmr_phase.status}")
    
    if bulk_phase.status == 'completed':
        print("✅ bulk_packing is completed")
    elif bulk_phase.status == 'in_progress':
        print("✓ bulk_packing is in progress (partially tested)")
    else:
        print(f"❌ bulk_packing should be in_progress or completed but is {bulk_phase.status}")
    
    if secondary_phase.status == 'pending':
        print("✅ secondary_packaging is pending (activated after bulk_packing)")
    elif secondary_phase.status == 'not_ready' and bulk_phase.status != 'completed':
        print("✓ secondary_packaging is not_ready (will be activated when bulk_packing completes)")
    else:
        print(f"❌ secondary_packaging should be pending or not_ready but is {secondary_phase.status}")
    
    print("\nBulk packing workflow test completed!")

if __name__ == "__main__":
    test_bulk_workflow()
