"""
Full workflow test for tablet type 2 products
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
from products.models import Product
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

def check_phase_ordering():
    """Check if our phase ordering is correct"""
    print("=== Checking phase ordering ===")
    
    # Check tablet phases
    tablet_phases = ProductionPhase.objects.filter(
        product_type='tablet'
    ).order_by('phase_order')
    
    print("\nTablet phases order:")
    for i, phase in enumerate(tablet_phases):
        print(f"{i+1:2d}. {phase.phase_name:30} {phase.phase_order}")
    
    # Check that bulk_packing is properly ordered
    packaging_material_release = tablet_phases.filter(phase_name='packaging_material_release').first()
    bulk_packing = tablet_phases.filter(phase_name='bulk_packing').first()
    blister_packing = tablet_phases.filter(phase_name='blister_packing').first()
    secondary_packaging = tablet_phases.filter(phase_name='secondary_packaging').first()
    
    if packaging_material_release and bulk_packing and blister_packing and secondary_packaging:
        print("\nChecking critical phase ordering:")
        print(f"packaging_material_release: {packaging_material_release.phase_order}")
        print(f"blister_packing: {blister_packing.phase_order}")
        print(f"bulk_packing: {bulk_packing.phase_order}")
        print(f"secondary_packaging: {secondary_packaging.phase_order}")
        
        if packaging_material_release.phase_order < bulk_packing.phase_order < secondary_packaging.phase_order:
            print("✅ Phase ordering is correct!")
        else:
            print("❌ Phase ordering is incorrect!")
    else:
        print("❌ Critical phases are missing!")

def check_special_workflow_handling():
    """Check if our special workflow handling is working"""
    print("\n=== Testing workflow with a new BMR ===")
    
    # Create a test product if needed
    tablet2_product = Product.objects.filter(
        product_type='tablet', 
        tablet_type='tablet_2',
        is_active=True
    ).first()
    
    if not tablet2_product:
        print("Creating test tablet type 2 product...")
        tablet2_product = Product.objects.create(
            product_name="Test Tablet Type 2",
            product_type="tablet",
            tablet_type="tablet_2",
            coating_type="uncoated",
            is_active=True
        )
    
    print(f"Using product: {tablet2_product.product_name}")
    
    # Create a test BMR
    user = User.objects.filter(is_staff=True).first()
    
    with transaction.atomic():
        test_batch_number = f"T{timezone.now().strftime('%d%H%M')}"
        test_bmr = BMR.objects.create(
            batch_number=test_batch_number,
            product=tablet2_product,
            batch_size=1000,
            created_by=user,
            status='draft'
        )
        
        # Initialize workflow
        WorkflowService.initialize_workflow_for_bmr(test_bmr)
    
    print(f"Created test BMR {test_batch_number}")
    
    # Verify phases
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    print("\nPhases created:")
    for i, phase in enumerate(phases):
        print(f"{i+1:2d}. {phase.phase.phase_name:30} {phase.status}")
    
    # Verify bulk_packing is in the workflow
    bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
    if bulk_packing:
        print("✅ bulk_packing phase was correctly created")
    else:
        print("❌ bulk_packing phase is missing!")
        return
    
    print("\n=== Testing workflow progression ===")
    
    # Progress through the phases
    for phase in phases:
        if phase.status == 'completed':
            continue
            
        if phase.status == 'not_ready':
            # Make it pending first
            phase.status = 'pending'
            phase.save()
        
        if phase.status == 'pending':
            print(f"Starting phase: {phase.phase.phase_name}")
            phase.status = 'in_progress'
            phase.started_by = user
            phase.started_date = timezone.now()
            phase.save()
        
        if phase.status == 'in_progress':
            print(f"Completing phase: {phase.phase.phase_name}")
            next_phase = WorkflowService.complete_phase(test_bmr, phase.phase.phase_name, user)
            
            if next_phase:
                print(f"Next phase activated: {next_phase.phase.phase_name}")
            else:
                print("No next phase activated")
    
    # Final verification
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    print("\nFinal phases status:")
    for phase in phases:
        print(f"{phase.phase.phase_name:30} {phase.status}")
    
    # Check if we followed the right sequence
    bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_packaging = phases.filter(phase__phase_name='secondary_packaging').first()
    
    if bulk_packing and bulk_packing.status == 'completed' and secondary_packaging.status == 'completed':
        print("\n✅ Successfully progressed through bulk_packing to secondary_packaging!")
    else:
        print("\n❌ Failed to progress through workflow correctly")

if __name__ == "__main__":
    # Check phase ordering
    check_phase_ordering()
    
    # Test special workflow handling
    check_special_workflow_handling()
