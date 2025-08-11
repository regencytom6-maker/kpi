#!/usr/bin/env python
"""
Check tablet products and their types in the database
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from products.models import Product

# Get all tablet products
tablet_products = Product.objects.filter(product_type='tablet')
print(f"Found {tablet_products.count()} tablet products:")

for product in tablet_products:
    print(f"- {product.product_name}")
    print(f"  * Tablet Type: '{product.tablet_type}' ({type(product.tablet_type)})")
    print(f"  * Coating Type: '{product.coating_type}' ({type(product.coating_type)})")
    print("")

# Check specifically for tablet_2
tablet2_products = Product.objects.filter(product_type='tablet', tablet_type='tablet_2')
print(f"\nFound {tablet2_products.count()} tablet_2 products:")
for product in tablet2_products:
    print(f"- {product.product_name}")

# Try other possibilities
print("\nTrying other potential tablet type values:")
for possible_type in ['2', 'type_2', 'Type 2']:
    count = Product.objects.filter(product_type='tablet', tablet_type=possible_type).count()
    print(f"- '{possible_type}': {count} products")

# List all unique tablet_type values
print("\nAll unique tablet_type values in the database:")
unique_types = Product.objects.filter(product_type='tablet').values_list('tablet_type', flat=True).distinct()
for t in unique_types:
    count = Product.objects.filter(tablet_type=t).count()
    print(f"- '{t}': {count} products")
