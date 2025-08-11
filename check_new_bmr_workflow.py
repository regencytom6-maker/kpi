#!/usr/bin/env python3
"""
Check workflow order for newly created BMRs
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
from products.models import Product

print("🔍 CHECKING NEW BMR WORKFLOW ORDER")
print("=" * 50)

# Check the most recent BMRs
recent_bmrs = BMR.objects.filter(
    product__product_type='tablet',
    product__tablet_type='tablet_2'
).order_by('-created_date')[:3]

for bmr in recent_bmrs:
    print(f"\n📋 BMR: {bmr.batch_number} - {bmr.product.product_name}")
    print(f"   Created: {bmr.created_date}")
    
    # Get all phases for this BMR in order
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    
    print(f"   📊 Workflow Order:")
    packaging_found = False
    bulk_found = False
    secondary_found = False
    
    for phase in phases:
        print(f"      {phase.phase.phase_order:2d}. {phase.phase.phase_name:25} - {phase.status}")
        
        if phase.phase.phase_name == 'packaging_material_release':
            packaging_found = True
            packaging_order = phase.phase.phase_order
        elif phase.phase.phase_name == 'bulk_packing':
            bulk_found = True
            bulk_order = phase.phase.phase_order
        elif phase.phase.phase_name == 'secondary_packaging':
            secondary_found = True
            secondary_order = phase.phase.phase_order
    
    # Check the order
    if packaging_found and bulk_found and secondary_found:
        print(f"\n   🔍 Order Analysis:")
        print(f"      Packaging Material Release: {packaging_order}")
        print(f"      Bulk Packing: {bulk_order}")
        print(f"      Secondary Packaging: {secondary_order}")
        
        if packaging_order < bulk_order < secondary_order:
            print(f"      ✅ CORRECT: packaging → bulk → secondary")
        else:
            print(f"      ❌ WRONG ORDER!")
            if bulk_order > secondary_order:
                print(f"         🚨 ERROR: bulk_packing ({bulk_order}) comes AFTER secondary_packaging ({secondary_order})")

# Also check the ProductionPhase definitions
print(f"\n🏭 CHECKING PRODUCTION PHASE DEFINITIONS:")
tablet_phases = ProductionPhase.objects.filter(
    product_type='tablet'
).order_by('phase_order')

print(f"   Tablet workflow phases:")
for phase in tablet_phases:
    print(f"      {phase.phase_order:2d}. {phase.phase_name:25} - {phase.product_type}")
    if phase.phase_name in ['packaging_material_release', 'bulk_packing', 'secondary_packaging']:
        print(f"          ⚠️  CRITICAL PHASE")
