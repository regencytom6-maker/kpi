"""
Test script to verify tablet type 2 workflow with new BMR creation
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from accounts.models import CustomUser
from django.utils import timezone

def create_test_bmr():
    """Create a new test BMR for tablet type 2 with coating"""
    
    # Find a tablet type 2 product with coating
    try:
        product = Product.objects.get(
            product_type='tablet',
            tablet_type='tablet_2',
            coating_type='coated'
        )
    except Product.DoesNotExist:
        # Create one if it doesn't exist
        product = Product.objects.create(
            product_name='Test Coated Tablet Type 2',
            product_type='tablet',
            tablet_type='tablet_2',
            coating_type='coated'
        )
        print(f"Created new test product: {product.product_name}")
    
    # Get a user to be the BMR creator
    user = CustomUser.objects.filter(is_staff=True).first()
    if not user:
        user = CustomUser.objects.first()
    
    # Generate a unique batch number: format XXX-YYYY (e.g., 0012025)
    current_year = datetime.now().year
    # Get highest sequence number for current year and add 100 to ensure uniqueness
    max_bmr = BMR.objects.filter(batch_number__endswith=str(current_year)[-4:]).order_by('-batch_number').first()
    if max_bmr:
        try:
            sequence = int(max_bmr.batch_number[:3]) + 100
        except ValueError:
            sequence = 900  # Fallback if format is wrong
    else:
        sequence = 900
    batch_number = f"{sequence:03d}{current_year}"
    
    # Create the BMR
    bmr = BMR.objects.create(
        batch_number=batch_number,
        product=product,
        batch_size=1000,  # Example batch size
        created_by=user,
        created_date=timezone.now()
    )
    
    print(f"Created new BMR {bmr.batch_number} for product {product.product_name}")
    
    # Initialize workflow for this BMR
    WorkflowService.initialize_workflow_for_bmr(bmr)
    print(f"Initialized workflow for BMR {bmr.batch_number}")
    
    return bmr

def check_workflow_phases(bmr):
    """Check the workflow phases for a BMR"""
    
    print(f"\n=== CHECKING WORKFLOW FOR BMR {bmr.batch_number} ===")
    print(f"Product: {bmr.product.product_name}")
    print(f"Product Type: {bmr.product.product_type}")
    print(f"Tablet Type: {bmr.product.tablet_type}")
    print(f"Is Coated: {bmr.product.is_coated}")
    
    # Get all phases for this BMR
    phase_executions = BatchPhaseExecution.objects.filter(
        bmr=bmr
    ).select_related('phase').order_by('phase__phase_order')
    
    print("\nPhase Sequence:")
    for idx, phase in enumerate(phase_executions, 1):
        print(f"{idx}. {phase.phase.phase_name} (Order: {phase.phase.phase_order}, Status: {phase.status})")
    
    # Check for correct ordering of coating -> bulk_packing -> secondary_packaging
    coating = phase_executions.filter(phase__phase_name='coating').first()
    bulk_packing = phase_executions.filter(phase__phase_name='bulk_packing').first()
    blister_packing = phase_executions.filter(phase__phase_name='blister_packing').first()
    secondary_packaging = phase_executions.filter(phase__phase_name='secondary_packaging').first()
    
    print("\nChecking phase order...")
    
    # Ensure we have the right phases
    if not bulk_packing:
        print("❌ ERROR: No bulk_packing phase for tablet type 2!")
    elif blister_packing:
        print("❌ ERROR: Has blister_packing when it should only have bulk_packing!")
    else:
        print("✅ CORRECT: Has bulk_packing and no blister_packing")
    
    if coating and bulk_packing and coating.phase.phase_order >= bulk_packing.phase.phase_order:
        print(f"❌ ERROR: Coating (order {coating.phase.phase_order}) should come before bulk_packing (order {bulk_packing.phase.phase_order})")
    elif coating and bulk_packing:
        print("✅ CORRECT: coating comes before bulk_packing")
        
    if bulk_packing and secondary_packaging and bulk_packing.phase.phase_order >= secondary_packaging.phase.phase_order:
        print(f"❌ ERROR: Bulk Packing (order {bulk_packing.phase.phase_order}) should come before secondary_packaging (order {secondary_packaging.phase.phase_order})")
    elif bulk_packing and secondary_packaging:
        print("✅ CORRECT: bulk_packing comes before secondary_packaging")

if __name__ == "__main__":
    # Check if we should create a new BMR or use existing ones
    if len(sys.argv) > 1 and sys.argv[1] == "new":
        bmr = create_test_bmr()
        check_workflow_phases(bmr)
    else:
        # Test with existing BMRs
        tablet2_bmrs = BMR.objects.filter(
            product__product_type='tablet',
            product__tablet_type='tablet_2'
        )
        
        if tablet2_bmrs.exists():
            for bmr in tablet2_bmrs[:3]:  # Check up to 3 BMRs
                check_workflow_phases(bmr)
        else:
            print("No existing tablet type 2 BMRs found. Run with 'new' parameter to create one.")
            bmr = create_test_bmr()
            check_workflow_phases(bmr)
