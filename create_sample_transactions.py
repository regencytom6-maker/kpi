"""
Script to create sample inventory transactions for testing the store dashboard
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from raw_materials.models import RawMaterialBatch
from raw_materials.models_transaction import InventoryTransaction

User = get_user_model()

def create_sample_transactions():
    # Get some batches and users
    batches = RawMaterialBatch.objects.filter(status='approved')[:5]
    users = User.objects.filter(is_staff=True)[:3]
    
    if not batches:
        print("No approved material batches found. Cannot create sample transactions.")
        return
        
    if not users:
        print("No users found. Cannot create sample transactions.")
        return
    
    transaction_types = ['received', 'dispensed', 'adjusted', 'returned']
    
    # Create 20 sample transactions
    print(f"Creating sample inventory transactions...")
    for i in range(20):
        # Random batch, user, and transaction type
        batch = random.choice(batches)
        user = random.choice(users)
        transaction_type = random.choice(transaction_types)
        
        # Random date in the last 30 days
        days_ago = random.randint(0, 30)
        transaction_date = timezone.now() - timedelta(days=days_ago)
        
        # Random quantity (between 1 and 5 units)
        quantity = round(random.uniform(1, 5), 2)
        
        # Create transaction
        InventoryTransaction.objects.create(
            material_batch=batch,
            transaction_type=transaction_type,
            quantity=quantity,
            transaction_date=transaction_date,
            user=user,
            notes=f"Sample transaction {i+1} for testing"
        )
    
    print(f"Successfully created 20 sample inventory transactions.")

if __name__ == '__main__':
    create_sample_transactions()
    print("Sample data creation completed.")
