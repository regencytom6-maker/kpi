import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from fgs_management.models import FGSInventory, ProductRelease
from bmr.models import BMR
from products.models import Product
from accounts.models import CustomUser
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Get existing data
print("Setting up test data for analytics...")

# Get some BMRs and products
bmrs = BMR.objects.all()[:5]
products = Product.objects.all()[:3]
qa_user = CustomUser.objects.filter(role='qa').first()

if not qa_user:
    print("No QA user found")
    exit()

# Create sample inventory with different statuses
statuses = ['available', 'released', 'quarantine', 'expired']
locations = ['Warehouse A-1', 'Warehouse A-2', 'Warehouse B-1', 'Warehouse B-2', 'Cold Storage']

for i, bmr in enumerate(bmrs):
    status = random.choice(statuses)
    location = random.choice(locations)
    
    # Create inventory with varying quantities and dates
    base_date = timezone.now().date() - timedelta(days=random.randint(1, 90))
    expiry_date = base_date + timedelta(days=random.randint(365, 730))
    
    inventory, created = FGSInventory.objects.get_or_create(
        bmr=bmr,
        defaults={
            'product': bmr.product,
            'batch_number': f"BATCH{2025}{str(i+1).zfill(3)}",
            'quantity_produced': random.randint(5000, 20000),
            'quantity_available': random.randint(1000, 15000),
            'unit_of_measure': random.choice(['tablets', 'capsules', 'bottles', 'vials']),
            'storage_location': location,
            'shelf_life_months': 24,
            'expiry_date': expiry_date,
            'status': status,
            'created_by': qa_user,
            'storage_date': base_date,
        }
    )
    
    if created:
        print(f"Created inventory: {inventory.batch_number} - {inventory.quantity_available} {inventory.unit_of_measure}")
        
        # Create some releases for available inventory
        if status == 'available' and random.choice([True, False]):
            release_quantity = random.randint(100, 2000)
            release = ProductRelease.objects.create(
                inventory=inventory,
                quantity_released=release_quantity,
                release_type=random.choice(['sale', 'distribution', 'transfer']),
                release_reference=f"REL{2025}{str(i+1).zfill(4)}",
                destination=random.choice(['Pharmacy A', 'Hospital B', 'Clinic C', 'Distributor D']),
                notes=f"Sample release for batch {inventory.batch_number}",
                released_by=qa_user,
                release_date=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            
            # Update inventory quantity
            inventory.quantity_available -= release_quantity
            inventory.save()
            
            print(f"  - Created release: {release.release_reference} ({release_quantity} units)")

print("Test data setup complete!")
print(f"Total inventory items: {FGSInventory.objects.count()}")
print(f"Total releases: {ProductRelease.objects.count()}")
