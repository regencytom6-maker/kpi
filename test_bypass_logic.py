#!/usr/bin/env python
"""
Test the BYPASS of standard logic in trigger_next_phase for tablet_2
This verifies that packaging_material_release -> bulk_packing bypasses standard logic completely
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
from django.utils import timezone

def test_standard_logic_bypass():
    print("🧪 TESTING STANDARD LOGIC BYPASS FOR TABLET TYPE 2")
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
    test_batch_number = f"BYPASS{random.randint(10000, 99999)}2025"
    
    print(f"\n🎬 CREATING NEW BMR: {test_batch_number}")
    new_bmr = BMR.objects.create(
        batch_number=test_batch_number,
        product=tablet_2_product,
        created_by=qa_user,
        status='draft',
        batch_size=100
    )
    print(f"   ✅ BMR created: {new_bmr.batch_number}")
    
    # Initialize workflow
    print(f"   🚀 Initializing workflow...")
    WorkflowService.initialize_workflow_for_bmr(new_bmr)
    
    # Get key phases
    phases = BatchPhaseExecution.objects.filter(bmr=new_bmr).select_related('phase').order_by('phase__phase_order')
    packaging_phase = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_phase = phases.filter(phase__phase_name='secondary_packaging').first()
    
    print(f"\n📦 INITIAL STATE:")
    if packaging_phase:
        print(f"   📦 packaging_material_release: {packaging_phase.status}")
    if bulk_phase:
        print(f"   📦 bulk_packing: {bulk_phase.status}")
    if secondary_phase:
        print(f"   📦 secondary_packaging: {secondary_phase.status}")
    
    # Simulate completing packaging_material_release
    print(f"\n🎯 SIMULATING PACKAGING MATERIAL RELEASE COMPLETION...")
    if packaging_phase:
        # Mark as completed
        packaging_phase.status = 'completed'
        packaging_phase.completed_by = qa_user
        packaging_phase.completed_date = timezone.now()
        packaging_phase.save()
        print(f"   ✅ Marked packaging_material_release as completed")
        
        # Call trigger_next_phase and capture the result
        print(f"   🚀 Calling trigger_next_phase...")
        result = WorkflowService.trigger_next_phase(new_bmr, packaging_phase.phase)
        print(f"   📋 trigger_next_phase result: {result}")
        
        # Refresh phases from database
        bulk_phase.refresh_from_db()
        secondary_phase.refresh_from_db()
        
        print(f"\n🔍 STATE AFTER trigger_next_phase:")
        print(f"   📦 bulk_packing: {bulk_phase.status}")
        print(f"   📦 secondary_packaging: {secondary_phase.status}")
        
        # TEST 1: Check if bulk_packing was activated
        if bulk_phase.status == 'pending':
            print(f"   ✅ SUCCESS: bulk_packing activated correctly")
        else:
            print(f"   ❌ FAILURE: bulk_packing not activated (status: {bulk_phase.status})")
        
        # TEST 2: Check if secondary_packaging remained not_ready
        if secondary_phase.status == 'not_ready':
            print(f"   ✅ SUCCESS: secondary_packaging correctly kept as not_ready")
        else:
            print(f"   ❌ FAILURE: secondary_packaging should be not_ready (status: {secondary_phase.status})")
        
        # TEST 3: Check if trigger_next_phase returned True (indicating successful handling)
        if result:
            print(f"   ✅ SUCCESS: trigger_next_phase returned True (standard logic bypassed)")
        else:
            print(f"   ❌ FAILURE: trigger_next_phase returned False (standard logic may have run)")
        
        # TEST 4: Check that no other phases were inadvertently activated
        all_phases = BatchPhaseExecution.objects.filter(bmr=new_bmr).select_related('phase').order_by('phase__phase_order')
        unexpected_pending = []
        for phase in all_phases:
            if (phase.status == 'pending' and 
                phase.phase.phase_name not in ['bulk_packing'] and
                phase.phase.phase_order > packaging_phase.phase.phase_order):
                unexpected_pending.append(phase.phase.phase_name)
        
        if not unexpected_pending:
            print(f"   ✅ SUCCESS: No unexpected phases activated")
        else:
            print(f"   ❌ FAILURE: Unexpected phases activated: {unexpected_pending}")
        
        # Show complete phase status
        print(f"\n📊 Complete Phase Status After Test:")
        for phase in all_phases:
            status_icon = "✅" if phase.status == "completed" else "⏳" if phase.status == "pending" else "❌" if phase.status == "not_ready" else "🔄"
            print(f"       {phase.phase.phase_order:2d}. {status_icon} {phase.phase.phase_name:25} - {phase.status}")
    
    # Clean up
    print(f"\n🧹 CLEANING UP...")
    new_bmr.delete()
    print(f"   ✅ Test BMR deleted")
    
    print(f"\n🎉 STANDARD LOGIC BYPASS TEST COMPLETED!")
    return True

if __name__ == "__main__":
    test_standard_logic_bypass()
