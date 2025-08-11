#!/usr/bin/env python
"""
Test script to verify that new BMRs for tablet type 2 get the correct workflow with bulk packing
"""

import os
import sys
import django

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

User = get_user_model()

def test_new_bmr_workflow():
    """Test creating a new BMR for tablet type 2 and check workflow initialization"""
    print("=" * 80)
    print("TESTING NEW BMR WORKFLOW FOR TABLET TYPE 2")
    print("=" * 80)
    
    # Step 1: Get or create a tablet type 2 product
    print("\n1. Creating/Getting tablet type 2 product...")
    
    # Check if we have any tablet_2 products
    tablet2_products = Product.objects.filter(
        product_type='tablet',
        tablet_type='tablet_2'
    )
    
    if tablet2_products.exists():
        product = tablet2_products.first()
        print(f"   Using existing product: {product}")
    else:
        # Create a new tablet type 2 product
        product = Product.objects.create(
            product_name='Test Tablet Type 2 Coated',
            product_type='tablet',
            coating_type='coated',
            tablet_type='tablet_2'
        )
        print(f"   Created new product: {product}")
    
    # Step 2: Get a QA user
    print("\n2. Getting QA user...")
    qa_user = User.objects.filter(role='qa').first()
    if not qa_user:
        qa_user = User.objects.create_user(
            username='qa_test_user',
            email='qa@test.com',
            password='testpass123',
            role='qa',
            first_name='QA',
            last_name='Tester'
        )
        print(f"   Created QA user: {qa_user}")
    else:
        print(f"   Using existing QA user: {qa_user}")
    
    # Step 3: Create a new BMR
    print("\n3. Creating new BMR...")
    import uuid
    batch_number = f"TB2-{uuid.uuid4().hex[:8].upper()}"
    
    bmr = BMR.objects.create(
        batch_number=batch_number,
        product=product,
        batch_size=1000,
        created_by=qa_user
    )
    print(f"   Created BMR: {bmr}")
    
    # Step 4: Initialize workflow
    print("\n4. Initializing workflow...")
    try:
        WorkflowService.initialize_workflow_for_bmr(bmr)
        print("   ✅ Workflow initialized successfully")
    except Exception as e:
        print(f"   ❌ Error initializing workflow: {e}")
        return False
    
    # Step 5: Check the workflow phases
    print("\n5. Checking workflow phases...")
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
    
    expected_phases = [
        'bmr_creation',
        'regulatory_approval',
        'material_dispensing',
        'granulation',
        'blending',
        'compression',
        'post_compression_qc',
        'sorting'
    ]
    
    # Add coating if product is coated
    if product.is_coated:
        expected_phases.append('coating')
    
    # Add the critical packaging phases
    expected_phases.extend([
        'packaging_material_release',
        'bulk_packing',  # This is the critical phase for tablet_2
        'secondary_packaging',
        'final_qa',
        'finished_goods_store'
    ])
    
    print(f"   Expected phases: {expected_phases}")
    
    actual_phases = [phase.phase.phase_name for phase in phases]
    print(f"   Actual phases: {actual_phases}")
    
    # Check if bulk_packing is present
    if 'bulk_packing' in actual_phases:
        print("   ✅ BULK_PACKING phase is present in workflow")
        bulk_phase_index = actual_phases.index('bulk_packing')
        packaging_material_index = actual_phases.index('packaging_material_release')
        secondary_packaging_index = actual_phases.index('secondary_packaging')
        
        if packaging_material_index < bulk_phase_index < secondary_packaging_index:
            print("   ✅ Phases are in correct order: packaging_material_release → bulk_packing → secondary_packaging")
        else:
            print("   ❌ Phases are NOT in correct order!")
            return False
    else:
        print("   ❌ BULK_PACKING phase is MISSING from workflow!")
        return False
    
    # Check if blister_packing is NOT present (it should be replaced by bulk_packing)
    if 'blister_packing' in actual_phases:
        print("   ❌ BLISTER_PACKING phase should NOT be present for tablet_2!")
        return False
    else:
        print("   ✅ BLISTER_PACKING phase is correctly absent for tablet_2")
    
    # Step 6: Check phase statuses
    print("\n6. Checking phase statuses...")
    for phase in phases:
        print(f"   {phase.phase.phase_name} (order: {phase.phase.phase_order}): {phase.status}")
    
    # Step 7: Verify the workflow service logic
    print("\n7. Testing WorkflowService methods...")
    
    # Test get_next_phase
    next_phase = WorkflowService.get_next_phase(bmr)
    if next_phase:
        print(f"   Next available phase: {next_phase.phase.phase_name}")
    else:
        print("   No next phase available")
    
    # Test that bulk_packing can be started after packaging_material_release
    print("\n8. Testing bulk_packing availability after packaging_material_release...")
    
    # Simulate completing phases up to packaging_material_release
    completed_phases = ['regulatory_approval', 'material_dispensing', 'granulation', 
                       'blending', 'compression', 'post_compression_qc', 'sorting']
    
    if product.is_coated:
        completed_phases.append('coating')
    
    completed_phases.append('packaging_material_release')
    
    # Mark phases as completed
    for phase_name in completed_phases:
        try:
            phase_exec = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name=phase_name)
            if phase_exec.status != 'completed':
                phase_exec.status = 'completed'
                phase_exec.completed_by = qa_user
                phase_exec.completed_date = django.utils.timezone.now()
                phase_exec.save()
                print(f"   Marked {phase_name} as completed")
        except BatchPhaseExecution.DoesNotExist:
            print(f"   ⚠️  Phase {phase_name} not found")
    
    # Now check if bulk_packing becomes available
    next_phase_after = WorkflowService.get_next_phase(bmr)
    if next_phase_after and next_phase_after.phase.phase_name == 'bulk_packing':
        print("   ✅ BULK_PACKING is correctly available after packaging_material_release")
    else:
        print(f"   ❌ Expected bulk_packing but got: {next_phase_after.phase.phase_name if next_phase_after else 'None'}")
        return False
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✅ New BMR workflow for tablet type 2 is CORRECTLY configured")
    print("✅ Bulk packing phase is present and in correct order")
    print("✅ Workflow progression works as expected")
    
    return True

if __name__ == '__main__':
    success = test_new_bmr_workflow()
    if success:
        print("\n🎉 All tests passed! New BMR workflow for tablet type 2 is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the workflow configuration.")
