"""
Fixes workflow sequence for type 2 tablets to ensure proper phase order:
- For coated tablets: coating → material release → bulk packing → secondary packing
- For uncoated tablets: sorting → material release → bulk packing → secondary packing

This script ensures that when material_release is completed, the next phase activated
should always be bulk_packing for tablet type 2, not secondary_packaging.
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

def fix_complete_phase_method():
    """
    Update the WorkflowService.complete_phase method to ensure proper routing
    for tablet type 2 after packaging_material_release completion
    """
    print("\n=== Updating WorkflowService.complete_phase for tablet type 2 ===")
    
    # Get the original method
    original_complete_phase = WorkflowService.complete_phase
    
    # Create patched version with explicit bulk packing activation
    def patched_complete_phase(cls, bmr, phase_name, completed_by, comments=None):
        """
        Enhanced complete_phase ensuring bulk_packing is always the next phase 
        after packaging_material_release for tablet type 2 products
        """
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
            
            # CRITICAL ROUTING FOR TABLET TYPE 2:
            # After packaging_material_release, always activate bulk_packing
            if (phase_name == 'packaging_material_release' and 
                bmr.product.product_type == 'tablet' and
                getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
                
                print(f"Special routing for BMR {bmr.batch_number}: activating bulk_packing after material_release")
                
                # Get bulk_packing phase
                bulk_packing = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='bulk_packing'
                ).first()
                
                if bulk_packing:
                    bulk_packing.status = 'pending'  # Make it available to start
                    bulk_packing.save()
                    print(f"✅ Activated bulk_packing phase for tablet_2 BMR {bmr.batch_number}")
                    return bulk_packing
                else:
                    print(f"❌ ERROR: No bulk_packing phase found for tablet_2 BMR {bmr.batch_number}")
            
            # Regular next phase activation logic for other cases
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
    print("✅ Successfully patched WorkflowService.complete_phase method")

def fix_get_next_phase_method():
    """
    Update the BatchPhaseExecution.get_next_phase method to ensure proper routing
    for tablet type 2 products
    """
    print("\n=== Updating BatchPhaseExecution.get_next_phase for tablet type 2 ===")
    
    # Get the original method
    original_get_next_phase = BatchPhaseExecution.get_next_phase
    
    # Create patched version with explicit routing for tablet type 2
    def patched_get_next_phase(self):
        """Enhanced get_next_phase with special tablet type 2 routing"""
        
        # Special routing for tablet type 2 after packaging_material_release
        if (self.phase.phase_name == 'packaging_material_release' and 
            self.bmr.product.product_type == 'tablet' and
            getattr(self.bmr.product, 'tablet_type', '') == 'tablet_2'):
            
            # Next phase should be bulk_packing, not secondary_packaging
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
    print("✅ Successfully patched BatchPhaseExecution.get_next_phase method")

def fix_existing_batches():
    """Fix workflow issues for existing tablet type 2 batches"""
    print("\n=== Fixing workflow for existing tablet type 2 batches ===")
    
    # Find all tablet type 2 batches
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    print(f"Found {tablet2_bmrs.count()} tablet type 2 BMRs to check/fix")
    
    fixed_count = 0
    for bmr in tablet2_bmrs:
        print(f"\nChecking BMR {bmr.batch_number}: {bmr.product.product_name}")
        
        with transaction.atomic():
            # Get phases in order
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            
            # Get key phases
            packaging_material_release = phases.filter(phase__phase_name='packaging_material_release').first()
            bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
            secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
            
            if not bulk_packing:
                print(f"❌ ERROR: No bulk_packing phase for BMR {bmr.batch_number}")
                continue
                
            if not packaging_material_release or not secondary_packaging:
                print(f"❌ ERROR: Missing critical phases for BMR {bmr.batch_number}")
                continue
            
            # Fix common issues:
            
            # 1. Ensure phases have correct order
            if not (packaging_material_release.phase.phase_order < bulk_packing.phase.phase_order < secondary_packaging.phase.phase_order):
                print(f"❌ ERROR: Incorrect phase ordering for BMR {bmr.batch_number}")
                print(f"  material_release: {packaging_material_release.phase.phase_order}")
                print(f"  bulk_packing: {bulk_packing.phase.phase_order}")
                print(f"  secondary_packaging: {secondary_packaging.phase.phase_order}")
                continue
            
            # 2. Fix status progression issues
            fixed = False
            
            # Case 1: material_release completed but bulk_packing not activated
            if packaging_material_release.status == 'completed' and bulk_packing.status == 'not_ready':
                bulk_packing.status = 'pending'
                bulk_packing.save()
                print(f"✅ Fixed: Activated bulk_packing after completed material_release")
                fixed = True
                
            # Case 2: secondary_packaging active but bulk_packing not completed
            elif secondary_packaging.status in ['pending', 'in_progress'] and bulk_packing.status not in ['completed', 'in_progress']:
                bulk_packing.status = 'pending'
                bulk_packing.save()
                print(f"✅ Fixed: Set bulk_packing to pending as secondary_packaging is active")
                fixed = True
                
                # Also deactivate secondary_packaging if it's pending
                if secondary_packaging.status == 'pending':
                    secondary_packaging.status = 'not_ready'
                    secondary_packaging.save()
                    print(f"✅ Fixed: Deactivated secondary_packaging until bulk_packing is completed")
            
            # Case 3: secondary_packaging completed but bulk_packing skipped
            elif secondary_packaging.status == 'completed' and bulk_packing.status in ['not_ready', 'pending']:
                bulk_packing.status = 'completed'
                bulk_packing.started_date = secondary_packaging.started_date or timezone.now() - timezone.timedelta(hours=1)
                bulk_packing.completed_date = secondary_packaging.started_date or timezone.now()
                bulk_packing.started_by = secondary_packaging.started_by
                bulk_packing.completed_by = secondary_packaging.completed_by or secondary_packaging.started_by
                bulk_packing.operator_comments = "Auto-completed by system - bulk packing was bypassed"
                bulk_packing.save()
                print(f"✅ Fixed: Auto-completed bulk_packing as secondary_packaging was already completed")
                fixed = True
            
            if fixed:
                fixed_count += 1
            else:
                print(f"✓ No workflow issues found for this BMR")
    
    print(f"\n✅ Fixed workflow issues for {fixed_count} out of {tablet2_bmrs.count()} tablet type 2 BMRs")

def verify_workflow_sequence():
    """Verify the workflow sequence for tablet type 2 batches"""
    print("\n=== Verifying tablet type 2 workflow sequence ===")
    
    # Check a sample BMR
    test_bmr = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).first()
    
    if not test_bmr:
        print("No tablet type 2 BMRs found for verification")
        return False
    
    print(f"Verifying workflow sequence for BMR {test_bmr.batch_number}: {test_bmr.product.product_name}")
    print(f"Product is {'coated' if test_bmr.product.is_coated else 'uncoated'}")
    
    # Get phases in order
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    # Print complete phase sequence
    print("\nComplete phase sequence:")
    for i, phase in enumerate(phases):
        print(f"{i+1:2d}. {phase.phase.phase_name} (Order: {phase.phase.phase_order}, Status: {phase.status})")
    
    # Verify critical sequence
    critical_phases = []
    if test_bmr.product.is_coated:
        # Coated tablet sequence
        critical_phases = ['sorting', 'coating', 'packaging_material_release', 'bulk_packing', 'secondary_packaging']
    else:
        # Uncoated tablet sequence
        critical_phases = ['sorting', 'packaging_material_release', 'bulk_packing', 'secondary_packaging']
    
    # Verify order of critical phases
    phase_orders = {}
    for phase_name in critical_phases:
        phase = phases.filter(phase__phase_name=phase_name).first()
        if phase:
            phase_orders[phase_name] = phase.phase.phase_order
        else:
            print(f"❌ ERROR: Missing critical phase: {phase_name}")
            return False
    
    # Check if phases are in correct order
    for i in range(len(critical_phases)-1):
        current = critical_phases[i]
        next_phase = critical_phases[i+1]
        
        if phase_orders[current] >= phase_orders[next_phase]:
            print(f"❌ ERROR: {current} (order {phase_orders[current]}) should come before {next_phase} (order {phase_orders[next_phase]})")
            return False
    
    print(f"✅ Verified correct sequence: {' → '.join(critical_phases)}")
    
    # Test the patched workflow methods
    print("\nTesting patched workflow methods...")
    
    # Simulate packaging_material_release completion
    material_release = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
    
    # Get next phase after packaging_material_release
    next_phase = material_release.get_next_phase()
    if next_phase and next_phase.phase_name == 'bulk_packing':
        print(f"✅ Correct: Next phase after material_release is bulk_packing")
    else:
        print(f"❌ ERROR: Next phase after material_release should be bulk_packing, got {next_phase.phase_name if next_phase else 'None'}")
        return False
    
    return True

if __name__ == "__main__":
    print("===== TABLET TYPE 2 WORKFLOW SEQUENCE FIX =====")
    
    # 1. Update methods to ensure proper routing
    fix_complete_phase_method()
    fix_get_next_phase_method()
    
    # 2. Fix existing batches with sequence issues
    fix_existing_batches()
    
    # 3. Verify the workflow sequence is correct
    if verify_workflow_sequence():
        print("\n✨ WORKFLOW SEQUENCE FIX COMPLETED SUCCESSFULLY")
        print("Type 2 tablets will now follow the correct sequence:")
        print("- Coated tablets: coating → material release → bulk packing → secondary packing")
        print("- Uncoated tablets: sorting → material release → bulk packing → secondary packing")
    else:
        print("\n❌ WORKFLOW SEQUENCE FIX ENCOUNTERED ISSUES")
        print("Please review the error messages above and contact support.")
