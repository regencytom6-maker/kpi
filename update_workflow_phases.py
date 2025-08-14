#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import ProductionPhase, BatchPhaseExecution
from workflow.services import WorkflowService

print("=== Adding Raw Material Release Phase to Existing BMRs ===")

# Get all existing BMRs
bmrs = BMR.objects.all()
print(f"Found {bmrs.count()} BMRs to update")

updated_count = 0
for bmr in bmrs:
    print(f"\nProcessing BMR {bmr.batch_number}...")
    
    # Check if raw_material_release phase already exists
    existing_release_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='raw_material_release'
    ).first()
    
    if existing_release_phase:
        print(f"  ✓ Raw material release phase already exists")
        continue
    
    # Get the product type
    product_type = bmr.product.product_type
    
    # Get or create the raw_material_release production phase
    release_phase, created = ProductionPhase.objects.get_or_create(
        product_type=product_type,
        phase_name='raw_material_release',
        defaults={
            'phase_order': 3,  # After BMR creation (1) and regulatory approval (2)
            'is_mandatory': True,
            'requires_approval': False
        }
    )
    
    if created:
        print(f"  ✓ Created raw_material_release phase definition for {product_type}")
    
    # Check if regulatory approval is completed
    regulatory_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='regulatory_approval'
    ).first()
    
    if regulatory_phase and regulatory_phase.status == 'completed':
        # Regulatory is done, so raw material release should be pending
        initial_status = 'pending'
        print(f"  → Raw material release will be PENDING (regulatory approved)")
    else:
        # Regulatory not done yet, so raw material release should be not_ready
        initial_status = 'not_ready'
        print(f"  → Raw material release will be NOT_READY (regulatory pending)")
    
    # Create the batch phase execution
    BatchPhaseExecution.objects.create(
        bmr=bmr,
        phase=release_phase,
        status=initial_status
    )
    
    # Update material_dispensing phase to be not_ready (will be activated by release completion)
    dispensing_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='material_dispensing'
    ).first()
    
    if dispensing_phase and dispensing_phase.status == 'pending':
        dispensing_phase.status = 'not_ready'
        dispensing_phase.save()
        print(f"  → Updated material_dispensing to NOT_READY (will be activated by release)")
    
    updated_count += 1
    print(f"  ✓ Added raw_material_release phase with status: {initial_status}")

print(f"\n=== Summary ===")
print(f"Updated {updated_count} BMRs with raw_material_release phase")
print(f"Total BMRs processed: {bmrs.count()}")

print(f"\n=== Workflow Status ===")
for bmr in BMR.objects.all()[:5]:  # Show first 5 as example
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
    print(f"\nBMR {bmr.batch_number}:")
    for phase in phases:
        print(f"  {phase.phase.phase_name}: {phase.status}")
