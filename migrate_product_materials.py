"""
Script to migrate from Product.raw_materials M2M relationship to ProductMaterial model
"""
from django.db import transaction
from products.models import Product
from products.models_material import ProductMaterial
from raw_materials.models import RawMaterial

def run():
    # Get all products with raw materials defined
    products = Product.objects.prefetch_related('raw_materials').all()
    print(f"Found {products.count()} products to process")
    
    # Migrate each product's raw materials to the new model
    created_count = 0
    for product in products:
        print(f"Processing {product.product_name}")
        raw_materials = product.raw_materials.all()
        print(f"- Found {raw_materials.count()} raw materials")
        
        for raw_material in raw_materials:
            # Check if a ProductMaterial already exists
            product_material, created = ProductMaterial.objects.get_or_create(
                product=product,
                raw_material=raw_material,
                defaults={
                    'required_quantity': 1.0,  # Default quantity
                    'unit_of_measure': raw_material.unit_of_measure,
                    'is_active_ingredient': raw_material.category == 'active'
                }
            )
            
            if created:
                print(f"- Created relationship for {raw_material.material_name}")
                created_count += 1
    
    print(f"Migration complete. Created {created_count} new product-material relationships.")

if __name__ == "__main__":
    with transaction.atomic():
        run()
