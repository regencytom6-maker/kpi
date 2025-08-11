"""
Test script to create and process 6 different product types through the entire workflow
This will help verify the workflow logic and populate the dashboard with data
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from accounts.models import CustomUser
from django.utils import timezone

# Define our 6 product types
TEST_PRODUCTS = [
    {
        'name': 'Normal Uncoated Tablet',
        'product_type': 'tablet',
        'tablet_type': 'normal',
        'coating_type': 'uncoated'
    },
    {
        'name': 'Normal Coated Tablet',
        'product_type': 'tablet',
        'tablet_type': 'normal',
        'coating_type': 'coated'
    },
    {
        'name': 'Type 2 Uncoated Tablet',
        'product_type': 'tablet',
        'tablet_type': 'tablet_2',
        'coating_type': 'uncoated'
    },
    {
        'name': 'Type 2 Coated Tablet',
        'product_type': 'tablet',
        'tablet_type': 'tablet_2',
        'coating_type': 'coated'
    },
    {
        'name': 'Standard Capsule',
        'product_type': 'capsule',
        'capsule_type': 'standard'
    },
    {
        'name': 'Standard Ointment',
        'product_type': 'ointment',
        'ointment_type': 'standard'
    }
]

def create_test_products():
    """Create test products if they don't exist"""
    created_products = []
    
    for product_data in TEST_PRODUCTS:
        try:
            # Check if product already exists
            if product_data['product_type'] == 'tablet':
                product = Product.objects.get(
                    product_name=product_data['name'],
                    product_type=product_data['product_type'],
                    tablet_type=product_data['tablet_type'],
                    coating_type=product_data['coating_type']
                )
            elif product_data['product_type'] == 'capsule':
                product = Product.objects.get(
                    product_name=product_data['name'],
                    product_type=product_data['product_type']
                )
            elif product_data['product_type'] == 'ointment':
                product = Product.objects.get(
                    product_name=product_data['name'],
                    product_type=product_data['product_type']
                )
            
            print(f"Product already exists: {product.product_name}")
            
        except Product.DoesNotExist:
            # Create new product
            product = Product(
                product_name=product_data['name'],
                product_type=product_data['product_type']
            )
            
            # Set tablet-specific fields
            if product_data['product_type'] == 'tablet':
                product.tablet_type = product_data['tablet_type']
                product.coating_type = product_data['coating_type']
                
            product.save()
            print(f"Created new product: {product.product_name}")
        
        created_products.append(product)
    
    return created_products

def generate_unique_batch_number():
    """Generate a unique batch number"""
    current_year = datetime.now().year
    # Get the highest batch number in current year
    latest_bmr = BMR.objects.filter(batch_number__endswith=str(current_year)[-4:]).order_by('-batch_number').first()
    
    if latest_bmr:
        try:
            sequence = int(latest_bmr.batch_number[:3]) + 1
        except ValueError:
            sequence = random.randint(300, 999)  # Fallback if format is wrong
    else:
        sequence = 300  # Start at 300 for test BMRs
        
    return f"{sequence:03d}{current_year}"

def create_bmr_for_product(product, user):
    """Create a BMR for the given product"""
    batch_number = generate_unique_batch_number()
    
    bmr = BMR.objects.create(
        batch_number=batch_number,
        product=product,
        batch_size=1000,  # Example batch size
        created_by=user,
        created_date=timezone.now()
    )
    
    print(f"Created BMR {bmr.batch_number} for {product.product_name}")
    
    # Initialize workflow
    WorkflowService.initialize_workflow_for_bmr(bmr)
    print(f"Initialized workflow for BMR {bmr.batch_number}")
    
    return bmr

def get_phases_for_bmr(bmr):
    """Get all phases for the BMR in execution order"""
    return BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')

def complete_all_phases(bmr, user):
    """Complete all phases for the BMR"""
    phases = get_phases_for_bmr(bmr)
    phase_list = list(phases)  # Convert to list to avoid requerying
    
    print(f"\nProcessing BMR {bmr.batch_number} for {bmr.product.product_name}:")
    print(f"Product Type: {bmr.product.product_type}")
    
    if bmr.product.product_type == 'tablet':
        print(f"Tablet Type: {bmr.product.tablet_type}")
        print(f"Coating Type: {bmr.product.coating_type}")
    
    # Start from first pending phase
    current_phase = next((p for p in phase_list if p.status == 'pending'), None)
    
    # In case all phases are already started/completed
    if not current_phase:
        print("No pending phases found")
        return
        
    # Track expected workflow paths
    phase_names = [p.phase.phase_name for p in phase_list]
    print(f"Phase sequence: {' -> '.join(phase_names)}")
    
    while current_phase:
        phase_name = current_phase.phase.phase_name
        
        # Start phase
        print(f"  Starting phase: {phase_name}")
        current_phase.status = 'in_progress'
        current_phase.started_by = user
        current_phase.started_date = timezone.now()
        current_phase.save()
        
        # Wait a random time (simulating work being done)
        elapsed_time = random.randint(1, 5)
        completion_date = current_phase.started_date + timedelta(hours=elapsed_time)
        
        # Complete phase
        print(f"  Completing phase: {phase_name} (after {elapsed_time} hours)")
        current_phase.status = 'completed'
        current_phase.completed_by = user
        current_phase.completed_date = completion_date
        current_phase.operator_comments = f"Completed by test script in {elapsed_time} hours"
        current_phase.save()
        
        # Find next phase
        next_phases = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            status='not_ready',
            phase__phase_order__gt=current_phase.phase.phase_order
        ).order_by('phase__phase_order')
        
        if next_phases.exists():
            # Activate next phase
            next_phase = next_phases.first()
            next_phase.status = 'pending'
            next_phase.save()
            
            current_phase = next_phase
        else:
            print("  All phases completed!")
            break
    
    print(f"BMR {bmr.batch_number} workflow completed successfully!")

def run_test():
    """Main test function"""
    # Get admin user for creating BMRs
    admin_user = CustomUser.objects.filter(is_staff=True).first()
    
    if not admin_user:
        print("No admin user found. Creating test admin...")
        admin_user = CustomUser.objects.create_superuser(
            username='testadmin',
            email='testadmin@example.com',
            password='testpassword',
            first_name='Test',
            last_name='Admin'
        )
    
    # Create test products
    print("Creating test products...")
    products = create_test_products()
    
    # Create and process BMRs for each product
    created_bmrs = []
    for product in products:
        bmr = create_bmr_for_product(product, admin_user)
        created_bmrs.append(bmr)
    
    # Process each BMR through the entire workflow
    print("\nProcessing BMRs through workflow phases...\n")
    for bmr in created_bmrs:
        complete_all_phases(bmr, admin_user)
    
    # Verify all BMRs completed to finished_goods_store
    print("\nVerifying BMRs reached finished goods store...")
    for bmr in created_bmrs:
        fgs_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='finished_goods_store'
        ).first()
        
        if fgs_phase and fgs_phase.status == 'completed':
            print(f"✓ BMR {bmr.batch_number} ({bmr.product.product_name}) successfully completed to FGS")
        else:
            print(f"✗ BMR {bmr.batch_number} ({bmr.product.product_name}) did not reach FGS")
    
    # Count total BMRs now in the system
    total_bmrs = BMR.objects.count()
    fgs_completed = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_store',
        status='completed'
    ).count()
    
    print(f"\nTotal BMRs in system: {total_bmrs}")
    print(f"BMRs with completed FGS phase: {fgs_completed}")
    
    # List all phases for a Type 2 coated tablet BMR
    print("\nDetailed phase listing for Type 2 Coated Tablet:")
    type2_coated_bmr = created_bmrs[3]  # Index 3 is Type 2 Coated Tablet
    
    phases = get_phases_for_bmr(type2_coated_bmr)
    for idx, phase in enumerate(phases, 1):
        print(f"{idx}. {phase.phase.phase_name} - Status: {phase.status}")

if __name__ == "__main__":
    run_test()
