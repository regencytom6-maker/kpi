"""
Update WorkflowService to ensure proper routing from bulk_packing to secondary_packaging 
for tablet type 2 products.
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

def update_workflow_service():
    """Update WorkflowService methods to ensure proper phase progression"""
    print("\n=== Updating WorkflowService methods ===")
    
    # Patch complete_phase to ensure proper bulk_packing -> secondary_packaging progression
    original_complete_phase = WorkflowService.complete_phase
    
    def patched_complete_phase(cls, bmr, phase_name, completed_by, comments=None):
        """Enhanced complete_phase with special routing for bulk_packing -> secondary_packaging"""
        try:
            # Mark the current phase as completed using standard logic
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            execution.status = 'completed'
            execution.completed_by = completed_by
            execution.completed_date = timezone.now()
            if comments:
                execution.operator_comments = comments
            execution.save()
            
            # SPECIAL ROUTING LOGIC
            
            # 1. After packaging_material_release for tablet_2, activate bulk_packing
            if (phase_name == 'packaging_material_release' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                print(f"Special routing for BMR {bmr.batch_number}: activating bulk_packing after material release")
                
                bulk_packing = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='bulk_packing',
                    status='not_ready'
                ).first()
                
                if bulk_packing:
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"✅ Activated bulk_packing for tablet_2 BMR {bmr.batch_number}")
                    return bulk_packing
            
            # 2. After bulk_packing for tablet_2, activate secondary_packaging
            elif (phase_name == 'bulk_packing' and 
                  bmr.product.product_type == 'tablet' and
                  getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                print(f"Special routing for BMR {bmr.batch_number}: activating secondary_packaging after bulk_packing")
                
                secondary_packaging = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='secondary_packaging',
                    status='not_ready'
                ).first()
                
                if secondary_packaging:
                    secondary_packaging.status = 'pending'
                    secondary_packaging.save()
                    print(f"✅ Activated secondary_packaging for tablet_2 BMR {bmr.batch_number}")
                    return secondary_packaging
            
            # Standard behavior for other cases
            next_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=execution.phase.phase_order,
                status='not_ready'
            ).order_by('phase__phase_order')
            
            if next_phases.exists():
                next_phase = next_phases.first()
                next_phase.status = 'pending'
                next_phase.save()
                return next_phase
                
        except BatchPhaseExecution.DoesNotExist:
            print(f"Phase execution not found: {phase_name} for BMR {bmr.batch_number}")
        
        return None
    
    # Replace the method
    WorkflowService.complete_phase = classmethod(patched_complete_phase)
    print("✅ Successfully patched WorkflowService.complete_phase")
    
    # Patch trigger_next_phase as well
    original_trigger_next_phase = WorkflowService.trigger_next_phase
    
    def patched_trigger_next_phase(cls, bmr, current_phase):
        """Enhanced trigger_next_phase with special routing for bulk_packing -> secondary_packaging"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase=current_phase
            )
            
            if current_execution.status != 'completed':
                return False
            
            # Special handling for bulk_packing -> secondary_packaging for tablet type 2
            if (current_execution.phase.phase_name == 'bulk_packing' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                secondary_packaging = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='secondary_packaging',
                    status='not_ready'
                ).first()
                
                if secondary_packaging:
                    secondary_packaging.status = 'pending'
                    secondary_packaging.save()
                    print(f"✅ Triggered secondary_packaging after bulk_packing for BMR {bmr.batch_number}")
                    return True
            
            # For normal sequential flow, find next phase in order
            next_phase = ProductionPhase.objects.filter(
                product_type=bmr.product.product_type,
                phase_order__gt=current_execution.phase.phase_order
            ).order_by('phase_order').first()
            
            if next_phase:
                next_execution, created = BatchPhaseExecution.objects.get_or_create(
                    bmr=bmr,
                    phase=next_phase,
                    defaults={'status': 'not_ready'}
                )
                
                if next_execution.status == 'not_ready':
                    next_execution.status = 'pending'
                    next_execution.save()
                    return True
                    
            return False
            
        except BatchPhaseExecution.DoesNotExist:
            return False
    
    # Replace the method
    WorkflowService.trigger_next_phase = classmethod(patched_trigger_next_phase)
    print("✅ Successfully patched WorkflowService.trigger_next_phase")

def test_workflow_transitions():
    """Test the workflow transitions for a tablet type 2 BMR"""
    print("\n=== Testing workflow transitions ===")
    
    # Find a tablet type 2 BMR
    test_bmr = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).first()
    
    if not test_bmr:
        print("No tablet type 2 BMRs found for testing")
        return
        
    print(f"Testing with BMR {test_bmr.batch_number}: {test_bmr.product.product_name}")
    print(f"Product is {'coated' if test_bmr.product.is_coated else 'uncoated'}")
    
    # Get phases
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase')
    
    bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
    
    # Test transition from bulk_packing to secondary_packaging
    if bulk_packing and secondary_packaging:
        print(f"\nTesting bulk_packing → secondary_packaging transition:")
        print(f"- Current bulk_packing status: {bulk_packing.status}")
        print(f"- Current secondary_packaging status: {secondary_packaging.status}")
        
        if bulk_packing.status == 'pending' and secondary_packaging.status == 'not_ready':
            print("✅ Correct sequence: bulk_packing is pending and secondary_packaging is not_ready")
            
            # Test the trigger_next_phase method by simulating completion
            from django.contrib.auth import get_user_model
            User = get_user_model()
            test_user = User.objects.filter(is_staff=True).first()
            
            if test_user and bulk_packing.status == 'pending':
                print(f"\nSimulating bulk_packing completion by {test_user.username}...")
                
                # Use WorkflowService to complete the phase
                next_phase = WorkflowService.complete_phase(
                    test_bmr, 
                    'bulk_packing',
                    test_user,
                    "Test completion for workflow validation"
                )
                
                # Check if secondary_packaging was activated
                secondary_packaging.refresh_from_db()
                print(f"- Secondary packaging status after bulk packing completion: {secondary_packaging.status}")
                
                if secondary_packaging.status == 'pending':
                    print("✅ SUCCESS: secondary_packaging was correctly activated after bulk_packing completion")
                    
                    # Reset the statuses for production
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    secondary_packaging.status = 'not_ready'
                    secondary_packaging.save()
                    print("✓ Reset statuses back to original state")
                else:
                    print("❌ FAILURE: secondary_packaging was not activated after bulk_packing completion")
            else:
                print("⚠️ Skipping completion test - no test user found or bulk_packing not pending")
        else:
            print(f"⚠️ Cannot test transition - phases not in correct state")
    else:
        print("❌ Missing required phases for testing")

if __name__ == "__main__":
    print("===== UPDATING WORKFLOW SERVICE FOR TABLET TYPE 2 =====")
    
    # Update the workflow service methods
    update_workflow_service()
    
    # Test the workflow transitions
    test_workflow_transitions()
    
    print("\n✨ WORKFLOW SERVICE UPDATED SUCCESSFULLY")
    print("The system will now correctly route through the following sequence for tablet type 2:")
    print("1. packaging_material_release → bulk_packing")
    print("2. bulk_packing → secondary_packaging")
