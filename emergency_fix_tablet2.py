#!/usr/bin/env python
"""
EMERGENCY FIX: Fix phase orders for tablet_2 - bulk_packing must come before secondary_packaging
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase

def emergency_fix_tablet2_orders():
    """EMERGENCY: Fix tablet_2 phase orders"""
    print("="*80)
    print("🚨 EMERGENCY FIX: TABLET_2 PHASE ORDERS")
    print("="*80)
    
    # Get tablet_2 phases that are causing problems
    tablet2_phases = ProductionPhase.objects.filter(product_type='tablet_2').order_by('phase_order')
    
    print("\n❌ CURRENT TABLET_2 ORDERS (BROKEN):")
    for phase in tablet2_phases:
        print(f"  {phase.phase_order:3d}. {phase.phase_name}")
        
    # Find the problematic phases
    packaging_release = ProductionPhase.objects.filter(
        product_type='tablet_2', 
        phase_name='packaging_material_release'
    ).first()
    
    bulk_packing = ProductionPhase.objects.filter(
        product_type='tablet_2', 
        phase_name='bulk_packing'
    ).first()
    
    secondary_packing = ProductionPhase.objects.filter(
        product_type='tablet_2', 
        phase_name='secondary_packaging'
    ).first()
    
    if packaging_release and bulk_packing and secondary_packing:
        print(f"\n🔧 FIXING ORDERS:")
        print(f"   Current - Packaging Release: {packaging_release.phase_order}")
        print(f"   Current - Bulk Packing: {bulk_packing.phase_order}")
        print(f"   Current - Secondary Packing: {secondary_packing.phase_order}")
        
        # Set correct order
        bulk_packing.phase_order = packaging_release.phase_order + 1  # Right after packaging release
        secondary_packing.phase_order = bulk_packing.phase_order + 1   # After bulk packing
        
        bulk_packing.save()
        secondary_packing.save()
        
        print(f"\n✅ FIXED:")
        print(f"   Packaging Release: {packaging_release.phase_order}")
        print(f"   Bulk Packing: {bulk_packing.phase_order}")
        print(f"   Secondary Packing: {secondary_packing.phase_order}")
    else:
        print("❌ Cannot find required phases!")
        if not packaging_release:
            print("   Missing: packaging_material_release")
        if not bulk_packing:
            print("   Missing: bulk_packing")
        if not secondary_packing:
            print("   Missing: secondary_packaging")
    
    # Show final corrected order
    print(f"\n✅ FINAL TABLET_2 PHASE ORDER:")
    tablet2_phases = ProductionPhase.objects.filter(product_type='tablet_2').order_by('phase_order')
    for phase in tablet2_phases:
        if phase.phase_name in ['packaging_material_release', 'bulk_packing', 'secondary_packaging']:
            print(f"  {phase.phase_order:3d}. {phase.phase_name} ⭐")
        else:
            print(f"  {phase.phase_order:3d}. {phase.phase_name}")
    
    print(f"\n🎉 EMERGENCY FIX COMPLETE!")
    print(f"   Tablet Type 2 workflow should now be correct!")

if __name__ == "__main__":
    emergency_fix_tablet2_orders()
