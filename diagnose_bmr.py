from bmr.models import BMR
from products.models import Product, ProductMaterial

# BMR that was created with no materials
bmr_number = "BMR20250003"

try:
    bmr = BMR.objects.get(bmr_number=bmr_number)
    product = bmr.product
    
    print(f"Found BMR: {bmr.bmr_number} (Batch: {bmr.batch_number})")
    print(f"Product: {product.product_name} (ID: {product.id})")
    
    # Check if product has raw materials
    product_materials = ProductMaterial.objects.filter(product=product)
    
    if not product_materials.exists():
        print(f"Problem identified: Product '{product.product_name}' has no raw materials associated with it.")
        print("This is why the BMR has no materials - they're derived from the product materials.")
        
        # Check if the product is in the M2M relationship with raw materials
        direct_materials = product.raw_materials.all()
        if direct_materials.exists():
            print(f"However, the product has {direct_materials.count()} raw materials in the direct M2M relationship:")
            for material in direct_materials:
                print(f"- {material.material_name} (Code: {material.material_code})")
            print("But these are not properly associated with quantities in the ProductMaterial model.")
        else:
            print("The product also has no direct M2M relationship with raw materials.")
    else:
        print(f"Product has {product_materials.count()} raw materials:")
        for pm in product_materials:
            print(f"- {pm.raw_material.material_name}: {pm.required_quantity} {pm.unit_of_measure}")
        
        print("\nBMR materials:")
        bmr_materials = bmr.materials.all()
        if bmr_materials.exists():
            for material in bmr_materials:
                print(f"- {material.material_name}: {material.required_quantity} {material.unit_of_measure}")
        else:
            print("BMR has 0 materials - this should not happen if the product has materials.")
            
except BMR.DoesNotExist:
    print(f"BMR {bmr_number} not found")
