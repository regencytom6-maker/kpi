#!/usr/bin/env python
"""
Script to check existing products and their current batch sizes from BMRs
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from products.models import Product
from bmr.models import BMR
from collections import defaultdict

def check_existing_data():
    print("=== Existing Products ===")
    products = Product.objects.all()
    
    if not products:
        print("No products found in database.")
        return
    
    for product in products:
        print(f"Product: {product.product_name} ({product.product_type})")
        
        # Find BMRs for this product to see what batch sizes were used
        bmrs = BMR.objects.filter(product=product)
        if bmrs:
            batch_sizes = [bmr.batch_size for bmr in bmrs if hasattr(bmr, 'batch_size')]
            if batch_sizes:
                print(f"  Previous batch sizes used: {set(batch_sizes)}")
                print(f"  Most common: {max(set(batch_sizes), key=batch_sizes.count) if batch_sizes else 'N/A'}")
            else:
                print(f"  No batch sizes found in BMRs")
        else:
            print(f"  No BMRs found for this product")
        print()

if __name__ == "__main__":
    check_existing_data()
