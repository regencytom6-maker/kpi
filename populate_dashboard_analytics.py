"""
This script populates analyt    # Create test products if they don't exist
    products = [
        {'name': 'Paracetamol 500mg', 'type': 'tablet'},
        {'name': 'Ibuprofen 400mg', 'type': 'tablet'},
        {'name': 'Hydrocortisone 1%', 'type': 'ointment'},
        {'name': 'Amoxicillin 250mg', 'type': 'capsule'},
    ]
    
    for p in products:
        if not Product.objects.filter(product_name=p['name']).exists():
            product = Product.objects.create(
                product_name=p['name'],
                product_type=p['type']
            )
            print(f"Created product: {p['name']} ({p['type']})") admin dashboard
"""

import os
import sys
import django
import random
from datetime import timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db.models import Count
from django.utils import timezone
from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, ProductionPhase
from django.contrib.auth import get_user_model
from workflow.services import WorkflowService

User = get_user_model()

def create_test_data():
    """Create sample data for the analytics panels"""
    print("Starting analytics data population...")
    
    # Check available product types from the existing model
    product_types = ['tablet', 'ointment', 'capsule']
    print(f"Using product types: {product_types}")
    
    # Create test products if they don't exist
    products = [
        {'name': 'Paracetamol 500mg', 'type': 'tablet'},
        {'name': 'Ibuprofen 400mg', 'type': 'tablet'},
        {'name': 'Hydrocortisone 1%', 'type': 'ointment'},
        {'name': 'Amoxicillin 250mg', 'type': 'capsule'},
    ]
    
    for p in products:
        product_type = ProductType.objects.get(name=p['type'])
        if not Product.objects.filter(product_name=p['name']).exists():
            product = Product.objects.create(
                product_name=p['name'],
                product_type=product_type
            )
            print(f"Created product: {p['name']} ({p['type']})")
    
    # Make sure we have some BMRs
    if BMR.objects.count() < 10:
        # Create test users for each role if needed
        roles = ['QA', 'QC', 'Production', 'Regulatory', 'Store']
        
        for i, role in enumerate(roles):
            username = f"{role.lower()}_analytics_user"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create(
                    username=username,
                    first_name=f"{role} Analytics",
                    last_name="User",
                    email=f"{username}@example.com",
                    employee_id=f"EMP{i+500}",  # Use higher employee IDs to avoid conflicts
                    department=role
                )
                user.set_password("password123")
                user.save()
                print(f"Created {role} user: {username}")
        
        # Get users for different roles
        qa_user = User.objects.filter(department='QA').first()
        regulatory_user = User.objects.filter(department='Regulatory').first()
        production_user = User.objects.filter(department='Production').first()
        qc_user = User.objects.filter(department='QC').first()
        
        # Create BMRs for different product types
        products = Product.objects.all()
        
        for i, product in enumerate(products):
            # Create multiple BMRs for each product
            for j in range(3):
                bmr_number = f"BMR2025{i+1:02d}{j+1:02d}"
                batch_number = f"{i+1:02d}{j+1:02d}2025"
                if not BMR.objects.filter(batch_number=batch_number).exists():
                    bmr = BMR.objects.create(
                        bmr_number=bmr_number,
                        batch_number=batch_number,
                        product=product,
                        batch_size=random.randint(5000, 10000),
                        created_by=qa_user,
                        status='approved',
                        approved_by=regulatory_user,
                        approved_date=timezone.now() - timedelta(days=random.randint(10, 30))
                    )
                    print(f"Created BMR: {bmr_number} for {product.product_name}")
                    
                    # Initialize workflow for this BMR
                    try:
                        workflow_service = WorkflowService()
                        workflow_service.initialize_workflow(bmr)
                        print(f"Initialized workflow for BMR: {bmr_no}")
                    except Exception as e:
                        print(f"Error initializing workflow for {bmr_no}: {e}")
    
    # Create and complete phases for various BMRs to generate chart data
    bmrs = BMR.objects.all()
    print(f"Found {bmrs.count()} BMRs to process")
    
    # Get QC users
    qc_users = User.objects.filter(department='QC')
    production_users = User.objects.filter(department='Production')
    
    # Process each BMR and move through workflow phases
    for i, bmr in enumerate(bmrs):
        batch_phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
        
        if not batch_phases.exists():
            print(f"No phases found for BMR {bmr.bmr_no}, skipping")
            continue
            
        print(f"Processing BMR {bmr.bmr_no} - {bmr.product.product_name}")
        
        # For some BMRs, complete all phases, for others leave some pending
        phases_to_complete = len(batch_phases)
        if i % 3 == 0:  # Every 3rd BMR is partially complete
            phases_to_complete = random.randint(2, len(batch_phases) - 1)
        
        # Process phases in order
        for j, phase in enumerate(batch_phases[:phases_to_complete]):
            if phase.status == 'pending':
                # Choose appropriate user based on phase type
                is_qc_phase = 'qc' in phase.phase.phase_name
                user = random.choice(qc_users) if is_qc_phase else random.choice(production_users)
                
                # Start the phase
                phase.status = 'in_progress'
                phase.started_by = user
                phase.started_date = timezone.now() - timedelta(days=random.randint(5, 20))
                phase.save()
                print(f"  Started phase {phase.phase.phase_name}")
                
                # For some phases, mark as failed (QC phases)
                should_fail = is_qc_phase and random.random() < 0.2
                
                # Complete the phase
                if not should_fail:
                    phase.status = 'completed'
                    phase.completed_by = user
                    phase.completed_date = phase.started_date + timedelta(hours=random.randint(2, 24))
                    phase.operator_comments = f"Phase completed successfully"
                    phase.save()
                    print(f"  Completed phase {phase.phase.phase_name}")
                else:
                    phase.status = 'failed'
                    phase.completed_by = user
                    phase.completed_date = phase.started_date + timedelta(hours=random.randint(2, 24))
                    phase.operator_comments = f"Failed QC check - {random.choice(['Impurities detected', 'Weight variation', 'Content uniformity'])}"
                    phase.save()
                    print(f"  Failed QC phase {phase.phase.phase_name}")
                    break  # Stop processing after a failure
    
    # Update weekly trend data to have distributed dates
    fgs_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_store',
        status='completed'
    )
    
    # Distribute FGS completions over the last 4 weeks
    now = timezone.now()
    for i, phase in enumerate(fgs_phases):
        days_ago = random.randint(0, 28)
        new_date = now - timedelta(days=days_ago)
        phase.completed_date = new_date
        phase.save()
    
    print(f"Updated dates for {fgs_phases.count()} finished goods store phases")
    print("Analytics data population complete!")

if __name__ == '__main__':
    create_test_data()
