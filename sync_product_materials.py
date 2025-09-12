"""
Script to synchronize ProductMaterial entries with raw_materials M2M field.
This ensures that any existing relationships are correctly reflected in both systems.
"""
from django.db import transaction
from products.models import Product, ProductMaterial
from raw_materials.models import RawMaterial

def run():
    # Get all products with ProductMaterial entries
    products = Product.objects.prefetch_related('product_materials').all()
    print(f"Found {products.count()} products to process")
    
    # Synchronize each product's raw materials with ProductMaterial entries
    updated_count = 0
    for product in products:
        print(f"Processing {product.product_name}")
        
        # Clear existing raw_materials to prevent duplicates
        initial_count = product.raw_materials.count()
        if initial_count > 0:
            print(f"- Found {initial_count} existing raw materials")
        
        # Add all materials from ProductMaterial to raw_materials
        for product_material in product.product_materials.all():
            product.raw_materials.add(product_material.raw_material)
            print(f"- Added {product_material.raw_material.material_name} to raw_materials")
            updated_count += 1
    
    print(f"Synchronization complete. Added {updated_count} materials to raw_materials relationships.")

if __name__ == "__main__":
    with transaction.atomic():
        run()
