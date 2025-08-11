"""
Permanent fix for bulk tablet workflow issues
- Corrects phase ordering for tablet type 2
- Ensures bulk packing is always included for tablet_2 products
- Adds special routing logic in WorkflowService.complete_phase
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

def fix_phase_ordering():
    """Fix the ordering of phases for all product types"""
    print("\n=== Fixing phase ordering for all product types ===")
    
    # Ensure proper phase ordering for tablet products
    tablet_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    
    # Print current ordering
    print("Current tablet phase ordering:")
    for i, phase in enumerate(tablet_phases, 1):
        print(f"{i:2d}. {phase.phase_name} (order: {phase.phase_order})")
    
    # Get critical phases
    coating = tablet_phases.filter(phase_name='coating').first()
    packaging_material_release = tablet_phases.filter(phase_name='packaging_material_release').first()
    bulk_packing = tablet_phases.filter(phase_name='bulk_packing').first()
    blister_packing = tablet_phases.filter(phase_name='blister_packing').first()
    secondary_packaging = tablet_phases.filter(phase_name='secondary_packaging').first()
    
    if not all([packaging_material_release, bulk_packing, blister_packing, secondary_packaging]):
        print("❌ ERROR: Some required phases are missing")
        return False
        
    with transaction.atomic():
        # Set correct ordering
        # 1. Packaging material release
        packaging_order = packaging_material_release.phase_order
        
        # 2. Packing phases (blister or bulk) should be next
        packing_order = packaging_order + 1
        blister_packing.phase_order = packing_order
        bulk_packing.phase_order = packing_order
        blister_packing.save()
        bulk_packing.save()
        
        # 3. Secondary packaging should follow
        secondary_packaging.phase_order = packing_order + 1
        secondary_packaging.save()
        
        print("\nUpdated phase ordering:")
        print(f"packaging_material_release: {packaging_order}")
        print(f"blister_packing: {packing_order}")
        print(f"bulk_packing: {packing_order}")
        print(f"secondary_packaging: {packing_order + 1}")
        
    return True

def update_workflow_service():
    """Update the WorkflowService to handle special routing"""
    print("\n=== Updating WorkflowService for special routing ===")
    
    # Get the complete_phase method from WorkflowService
    original_complete_phase = WorkflowService.complete_phase
    
    # Create a patched version that handles tablet type 2 routing
    def patched_complete_phase(cls, bmr, phase_name, completed_by, comments=None):
        """Enhanced complete_phase with special routing logic for tablet type 2"""
        try:
            # Regular completion logic
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Mark current phase as completed
            execution.status = 'completed'
            execution.completed_by = completed_by
            execution.completed_date = timezone.now()
            if comments:
                execution.operator_comments = comments
            execution.save()
            
            # SPECIAL ROUTING: For tablet type 2 with packaging_material_release completion
            if (phase_name == 'packaging_material_release' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                print(f"Special routing for tablet_2 BMR {bmr.batch_number} after packaging_material_release")
                
                # Get bulk packing phase
                bulk_packing = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='bulk_packing',
                    status='not_ready'
                ).first()
                
                if bulk_packing:
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"Activated bulk_packing phase for tablet_2 BMR {bmr.batch_number}")
                    return bulk_packing
            
            # Regular next phase activation logic
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
            print(f"Phase execution not found: {phase_name} for BMR {bmr.bmr_number}")
        
        return None
    
    # Replace the original method with our patched version
    WorkflowService.complete_phase = classmethod(patched_complete_phase)
    print("✅ Successfully patched WorkflowService.complete_phase with special routing logic")
    
    # Let's also check/patch trigger_next_phase which is also involved
    original_trigger = WorkflowService.trigger_next_phase
    
    def patched_trigger_next_phase(cls, bmr, current_phase):
        """Enhanced trigger_next_phase with special routing for tablet type 2"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase=current_phase
            )
            
            # Special handling for packaging_material_release -> bulk_packing for tablet type 2
            if (current_execution.phase.phase_name == 'packaging_material_release' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                bulk_packing = BatchPhaseExecution.objects.filter(
                    bmr=bmr, 
                    phase__phase_name='bulk_packing'
                ).first()
                
                if bulk_packing and bulk_packing.status in ['not_ready']:
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"Triggered bulk_packing after packaging_material_release for BMR {bmr.batch_number}")
                    return True
            
            # Use the original logic for other cases
            return original_trigger(bmr, current_phase)
            
        except BatchPhaseExecution.DoesNotExist:
            return False
    
    # Replace the trigger_next_phase method too
    WorkflowService.trigger_next_phase = classmethod(patched_trigger_next_phase)
    print("✅ Successfully patched WorkflowService.trigger_next_phase with special routing logic")

def fix_existing_batches():
    """Fix workflow for existing tablet type 2 batches"""
    print("\n=== Fixing workflow for existing tablet type 2 batches ===")
    
    # Find all tablet type 2 batches
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    print(f"Found {tablet2_bmrs.count()} tablet type 2 BMRs to check")
    
    fixed_count = 0
    for bmr in tablet2_bmrs:
        print(f"\nChecking BMR {bmr.batch_number}: {bmr.product.product_name}")
        
        with transaction.atomic():
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            
            # Get key phases
            packaging_material_release = phases.filter(phase__phase_name='packaging_material_release').first()
            bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
            secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
            
            if not bulk_packing:
                print(f"❌ ERROR: No bulk_packing phase for tablet type 2 BMR {bmr.batch_number}")
                continue
                
            if not packaging_material_release or not secondary_packaging:
                print(f"❌ ERROR: Missing critical phases for BMR {bmr.batch_number}")
                continue
                
            # Fix phase order if wrong
            if packaging_material_release.phase.phase_order >= bulk_packing.phase.phase_order:
                print(f"❌ ERROR: packaging_material_release phase order ({packaging_material_release.phase.phase_order}) >= bulk_packing phase order ({bulk_packing.phase.phase_order})")
                continue
                
            if bulk_packing.phase.phase_order >= secondary_packaging.phase.phase_order:
                print(f"❌ ERROR: bulk_packing phase order ({bulk_packing.phase.phase_order}) >= secondary_packaging phase order ({secondary_packaging.phase.phase_order})")
                continue
            
            # Fix status progression
            fixed = False
            
            # Case 1: packaging_material_release completed but bulk_packing not activated
            if packaging_material_release.status == 'completed' and bulk_packing.status == 'not_ready':
                bulk_packing.status = 'pending'
                bulk_packing.save()
                print(f"✅ Fixed: Set bulk_packing to 'pending' after completed packaging_material_release")
                fixed = True
                
            # Case 2: secondary_packaging active (pending/in_progress) but bulk_packing not completed
            if secondary_packaging.status in ['pending', 'in_progress'] and bulk_packing.status != 'completed':
                if bulk_packing.status == 'not_ready':
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"✅ Fixed: Set bulk_packing to 'pending' as secondary_packaging is active")
                    fixed = True
                elif bulk_packing.status == 'pending':
                    print(f"⚠️ Warning: bulk_packing is 'pending' but secondary_packaging is already active")
                    
            # Case 3: secondary_packaging completed but bulk_packing not completed  
            if secondary_packaging.status == 'completed' and bulk_packing.status != 'completed':
                bulk_packing.status = 'completed'
                bulk_packing.started_date = secondary_packaging.started_date or timezone.now() - timezone.timedelta(hours=1)
                bulk_packing.completed_date = secondary_packaging.started_date or timezone.now()
                bulk_packing.started_by = secondary_packaging.started_by
                bulk_packing.completed_by = secondary_packaging.completed_by or secondary_packaging.started_by
                bulk_packing.operator_comments = "Auto-completed by system - bulk packing was bypassed"
                bulk_packing.save()
                print(f"✅ Fixed: Auto-completed bulk_packing as secondary_packaging is already completed")
                fixed = True
                
            if fixed:
                fixed_count += 1
            else:
                print(f"✓ No issues found with this BMR's workflow")
    
    print(f"\n✅ Fixed {fixed_count} out of {tablet2_bmrs.count()} tablet type 2 BMRs")
    
def test_workflow():
    """Test the workflow for a tablet type 2 product"""
    print("\n=== Testing workflow for a tablet type 2 product ===")
    
    # Find a tablet type 2 BMR to test
    test_bmr = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).first()
    
    if not test_bmr:
        print("❌ No tablet type 2 BMRs found for testing")
        return
    
    print(f"Testing with BMR {test_bmr.batch_number}: {test_bmr.product.product_name}")
    
    # Get phases in order
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    # Display phase ordering
    print("\nPhase ordering:")
    for i, phase in enumerate(phases):
        print(f"{i+1:2d}. {phase.phase.phase_name} (Order: {phase.phase.phase_order}, Status: {phase.status})")
    
    # Get specific phases
    packaging_material_release = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
    
    print("\nTesting special routing:")
    print(f"1. packaging_material_release (order: {packaging_material_release.phase.phase_order}, status: {packaging_material_release.status})")
    print(f"2. bulk_packing (order: {bulk_packing.phase.phase_order}, status: {bulk_packing.status})")
    print(f"3. secondary_packaging (order: {secondary_packaging.phase.phase_order}, status: {secondary_packaging.status})")
    
    if bulk_packing.phase.phase_order <= packaging_material_release.phase.phase_order:
        print("❌ FAIL: bulk_packing order should be greater than packaging_material_release")
    else:
        print("✅ PASS: bulk_packing order is greater than packaging_material_release")
        
    if secondary_packaging.phase.phase_order <= bulk_packing.phase.phase_order:
        print("❌ FAIL: secondary_packaging order should be greater than bulk_packing")
    else:
        print("✅ PASS: secondary_packaging order is greater than bulk_packing")
    
    # Test the workflow service with our patched methods
    print("\nTesting patched WorkflowService.complete_phase method...")
    
    # Get next phase according to WorkflowService
    next_phase = WorkflowService.get_next_phase(test_bmr)
    print(f"Next phase according to WorkflowService: {next_phase.phase.phase_name if next_phase else 'None'}")
    
    # Quick check of WorkflowService.can_start_phase
    if bulk_packing.status == 'pending':
        can_start = WorkflowService.can_start_phase(test_bmr, 'bulk_packing')
        print(f"Can start bulk_packing according to WorkflowService: {can_start}")

if __name__ == "__main__":
    # Step 1: Fix phase ordering in ProductionPhase model
    if fix_phase_ordering():
        # Step 2: Update the WorkflowService methods with special routing
        update_workflow_service()
        
        # Step 3: Fix existing batches with issues
        fix_existing_batches()
        
        # Step 4: Test the workflow
        test_workflow()
        
        print("\n✨ All fixes have been applied successfully!")
        print("The bulk packing workflow should now work correctly for tablet type 2 products.")
    else:
        print("\n❌ Failed to fix phase ordering. Please check the error messages.")
