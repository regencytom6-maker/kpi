#!/usr/bin/env python
"""
URGENT FIX: Check and correct phase orders - Secondary Packaging should come AFTER Bulk Packing
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase

def fix_phase_orders():
    """Fix the phase orders - this is the root cause of the problem"""
    print("="*80)
    print("URGENT: FIXING PHASE ORDERS - SECONDARY BEFORE BULK IS WRONG!")
    print("="*80)
    
    # Get current phase orders
    phases = ProductionPhase.objects.all().order_by('phase_order')
    
    print("\n🔍 CURRENT PHASE ORDERS (THIS IS THE PROBLEM!):")
    print("-" * 60)
    for phase in phases:
        if phase.phase_name in ['bulk_packing', 'secondary_packing', 'packaging_material_release', 'blister_packing']:
            status = "❌ WRONG ORDER!" if phase.phase_name == 'secondary_packing' and phase.phase_order < 300 else ""
            print(f"  {phase.phase_order:3d}. {phase.phase_name} {status}")
        else:
            print(f"  {phase.phase_order:3d}. {phase.phase_name}")
    
    # Check specifically for the problem
    bulk_packing = ProductionPhase.objects.filter(phase_name='bulk_packing').first()
    secondary_packing = ProductionPhase.objects.filter(phase_name='secondary_packing').first()
    
    if bulk_packing and secondary_packing:
        print(f"\n🚨 FOUND THE PROBLEM:")
        print(f"   Bulk Packing Order: {bulk_packing.phase_order}")
        print(f"   Secondary Packing Order: {secondary_packing.phase_order}")
        
        if secondary_packing.phase_order < bulk_packing.phase_order:
            print(f"   ❌ CRITICAL ERROR: Secondary comes before Bulk!")
            print(f"   This is why your workflow timeline shows Secondary before Bulk!")
            
            # FIX IT NOW
            print(f"\n🔧 FIXING THE ORDERS:")
            
            # Get packaging material release order as reference
            packaging_release = ProductionPhase.objects.filter(phase_name='packaging_material_release').first()
            if packaging_release:
                # Set correct order: packaging_material_release -> bulk_packing -> secondary_packing
                bulk_packing.phase_order = packaging_release.phase_order + 10
                secondary_packing.phase_order = bulk_packing.phase_order + 10
                
                bulk_packing.save()
                secondary_packing.save()
                
                print(f"   ✅ Fixed Bulk Packing Order: {bulk_packing.phase_order}")
                print(f"   ✅ Fixed Secondary Packing Order: {secondary_packing.phase_order}")
                print(f"   ✅ Now: Packaging Release -> Bulk Packing -> Secondary Packing")
            else:
                # Manual fix if packaging release not found
                bulk_packing.phase_order = 280
                secondary_packing.phase_order = 290
                
                bulk_packing.save()
                secondary_packing.save()
                
                print(f"   ✅ Manual Fix - Bulk Packing Order: {bulk_packing.phase_order}")
                print(f"   ✅ Manual Fix - Secondary Packing Order: {secondary_packing.phase_order}")
        else:
            print(f"   ✅ Orders are correct")
    else:
        if not bulk_packing:
            print(f"   ❌ BULK_PACKING phase not found in database!")
        if not secondary_packing:
            print(f"   ❌ SECONDARY_PACKING phase not found in database!")
    
    # Show final orders
    print(f"\n✅ CORRECTED PHASE ORDERS:")
    print("-" * 60)
    phases = ProductionPhase.objects.all().order_by('phase_order')
    for phase in phases:
        if phase.phase_name in ['packaging_material_release', 'bulk_packing', 'secondary_packing', 'blister_packing']:
            print(f"  {phase.phase_order:3d}. {phase.phase_name} ⭐")
        else:
            print(f"  {phase.phase_order:3d}. {phase.phase_name}")
    
    print(f"\n🎉 PHASE ORDER FIX COMPLETE!")
    print(f"   Now create a new BMR and the workflow should be correct!")

if __name__ == "__main__":
    fix_phase_orders()
