#!/usr/bin/env python
"""
Script to set realistic batch sizes for products based on their type
Run this after the migration is complete
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from products.models import Product

def set_realistic_batch_sizes():
    """Set realistic batch sizes based on product type"""
    
    print("Setting realistic batch sizes for products...")
    
    products = Product.objects.all()
    
    if not products:
        print("No products found in database.")
        return
    
    for product in products:
        old_batch_size = getattr(product, 'standard_batch_size', None)
        
        # Set batch size based on product type
        if product.product_type == 'tablet':
            product.standard_batch_size = 25000
            product.batch_size_unit = 'units'
            product.minimum_batch_size = 10000
            product.maximum_batch_size = 50000
        elif product.product_type == 'ointment':
            product.standard_batch_size = 250
            product.batch_size_unit = 'kg'
            product.minimum_batch_size = 100
            product.maximum_batch_size = 500
        elif product.product_type == 'capsule':
            product.standard_batch_size = 15000
            product.batch_size_unit = 'units'
            product.minimum_batch_size = 5000
            product.maximum_batch_size = 30000
        else:
            product.standard_batch_size = 1000
            product.batch_size_unit = 'units'
            product.minimum_batch_size = 500
            product.maximum_batch_size = 2000
        
        product.save()
        
        print(f"✓ {product.product_name} ({product.product_type}): "
              f"{product.standard_batch_size} {product.batch_size_unit} "
              f"(was: {old_batch_size})")
    
    print(f"\nUpdated {products.count()} products with realistic batch sizes.")
    print("\nRecommendations:")
    print("1. Review these batch sizes through Django Admin")
    print("2. Adjust based on your actual production requirements")
    print("3. Consider regulatory requirements for batch sizes")

if __name__ == "__main__":
    set_realistic_batch_sizes()
