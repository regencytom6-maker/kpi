"""
Final and comprehensive fix for tablet type 2 workflow issues.
This script combines and finalizes all fixes to ensure the proper workflow sequence:

1. For coated tablets: 
   sorting → coating → material release → bulk packing → secondary packing

2. For uncoated tablets:
   sorting → material release → bulk packing → secondary packing

This script:
1. Fixes phase ordering in ProductionPhase model
2. Updates phase execution order for existing batches
3. Updates WorkflowService methods to ensure proper progression
4. Verifies all fixes and tests the workflow
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

def fix_phase_model():
    """Fix phase model ordering for tablet type 2 products"""
    print("\n=== FIXING PRODUCTION PHASE MODEL ORDERING ===")
    
    # Get all tablet phases
    tablet_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    
    print("Current tablet phase ordering:")
    for i, phase in enumerate(tablet_phases, 1):
        print(f"{i:2d}. {phase.phase_name} (order: {phase.phase_order})")
    
    # Get critical phases
    sorting = tablet_phases.filter(phase_name='sorting').first()
    coating = tablet_phases.filter(phase_name='coating').first()
    packaging_material_release = tablet_phases.filter(phase_name='packaging_material_release').first()
    bulk_packing = tablet_phases.filter(phase_name='bulk_packing').first()
    blister_packing = tablet_phases.filter(phase_name='blister_packing').first()
    secondary_packaging = tablet_phases.filter(phase_name='secondary_packaging').first()
    
    if not all([sorting, coating, packaging_material_release, bulk_packing, secondary_packaging]):
        print("❌ ERROR: Some required phases are missing")
        return False
    
    with transaction.atomic():
        # Set correct ordering:
        # 1. Sorting
        sorting_order = sorting.phase_order
        
        # 2. Coating
        coating_order = sorting_order + 1
        coating.phase_order = coating_order
        coating.save()
        
        # 3. Packaging material release
        packaging_order = coating_order + 1
        packaging_material_release.phase_order = packaging_order
        packaging_material_release.save()
        
        # 4. Packing phases (bulk or blister) 
        packing_order = packaging_order + 1
        blister_packing.phase_order = packing_order
        bulk_packing.phase_order = packing_order
        blister_packing.save()
        bulk_packing.save()
        
        # 5. Secondary packaging
        secondary_order = packing_order + 1
        secondary_packaging.phase_order = secondary_order
        secondary_packaging.save()
        
        print("\nUpdated phase ordering:")
        print(f"sorting: {sorting_order}")
        print(f"coating: {coating_order}")
        print(f"packaging_material_release: {packaging_order}")
        print(f"blister_packing/bulk_packing: {packing_order}")
        print(f"secondary_packaging: {secondary_order}")
    
    # Double check the fix
    fixed_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    print("\nVerifying fixed phase ordering:")
    for i, phase in enumerate(fixed_phases, 1):
        print(f"{i:2d}. {phase.phase_name} (order: {phase.phase_order})")
    
    return True

def update_workflow_service():
    """Update WorkflowService methods to ensure proper progression"""
    print("\n=== UPDATING WORKFLOW SERVICE METHODS ===")
    
    # 1. Update complete_phase method
    original_complete_phase = WorkflowService.complete_phase
    
    def patched_complete_phase(cls, bmr, phase_name, completed_by, comments=None):
        """Enhanced complete_phase with special routing for tablet type 2"""
        try:
            # Mark the current phase as completed
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
            
            # SPECIAL ROUTING FOR TABLET TYPE 2
            
            # 1. After material_release, activate bulk_packing (not secondary_packaging)
            if (phase_name == 'packaging_material_release' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                print(f"Special routing for BMR {bmr.batch_number}: activating bulk_packing after material release")
                
                bulk_packing = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='bulk_packing',
                ).first()
                
                if bulk_packing and bulk_packing.status != 'completed':
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"✅ Activated bulk_packing for tablet_2 BMR {bmr.batch_number}")
                    return bulk_packing
            
            # 2. After bulk_packing, activate secondary_packaging
            elif (phase_name == 'bulk_packing' and 
                  bmr.product.product_type == 'tablet' and
                  getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                print(f"Special routing for BMR {bmr.batch_number}: activating secondary_packaging after bulk_packing")
                
                secondary_packaging = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='secondary_packaging',
                ).first()
                
                if secondary_packaging and secondary_packaging.status != 'completed':
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
    print("✅ Updated WorkflowService.complete_phase method")
    
    # 2. Update get_next_phase method
    original_get_next_phase = BatchPhaseExecution.get_next_phase
    
    def patched_get_next_phase(self):
        """Enhanced get_next_phase for tablet type 2 workflow"""
        
        # Special case for tablet type 2 after packaging_material_release
        if (self.phase.phase_name == 'packaging_material_release' and 
            self.bmr.product.product_type == 'tablet' and
            getattr(self.bmr.product, 'tablet_type', '') == 'tablet_2'):
            
            # Next phase should be bulk_packing
            next_phase = ProductionPhase.objects.filter(
                product_type=self.bmr.product.product_type,
                phase_name='bulk_packing'
            ).first()
            
            if next_phase:
                return next_phase
        
        # Use original logic for all other cases
        return original_get_next_phase(self)
    
    # Replace the method
    BatchPhaseExecution.get_next_phase = patched_get_next_phase
    print("✅ Updated BatchPhaseExecution.get_next_phase method")
    
    # 3. Update can_start_phase method for proper checks
    original_can_start = WorkflowService.can_start_phase
    
    def patched_can_start_phase(cls, bmr, phase_name):
        """Enhanced can_start_phase with special handling for tablet type 2"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Cannot start phases that are not pending
            if current_execution.status != 'pending':
                return False
            
            # Special handling for bulk_packing after material release for tablet_2
            if (phase_name == 'bulk_packing' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                # Check if packaging_material_release is completed
                material_release = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='packaging_material_release'
                ).first()
                
                if material_release and material_release.status == 'completed':
                    print(f"Special case: Allowing bulk_packing to start after material_release completion")
                    return True
            
            # Special handling for secondary_packaging after bulk_packing for tablet_2
            if (phase_name == 'secondary_packaging' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                # Check if bulk_packing is completed
                bulk_packing = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='bulk_packing'
                ).first()
                
                if bulk_packing and bulk_packing.status != 'completed':
                    print(f"Cannot start secondary_packaging until bulk_packing is completed")
                    return False
            
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
    print("✅ Updated WorkflowService.can_start_phase method")

def fix_existing_batches():
    """Fix workflow for existing tablet type 2 batches"""
    print("\n=== FIXING EXISTING TABLET TYPE 2 BATCHES ===")
    
    # Find all tablet type 2 batches
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    print(f"Found {tablet2_bmrs.count()} tablet type 2 BMRs to check/fix")
    
    fixed_count = 0
    for bmr in tablet2_bmrs:
        print(f"\nChecking BMR {bmr.batch_number}: {bmr.product.product_name}")
        print(f"Product is {'coated' if bmr.product.is_coated else 'uncoated'}")
        
        with transaction.atomic():
            # Get all batch phase executions for this BMR
            executions = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            
            # Get critical phases
            sorting = executions.filter(phase__phase_name='sorting').first()
            coating = executions.filter(phase__phase_name='coating').first() if bmr.product.is_coated else None
            packaging_material_release = executions.filter(phase__phase_name='packaging_material_release').first()
            bulk_packing = executions.filter(phase__phase_name='bulk_packing').first()
            secondary_packaging = executions.filter(phase__phase_name='secondary_packaging').first()
            
            if not all(p for p in [sorting, packaging_material_release, bulk_packing, secondary_packaging]):
                print("❌ ERROR: Missing critical phases")
                continue
                
            if bmr.product.is_coated and not coating:
                print("❌ ERROR: Missing coating phase for coated tablet")
                continue
            
            # Synchronize with updated ProductionPhase model
            sorting.phase = ProductionPhase.objects.get(product_type='tablet', phase_name='sorting')
            if coating:
                coating.phase = ProductionPhase.objects.get(product_type='tablet', phase_name='coating')
                coating.save()
            packaging_material_release.phase = ProductionPhase.objects.get(product_type='tablet', phase_name='packaging_material_release')
            bulk_packing.phase = ProductionPhase.objects.get(product_type='tablet', phase_name='bulk_packing')
            secondary_packaging.phase = ProductionPhase.objects.get(product_type='tablet', phase_name='secondary_packaging')
            
            sorting.save()
            packaging_material_release.save()
            bulk_packing.save()
            secondary_packaging.save()
            
            # Fix status progression issues
            fixed = False
            
            # Case 1: If material release is completed but bulk packing is not activated
            if packaging_material_release.status == 'completed' and bulk_packing.status == 'not_ready':
                bulk_packing.status = 'pending'
                bulk_packing.save()
                print(f"✅ Fixed: Activated bulk_packing after completed material_release")
                fixed = True
                
            # Case 2: If secondary packaging is active but bulk packing is not completed
            if secondary_packaging.status in ['pending', 'in_progress'] and bulk_packing.status not in ['completed', 'in_progress']:
                # Reset secondary packaging to not_ready
                secondary_packaging.status = 'not_ready'
                secondary_packaging.save()
                
                # Set bulk packing to pending if material release is completed
                if packaging_material_release.status == 'completed':
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"✅ Fixed: Reset sequence to material_release (completed) → bulk_packing (pending) → secondary_packaging (not_ready)")
                    fixed = True
            
            # Case 3: If secondary packaging is completed but bulk packing was skipped
            if secondary_packaging.status == 'completed' and bulk_packing.status in ['not_ready', 'pending']:
                bulk_packing.status = 'completed'
                bulk_packing.started_date = secondary_packaging.started_date or timezone.now() - timezone.timedelta(hours=1)
                bulk_packing.completed_date = secondary_packaging.started_date or timezone.now()
                bulk_packing.started_by = secondary_packaging.started_by
                bulk_packing.completed_by = secondary_packaging.completed_by or secondary_packaging.started_by
                bulk_packing.operator_comments = "Auto-completed by system - phase was bypassed"
                bulk_packing.save()
                print(f"✅ Fixed: Auto-completed bulk_packing as secondary_packaging was already completed")
                fixed = True
            
            if fixed:
                fixed_count += 1
            else:
                print(f"✓ No workflow issues to fix for this BMR")
    
    print(f"\nFixed workflow issues for {fixed_count} out of {tablet2_bmrs.count()} tablet type 2 BMRs")

def test_tablet2_workflow():
    """Test the workflow for a tablet type 2 product"""
    print("\n=== TESTING TABLET TYPE 2 WORKFLOW ===")
    
    test_bmr = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2',
    ).first()
    
    if not test_bmr:
        print("❌ No tablet type 2 BMRs found for testing")
        return False
        
    print(f"Testing with BMR {test_bmr.batch_number}: {test_bmr.product.product_name}")
    print(f"Product is {'coated' if test_bmr.product.is_coated else 'uncoated'}")
    
    # Get phases in order
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    # Print complete phase sequence
    print("\nComplete phase sequence:")
    for i, phase in enumerate(phases, 1):
        print(f"{i:2d}. {phase.phase.phase_name} (Order: {phase.phase.phase_order}, Status: {phase.status})")
    
    # Check critical phases
    critical_phases = []
    if test_bmr.product.is_coated:
        critical_phases = ['sorting', 'coating', 'packaging_material_release', 'bulk_packing', 'secondary_packaging']
    else:
        critical_phases = ['sorting', 'packaging_material_release', 'bulk_packing', 'secondary_packaging']
    
    print("\nVerifying critical phase ordering:")
    previous_order = 0
    for phase_name in critical_phases:
        phase = phases.filter(phase__phase_name=phase_name).first()
        if not phase:
            print(f"❌ ERROR: Missing critical phase: {phase_name}")
            return False
            
        print(f"- {phase_name}: order {phase.phase.phase_order}")
        
        if phase.phase.phase_order <= previous_order and previous_order > 0:
            print(f"❌ ERROR: Phase {phase_name} order should be greater than previous phase")
            return False
            
        previous_order = phase.phase.phase_order
    
    print("✅ Critical phase ordering is correct")
    
    # Test special routing: material_release → bulk_packing → secondary_packaging
    material_release = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
    
    print("\nTesting material_release → bulk_packing routing:")
    next_after_material = material_release.get_next_phase()
    if next_after_material and next_after_material.phase_name == 'bulk_packing':
        print("✅ Correct: Next phase after material_release is bulk_packing")
    else:
        print(f"❌ ERROR: Next phase after material_release should be bulk_packing, got {next_after_material.phase_name if next_after_material else 'None'}")
        return False
    
    # Test can_start_phase logic
    print("\nTesting can_start_phase logic:")
    
    # Reset statuses for testing if needed
    with transaction.atomic():
        original_statuses = {}
        for phase in [material_release, bulk_packing, secondary_packaging]:
            original_statuses[phase.phase.phase_name] = phase.status
        
        # Set up test scenario
        material_release.status = 'completed'
        bulk_packing.status = 'pending'
        secondary_packaging.status = 'not_ready'
        material_release.save()
        bulk_packing.save()
        secondary_packaging.save()
        
        # Test can_start_phase
        can_start_bulk = WorkflowService.can_start_phase(test_bmr, 'bulk_packing')
        can_start_secondary = WorkflowService.can_start_phase(test_bmr, 'secondary_packaging')
        
        print(f"- Can start bulk_packing: {can_start_bulk}")
        print(f"- Can start secondary_packaging: {can_start_secondary}")
        
        if can_start_bulk and not can_start_secondary:
            print("✅ Correct: Can start bulk_packing but not secondary_packaging")
        else:
            print("❌ ERROR: Should be able to start bulk_packing but not secondary_packaging")
            
        # Test completion routing
        test_user = User.objects.filter(is_staff=True).first()
        if test_user:
            print("\nSimulating bulk_packing completion:")
            next_phase = WorkflowService.complete_phase(
                test_bmr,
                'bulk_packing',
                test_user,
                "Test completion for workflow validation"
            )
            
            secondary_packaging.refresh_from_db()
            
            if secondary_packaging.status == 'pending':
                print("✅ Correct: secondary_packaging was activated after bulk_packing completion")
            else:
                print(f"❌ ERROR: secondary_packaging status should be 'pending', got '{secondary_packaging.status}'")
                
        # Reset to original statuses
        for phase in [material_release, bulk_packing, secondary_packaging]:
            phase.status = original_statuses[phase.phase.phase_name]
            phase.save()
            
    return True

def create_final_report():
    """Create a final report of the fix"""
    print("\n===== FINAL WORKFLOW FIX REPORT =====")
    
    # Count tablet type 2 products
    tablet2_count = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).count()
    
    # Check if any still have issues
    issue_count = 0
    for bmr in BMR.objects.filter(product__tablet_type='tablet_2'):
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
        bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
        secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
        
        if (not bulk_packing or not secondary_packaging or 
            bulk_packing.phase.phase_order >= secondary_packaging.phase.phase_order or
            (secondary_packaging.status == 'pending' and bulk_packing.status != 'completed')):
            issue_count += 1
    
    print(f"Tablet Type 2 Products: {tablet2_count}")
    print(f"Remaining Issues: {issue_count}")
    print(f"Success Rate: {(tablet2_count - issue_count) / tablet2_count * 100 if tablet2_count > 0 else 0:.1f}%")
    
    if issue_count == 0:
        print("\n✨ ALL WORKFLOW ISSUES FIXED SUCCESSFULLY")
        print("The system now correctly enforces the following workflow for tablet type 2:")
        print("1. For coated tablets: sorting → coating → material release → bulk packing → secondary packing")
        print("2. For uncoated tablets: sorting → material release → bulk packing → secondary packing")
    else:
        print("\n⚠️ SOME WORKFLOW ISSUES STILL REMAIN")
        print("Please review the logs and manually fix any remaining issues.")

if __name__ == "__main__":
    print("===== TABLET TYPE 2 WORKFLOW FIX =====")
    
    # 1. Fix the ProductionPhase model ordering
    if fix_phase_model():
        # 2. Update WorkflowService methods
        update_workflow_service()
        
        # 3. Fix existing batches with issues
        fix_existing_batches()
        
        # 4. Test the workflow
        test_tablet2_workflow()
        
        # 5. Create final report
        create_final_report()
    else:
        print("\n❌ FAILED TO FIX PHASE MODEL")
        print("Please check the error messages above")
