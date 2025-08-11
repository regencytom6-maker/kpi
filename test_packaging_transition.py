#!/usr/bin/env python3
"""
Test the packaging transition logic by simulating a completed packaging material release
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

def test_packaging_transition():
    print("🧪 TESTING PACKAGING TRANSITION NOTIFICATION")
    print("=" * 50)
    
    # Get a tablet type 2 BMR
    bmr = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).first()
    
    if not bmr:
        print("❌ No tablet type 2 BMR found!")
        return
    
    print(f"📋 Testing with BMR: {bmr.batch_number} - {bmr.product.product_name}")
    print(f"   Product Type: {bmr.product.product_type}")
    print(f"   Tablet Type: {getattr(bmr.product, 'tablet_type', 'N/A')}")
    
    # Show current workflow status
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    print(f"\n📊 Current Workflow Status:")
    for phase in phases:
        status_emoji = "✅" if phase.status == 'completed' else "⏳" if phase.status == 'pending' else "❌" if phase.status == 'not_ready' else "🔄"
        print(f"   {status_emoji} {phase.phase.phase_name:25} (order: {phase.phase.phase_order:2d}) - {phase.status}")
    
    # Test the specific logic from packaging dashboard
    print(f"\n🎯 Testing Packaging Dashboard Logic:")
    
    # Simulate what happens after packaging material release is completed
    print(f"   Checking condition: product_type == 'tablet' and tablet_type == 'tablet_2'")
    print(f"   Result: {bmr.product.product_type == 'tablet'} and {getattr(bmr.product, 'tablet_type', None) == 'tablet_2'}")
    
    if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2':
        print(f"   ✅ Condition met - should look for bulk_packing phase")
        
        # Check for bulk_packing phase
        next_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        if next_phase:
            print(f"   ✅ Found bulk_packing phase: {next_phase.phase.phase_name} (Status: {next_phase.status})")
            print(f"   📋 Phase order: {next_phase.phase.phase_order}")
            print(f"   💬 Display name: {next_phase.phase.get_phase_name_display()}")
        else:
            print(f"   ❌ No bulk_packing phase found!")
    
    # Test the fallback logic (get_next_phase)
    print(f"\n🔄 Testing WorkflowService.get_next_phase fallback:")
    next_phase = WorkflowService.get_next_phase(bmr)
    if next_phase:
        print(f"   ➡️  Service says next phase: {next_phase.phase.phase_name} (Status: {next_phase.status})")
        print(f"   📋 Phase order: {next_phase.phase.phase_order}")
        print(f"   💬 Display name: {next_phase.phase.get_phase_name_display()}")
    else:
        print(f"   ❌ Service returned no next phase")
    
    # Check the phase order around packaging
    print(f"\n🔍 Analyzing Phase Order Around Packaging:")
    packaging_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='packaging_material_release').first()
    if packaging_phase:
        print(f"   📦 Packaging Material Release: order {packaging_phase.phase.phase_order}")
        
        # Find phases that come after packaging
        following_phases = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_order__gt=packaging_phase.phase.phase_order
        ).select_related('phase').order_by('phase__phase_order')
        
        print(f"   📈 Phases that follow packaging material release:")
        for idx, phase in enumerate(following_phases[:3]):
            marker = "👉" if idx == 0 else "   "
            print(f"      {marker} {phase.phase.phase_name:25} (order: {phase.phase.phase_order:2d}) - {phase.status}")
            if idx == 0:
                print(f"         🎯 THIS IS THE NEXT PHASE THAT SHOULD BE MENTIONED")

if __name__ == '__main__':
    test_packaging_transition()
