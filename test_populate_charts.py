"""
This script populates the dashboard with test data for all 6 product types
It creates products, BMRs, and processes them through the workflow
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

# Import Django models
from django.utils import timezone
from django.contrib.auth import get_user_model
from bmr.models import BMR, Product
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

User = get_user_model()

# Get or create test users
def get_test_users():
    """Get or create test users for all roles"""
    roles = ['qa', 'regulatory', 'production', 'store', 'packaging']
    users = {}
    
    for role in roles:
        username = f'test_{role}'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                password='testpassword123',
                email=f'{username}@example.com',
                first_name=f'Test {role.title()}',
                last_name='User',
                role=role
            )
            print(f"Created user: {username} with role {role}")
        users[role] = user
    
    return users

def create_test_products():
    """Create test products for all 6 types"""
    print("Creating test products...")
    products = []
    
    # Normal Uncoated Tablet
    try:
        product = Product.objects.get(product_name='Normal Uncoated Tablet')
    except Product.DoesNotExist:
        product = Product.objects.create(
            product_name='Normal Uncoated Tablet',
            product_type='tablet',
            tablet_type='normal',
            coating_type='uncoated',
            created_by_id=1
        )
        print(f"Created new product: {product.product_name}")
    products.append(product)
    
    # Normal Coated Tablet
    try:
        product = Product.objects.get(product_name='Normal Coated Tablet')
    except Product.DoesNotExist:
        product = Product.objects.create(
            product_name='Normal Coated Tablet',
            product_type='tablet',
            tablet_type='normal',
            coating_type='coated',
            created_by_id=1
        )
        print(f"Created new product: {product.product_name}")
    products.append(product)
    
    # Type 2 Uncoated Tablet
    try:
        product = Product.objects.get(product_name='Type 2 Uncoated Tablet')
    except Product.DoesNotExist:
        product = Product.objects.create(
            product_name='Type 2 Uncoated Tablet',
            product_type='tablet',
            tablet_type='tablet_2',
            coating_type='uncoated',
            created_by_id=1
        )
        print(f"Created new product: {product.product_name}")
    products.append(product)
    
    # Type 2 Coated Tablet
    try:
        product = Product.objects.get(product_name='Type 2 Coated Tablet')
    except Product.DoesNotExist:
        product = Product.objects.create(
            product_name='Type 2 Coated Tablet',
            product_type='tablet',
            tablet_type='tablet_2',
            coating_type='coated',
            created_by_id=1
        )
        print(f"Created new product: {product.product_name}")
    products.append(product)
    
    # Standard Capsule
    try:
        product = Product.objects.get(product_name='Standard Capsule')
    except Product.DoesNotExist:
        product = Product.objects.create(
            product_name='Standard Capsule',
            product_type='capsule',
            created_by_id=1
        )
        print(f"Created new product: {product.product_name}")
    products.append(product)
    
    # Standard Ointment
    try:
        product = Product.objects.get(product_name='Standard Ointment')
    except Product.DoesNotExist:
        product = Product.objects.create(
            product_name='Standard Ointment',
            product_type='ointment',
            created_by_id=1
        )
        print(f"Created new product: {product.product_name}")
    products.append(product)
    
    return products

def create_and_process_bmrs(users, products):
    """Create BMRs for products and process them through workflow"""
    print("Processing BMRs through workflow phases...")
    
    # Create a BMR for each product if it doesn't exist
    bmrs = []
    for i, product in enumerate(products):
        # Generate batch number for testing
        batch_number = f"{i+227}2025"
        
        try:
            bmr = BMR.objects.get(batch_number=batch_number)
        except BMR.DoesNotExist:
            bmr = BMR.objects.create(
                batch_number=batch_number,
                product=product,
                status='approved',
                batch_size=1000,
                batch_size_unit='kg',
                created_by=users['qa'],
                approved_by=users['qa']
            )
            print(f"Created BMR {batch_number} for {product.product_name}")
            # Initialize workflow
            WorkflowService.initialize_workflow_for_bmr(bmr)
            print(f"Initialized workflow for BMR {batch_number}")
        
        bmrs.append(bmr)
    
    # Process each BMR through the workflow
    for bmr in bmrs:
        process_bmr_workflow(bmr, users)
    
    # Verify that all BMRs reached FGS
    print("\nVerifying BMRs reached finished goods store...")
    for bmr in bmrs:
        fgs_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='finished_goods_store',
            status='completed'
        ).exists()
        
        if fgs_phase:
            print(f"✓ BMR {bmr.batch_number} ({bmr.product.product_name}) successfully completed to FGS")
        else:
            print(f"✗ BMR {bmr.batch_number} ({bmr.product.product_name}) did not complete to FGS")
    
    # Print some stats
    total_bmrs = BMR.objects.count()
    complete_bmrs = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_store',
        status='completed'
    ).count()
    
    print(f"\nTotal BMRs in system: {total_bmrs}")
    print(f"BMRs with completed FGS phase: {complete_bmrs}")
    
    # Show details for a Type 2 Coated Tablet
    t2_coated = BMR.objects.filter(product__product_name='Type 2 Coated Tablet').first()
    if t2_coated:
        print("\nDetailed phase listing for Type 2 Coated Tablet:")
        phases = BatchPhaseExecution.objects.filter(bmr=t2_coated).order_by('phase__phase_order')
        for i, phase in enumerate(phases, 1):
            print(f"{i}. {phase.phase.phase_name} - Status: {phase.status}")

def process_bmr_workflow(bmr, users):
    """Process a BMR through its entire workflow"""
    print(f"\nProcessing BMR {bmr.batch_number} for {bmr.product.product_name}:")
    print(f"Product Type: {bmr.product.product_type}")
    
    if bmr.product.product_type == 'tablet':
        print(f"Tablet Type: {bmr.product.tablet_type}")
        print(f"Coating Type: {bmr.product.coating_type}")
    
    # Get all phases for this BMR
    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    
    # Print phase sequence
    phase_names = [p.phase.phase_name for p in phases]
    print(f"Phase sequence: {' -> '.join(phase_names)}")
    
    # Process each phase
    for phase in phases:
        phase_name = phase.phase.phase_name
        
        # Skip bmr_creation as it's already done
        if phase_name == 'bmr_creation':
            continue
            
        # Determine which user for this phase
        if 'qc' in phase_name:
            user = users['qa']
        elif 'qa' in phase_name:
            user = users['qa']
        elif phase_name == 'regulatory_approval':
            user = users['regulatory']
        elif 'material' in phase_name:
            user = users['store']
        elif any(p in phase_name for p in ['packing', 'packaging']):
            user = users['packaging']
        else:
            user = users['production']
            
        # Only process if not already completed
        if phase.status != 'completed':
            # Start phase if pending
            if phase.status == 'pending':
                hours_taken = random.randint(1, 5)
                phase.status = 'in_progress'
                phase.started_by = user
                phase.started_date = timezone.now() - timedelta(hours=hours_taken)
                phase.save()
                print(f"  Starting phase: {phase_name}")
                
            # Complete phase if in progress
            if phase.status == 'in_progress':
                hours_taken = random.randint(1, 5)
                phase.status = 'completed'
                phase.completed_by = user
                phase.completed_date = timezone.now() - timedelta(hours=hours_taken)
                phase.save()
                print(f"  Completing phase: {phase_name} (after {hours_taken} hours)")
                
                # Trigger next phase
                WorkflowService.trigger_next_phase(bmr, phase.phase)
    
    # Check if all phases completed
    all_completed = BatchPhaseExecution.objects.filter(
        bmr=bmr, 
        status='completed'
    ).count() == phases.count()
    
    if all_completed:
        print("  All phases completed!")
        print(f"BMR {bmr.batch_number} workflow completed successfully!")
    else:
        incomplete = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).exclude(status='completed')
        print(f"  BMR {bmr.batch_number} has {incomplete.count()} incomplete phases:")
        for phase in incomplete:
            print(f"    - {phase.phase.phase_name}: {phase.status}")

if __name__ == '__main__':
    users = get_test_users()
    products = create_test_products()
    create_and_process_bmrs(users, products)
