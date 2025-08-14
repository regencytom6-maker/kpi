#!/usr/bin/env python
"""
Script to update batch size units for existing products based on product type
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from products.models import Product

def update_batch_units():
    """Update batch size units for existing products"""
    
    print("Updating batch size units for existing products...")
    
    # Get all products
    products = Product.objects.all()
    
    updated_count = 0
    
    for product in products:
        old_unit = product.batch_size_unit
        
        # Set batch_size_unit based on product type
        if product.product_type == 'tablet':
            product.batch_size_unit = 'tablets'
        elif product.product_type == 'capsule':
            product.batch_size_unit = 'capsules'
        elif product.product_type == 'ointment':
            product.batch_size_unit = 'tubes'
        else:
            product.batch_size_unit = 'units'  # Default fallback
        
        # Only save if unit changed
        if old_unit != product.batch_size_unit:
            product.save()
            updated_count += 1
            print(f"Updated {product.product_name}: {old_unit} → {product.batch_size_unit}")
    
    print(f"\nUpdate complete! Updated {updated_count} products.")
    
    # Show summary of all products and their batch units
    print("\nCurrent product batch units:")
    for product in Product.objects.all():
        print(f"- {product.product_name} ({product.get_product_type_display()}): {product.batch_size_unit}")

if __name__ == '__main__':
    update_batch_units()
