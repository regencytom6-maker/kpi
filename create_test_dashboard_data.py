import os
import sys
import django

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, ProductionPhase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

def create_test_data():
    """Create test data for the dashboard charts"""
    print("Creating test data for dashboard charts...")
    
    # Create some products if none exist
    if Product.objects.count() < 5:
        product_types = ['tablet', 'capsule', 'ointment']
        
        for i in range(10):
            product_type = random.choice(product_types)
            name = f"{product_type.title()} Product {i+1}"
            
            Product.objects.get_or_create(
                product_name=name,
                product_type=product_type,
                defaults={
                    'strength': f"{random.randint(10, 500)}mg",
                    'packaging': f"{random.randint(10, 100)} units"
                }
            )
    
    print(f"Products in database: {Product.objects.count()}")
    
    # Create some BMRs if none exist
    if BMR.objects.count() < 10:
        products = Product.objects.all()
        users = User.objects.filter(is_staff=True)
        
        if not users:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='User'
            )
            users = [admin]
        
        statuses = ['draft', 'approved', 'in_production', 'completed', 'rejected']
        
        for i in range(20):
            product = random.choice(products)
            user = random.choice(users)
            status = random.choice(statuses)
            
            # Create a random date within the last 30 days
            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            bmr = BMR.objects.create(
                product=product,
                batch_number=f"B{random.randint(100000, 999999)}",
                batch_size=random.randint(1000, 10000),
                created_by=user,
                created_date=created_date,
                status=status
            )
            
            if status in ['approved', 'in_production', 'completed']:
                bmr.approved_by = user
                bmr.approved_date = created_date + timedelta(days=1)
                bmr.save()
    
    print(f"BMRs in database: {BMR.objects.count()}")
    
    # Create phase data if not enough exists
    if BatchPhaseExecution.objects.count() < 50:
        # Ensure we have the basic phases
        common_phases = ['mixing', 'drying', 'granulation', 'compression', 'packing', 'qc_review', 'finished_goods_store']
        phase_order = 10
        
        for phase_name in common_phases:
            ProductionPhase.objects.get_or_create(
                phase_name=phase_name,
                defaults={'phase_order': phase_order}
            )
            phase_order += 10
        
        phases = ProductionPhase.objects.all()
        bmrs = BMR.objects.all()
        users = User.objects.filter(is_staff=True)
        
        for bmr in bmrs:
            # For each BMR create some phase executions
            for phase in phases:
                # 70% chance to create this phase
                if random.random() < 0.7:
                    status_options = ['completed', 'in_progress', 'pending', 'failed']
                    weights = [0.5, 0.2, 0.2, 0.1]  # More completed than others
                    status = random.choices(status_options, weights=weights)[0]
                    
                    started_date = None
                    completed_date = None
                    started_by = None
                    completed_by = None
                    
                    if status in ['completed', 'in_progress', 'failed']:
                        started_date = bmr.created_date + timedelta(days=random.randint(1, 5))
                        started_by = random.choice(users)
                    
                    if status in ['completed', 'failed']:
                        completed_date = started_date + timedelta(days=random.randint(1, 3))
                        completed_by = random.choice(users)
                    
                    BatchPhaseExecution.objects.create(
                        bmr=bmr,
                        phase=phase,
                        status=status,
                        started_date=started_date,
                        completed_date=completed_date,
                        started_by=started_by,
                        completed_by=completed_by,
                        operator_comments=f"Test phase execution for {phase.phase_name}"
                    )
    
    print(f"Phase executions in database: {BatchPhaseExecution.objects.count()}")
    print("Test data creation complete!")

if __name__ == "__main__":
    create_test_data()
