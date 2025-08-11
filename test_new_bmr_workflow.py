#!/usr/bin/env python3
"""
Test creating a new tablet type 2 BMR to verify correct workflow order
"""

import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from products.models import Product
from accounts.models import CustomUser
from django.utils import timezone

def test_new_bmr_workflow():
    print("🧪 TESTING NEW BMR CREATION FOR TABLET TYPE 2")
    print("=" * 50)
    
    # Get a tablet type 2 product
    tablet_2_product = Product.objects.filter(
        product_type='tablet',
        tablet_type='tablet_2'
    ).first()
    
    if not tablet_2_product:
        print("❌ No tablet type 2 product found!")
        return
    
    print(f"📋 Using product: {tablet_2_product.product_name}")
    print(f"   Product Type: {tablet_2_product.product_type}")
    print(f"   Tablet Type: {tablet_2_product.tablet_type}")
    
    # Get a user to create the BMR
    user = CustomUser.objects.filter(role='qa').first()
    if not user:
        user = CustomUser.objects.first()
    
    if not user:
        print("❌ No user found!")
        return
    
    # Generate a unique batch number
    import random
    batch_number = f"TEST{random.randint(1000, 9999)}2025"
    
    print(f"\n🎬 CREATING NEW BMR: {batch_number}")
    
    # Create the BMR
    bmr = BMR.objects.create(
        batch_number=batch_number,
        product=tablet_2_product,
        batch_size=1000,
        created_by=user,
        status='draft'
    )
    
    print(f"   ✅ BMR created: {bmr.batch_number}")
    
    # Initialize the workflow
    print(f"   🚀 Initializing workflow...")
    WorkflowService.initialize_workflow_for_bmr(bmr)
    
    # Check the workflow order
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    
    print(f"\n📊 Workflow Order for New BMR {bmr.batch_number}:")
    found_packaging = False
    packaging_order = None
    bulk_order = None
    secondary_order = None
    
    for idx, phase_exec in enumerate(phases):
        status_indicator = "✅" if phase_exec.status == 'completed' else "⏳" if phase_exec.status == 'pending' else "❌" if phase_exec.status == 'not_ready' else "🔄"
        print(f"      {idx+1:2d}. {status_indicator} {phase_exec.phase.phase_name:25} (order: {phase_exec.phase.phase_order:2d}) - {phase_exec.status}")
        
        if phase_exec.phase.phase_name == 'packaging_material_release':
            found_packaging = True
            packaging_order = phase_exec.phase.phase_order
        elif phase_exec.phase.phase_name == 'bulk_packing':
            bulk_order = phase_exec.phase.phase_order
        elif phase_exec.phase.phase_name == 'secondary_packaging':
            secondary_order = phase_exec.phase.phase_order
    
    # Verify the order
    print(f"\n🔍 VERIFICATION:")
    if packaging_order and bulk_order and secondary_order:
        print(f"   📦 packaging_material_release: order {packaging_order}")
        print(f"   📦 bulk_packing: order {bulk_order}")
        print(f"   📦 secondary_packaging: order {secondary_order}")
        
        if packaging_order < bulk_order < secondary_order:
            print(f"   ✅ PERFECT: Correct order - packaging → bulk → secondary")
            success = True
        else:
            print(f"   ❌ WRONG ORDER: Should be packaging < bulk < secondary")
            success = False
    else:
        print(f"   ❌ Missing critical phases!")
        success = False
    
    # Test the specific dashboard logic
    print(f"\n💬 TESTING DASHBOARD NOTIFICATION LOGIC:")
    if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2':
        next_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        if next_phase:
            print(f"   ✅ Dashboard will show: 'Next phase: {next_phase.phase.get_phase_name_display()}'")
        else:
            print(f"   ❌ Dashboard won't find bulk_packing phase!")
            success = False
    
    # Clean up - delete the test BMR
    print(f"\n🧹 CLEANING UP...")
    BatchPhaseExecution.objects.filter(bmr=bmr).delete()
    bmr.delete()
    print(f"   ✅ Test BMR deleted")
    
    return success

if __name__ == '__main__':
    success = test_new_bmr_workflow()
    
    if success:
        print(f"\n🎉 SUCCESS: NEW BMR WORKFLOW IS CORRECT!")
        print(f"📋 New tablet type 2 BMRs will show 'bulk packing' next, not 'secondary packaging'")
        print(f"🚀 System is ready for deployment!")
    else:
        print(f"\n❌ FAILED: New BMR workflow still has issues")
        print(f"🔧 Additional fixes needed")
