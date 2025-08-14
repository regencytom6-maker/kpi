#!/usr/bin/env python
"""
Test script to verify the new batch size units are working correctly
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from products.models import Product
from bmr.models import BMR

def test_batch_units():
    """Test that batch size units are working correctly"""
    
    print("Testing batch size units...")
    print("\n=== Product Batch Units ===")
    
    # Show all products and their batch units
    for product in Product.objects.all():
        print(f"- {product.product_name} ({product.get_product_type_display()})")
        print(f"  Batch Size Unit: {product.batch_size_unit}")
        print(f"  Standard Batch Size: {product.standard_batch_size} {product.batch_size_unit}")
        if product.packaging_size_in_units:
            print(f"  Packaging Size: {product.packaging_size_in_units} units per package")
        else:
            print(f"  Packaging Size: Not set")
        print()
    
    print("\n=== BMR Batch Units ===")
    
    # Show some BMRs and their batch units
    bmrs = BMR.objects.select_related('product').all()[:5]  # First 5 BMRs
    for bmr in bmrs:
        print(f"- BMR {bmr.batch_number} ({bmr.product.product_name})")
        print(f"  Product Type: {bmr.product.get_product_type_display()}")
        print(f"  Batch Size: {bmr.batch_size} {bmr.batch_size_unit}")
        print()
    
    print("Test completed successfully!")

if __name__ == '__main__':
    test_batch_units()
