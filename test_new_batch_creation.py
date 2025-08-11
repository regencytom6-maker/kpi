#!/usr/bin/env python
"""
Test script to create new batches and verify workflow progression
Focuses on tablet type 2 bulk packing workflow
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, WorkflowPhase
from workflow.services import WorkflowService

User = get_user_model()

def test_new_batch_creation():
    """Test creating new batches and verifying workflow initialization"""
    print("="*60)
    print("TESTING NEW BATCH CREATION AND WORKFLOW PROGRESSION")
    print("="*60)
    
    # Get test users
    try:
        qa_user = User.objects.filter(role='qa').first()
        if not qa_user:
            print("❌ No QA user found. Please create one first.")
            return False
            
        print(f"✅ Using QA user: {qa_user.username}")
    except Exception as e:
        print(f"❌ Error getting QA user: {e}")
        return False
    
    # Get test products
    try:
        # Get tablet type 2 products
        tablet2_products = Product.objects.filter(
            product_type='tablet',
            tablet_type='tablet_2'
        )
        
        # Get other product types for comparison
        tablet_normal = Product.objects.filter(
            product_type='tablet',
            tablet_type='normal'
        ).first()
        
        capsule_product = Product.objects.filter(product_type='capsule').first()
        ointment_product = Product.objects.filter(product_type='ointment').first()
        
        print(f"\n📋 Available Products:")
        print(f"   - Tablet Type 2: {tablet2_products.count()} products")
        if tablet_normal:
            print(f"   - Normal Tablet: {tablet_normal.product_name}")
        if capsule_product:
            print(f"   - Capsule: {capsule_product.product_name}")
        if ointment_product:
            print(f"   - Ointment: {ointment_product.product_name}")
            
    except Exception as e:
        print(f"❌ Error getting products: {e}")
        return False
    
    test_results = []
    
    # Test 1: Create new BMR for Tablet Type 2 (Coated)
    if tablet2_products.exists():
        tablet2_coated = tablet2_products.filter(coating_type='coated').first()
        if tablet2_coated:
            print(f"\n🧪 TEST 1: Creating BMR for Tablet Type 2 (Coated)")
            print(f"   Product: {tablet2_coated.product_name}")
            
            try:
                # Generate unique batch number
                batch_number = f"TEST{datetime.now().strftime('%m%d%H%M')}"
                
                # Create BMR
                bmr = BMR.objects.create(
                    batch_number=batch_number,
                    product=tablet2_coated,
                    batch_size=1000,
                    created_by=qa_user,
                    status='draft'
                )
                
                print(f"   ✅ BMR created: {bmr.batch_number}")
                
                # Initialize workflow
                WorkflowService.initialize_workflow_for_bmr(bmr)
                
                # Get all phases for this BMR
                phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
                
                print(f"   📊 Workflow phases created: {phases.count()}")
                phase_names = [p.phase.phase_name for p in phases]
                
                # Verify bulk_packing is included
                has_bulk_packing = 'bulk_packing' in phase_names
                bulk_packing_order = None
                coating_order = None
                secondary_packing_order = None
                
                for i, phase in enumerate(phases):
                    print(f"      {i+1}. {phase.phase.phase_name} (Status: {phase.status})")
                    if phase.phase.phase_name == 'bulk_packing':
                        bulk_packing_order = i+1
                    elif phase.phase.phase_name == 'coating':
                        coating_order = i+1
                    elif phase.phase.phase_name == 'secondary_packing':
                        secondary_packing_order = i+1
                
                # Verify workflow correctness
                test_passed = True
                if not has_bulk_packing:
                    print("   ❌ FAIL: bulk_packing phase missing!")
                    test_passed = False
                else:
                    print(f"   ✅ bulk_packing found at position {bulk_packing_order}")
                
                # Check phase order for coated tablets
                if coating_order and bulk_packing_order:
                    if bulk_packing_order > coating_order:
                        print(f"   ✅ Correct order: coating ({coating_order}) before bulk_packing ({bulk_packing_order})")
                    else:
                        print(f"   ❌ FAIL: Wrong order - bulk_packing ({bulk_packing_order}) should come after coating ({coating_order})")
                        test_passed = False
                
                test_results.append({
                    'test': 'Tablet Type 2 (Coated)',
                    'bmr': bmr.batch_number,
                    'passed': test_passed,
                    'phases': len(phase_names),
                    'has_bulk_packing': has_bulk_packing
                })
                
            except Exception as e:
                print(f"   ❌ Error creating BMR: {e}")
                test_results.append({
                    'test': 'Tablet Type 2 (Coated)',
                    'bmr': 'FAILED',
                    'passed': False,
                    'error': str(e)
                })
    
    # Test 2: Create new BMR for Tablet Type 2 (Uncoated)
    tablet2_uncoated = tablet2_products.filter(coating_type='uncoated').first()
    if tablet2_uncoated:
        print(f"\n🧪 TEST 2: Creating BMR for Tablet Type 2 (Uncoated)")
        print(f"   Product: {tablet2_uncoated.product_name}")
        
        try:
            # Generate unique batch number
            batch_number = f"TEST{datetime.now().strftime('%m%d%H%M')}B"
            
            # Create BMR
            bmr = BMR.objects.create(
                batch_number=batch_number,
                product=tablet2_uncoated,
                batch_size=1000,
                created_by=qa_user,
                status='draft'
            )
            
            print(f"   ✅ BMR created: {bmr.batch_number}")
            
            # Initialize workflow
            WorkflowService.initialize_workflow_for_bmr(bmr)
            
            # Get all phases for this BMR
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
            
            print(f"   📊 Workflow phases created: {phases.count()}")
            phase_names = [p.phase.phase_name for p in phases]
            
            # Verify bulk_packing is included
            has_bulk_packing = 'bulk_packing' in phase_names
            has_coating = 'coating' in phase_names
            bulk_packing_order = None
            compression_order = None
            
            for i, phase in enumerate(phases):
                print(f"      {i+1}. {phase.phase.phase_name} (Status: {phase.status})")
                if phase.phase.phase_name == 'bulk_packing':
                    bulk_packing_order = i+1
                elif phase.phase.phase_name == 'compression':
                    compression_order = i+1
            
            # Verify workflow correctness
            test_passed = True
            if not has_bulk_packing:
                print("   ❌ FAIL: bulk_packing phase missing!")
                test_passed = False
            else:
                print(f"   ✅ bulk_packing found at position {bulk_packing_order}")
            
            if has_coating:
                print("   ❌ FAIL: coating phase should not be present for uncoated tablets!")
                test_passed = False
            else:
                print("   ✅ coating phase correctly excluded for uncoated tablets")
            
            # Check phase order for uncoated tablets
            if compression_order and bulk_packing_order:
                if bulk_packing_order > compression_order:
                    print(f"   ✅ Correct order: compression ({compression_order}) before bulk_packing ({bulk_packing_order})")
                else:
                    print(f"   ❌ FAIL: Wrong order - bulk_packing ({bulk_packing_order}) should come after compression ({compression_order})")
                    test_passed = False
            
            test_results.append({
                'test': 'Tablet Type 2 (Uncoated)',
                'bmr': bmr.batch_number,
                'passed': test_passed,
                'phases': len(phase_names),
                'has_bulk_packing': has_bulk_packing,
                'has_coating': has_coating
            })
            
        except Exception as e:
            print(f"   ❌ Error creating BMR: {e}")
            test_results.append({
                'test': 'Tablet Type 2 (Uncoated)',
                'bmr': 'FAILED',
                'passed': False,
                'error': str(e)
            })
    
    # Test 3: Create BMR for Normal Tablet (for comparison)
    if tablet_normal:
        print(f"\n🧪 TEST 3: Creating BMR for Normal Tablet (Comparison)")
        print(f"   Product: {tablet_normal.product_name}")
        
        try:
            # Generate unique batch number
            batch_number = f"TEST{datetime.now().strftime('%m%d%H%M')}C"
            
            # Create BMR
            bmr = BMR.objects.create(
                batch_number=batch_number,
                product=tablet_normal,
                batch_size=1000,
                created_by=qa_user,
                status='draft'
            )
            
            print(f"   ✅ BMR created: {bmr.batch_number}")
            
            # Initialize workflow
            WorkflowService.initialize_workflow_for_bmr(bmr)
            
            # Get all phases for this BMR
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
            
            print(f"   📊 Workflow phases created: {phases.count()}")
            phase_names = [p.phase.phase_name for p in phases]
            
            # Verify bulk_packing is NOT included (should use blister_packing)
            has_bulk_packing = 'bulk_packing' in phase_names
            has_blister_packing = 'blister_packing' in phase_names
            
            for i, phase in enumerate(phases):
                print(f"      {i+1}. {phase.phase.phase_name} (Status: {phase.status})")
            
            # Verify workflow correctness
            test_passed = True
            if has_bulk_packing:
                print("   ❌ FAIL: bulk_packing should not be present for normal tablets!")
                test_passed = False
            else:
                print("   ✅ bulk_packing correctly excluded for normal tablets")
            
            if not has_blister_packing:
                print("   ❌ FAIL: blister_packing should be present for normal tablets!")
                test_passed = False
            else:
                print("   ✅ blister_packing correctly included for normal tablets")
            
            test_results.append({
                'test': 'Normal Tablet',
                'bmr': bmr.batch_number,
                'passed': test_passed,
                'phases': len(phase_names),
                'has_bulk_packing': has_bulk_packing,
                'has_blister_packing': has_blister_packing
            })
            
        except Exception as e:
            print(f"   ❌ Error creating BMR: {e}")
            test_results.append({
                'test': 'Normal Tablet',
                'bmr': 'FAILED',
                'passed': False,
                'error': str(e)
            })
    
    # Test 4: Create BMR for Capsule (for comparison)
    if capsule_product:
        print(f"\n🧪 TEST 4: Creating BMR for Capsule (Comparison)")
        print(f"   Product: {capsule_product.product_name}")
        
        try:
            # Generate unique batch number
            batch_number = f"TEST{datetime.now().strftime('%m%d%H%M')}D"
            
            # Create BMR
            bmr = BMR.objects.create(
                batch_number=batch_number,
                product=capsule_product,
                batch_size=1000,
                created_by=qa_user,
                status='draft'
            )
            
            print(f"   ✅ BMR created: {bmr.batch_number}")
            
            # Initialize workflow
            WorkflowService.initialize_workflow_for_bmr(bmr)
            
            # Get all phases for this BMR
            phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
            
            print(f"   📊 Workflow phases created: {phases.count()}")
            phase_names = [p.phase.phase_name for p in phases]
            
            # Verify bulk_packing is NOT included (capsules use blister_packing)
            has_bulk_packing = 'bulk_packing' in phase_names
            has_blister_packing = 'blister_packing' in phase_names
            has_drying = 'drying' in phase_names
            has_filling = 'filling' in phase_names
            
            for i, phase in enumerate(phases):
                print(f"      {i+1}. {phase.phase.phase_name} (Status: {phase.status})")
            
            # Verify workflow correctness
            test_passed = True
            if has_bulk_packing:
                print("   ❌ FAIL: bulk_packing should not be present for capsules!")
                test_passed = False
            else:
                print("   ✅ bulk_packing correctly excluded for capsules")
            
            if not has_blister_packing:
                print("   ❌ FAIL: blister_packing should be present for capsules!")
                test_passed = False
            else:
                print("   ✅ blister_packing correctly included for capsules")
                
            if not has_drying:
                print("   ❌ FAIL: drying should be present for capsules!")
                test_passed = False
            else:
                print("   ✅ drying correctly included for capsules")
                
            if not has_filling:
                print("   ❌ FAIL: filling should be present for capsules!")
                test_passed = False
            else:
                print("   ✅ filling correctly included for capsules")
            
            test_results.append({
                'test': 'Capsule',
                'bmr': bmr.batch_number,
                'passed': test_passed,
                'phases': len(phase_names),
                'has_bulk_packing': has_bulk_packing,
                'has_blister_packing': has_blister_packing,
                'has_drying': has_drying,
                'has_filling': has_filling
            })
            
        except Exception as e:
            print(f"   ❌ Error creating BMR: {e}")
            test_results.append({
                'test': 'Capsule',
                'bmr': 'FAILED',
                'passed': False,
                'error': str(e)
            })
    
    # Print test summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} {result['test']}: BMR {result['bmr']}")
        if 'phases' in result:
            print(f"      Phases created: {result['phases']}")
        if 'has_bulk_packing' in result:
            print(f"      Has bulk_packing: {result['has_bulk_packing']}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
        if not result['passed']:
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! New batch workflow creation is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED! Please review the workflow logic.")
    
    return all_passed

if __name__ == "__main__":
    test_new_batch_creation()
