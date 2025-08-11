#!/usr/bin/env python3
"""
Check and fix ProductionPhase order for tablet type 2 workflow
"""

import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase

def check_and_fix_phase_order():
    print("🔍 CHECKING PRODUCTIONPHASE ORDER FOR TABLET TYPE 2")
    print("=" * 60)
    
    # Get all phases and their current order
    all_phases = ProductionPhase.objects.all().order_by('phase_order', 'phase_name')
    
    print("📊 Current ProductionPhase Order:")
    for phase in all_phases:
        print(f"  {phase.phase_order:2d}. {phase.phase_name:30} ({phase.product_type})")
    
    # Check for duplicate orders
    print("\n🔍 Checking for duplicate phase orders...")
    from collections import defaultdict
    order_counts = defaultdict(list)
    
    for phase in all_phases:
        order_counts[phase.phase_order].append(phase.phase_name)
    
    duplicates_found = False
    for order, phases in order_counts.items():
        if len(phases) > 1:
            print(f"  ⚠️  Order {order} has duplicates: {', '.join(phases)}")
            duplicates_found = True
    
    if not duplicates_found:
        print("  ✅ No duplicate phase orders found")
    
    # Check specific tablet phases
    print("\n📋 Tablet-specific phases:")
    tablet_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    
    for phase in tablet_phases:
        print(f"  {phase.phase_order:2d}. {phase.phase_name}")
    
    # Check the problematic phases
    packaging_phase = ProductionPhase.objects.filter(phase_name='packaging_material_release').first()
    bulk_phase = ProductionPhase.objects.filter(phase_name='bulk_packing').first()
    secondary_phase = ProductionPhase.objects.filter(phase_name='secondary_packaging').first()
    
    print(f"\n🎯 Critical phases for tablet type 2:")
    if packaging_phase:
        print(f"  📦 packaging_material_release: order {packaging_phase.phase_order}")
    if bulk_phase:
        print(f"  📦 bulk_packing: order {bulk_phase.phase_order}")
    if secondary_phase:
        print(f"  📦 secondary_packaging: order {secondary_phase.phase_order}")
    
    # Check if order is correct
    if bulk_phase and secondary_phase:
        if bulk_phase.phase_order < secondary_phase.phase_order:
            print(f"  ✅ CORRECT: bulk_packing ({bulk_phase.phase_order}) comes before secondary_packaging ({secondary_phase.phase_order})")
        elif bulk_phase.phase_order == secondary_phase.phase_order:
            print(f"  🚨 ERROR: bulk_packing and secondary_packaging have SAME ORDER ({bulk_phase.phase_order})!")
            return fix_phase_order()
        else:
            print(f"  🚨 ERROR: secondary_packaging ({secondary_phase.phase_order}) comes before bulk_packing ({bulk_phase.phase_order})!")
            return fix_phase_order()
    
    return True

def fix_phase_order():
    print(f"\n🔧 FIXING PHASE ORDER...")
    
    # Get the phases that need fixing
    bulk_phase = ProductionPhase.objects.filter(phase_name='bulk_packing').first()
    secondary_phase = ProductionPhase.objects.filter(phase_name='secondary_packaging').first()
    
    if not bulk_phase or not secondary_phase:
        print("❌ Could not find bulk_packing or secondary_packaging phases!")
        return False
    
    print(f"  Current: bulk_packing={bulk_phase.phase_order}, secondary_packaging={secondary_phase.phase_order}")
    
    # Fix the order: bulk_packing should be 11, secondary_packaging should be 12
    bulk_phase.phase_order = 11
    bulk_phase.save()
    
    secondary_phase.phase_order = 12
    secondary_phase.save()
    
    print(f"  Fixed: bulk_packing=11, secondary_packaging=12")
    
    # Verify the fix
    bulk_phase.refresh_from_db()
    secondary_phase.refresh_from_db()
    
    if bulk_phase.phase_order < secondary_phase.phase_order:
        print(f"  ✅ SUCCESS: Phase order fixed!")
        return True
    else:
        print(f"  ❌ FAILED: Phase order still incorrect!")
        return False

if __name__ == '__main__':
    success = check_and_fix_phase_order()
    
    if success:
        print(f"\n🎉 PHASE ORDER CHECK COMPLETE!")
        print(f"📋 New tablet type 2 BMRs will now have correct workflow order")
    else:
        print(f"\n❌ PHASE ORDER FIX FAILED!")
        print(f"🔧 Manual intervention required")
