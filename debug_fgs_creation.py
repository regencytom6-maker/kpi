#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from fgs_management.models import FGSInventory
from bmr.models import BMR
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def test_fgs_creation():
    try:
        # Get a BMR with ID 4961
        bmr = BMR.objects.get(id=4961)
        print(f"BMR: {bmr.batch_number}, Product: {bmr.product.product_name}")
        print(f"Batch size: {bmr.batch_size} {bmr.batch_size_unit}")
        
        # Get a user
        user = User.objects.first()
        print(f"User: {user}")
        
        # Try to create FGS inventory
        print("\nTrying to create FGS inventory...")
        inventory = FGSInventory.objects.create(
            bmr=bmr,
            product=bmr.product,
            batch_number=bmr.batch_number,
            quantity_available=bmr.batch_size,
            release_certificate_number='TEST-CERT-001',
            qa_approved_by=user,
            qa_approval_date=timezone.now(),
            status='available',
            created_by=user
        )
        print(f"SUCCESS: Created inventory {inventory}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Error type: {type(e)}")
        
        # Check what fields are expected
        print("\nFGSInventory model fields:")
        for field in FGSInventory._meta.fields:
            print(f"  {field.name}: {field}")

if __name__ == '__main__':
    test_fgs_creation()
