#!/usr/bin/env python3
"""
Fix the ProductionPhase order in the database
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

def fix_phase_order():
    print("🔧 FIXING PRODUCTION PHASE ORDER")
    print("=" * 40)
    
    # Show current problematic order
    tablet_phases = ProductionPhase.objects.filter(
        product_type='tablet'
    ).order_by('phase_order', 'phase_name')
    
    print("📊 Current Order (BEFORE FIX):")
    for phase in tablet_phases:
        marker = "🚨" if phase.phase_name in ['bulk_packing', 'secondary_packaging'] else "  "
        print(f"   {marker} {phase.phase_order:2d}. {phase.phase_name:25}")
    
    # Fix the order
    print(f"\n🔧 APPLYING FIXES:")
    
    # Set packaging_material_release to order 10
    packaging_phase = ProductionPhase.objects.filter(
        product_type='tablet',
        phase_name='packaging_material_release'
    ).first()
    if packaging_phase:
        packaging_phase.phase_order = 10
        packaging_phase.save()
        print(f"   ✅ packaging_material_release → order 10")
    
    # Set bulk_packing to order 11 (for tablet_2)
    bulk_phase = ProductionPhase.objects.filter(
        product_type='tablet',
        phase_name='bulk_packing'
    ).first()
    if bulk_phase:
        bulk_phase.phase_order = 11
        bulk_phase.save()
        print(f"   ✅ bulk_packing → order 11")
    
    # Set secondary_packaging to order 12 (comes AFTER bulk_packing)
    secondary_phase = ProductionPhase.objects.filter(
        product_type='tablet',
        phase_name='secondary_packaging'
    ).first()
    if secondary_phase:
        secondary_phase.phase_order = 12
        secondary_phase.save()
        print(f"   ✅ secondary_packaging → order 12")
    
    # Set final_qa to order 13
    final_qa_phase = ProductionPhase.objects.filter(
        product_type='tablet',
        phase_name='final_qa'
    ).first()
    if final_qa_phase:
        final_qa_phase.phase_order = 13
        final_qa_phase.save()
        print(f"   ✅ final_qa → order 13")
    
    # Set finished_goods_store to order 14
    fgs_phase = ProductionPhase.objects.filter(
        product_type='tablet',
        phase_name='finished_goods_store'
    ).first()
    if fgs_phase:
        fgs_phase.phase_order = 14
        fgs_phase.save()
        print(f"   ✅ finished_goods_store → order 14")
    
    # Show fixed order
    print(f"\n📊 Fixed Order (AFTER FIX):")
    tablet_phases = ProductionPhase.objects.filter(
        product_type='tablet'
    ).order_by('phase_order', 'phase_name')
    
    for phase in tablet_phases:
        marker = "✅" if phase.phase_name in ['packaging_material_release', 'bulk_packing', 'secondary_packaging'] else "  "
        print(f"   {marker} {phase.phase_order:2d}. {phase.phase_name:25}")
    
    print(f"\n🎉 PHASE ORDER FIXED!")
    print(f"   Now: packaging_material_release (10) → bulk_packing (11) → secondary_packaging (12)")

if __name__ == '__main__':
    fix_phase_order()
