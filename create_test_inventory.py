import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from fgs_management.models import FGSInventory
from bmr.models import BMR
from products.models import Product
from accounts.models import CustomUser
from datetime import datetime, timedelta
from django.utils import timezone

# Get a sample BMR and create inventory
bmr = BMR.objects.first()
if bmr:
    # Create sample inventory
    inventory, created = FGSInventory.objects.get_or_create(
        bmr=bmr,
        defaults={
            'product': bmr.product,
            'batch_number': bmr.batch_number,
            'quantity_produced': 10000,
            'quantity_available': 10000,
            'unit_of_measure': 'tablets',
            'storage_location': 'Main Warehouse A-1-2',
            'shelf_life_months': 24,
            'expiry_date': timezone.now().date() + timedelta(days=24*30),
            'status': 'available',
            'created_by': CustomUser.objects.filter(role='qa').first()
        }
    )
    if created:
        print(f'Created inventory for batch {bmr.batch_number}: {inventory.quantity_available} {inventory.unit_of_measure}')
    else:
        print(f'Inventory already exists for batch {bmr.batch_number}')
        
    # Show inventory info
    print(f'Product: {inventory.product.name}')
    print(f'Batch: {inventory.batch_number}')
    print(f'Available: {inventory.quantity_available} {inventory.unit_of_measure}')
    print(f'Location: {inventory.storage_location}')
    print(f'Expiry: {inventory.expiry_date}')
    
else:
    print('No BMR found to create inventory')
