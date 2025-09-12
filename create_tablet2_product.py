#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from products.models import Product

# Create a tablet_2 product if it doesn't exist
tablet_2, created = Product.objects.get_or_create(
    product_name="Paracetamol Tablets Type 2",
    defaults={
        'product_type': 'tablet_2',
        'dosage_form': 'tablet',
        'strength': '500mg',
        'is_coated': False,
        'tablet_type': 'tablet_2',
        'is_active': True
    }
)

if created:
    print("Created tablet_2 product for testing")
else:
    # Update to ensure it's tablet_2
    tablet_2.product_type = 'tablet_2'
    tablet_2.tablet_type = 'tablet_2' 
    tablet_2.save()
    print("Updated existing product to tablet_2")

print(f"Product: {tablet_2.product_name} - Type: {tablet_2.product_type}")
