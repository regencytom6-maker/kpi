#!/usr/bin/env python
"""
Comprehensive test to verify that new BMRs for tablet type 2 are correctly routed with bulk packing
This addresses the user's concern about new batches missing the bulk packing phase
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

def test_new_bmr_creation_and_workflow():
    """Test the complete process of creating new BMRs for tablet type 2 and checking workflow routing"""
    print("=" * 80)
    print("COMPREHENSIVE TEST: NEW BMR CREATION AND WORKFLOW ROUTING FOR TABLET TYPE 2")
    print("=" * 80)
    
    # Test 1: Coated Tablet Type 2
    print("\n" + "="*50)
    print("TEST 1: COATED TABLET TYPE 2")
    print("="*50)
    
    success1 = test_tablet_type_2_workflow(coating_type='coated')
    
    # Test 2: Uncoated Tablet Type 2
    print("\n" + "="*50)
    print("TEST 2: UNCOATED TABLET TYPE 2")
    print("="*50)
    
    success2 = test_tablet_type_2_workflow(coating_type='uncoated')
    
    # Test 3: Multiple BMRs creation simulation
    print("\n" + "="*50)
    print("TEST 3: MULTIPLE NEW BMR CREATION")
    print("="*50)
    
    success3 = test_multiple_bmr_creation()
    
    # Summary
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*80)
    
    if success1 and success2 and success3:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Coated tablet type 2 workflow is correct")
        print("✅ Uncoated tablet type 2 workflow is correct")
        print("✅ Multiple BMR creation works correctly")
        print("✅ New batches for tablet type 2 are properly routed with bulk packing")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"   Coated tablet type 2: {'✅' if success1 else '❌'}")
        print(f"   Uncoated tablet type 2: {'✅' if success2 else '❌'}")
        print(f"   Multiple BMR creation: {'✅' if success3 else '❌'}")
        return False

def test_tablet_type_2_workflow(coating_type='coated'):
    """Test workflow for a specific tablet type 2 configuration"""
    
    # Get or create product
    product_name = f"Test Tablet Type 2 {coating_type.title()}"
    product, created = Product.objects.get_or_create(
        product_name=product_name,
        product_type='tablet',
        defaults={
            'coating_type': coating_type,
            'tablet_type': 'tablet_2'
        }
    )
    
    # Update existing product if needed
    if not created:
        product.coating_type = coating_type
        product.tablet_type = 'tablet_2'
        product.save()
    
    print(f"1. Testing product: {product}")
    
    # Get QA user
    qa_user = User.objects.filter(role='qa').first()
    if not qa_user:
        qa_user = User.objects.create_user(
            username='test_qa_user',
            email='qa@test.com',
            password='testpass123',
            role='qa',
            first_name='Test',
            last_name='QA'
        )
    
    # Create new BMR
    import uuid
    batch_number = f"T2{coating_type[0].upper()}-{uuid.uuid4().hex[:6].upper()}"
    
    try:
        bmr = BMR.objects.create(
            batch_number=batch_number,
            product=product,
            batch_size=5000,
            created_by=qa_user
        )
        print(f"2. Created BMR: {bmr.bmr_number} | Batch: {bmr.batch_number}")
    except Exception as e:
        print(f"   ❌ Error creating BMR: {e}")
        return False
    
    # Initialize workflow
    try:
        WorkflowService.initialize_workflow_for_bmr(bmr)
        print("3. ✅ Workflow initialized successfully")
    except Exception as e:
        print(f"   ❌ Error initializing workflow: {e}")
        return False
    
    # Check workflow phases
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
    actual_phases = [phase.phase.phase_name for phase in phases]
    
    # Expected phases for tablet type 2
    expected_base = [
        'bmr_creation',
        'regulatory_approval',
        'material_dispensing',
        'granulation',
        'blending',
        'compression',
        'post_compression_qc',
        'sorting'
    ]
    
    if coating_type == 'coated':
        expected_base.append('coating')
    
    expected_base.extend([
        'packaging_material_release',
        'bulk_packing',  # Critical phase for tablet_2
        'secondary_packaging',
        'final_qa',
        'finished_goods_store'
    ])
    
    print(f"4. Expected phases: {len(expected_base)} phases")
    print(f"   Actual phases: {len(actual_phases)} phases")
    
    # Check if bulk_packing is present
    if 'bulk_packing' not in actual_phases:
        print("   ❌ CRITICAL ERROR: bulk_packing phase is MISSING!")
        return False
    
    print("   ✅ bulk_packing phase is present")
    
    # Check if blister_packing is absent
    if 'blister_packing' in actual_phases:
        print("   ❌ ERROR: blister_packing should NOT be present for tablet_2!")
        return False
    
    print("   ✅ blister_packing phase is correctly absent")
    
    # Check phase order
    try:
        bulk_index = actual_phases.index('bulk_packing')
        packaging_index = actual_phases.index('packaging_material_release')
        secondary_index = actual_phases.index('secondary_packaging')
        
        if packaging_index < bulk_index < secondary_index:
            print("   ✅ Phase order is correct: packaging_material_release → bulk_packing → secondary_packaging")
        else:
            print("   ❌ Phase order is INCORRECT!")
            return False
    except ValueError as e:
        print(f"   ❌ Error checking phase order: {e}")
        return False
    
    # Test workflow progression to bulk_packing
    print("5. Testing workflow progression to bulk_packing...")
    
    # Complete phases up to packaging_material_release
    phases_to_complete = ['regulatory_approval', 'material_dispensing', 'granulation', 
                         'blending', 'compression', 'post_compression_qc', 'sorting']
    
    if coating_type == 'coated':
        phases_to_complete.append('coating')
    
    phases_to_complete.append('packaging_material_release')
    
    for phase_name in phases_to_complete:
        try:
            phase_exec = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name=phase_name)
            phase_exec.status = 'completed'
            phase_exec.completed_by = qa_user
            phase_exec.completed_date = django.utils.timezone.now()
            phase_exec.save()
        except BatchPhaseExecution.DoesNotExist:
            print(f"   ⚠️  Phase {phase_name} not found")
    
    # Check if bulk_packing becomes available
    next_phase = WorkflowService.get_next_phase(bmr)
    if next_phase and next_phase.phase.phase_name == 'bulk_packing':
        print("   ✅ bulk_packing is correctly available after packaging_material_release")
    else:
        print(f"   ❌ Expected bulk_packing but got: {next_phase.phase.phase_name if next_phase else 'None'}")
        return False
    
    print(f"6. ✅ ALL CHECKS PASSED for {coating_type} tablet type 2")
    return True

def test_multiple_bmr_creation():
    """Test creating multiple new BMRs for tablet type 2 to ensure consistency"""
    print("1. Testing multiple BMR creation for tablet type 2...")
    
    # Get or create tablet type 2 product
    product, created = Product.objects.get_or_create(
        product_name="Multi-Test Tablet Type 2",
        product_type='tablet',
        defaults={
            'coating_type': 'coated',
            'tablet_type': 'tablet_2'
        }
    )
    
    qa_user = User.objects.filter(role='qa').first()
    
    # Create 3 BMRs
    bmrs_created = []
    for i in range(3):
        import uuid
        batch_number = f"MT2-{i+1}-{uuid.uuid4().hex[:4].upper()}"
        
        try:
            bmr = BMR.objects.create(
                batch_number=batch_number,
                product=product,
                batch_size=1000 * (i+1),
                created_by=qa_user
            )
            bmrs_created.append(bmr)
            print(f"   Created BMR {i+1}: {bmr.bmr_number}")
        except Exception as e:
            print(f"   ❌ Error creating BMR {i+1}: {e}")
            return False
    
    # Initialize workflows for all BMRs
    print("2. Initializing workflows...")
    for i, bmr in enumerate(bmrs_created):
        try:
            WorkflowService.initialize_workflow_for_bmr(bmr)
            print(f"   ✅ Workflow {i+1} initialized successfully")
        except Exception as e:
            print(f"   ❌ Error initializing workflow {i+1}: {e}")
            return False
    
    # Check all have bulk_packing
    print("3. Checking all BMRs have bulk_packing phase...")
    for i, bmr in enumerate(bmrs_created):
        phases = BatchPhaseExecution.objects.filter(bmr=bmr)
        phase_names = [p.phase.phase_name for p in phases]
        
        if 'bulk_packing' not in phase_names:
            print(f"   ❌ BMR {i+1} is missing bulk_packing phase!")
            return False
        
        if 'blister_packing' in phase_names:
            print(f"   ❌ BMR {i+1} incorrectly has blister_packing phase!")
            return False
        
        print(f"   ✅ BMR {i+1} has correct packing phases")
    
    print("4. ✅ ALL BMRs created with correct workflow")
    return True

if __name__ == '__main__':
    success = test_new_bmr_creation_and_workflow()
    
    if success:
        print("\n🎉 COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
        print("The workflow logic for new batches of tablet type 2 is working correctly.")
        print("New BMRs will always include the bulk_packing phase in the correct sequence.")
    else:
        print("\n❌ COMPREHENSIVE TEST FAILED!")
        print("There are issues with the workflow logic for new batches of tablet type 2.")
        print("Please review the WorkflowService.initialize_workflow_for_bmr method.")
