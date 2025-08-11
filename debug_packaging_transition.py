#!/usr/bin/env python3
"""
Debug script to check packaging transition logic for tablet type 2 BMRs
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
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from products.models import Product

def debug_packaging_transition():
    """Debug the transition from packaging material release to next phase"""
    
    print("🔍 DEBUGGING PACKAGING TRANSITION FOR TABLET TYPE 2")
    print("=" * 60)
    
    # Find tablet type 2 BMRs
    tablet_2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    if not tablet_2_bmrs.exists():
        print("❌ No tablet type 2 BMRs found!")
        return
    
    for bmr in tablet_2_bmrs[:3]:  # Check first 3 BMRs
        print(f"\n📋 BMR: {bmr.batch_number} - {bmr.product.product_name}")
        print(f"   Product Type: {bmr.product.product_type}")
        print(f"   Tablet Type: {getattr(bmr.product, 'tablet_type', 'N/A')}")
        
        # Get the packaging material release phase
        packaging_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='packaging_material_release'
        ).first()
        
        if not packaging_phase:
            print("   ❌ No packaging material release phase found")
            continue
        
        print(f"   📦 Packaging Material Release Status: {packaging_phase.status}")
        
        # Check what the next phase should be
        next_phase = WorkflowService.get_next_phase(bmr)
        if next_phase:
            print(f"   ➡️  Next Phase (by service): {next_phase.phase.phase_name} (Status: {next_phase.status})")
        else:
            print("   ❌ No next phase found by service")
        
        # Check the workflow order manually
        all_phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        print(f"   📊 Workflow Order for {bmr.batch_number}:")
        found_packaging = False
        for idx, phase_exec in enumerate(all_phases):
            status_indicator = "✅" if phase_exec.status == 'completed' else "⏳" if phase_exec.status == 'pending' else "❌" if phase_exec.status == 'not_ready' else "🔄"
            print(f"      {idx+1:2d}. {status_indicator} {phase_exec.phase.phase_name} (order: {phase_exec.phase.phase_order}) - {phase_exec.status}")
            
            if phase_exec.phase.phase_name == 'packaging_material_release':
                found_packaging = True
                
            # Check what comes immediately after packaging material release
            if found_packaging and phase_exec.phase.phase_name != 'packaging_material_release':
                print(f"         ⚠️  FIRST PHASE AFTER PACKAGING: {phase_exec.phase.phase_name}")
                if phase_exec.phase.phase_name == 'secondary_packaging':
                    print("         🚨 ERROR: secondary_packaging comes before bulk_packing!")
                elif phase_exec.phase.phase_name == 'bulk_packing':
                    print("         ✅ CORRECT: bulk_packing comes first")
                break
        
        # Test the specific logic from the packaging dashboard
        print(f"   🧪 Testing Packaging Dashboard Logic:")
        if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2':
            bulk_packing_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
            if bulk_packing_phase:
                print(f"      ✅ Found bulk_packing phase: {bulk_packing_phase.phase.phase_name} (Status: {bulk_packing_phase.status})")
            else:
                print(f"      ❌ No bulk_packing phase found!")
        
        print()

if __name__ == '__main__':
    debug_packaging_transition()
