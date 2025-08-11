#!/usr/bin/env python
"""
COMPREHENSIVE SYSTEM TEST: Simulate complete workflow for tablet type 2
This will test the FULL workflow including packaging material release
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

def complete_workflow_test():
    print("🧪 COMPREHENSIVE WORKFLOW TEST FOR TABLET TYPE 2")
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
    
    # Get users
    qa_user = CustomUser.objects.filter(role='qa').first()
    packaging_user = CustomUser.objects.filter(role='packaging_store').first()
    
    if not qa_user or not packaging_user:
        print("❌ Required users not found")
        return False
    
    # Create a new BMR
    import random
    test_batch_number = f"FULL{random.randint(10000, 99999)}2025"
    
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
    
    # Show initial workflow
    phases = BatchPhaseExecution.objects.filter(bmr=new_bmr).select_related('phase').order_by('phase__phase_order')
    print(f"\n📊 Initial Workflow Order:")
    for phase in phases:
        status_icon = "✅" if phase.status == "completed" else "⏳" if phase.status == "pending" else "❌"
        print(f"       {phase.phase.phase_order:2d}. {status_icon} {phase.phase.phase_name:25} - {phase.status}")
    
    # SIMULATE WORKFLOW PROGRESSION TO PACKAGING MATERIAL RELEASE
    print(f"\n🚀 SIMULATING WORKFLOW PROGRESSION...")
    
    # Complete phases up to packaging_material_release
    phases_to_complete = [
        'regulatory_approval', 'material_dispensing', 'granulation', 
        'blending', 'compression', 'post_compression_qc', 'sorting'
    ]
    
    for phase_name in phases_to_complete:
        phase_exec = phases.filter(phase__phase_name=phase_name).first()
        if phase_exec:
            phase_exec.status = 'completed'
            phase_exec.completed_by = qa_user
            phase_exec.completed_date = timezone.now()
            phase_exec.save()
            print(f"   ✅ Completed: {phase_name}")
            
            # Trigger next phase
            WorkflowService.trigger_next_phase(new_bmr, phase_exec.phase)
    
    # Now check the state at packaging_material_release
    print(f"\n📦 STATE BEFORE PACKAGING MATERIAL RELEASE:")
    packaging_phase = phases.filter(phase__phase_name='packaging_material_release').first()
    bulk_phase = phases.filter(phase__phase_name='bulk_packing').first()
    secondary_phase = phases.filter(phase__phase_name='secondary_packaging').first()
    
    if packaging_phase:
        print(f"   📦 packaging_material_release: {packaging_phase.status}")
    if bulk_phase:
        print(f"   📦 bulk_packing: {bulk_phase.status}")
    if secondary_phase:
        print(f"   📦 secondary_packaging: {secondary_phase.status}")
    
    # COMPLETE PACKAGING MATERIAL RELEASE
    print(f"\n🎯 COMPLETING PACKAGING MATERIAL RELEASE...")
    if packaging_phase and packaging_phase.status == 'pending':
        packaging_phase.status = 'in_progress'
        packaging_phase.started_by = packaging_user
        packaging_phase.started_date = timezone.now()
        packaging_phase.save()
        print(f"   📦 Started packaging material release")
        
        # Complete it
        packaging_phase.status = 'completed'
        packaging_phase.completed_by = packaging_user
        packaging_phase.completed_date = timezone.now()
        packaging_phase.save()
        print(f"   ✅ Completed packaging material release")
        
        # Trigger next phase
        result = WorkflowService.trigger_next_phase(new_bmr, packaging_phase.phase)
        print(f"   📋 trigger_next_phase result: {result}")
    
    # CHECK THE FINAL STATE
    print(f"\n🔍 FINAL STATE AFTER PACKAGING MATERIAL RELEASE:")
    # Refresh from database
    bulk_phase.refresh_from_db()
    secondary_phase.refresh_from_db()
    
    print(f"   📦 bulk_packing: {bulk_phase.status}")
    print(f"   📦 secondary_packaging: {secondary_phase.status}")
    
    # Test get_next_phase
    next_phase = WorkflowService.get_next_phase(new_bmr)
    if next_phase:
        print(f"   🎯 Next phase: {next_phase.phase.phase_name}")
        if next_phase.phase.phase_name == 'bulk_packing':
            print(f"   🎉 SUCCESS: System correctly shows bulk_packing as next!")
        else:
            print(f"   ❌ FAILURE: Expected bulk_packing, got {next_phase.phase.phase_name}")
    else:
        print(f"   ❌ No next phase found")
    
    # Show current workflow state
    phases.refresh_from_db()
    print(f"\n📊 Final Workflow State:")
    for phase in phases:
        status_icon = "✅" if phase.status == "completed" else "⏳" if phase.status == "pending" else "❌" if phase.status == "not_ready" else "🔄"
        print(f"       {phase.phase.phase_order:2d}. {status_icon} {phase.phase.phase_name:25} - {phase.status}")
    
    # Clean up
    print(f"\n🧹 CLEANING UP...")
    new_bmr.delete()
    print(f"   ✅ Test BMR deleted")
    
    print(f"\n🎉 COMPREHENSIVE TEST COMPLETED!")
    return True

if __name__ == "__main__":
    complete_workflow_test()
