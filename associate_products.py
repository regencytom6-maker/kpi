"""
Utility script for managing product-material associations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db import transaction
from products.models import Product
from raw_materials.models import RawMaterial
from products.models_material import ProductMaterial

def associate_products_with_materials():
    """Associate each product with at least one material (Legacy method)"""
    
    materials = RawMaterial.objects.all()
    products = Product.objects.all()
    
    if not materials.exists():
        print("No materials found in database!")
        return
        
    if not products.exists():
        print("No products found in database!")
        return
    
    # Associate each product with at least one material
    for i, product in enumerate(products):
        # Get some materials to associate with this product
        material_count = min(3, materials.count())
        materials_to_associate = materials[i % materials.count():i % materials.count() + material_count]
        
        # Print what we're doing
        print(f"Associating product '{product.product_name}' with materials:")
        
        for material in materials_to_associate:
            # Add association
            product.raw_materials.add(material)
            print(f"  - {material.material_name}")
    
        # Save the product
        product.save()
        
    print("\nAssociation complete!")
    print(f"Associated {products.count()} products with materials")

def associate_material_to_product(product_name, material_code, quantity=1.0, unit_of_measure=None, is_active=False, notes=None):
    """
    Associate a raw material to a product
    
    Args:
        product_name (str): Name of the product
        material_code (str): Material code
        quantity (float): Required quantity
        unit_of_measure (str): Unit of measure. If None, will use the material's default
        is_active (bool): Whether this is an active ingredient
        notes (str): Optional notes
    
    Returns:
        ProductMaterial: The created or updated relationship
    """
    try:
        # Find the product and material
        product = Product.objects.get(product_name=product_name)
        material = RawMaterial.objects.get(material_code=material_code)
        
        # Use the material's unit if none provided
        if not unit_of_measure:
            unit_of_measure = material.unit_of_measure
        
        # Create or update the relationship
        product_material, created = ProductMaterial.objects.update_or_create(
            product=product,
            raw_material=material,
            defaults={
                'required_quantity': quantity,
                'unit_of_measure': unit_of_measure,
                'is_active_ingredient': is_active,
                'notes': notes
            }
        )
        
        if created:
            print(f"Created new relationship: {product_material}")
        else:
            print(f"Updated existing relationship: {product_material}")
            
        return product_material
    
    except Product.DoesNotExist:
        print(f"Error: Product '{product_name}' not found")
        return None
    except RawMaterial.DoesNotExist:
        print(f"Error: Material '{material_code}' not found")
        return None

def list_products_with_materials():
    """
    List all products and their associated materials
    """
    products = Product.objects.prefetch_related('product_materials__raw_material').all()
    
    print(f"Found {products.count()} products")
    print("=" * 80)
    
    for product in products:
        print(f"{product.product_name} ({product.product_type}):")
        materials = product.product_materials.all()
        
        if materials:
            print("  Materials:")
            for pm in materials:
                active_str = " (ACTIVE)" if pm.is_active_ingredient else ""
                print(f"  - {pm.raw_material.material_name} ({pm.raw_material.material_code}): {pm.required_quantity} {pm.unit_of_measure}{active_str}")
        else:
            print("  No materials associated")
        
        print("-" * 80)
    
def list_materials_with_products():
    """
    List all raw materials and the products they're used in
    """
    materials = RawMaterial.objects.prefetch_related('product_materials__product').all()
    
    print(f"Found {materials.count()} raw materials")
    print("=" * 80)
    
    for material in materials:
        print(f"{material.material_name} ({material.material_code}):")
        product_materials = material.product_materials.all()
        
        if product_materials:
            print("  Used in products:")
            for pm in product_materials:
                print(f"  - {pm.product.product_name}: {pm.required_quantity} {pm.unit_of_measure}")
        else:
            print("  Not used in any products")
        
        print("-" * 80)

if __name__ == "__main__":
    # Example usage - uncomment the function you want to use
    # associate_products_with_materials()  # Legacy function using M2M
    # associate_material_to_product("ACTIZINE TABLETS 100 BLISTER", "RAW-ACT-371", 10.0, "mg", True, "Active ingredient")
    list_products_with_materials()
    # list_materials_with_products()
