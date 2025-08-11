import os
import sys
import django
import random
from datetime import timedelta

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.utils import timezone
from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, ProductionPhase
from django.contrib.auth import get_user_model

User = get_user_model()

def populate_chart_data():
    """Create specific test data for dashboard charts"""
    print("Populating data for dashboard charts...")
    
    # 1. Create products by type for Product Type Chart
    product_types = [
        {'name': 'Tablet Type 1', 'type': 'tablet'},
        {'name': 'Tablet Type 2', 'type': 'tablet'},
        {'name': 'Tablet Type 3', 'type': 'tablet'},
        {'name': 'Capsule Type 1', 'type': 'capsule'},
        {'name': 'Capsule Type 2', 'type': 'capsule'},
        {'name': 'Ointment Type 1', 'type': 'ointment'},
    ]
    
    for product_type in product_types:
        Product.objects.get_or_create(
            product_name=product_type['name'],
            defaults={
                'product_type': product_type['type']
            }
        )
    
    print(f"Products by type - Tablet: {Product.objects.filter(product_type__icontains='tablet').count()}, "
          f"Capsule: {Product.objects.filter(product_type__icontains='capsule').count()}, "
          f"Ointment: {Product.objects.filter(product_type__icontains='ointment').count()}")
    
    # 2. Use existing phases or create if they don't exist
    phase_names = ['mixing', 'drying', 'granulation', 'compression', 'packing', 'qc_review']
    phases_by_name = {}
    
    for i, phase_name in enumerate(phase_names):
        # Get the first phase with this name or create a new one
        try:
            phase = ProductionPhase.objects.filter(phase_name=phase_name).first()
            if not phase:
                phase = ProductionPhase.objects.create(
                    phase_name=phase_name,
                    phase_order=(i+1)*10
                )
            phases_by_name[phase_name] = phase
        except Exception as e:
            print(f"Error with phase {phase_name}: {e}")
            continue
    
    # 3. Create BMRs with phase executions for phase status chart
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    # Create at least 20 BMRs with phase executions
    products = Product.objects.all()
    phases = ProductionPhase.objects.all()
    
    for i in range(20):
        product = random.choice(products)
        
        # Create BMR with a more unique batch number
        batch_number = f"CHART-{i+1000}-{random.randint(10000, 99999)}"
        
        # Check if this batch number already exists
        if BMR.objects.filter(batch_number=batch_number).exists():
            batch_number = f"CHART-{i+1000}-{random.randint(100000, 999999)}"
        
        try:
            bmr = BMR.objects.create(
                product=product,
                batch_number=batch_number,
                batch_size=random.randint(1000, 10000),
                created_by=admin_user,
                status='approved',
                approved_by=admin_user,
                approved_date=timezone.now()
            )
        except Exception as e:
            print(f"Error creating BMR with batch number {batch_number}: {e}")
            continue
        
        # Create phase executions for each phase
        for phase in phases:
            # Check if this phase already exists for this BMR
            if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=phase).exists():
                # Randomize status
                status_choices = ['completed', 'in_progress', 'pending']
                status_weights = [0.6, 0.2, 0.2]  # More completed than others
                status = random.choices(status_choices, weights=status_weights)[0]
                
                started_date = None
                completed_date = None
                
                if status in ['completed', 'in_progress']:
                    started_date = timezone.now() - timedelta(days=random.randint(1, 7))
                    
                if status == 'completed':
                    completed_date = started_date + timedelta(days=random.randint(1, 3))
                
                try:
                    BatchPhaseExecution.objects.create(
                        bmr=bmr,
                        phase=phase,
                        status=status,
                        started_date=started_date,
                        completed_date=completed_date,
                        started_by=admin_user if started_date else None,
                        completed_by=admin_user if completed_date else None
                    )
                except Exception as e:
                    print(f"Error creating phase execution for BMR {bmr.batch_number}, phase {phase.phase_name}: {e}")
                    continue
    
    # 4. Create weekly data for trend chart
    today = timezone.now().date()
    
    # Generate weekly data for the last 4 weeks
    for week in range(4):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=week)
        week_end = week_start + timedelta(days=6)
        
        # Create BMRs for this week
        num_bmrs = random.randint(3, 8)
        
        for i in range(num_bmrs):
            created_date = timezone.make_aware(timezone.datetime.combine(
                week_start + timedelta(days=random.randint(0, 6)),
                timezone.datetime.min.time()
            ))
            
            product = random.choice(products)
            
            batch_number = f"WEEK{week+1}-{i+1000}-{random.randint(10000, 99999)}"
            
            # Check if this batch number already exists
            if BMR.objects.filter(batch_number=batch_number).exists():
                batch_number = f"WEEK{week+1}-{i+1000}-{random.randint(100000, 999999)}"
            
            try:
                bmr = BMR.objects.create(
                    product=product,
                    batch_number=batch_number,
                    batch_size=random.randint(1000, 10000),
                    created_by=admin_user,
                    created_date=created_date,
                    status='approved',
                    approved_by=admin_user,
                    approved_date=created_date + timedelta(hours=random.randint(1, 24))
                )
            except Exception as e:
                print(f"Error creating weekly BMR with batch number {batch_number}: {e}")
                continue
            
            # For half of them, complete them in the same week
            if random.random() > 0.5:
                # Create FGS phase as completed
                try:
                    fgs_phase = ProductionPhase.objects.filter(phase_name='finished_goods_store').first()
                    if not fgs_phase:
                        fgs_phase = ProductionPhase.objects.create(
                            phase_name='finished_goods_store',
                            phase_order=100
                        )
                except Exception as e:
                    print(f"Error with FGS phase: {e}")
                    continue
                
                completed_date = created_date + timedelta(days=random.randint(1, 5))
                if completed_date.date() > week_end:
                    completed_date = timezone.make_aware(timezone.datetime.combine(
                        week_end, timezone.datetime.max.time()
                    ))
                
                # Check if this phase already exists for this BMR
                if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=fgs_phase).exists():
                    try:
                        BatchPhaseExecution.objects.create(
                            bmr=bmr,
                            phase=fgs_phase,
                            status='completed',
                            started_date=created_date + timedelta(hours=random.randint(1, 24)),
                            completed_date=completed_date,
                            started_by=admin_user,
                            completed_by=admin_user
                        )
                    except Exception as e:
                        print(f"Error creating FGS phase for BMR {bmr.batch_number}: {e}")
                        continue
    
    # 5. Create QC data
    try:
        qc_phase = ProductionPhase.objects.filter(phase_name='qc_review').first()
        if not qc_phase:
            qc_phase = ProductionPhase.objects.create(
                phase_name='qc_review',
                phase_order=50
            )
    except Exception as e:
        print(f"Error with QC phase: {e}")
        return
    
    # Create QC executions
    for i in range(30):
        bmr = random.choice(BMR.objects.all())
        status_choices = ['completed', 'failed', 'pending']
        status_weights = [0.7, 0.2, 0.1]  # More passed than failed
        status = random.choices(status_choices, weights=status_weights)[0]
        
        # Check if this bmr already has a QC phase execution
        if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=qc_phase).exists():
            try:
                BatchPhaseExecution.objects.create(
                    bmr=bmr,
                    phase=qc_phase,
                    status=status,
                    started_date=timezone.now() - timedelta(days=random.randint(1, 7)),
                    completed_date=timezone.now() - timedelta(days=random.randint(0, 3)) if status != 'pending' else None,
                    started_by=admin_user,
                    completed_by=admin_user if status != 'pending' else None
                )
            except Exception as e:
                print(f"Error creating QC phase for BMR {bmr.batch_number}: {e}")
                continue
    
    print("Chart data population complete!")
    
    # Print summary statistics
    print(f"Total BMRs: {BMR.objects.count()}")
    print(f"Total Products: {Product.objects.count()}")
    print(f"Total Phase Executions: {BatchPhaseExecution.objects.count()}")
    print(f"QC Reviews: {BatchPhaseExecution.objects.filter(phase__phase_name='qc_review').count()}")
    
    # Verify phase completion status
    for phase_name in phase_names:
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name=phase_name,
            status='completed'
        ).count()
        
        in_progress = BatchPhaseExecution.objects.filter(
            phase__phase_name=phase_name,
            status='in_progress'
        ).count()
        
        print(f"{phase_name.ljust(20)} - Completed: {completed}, In Progress: {in_progress}")
    
    # Verify QC data
    qc_passed = BatchPhaseExecution.objects.filter(
        phase__phase_name='qc_review',
        status='completed'
    ).count()
    
    qc_failed = BatchPhaseExecution.objects.filter(
        phase__phase_name='qc_review',
        status='failed'
    ).count()
    
    qc_pending = BatchPhaseExecution.objects.filter(
        phase__phase_name='qc_review',
        status='pending'
    ).count()
    
    print(f"QC Stats - Passed: {qc_passed}, Failed: {qc_failed}, Pending: {qc_pending}")

if __name__ == "__main__":
    populate_chart_data()
