"""
This script lists all products in the system and their associated raw materials,
helping to identify any inconsistencies between the M2M relationship and ProductMaterial model.

Copy and paste this into Django shell or save as a management command.
"""

from products.models import Product, ProductMaterial
from raw_materials.models import RawMaterial
from decimal import Decimal

def list_products_and_materials():
    """List all products and their raw materials"""
    
    print("=" * 100)
    print(f"{'PRODUCT ID':<10} {'PRODUCT NAME':<40} {'TYPE':<15} {'BATCH SIZE':<15} {'UNIT':<10}")
    print("=" * 100)
    
    # Get all products
    products = Product.objects.all().order_by('id')
    
    for product in products:
        # Print product info
        print(f"{product.id:<10} {product.product_name[:40]:<40} {product.product_type:<15} {product.standard_batch_size:<15} {product.batch_size_unit:<10}")
        
        # Check M2M raw materials
        m2m_raw_materials = product.raw_materials.all()
        
        # Check ProductMaterial entries
        product_materials = ProductMaterial.objects.filter(product=product)
        
        # Check if the counts match
        if m2m_raw_materials.count() != product_materials.count():
            print(f"  [WARNING] M2M count ({m2m_raw_materials.count()}) doesn't match ProductMaterial count ({product_materials.count()})")
        
        # Print raw materials info
        if m2m_raw_materials.exists():
            print(f"\n  {'MATERIAL ID':<12} {'MATERIAL NAME':<40} {'CODE':<15} {'IN M2M':<8} {'IN PM':<8} {'QTY':<10} {'UNIT':<10} {'AVAILABLE':<15}")
            print("  " + "-" * 98)
            
            # Combine both sets for display
            all_materials = set()
            for mat in m2m_raw_materials:
                all_materials.add(mat.id)
            for pm in product_materials:
                all_materials.add(pm.raw_material.id)
            
            # Sort materials by ID for consistency
            all_materials = sorted(all_materials)
            
            for material_id in all_materials:
                material = RawMaterial.objects.get(id=material_id)
                
                # Check if in M2M
                in_m2m = "Yes" if material in m2m_raw_materials else "No"
                
                # Check if in ProductMaterial
                pm_entry = product_materials.filter(raw_material=material).first()
                in_pm = "Yes" if pm_entry else "No"
                
                # Get quantity from ProductMaterial
                qty = pm_entry.required_quantity if pm_entry else "N/A"
                unit = pm_entry.unit_of_measure if pm_entry else "N/A"
                
                # Get available quantity
                available = material.current_stock
                
                print(f"  {material.id:<12} {material.material_name[:40]:<40} {material.material_code:<15} "
                      f"{in_m2m:<8} {in_pm:<8} {qty:<10} {unit:<10} {available:<15}")
        else:
            print(f"\n  No raw materials associated with this product.")
            
        print("\n" + "-" * 100)

if __name__ == "__main__":
    list_products_and_materials()
    
# Execute when running in Django shell
list_products_and_materials()
