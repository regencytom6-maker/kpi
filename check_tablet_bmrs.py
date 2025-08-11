#!/usr/bin/env python
"""
Check BMRs and their workflow statuses for tablets
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db.models import Q
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from products.models import Product

# Check all BMRs for tablets
print("\n=== CHECKING ALL TABLET BMRs ===\n")

tablet_bmrs = BMR.objects.filter(product__product_type='tablet')
print(f"Found {tablet_bmrs.count()} tablet BMRs:")

for bmr in tablet_bmrs:
    print(f"\nBMR {bmr.batch_number}: {bmr.product.product_name}")
    print(f"Product Type: {bmr.product.product_type}")
    print(f"Tablet Type: '{bmr.product.tablet_type}'")
    print(f"Coating Type: '{bmr.product.coating_type}'")
    
    # Check if product name contains "Type 2" or similar
    is_type2_by_name = "type 2" in bmr.product.product_name.lower() or "type2" in bmr.product.product_name.lower()
    if is_type2_by_name:
        print(f"Product appears to be Type 2 based on name")
    
    # Check if this BMR should have bulk packing instead of blister packing
    bulk_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
    blister_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='blister_packing').first()
    secondary_exec = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='secondary_packaging').first()
    
    print("Phase execution statuses:")
    if bulk_exec:
        print(f"- bulk_packing: {bulk_exec.status}")
    else:
        print("- bulk_packing: Not found")
    
    if blister_exec:
        print(f"- blister_packing: {blister_exec.status}")
    else:
        print("- blister_packing: Not found")
    
    if secondary_exec:
        print(f"- secondary_packaging: {secondary_exec.status}")
    else:
        print("- secondary_packaging: Not found")
    
    # Detect if this is a Type 2 BMR based on phase configuration
    if bulk_exec and not blister_exec:
        print("This appears to be a Type 2 tablet (has bulk_packing but no blister_packing)")
    elif not bulk_exec and blister_exec:
        print("This appears to be a Normal tablet (has blister_packing but no bulk_packing)")
    elif bulk_exec and blister_exec:
        print("This has BOTH bulk_packing AND blister_packing (unusual configuration)")
    else:
        print("This has NEITHER bulk_packing NOR blister_packing (incomplete workflow)")
    
    # Check if this BMR has incorrect workflow
    if bulk_exec and secondary_exec:
        if secondary_exec.status not in ['not_ready', 'skipped'] and bulk_exec.status not in ['completed', 'skipped']:
            print("ERROR: Secondary packaging is active but bulk packing is not completed!")
            print("This BMR needs fixing.")
        elif secondary_exec.status == 'pending' and bulk_exec.status == 'not_ready':
            print("ERROR: Secondary packaging is pending but bulk packing is not ready!")
            print("This BMR needs fixing.")
