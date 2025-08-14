#!/usr/bin/env python
"""
Test script to verify packaging unit calculations
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

def test_packaging_calculations():
    """Test packaging unit calculations for different products"""
    
    print("Testing packaging unit calculations...")
    print("=" * 50)
    
    # Get some products and show packaging calculations
    products = Product.objects.all()
    
    for product in products:
        print(f"\n📦 Product: {product.product_name}")
        print(f"   Type: {product.get_product_type_display()}")
        print(f"   Batch Size Unit: {product.batch_size_unit}")
        print(f"   Standard Batch Size: {product.standard_batch_size}")
        
        if product.packaging_size_in_units:
            print(f"   Packaging Size: {product.packaging_size_in_units} units per package")
            
            # Calculate number of packages needed
            packages_needed = int(product.standard_batch_size / product.packaging_size_in_units)
            print(f"   📊 Packages needed for standard batch: {packages_needed} packages")
        else:
            print(f"   ⚠️  Packaging size not set")
    
    print("\n" + "=" * 50)
    print("BMR Packaging Examples:")
    print("=" * 50)
    
    # Show some BMR examples
    bmrs = BMR.objects.select_related('product').all()[:3]
    
    for bmr in bmrs:
        print(f"\n🧾 BMR: {bmr.batch_number}")
        print(f"   Product: {bmr.product.product_name}")
        print(f"   Batch Size: {bmr.batch_size} {bmr.batch_size_unit}")
        
        if bmr.product.packaging_size_in_units:
            packages_needed = int(bmr.batch_size / bmr.product.packaging_size_in_units)
            print(f"   📦 Packaging units needed: {packages_needed} packages")
            print(f"   💡 Each package contains: {bmr.product.packaging_size_in_units} units")
        else:
            print(f"   ⚠️  Packaging size not configured for this product")

if __name__ == '__main__':
    test_packaging_calculations()
