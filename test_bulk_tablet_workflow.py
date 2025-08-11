"""
Test script to verify that after coating, Type 2 tablets go to bulk packing not secondary packaging
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

def test_specific_bmr(batch_number=None):
    """Test a specific BMR for correct workflow progression"""
    
    # If no batch number provided, get all Type 2 tablet BMRs
    if not batch_number:
        bmrs = BMR.objects.filter(
            product__product_type='tablet',
            product__tablet_type='tablet_2',
            product__coating_type='coated'
        )
        
        if not bmrs:
            print("No Type 2 coated tablet BMRs found!")
            return
            
        bmr = bmrs.first()
    else:
        try:
            bmr = BMR.objects.get(batch_number=batch_number)
        except BMR.DoesNotExist:
            print(f"BMR {batch_number} not found!")
            return
    
    print(f"=== TESTING WORKFLOW FOR BMR {bmr.batch_number} ===")
    print(f"Product: {bmr.product.product_name}")
    print(f"Product Type: {bmr.product.product_type}")
    print(f"Tablet Type: {bmr.product.tablet_type}")
    print(f"Is Coated: {bmr.product.is_coated}")
    
    # Get all phases for this BMR
    phase_executions = BatchPhaseExecution.objects.filter(
        bmr=bmr
    ).select_related('phase').order_by('phase__phase_order')
    
    print("\nPhase Sequence:")
    for idx, phase in enumerate(phase_executions, 1):
        print(f"{idx}. {phase.phase.phase_name} (Order: {phase.phase.phase_order}, Status: {phase.status})")
    
    # Find coating phase
    coating = phase_executions.filter(phase__phase_name='coating').first()
    packaging_material_release = phase_executions.filter(phase__phase_name='packaging_material_release').first()
    bulk_packing = phase_executions.filter(phase__phase_name='bulk_packing').first()
    blister_packing = phase_executions.filter(phase__phase_name='blister_packing').first()
    secondary_packaging = phase_executions.filter(phase__phase_name='secondary_packaging').first()
    
    if coating:
        print(f"\nCoating phase exists (Status: {coating.status})")
        
        # Check what comes after coating
        if coating.status == 'completed':
            # What phase should be active now?
            print("\nTesting coating completion -> next phase activation:")
            if bulk_packing:
                if bulk_packing.status == 'pending' or bulk_packing.status == 'in_progress':
                    print("✅ CORRECT: After coating completion, bulk_packing is active")
                else:
                    print(f"❌ ERROR: After coating completion, bulk_packing status is {bulk_packing.status}")
            else:
                print("❌ ERROR: No bulk_packing phase found!")
    
    # Verify correct phase order
    print("\nPhase Order Check:")
    if coating and bulk_packing:
        if coating.phase.phase_order < bulk_packing.phase.phase_order:
            print("✅ CORRECT: coating comes before bulk_packing")
        else:
            print(f"❌ ERROR: coating (order {coating.phase.phase_order}) does not come before bulk_packing (order {bulk_packing.phase.phase_order})")
    
    if packaging_material_release and bulk_packing:
        if packaging_material_release.phase.phase_order < bulk_packing.phase.phase_order:
            print("✅ CORRECT: packaging_material_release comes before bulk_packing")
        else:
            print(f"❌ ERROR: packaging_material_release (order {packaging_material_release.phase.phase_order}) does not come before bulk_packing (order {bulk_packing.phase.phase_order})")
    
    if bulk_packing and secondary_packaging:
        if bulk_packing.phase.phase_order < secondary_packaging.phase.phase_order:
            print("✅ CORRECT: bulk_packing comes before secondary_packaging")
        else:
            print(f"❌ ERROR: bulk_packing (order {bulk_packing.phase.phase_order}) does not come before secondary_packaging (order {secondary_packaging.phase.phase_order})")
    
    # Test simulated completion of coating phase
    if coating and coating.status != 'completed' and bmr.product.is_coated:
        print("\nSimulating coating phase completion:")
        
        # Back up current states
        next_phase_before = WorkflowService.get_next_phase(bmr)
        print(f"Current next phase before: {next_phase_before.phase.phase_name if next_phase_before else 'None'}")
        
        # Complete the coating phase
        print("Completing coating phase (simulation only)...")
        WorkflowService.complete_phase(bmr, 'coating', coating.started_by or bmr.created_by, "Test completion")
        
        # Check what's next
        next_phase_after = WorkflowService.get_next_phase(bmr)
        print(f"Next phase after coating completion: {next_phase_after.phase.phase_name if next_phase_after else 'None'}")
        
        # Verify that bulk_packing is the next phase
        if next_phase_after and next_phase_after.phase.phase_name == 'bulk_packing':
            print("✅ CORRECT: After coating completion, bulk_packing is the next active phase")
        else:
            next_name = next_phase_after.phase.phase_name if next_phase_after else 'None'
            print(f"❌ ERROR: After coating completion, {next_name} is the next phase instead of bulk_packing")
        
        # Now revert the simulation 
        coating.refresh_from_db()
        coating.status = 'in_progress'
        coating.completed_by = None
        coating.completed_date = None
        coating.save()
        
        if bulk_packing:
            bulk_packing.refresh_from_db()
            bulk_packing.status = 'not_ready'
            bulk_packing.save()
            
        print("Reverted simulation changes")

if __name__ == "__main__":
    # Get batch number from command line if provided
    batch_number = None
    if len(sys.argv) > 1:
        batch_number = sys.argv[1]
    
    test_specific_bmr(batch_number)
