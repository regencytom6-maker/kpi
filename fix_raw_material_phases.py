#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import ProductionPhase, BatchPhaseExecution

print("=== Quick Fix: Adding Raw Material Release Phases ===")

# First, ensure raw_material_release ProductionPhases exist for all product types
product_types = BMR.objects.values_list('product__product_type', flat=True).distinct()
print(f"Product types in system: {list(product_types)}")

for product_type in product_types:
    release_phase, created = ProductionPhase.objects.get_or_create(
        product_type=product_type,
        phase_name='raw_material_release',
        defaults={
            'phase_order': 3,
            'is_mandatory': True,
            'requires_approval': False
        }
    )
    if created:
        print(f"✓ Created raw_material_release phase for {product_type}")
    else:
        print(f"- raw_material_release phase already exists for {product_type}")

# Now add BatchPhaseExecution for approved BMRs
approved_bmrs = BMR.objects.filter(status='approved')
print(f"\nProcessing {approved_bmrs.count()} approved BMRs...")

for bmr in approved_bmrs:
    # Check if already has raw material release phase
    existing = BatchPhaseExecution.objects.filter(
        bmr=bmr, 
        phase__phase_name='raw_material_release'
    ).exists()
    
    if existing:
        print(f"- {bmr.bmr_number}: Already has raw material release phase")
        continue
    
    # Get the production phase for this product type
    try:
        production_phase = ProductionPhase.objects.get(
            product_type=bmr.product.product_type,
            phase_name='raw_material_release'
        )
        
        # Create the batch phase execution as pending (ready for store manager)
        BatchPhaseExecution.objects.create(
            bmr=bmr,
            phase=production_phase,
            status='pending'  # Ready for store manager to work on
        )
        print(f"✓ {bmr.bmr_number}: Added raw material release phase (PENDING)")
        
    except ProductionPhase.DoesNotExist:
        print(f"✗ {bmr.bmr_number}: No production phase found for {bmr.product.product_type}")

print("\n=== Verification ===")
# Check results
for bmr in approved_bmrs[:3]:
    raw_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr, 
        phase__phase_name='raw_material_release'
    ).first()
    if raw_phase:
        print(f"{bmr.bmr_number}: raw_material_release = {raw_phase.status}")
    else:
        print(f"{bmr.bmr_number}: NO raw_material_release phase")

print("\nDone!")
