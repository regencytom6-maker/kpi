#!/usr/bin/env python3
"""
Simple check for BMRs and workflow status
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
from products.models import Product

print("System Status Check:")
print(f"Total BMRs: {BMR.objects.count()}")
print(f"Total Products: {Product.objects.count()}")
print(f"Total Phase Executions: {BatchPhaseExecution.objects.count()}")

# Check recent BMRs
recent_bmrs = BMR.objects.all().order_by('-created_date')[:5]
print(f"\nRecent BMRs:")
for bmr in recent_bmrs:
    product_type = bmr.product.product_type if bmr.product else 'Unknown'
    tablet_type = getattr(bmr.product, 'tablet_type', 'N/A') if bmr.product else 'N/A'
    print(f"  {bmr.batch_number} - {product_type} - tablet_type: {tablet_type}")

# Look for tablet type 2 specifically
tablet_2_products = Product.objects.filter(tablet_type='tablet_2')
print(f"\nTablet Type 2 Products: {tablet_2_products.count()}")
for product in tablet_2_products:
    print(f"  {product.product_name} - {product.product_type}")

# Check if there are any BMRs with these products
if tablet_2_products.exists():
    tablet_2_bmrs = BMR.objects.filter(product__in=tablet_2_products)
    print(f"\nTablet Type 2 BMRs: {tablet_2_bmrs.count()}")
    for bmr in tablet_2_bmrs[:3]:
        print(f"  {bmr.batch_number} - {bmr.product.product_name}")
        
        # Check packaging material release phase
        packaging_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='packaging_material_release'
        ).first()
        
        if packaging_phase:
            print(f"    Packaging Material Release: {packaging_phase.status}")
            
        # Check bulk packing phase
        bulk_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='bulk_packing'
        ).first()
        
        if bulk_phase:
            print(f"    Bulk Packing: {bulk_phase.status}")
            
        # Check secondary packaging phase
        secondary_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='secondary_packaging'
        ).first()
        
        if secondary_phase:
            print(f"    Secondary Packaging: {secondary_phase.status}")
