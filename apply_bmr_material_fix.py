import os
import django
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from bmr.models import BMR
from products.models import Product, ProductMaterial
from raw_materials.models import RawMaterial
from decimal import Decimal

def fix_product_materials():
    # Find the specific product
    try:
        product = Product.objects.get(id=67)  # ACTIZINE TABLETS 100 BLISTER UG
        print(f"Found product: {product.product_name} (ID: {product.id})")
        
        # Check current raw materials
        raw_materials = product.raw_materials.all()
        print(f"Product has {raw_materials.count()} raw materials in M2M relationship:")
        for material in raw_materials:
            print(f"- {material.material_name} (Code: {material.material_code})")
        
        # Check current ProductMaterial entries
        product_materials = ProductMaterial.objects.filter(product=product)
        print(f"Product has {product_materials.count()} ProductMaterial entries:")
        for pm in product_materials:
            print(f"- {pm.raw_material.material_name}: {pm.required_quantity} {pm.unit_of_measure}")
        
        # Create ProductMaterial entries for any missing materials
        for material in raw_materials:
            pm, created = ProductMaterial.objects.get_or_create(
                product=product,
                raw_material=material,
                defaults={
                    'required_quantity': Decimal('1.0'),
                    'unit_of_measure': material.unit_of_measure,
                    'is_active_ingredient': material.category == 'active'
                }
            )
            
            if created:
                print(f"Created new ProductMaterial entry for {material.material_name} with quantity {pm.required_quantity} {pm.unit_of_measure}")
        
        # Check if it worked
        product_materials_after = ProductMaterial.objects.filter(product=product)
        print(f"\nAfter fix, product has {product_materials_after.count()} ProductMaterial entries:")
        for pm in product_materials_after:
            print(f"- {pm.raw_material.material_name}: {pm.required_quantity} {pm.unit_of_measure}")
        
        # Find the BMR and fix it
        bmr = BMR.objects.get(bmr_number="BMR20250003")
        print(f"\nFound BMR: {bmr.bmr_number} (Batch: {bmr.batch_number})")
        
        # Check current BMR materials
        bmr_materials = bmr.materials.all()
        print(f"BMR has {bmr_materials.count()} materials:")
        for material in bmr_materials:
            print(f"- {material.material_name}: {material.required_quantity} {material.unit_of_measure}")
        
        # Recreate BMR materials from product
        bmr.create_materials_from_product()
        
        # Check if it worked
        bmr_materials_after = bmr.materials.all()
        print(f"\nAfter fix, BMR has {bmr_materials_after.count()} materials:")
        for material in bmr_materials_after:
            print(f"- {material.material_name}: {material.required_quantity} {material.unit_of_measure}")
        
        return True
        
    except Product.DoesNotExist:
        print("Product with ID 67 not found")
        return False
    except BMR.DoesNotExist:
        print("BMR with number BMR20250003 not found")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_product_materials()
    if success:
        print("\nFix completed successfully!")
    else:
        print("\nFix failed.")
