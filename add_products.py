#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kpi.settings')
django.setup()

# Import models after Django setup
from products.models import Product

def add_sample_products():
    """Add sample pharmaceutical products to the database"""
    
    sample_products = [
        {
            'product_name': 'Paracetamol 500mg',
            'product_type': 'tablet',
            'standard_batch_size': 100000,
            'batch_size_unit': 'tablets'
        },
        {
            'product_name': 'Amoxicillin 250mg',
            'product_type': 'capsule',
            'standard_batch_size': 50000,
            'batch_size_unit': 'capsules'
        },
        {
            'product_name': 'Ibuprofen 400mg',
            'product_type': 'tablet',
            'standard_batch_size': 75000,
            'batch_size_unit': 'tablets'
        },
        {
            'product_name': 'Vitamin C Syrup',
            'product_type': 'liquid',
            'standard_batch_size': 1000,
            'batch_size_unit': 'L'
        },
        {
            'product_name': 'Diazepam 5mg',
            'product_type': 'tablet',
            'standard_batch_size': 50000,
            'batch_size_unit': 'tablets'
        },
        {
            'product_name': 'Omeprazole 20mg',
            'product_type': 'capsule',
            'standard_batch_size': 60000,
            'batch_size_unit': 'capsules'
        },
        {
            'product_name': 'Hydrocortisone Cream 1%',
            'product_type': 'cream',
            'standard_batch_size': 500,
            'batch_size_unit': 'kg'
        },
        {
            'product_name': 'Metronidazole 400mg',
            'product_type': 'tablet',
            'standard_batch_size': 80000,
            'batch_size_unit': 'tablets'
        },
        {
            'product_name': 'Insulin 100IU',
            'product_type': 'injection',
            'standard_batch_size': 10000,
            'batch_size_unit': 'units'
        },
    ]
    
    print("Adding sample products:")
    count = 0
    
    for product_data in sample_products:
        # Check if product already exists
        if not Product.objects.filter(product_name=product_data['product_name']).exists():
            product = Product.objects.create(**product_data)
            print(f"Created: {product.product_name} ({product.get_product_type_display()})")
            count += 1
        else:
            print(f"Skipped (already exists): {product_data['product_name']}")
    
    print(f"\n{count} sample products added to the database.")

if __name__ == "__main__":
    add_sample_products()
