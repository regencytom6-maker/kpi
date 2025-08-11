#!/usr/bin/env python
"""
Test script to verify the fix worked - create new BMR and check workflow order
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
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

User = get_user_model()

def test_fixed_workflow():
    """Test that the workflow fix is working for new BMRs"""
    print("="*80)
    print("🧪 TESTING FIXED WORKFLOW FOR NEW BMR")
    print("="*80)
    
    # Get tablet type 2 product
    tablet2_product = Product.objects.filter(
        product_type='tablet',
        tablet_type='tablet_2'
    ).first()
    
    if not tablet2_product:
        print("❌ No tablet type 2 product found!")
        return False
    
    # Get QA user
    qa_user = User.objects.filter(role='qa').first()
    if not qa_user:
        print("❌ No QA user found!")
        return False
    
    print(f"📦 Testing with product: {tablet2_product.product_name}")
    print(f"👤 Using QA user: {qa_user.username}")
    
    # Create test BMR
    test_batch = f"FIX{datetime.now().strftime('%H%M%S')}"
    try:
        test_bmr = BMR.objects.create(
            batch_number=test_batch,
            product=tablet2_product,
            batch_size=1000,
            created_by=qa_user,
            status='draft'
        )
        
        print(f"✅ Created test BMR: {test_bmr.batch_number}")
        
        # Initialize workflow
        WorkflowService.initialize_workflow_for_bmr(test_bmr)
        
        # Get all phases for this BMR
        phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).order_by('phase__phase_order')
        
        print(f"\n📋 WORKFLOW PHASES ({phases.count()} total):")
        print("-" * 60)
        
        packaging_order = None
        bulk_order = None
        secondary_order = None
        
        for i, phase_exec in enumerate(phases, 1):
            phase_name = phase_exec.phase.phase_name
            phase_order = phase_exec.phase.phase_order
            
            if phase_name == 'packaging_material_release':
                packaging_order = phase_order
                print(f"  {i:2d}. {phase_name} (Order: {phase_order}) ⭐")
            elif phase_name == 'bulk_packing':
                bulk_order = phase_order
                print(f"  {i:2d}. {phase_name} (Order: {phase_order}) ⭐ BULK")
            elif phase_name == 'secondary_packaging':
                secondary_order = phase_order
                print(f"  {i:2d}. {phase_name} (Order: {phase_order}) ⭐ SECONDARY")
            else:
                print(f"  {i:2d}. {phase_name} (Order: {phase_order})")
        
        # Verify the fix worked
        print(f"\n🔍 VERIFICATION:")
        print("-" * 40)
        
        success = True
        
        if not bulk_order:
            print("❌ FAIL: bulk_packing phase not found!")
            success = False
        
        if not secondary_order:
            print("❌ FAIL: secondary_packaging phase not found!")
            success = False
        
        if bulk_order and secondary_order:
            if bulk_order < secondary_order:
                print(f"✅ CORRECT: bulk_packing ({bulk_order}) comes before secondary_packaging ({secondary_order})")
            else:
                print(f"❌ FAIL: bulk_packing ({bulk_order}) should come before secondary_packaging ({secondary_order})")
                success = False
        
        if packaging_order and bulk_order:
            if packaging_order < bulk_order:
                print(f"✅ CORRECT: packaging_material_release ({packaging_order}) comes before bulk_packing ({bulk_order})")
            else:
                print(f"❌ FAIL: packaging_material_release ({packaging_order}) should come before bulk_packing ({bulk_order})")
                success = False
        
        # Expected sequence check
        expected_sequence = ['packaging_material_release', 'bulk_packing', 'secondary_packaging']
        actual_sequence = []
        
        for phase_exec in phases:
            if phase_exec.phase.phase_name in expected_sequence:
                actual_sequence.append(phase_exec.phase.phase_name)
        
        if actual_sequence == expected_sequence:
            print(f"✅ PERFECT: Correct sequence maintained!")
            print(f"   Expected: {' → '.join(expected_sequence)}")
            print(f"   Actual:   {' → '.join(actual_sequence)}")
        else:
            print(f"❌ SEQUENCE ERROR:")
            print(f"   Expected: {' → '.join(expected_sequence)}")
            print(f"   Actual:   {' → '.join(actual_sequence)}")
            success = False
        
        # Clean up test BMR
        test_bmr.delete()
        print(f"\n🗑️  Cleaned up test BMR")
        
        if success:
            print(f"\n🎉 SUCCESS! The workflow fix is working correctly!")
            print(f"   New BMRs for tablet type 2 will now have bulk_packing before secondary_packaging!")
        else:
            print(f"\n❌ FAILURE! The workflow still has issues!")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    test_fixed_workflow()
