"""
Script to create missing active ingredients for products
"""
from raw_materials.models import RawMaterial, RawMaterialBatch, RawMaterialQC
from bmr.models import BMR
from django.utils import timezone

# Get all BMRs with unapproved materials
bmrs = BMR.objects.filter(materials_approved=False)
print(f"Found {bmrs.count()} BMRs with unapproved materials")

# No category model available, we'll just set category as a string
category = "Active Ingredients"
print(f"Using category: {category}")

# Helper function to create material and batch
def create_material_and_batch(code, name):
    # Create material if it doesn't exist
    material, created = RawMaterial.objects.get_or_create(
        material_code=code,
        defaults={
            "material_name": name,
            "description": f"Active ingredient for {name}",
            "category": category,
            "unit_of_measure": "kg",
            "reorder_level": 10.0
        }
    )
    
    if created:
        print(f"Created new material: {material.material_name} ({material.material_code})")
    else:
        print(f"Material already exists: {material.material_name} ({material.material_code})")
    
    # Create a batch with approved status
    batch, batch_created = RawMaterialBatch.objects.get_or_create(
        material=material,
        batch_number=f"BATCH-{code}-20250901",
        defaults={
            "quantity_received": 100.0,
            "quantity_remaining": 100.0,
            "supplier": "KPI Supplier",
            "received_date": timezone.now().date(),
            "manufacturing_date": (timezone.now() - timezone.timedelta(days=30)).date(),
            "expiry_date": (timezone.now() + timezone.timedelta(days=365)).date(),
            "status": "approved",
            "approved_date": timezone.now(),
            "approved_by_id": 1,  # Assuming user ID 1 exists
            "received_by_id": 1   # Assuming user ID 1 exists
        }
    )
    
    if batch_created:
        print(f"Created new batch: {batch.batch_number}")
    else:
        print(f"Batch already exists: {batch.batch_number}")
    
    # Create QC test for the batch if it doesn't exist
    qc_test, qc_created = RawMaterialQC.objects.get_or_create(
        material_batch=batch,
        defaults={
            "test_date": timezone.now().date(),
            "appearance_result": "pass",
            "identification_result": "pass",
            "assay_result": "pass",
            "purity_result": "pass",
            "final_result": "pass",
            "status": "completed",
            "started_date": timezone.now().date(),
            "completed_date": timezone.now().date(),
            "test_notes": "Auto-created QC test for missing active ingredient",
            "tested_by_id": 1,  # Assuming user ID 1 exists
            "started_by_id": 1,  # Assuming user ID 1 exists
            "completed_by_id": 1,  # Assuming user ID 1 exists
            "approved_by_id": 1   # Assuming user ID 1 exists
        }
    )
    
    if qc_created:
        print(f"Created QC test for batch: {batch.batch_number}")
    else:
        print(f"QC test already exists for batch: {batch.batch_number}")
    
    return material, batch, qc_test

# Process each BMR and create missing materials
for bmr in bmrs:
    print(f"\nProcessing BMR: {bmr.batch_number} - {bmr.product.product_name}")
    
    for bmr_material in bmr.materials.all():
        code = bmr_material.material_code
        name = bmr_material.material_name
        
        if "RAW-ACT" in code:
            print(f"Found missing active ingredient: {name} ({code})")
            material, batch, qc_test = create_material_and_batch(code, name)

print("\nMaterial creation complete!")
