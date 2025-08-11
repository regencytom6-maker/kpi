#!/usr/bin/env python
"""
Test the SYSTEM ROUTING for new tablet type 2 BMRs
This tests the workflow initialization and next phase logic
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from accounts.models import CustomUser

def test_system_routing():
    print("🧪 TESTING SYSTEM ROUTING FOR TABLET TYPE 2")
    print("=" * 60)
    
    # Find or create a tablet type 2 product
    tablet_2_product = Product.objects.filter(
        product_type='tablet',
        tablet_type='tablet_2'
    ).first()
    
    if not tablet_2_product:
        print("❌ No tablet type 2 product found in system")
        return False
    
    print(f"📋 Using product: {tablet_2_product.product_name}")
    print(f"   Product Type: {tablet_2_product.product_type}")
    print(f"   Tablet Type: {getattr(tablet_2_product, 'tablet_type', 'N/A')}")
    
    # Get QA user
    qa_user = CustomUser.objects.filter(role='qa').first()
    if not qa_user:
        print("❌ No QA user found")
        return False
    
    # Create a new BMR
    import random
    test_batch_number = f"TEST{random.randint(10000, 99999)}2025"
    
    print(f"\n🎬 CREATING NEW BMR: {test_batch_number}")
    new_bmr = BMR.objects.create(
        batch_number=test_batch_number,
        product=tablet_2_product,
        created_by=qa_user,
        status='draft',
        batch_size=100  # Add required batch_size
    )
    print(f"   ✅ BMR created: {new_bmr.batch_number}")
    
    # Initialize workflow
    print(f"   🚀 Initializing workflow...")
    WorkflowService.initialize_workflow_for_bmr(new_bmr)
    
    # Check the workflow order
    phases = BatchPhaseExecution.objects.filter(bmr=new_bmr).select_related('phase').order_by('phase__phase_order')
    
    print(f"\n📊 Workflow Order for New BMR {new_bmr.batch_number}:")
    for phase in phases:
        status_icon = "✅" if phase.status == "completed" else "⏳" if phase.status == "pending" else "❌"
        print(f"       {phase.phase.phase_order:2d}. {status_icon} {phase.phase.phase_name:25} (order: {phase.phase.phase_order:2d}) - {phase.status}")
    
    # Find key phases
    packaging_phase = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_phase = phases.filter(phase__phase_name='secondary_packaging').first()
    
    print(f"\n🔍 VERIFICATION:")
    if packaging_phase and bulk_phase and secondary_phase:
        packaging_order = packaging_phase.phase.phase_order
        bulk_order = bulk_phase.phase.phase_order
        secondary_order = secondary_phase.phase.phase_order
        
        print(f"   📦 packaging_material_release: order {packaging_order}")
        print(f"   📦 bulk_packing: order {bulk_order}")
        print(f"   📦 secondary_packaging: order {secondary_order}")
        
        if packaging_order < bulk_order < secondary_order:
            print(f"   ✅ PERFECT: Correct order - packaging → bulk → secondary")
        else:
            print(f"   ❌ WRONG ORDER: Should be packaging < bulk < secondary")
            
    # Test get_next_phase logic
    print(f"\n💬 TESTING GET_NEXT_PHASE LOGIC:")
    next_phase = WorkflowService.get_next_phase(new_bmr)
    if next_phase:
        print(f"   ✅ Next phase: {next_phase.phase.phase_name}")
    else:
        print(f"   ❌ No next phase found")
    
    # Simulate packaging material release completion and test trigger_next_phase
    print(f"\n🧪 TESTING TRIGGER_NEXT_PHASE FOR PACKAGING MATERIAL RELEASE:")
    if packaging_phase:
        # Mark packaging as completed
        packaging_phase.status = 'completed'
        packaging_phase.save()
        print(f"   📦 Marked packaging_material_release as completed")
        
        # Test trigger_next_phase
        result = WorkflowService.trigger_next_phase(new_bmr, packaging_phase.phase)
        print(f"   📋 trigger_next_phase result: {result}")
        
        # Check what phase became pending
        current_phase = WorkflowService.get_current_phase(new_bmr)
        if current_phase:
            print(f"   ✅ Current phase after trigger: {current_phase.phase.phase_name}")
            if current_phase.phase.phase_name == 'bulk_packing':
                print(f"   🎉 SUCCESS: System correctly routed to bulk_packing!")
            else:
                print(f"   ❌ FAILURE: Expected bulk_packing, got {current_phase.phase.phase_name}")
        else:
            print(f"   ❌ No current phase found after trigger")
    
    # Clean up
    print(f"\n🧹 CLEANING UP...")
    new_bmr.delete()
    print(f"   ✅ Test BMR deleted")
    
    print(f"\n🎉 SYSTEM ROUTING TEST COMPLETED!")
    return True

if __name__ == "__main__":
    test_system_routing()
