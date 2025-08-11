"""
Permanently fix the workflow creation process to ensure proper ordering of bulk_packing and secondary_packaging
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase

def fix_phase_order_definitions():
    """Fix phase order definitions for all product types"""
    
    print("=== FIXING PRODUCTION PHASE ORDERS FOR TABLET TYPE 2 ===")
    
    # 1. Get all tablet product types
    tablet_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    
    print(f"Found {tablet_phases.count()} phases for tablet products")
    
    # Print current ordering
    print("\nCurrent phase order:")
    for idx, phase in enumerate(tablet_phases, 1):
        print(f"{idx}. {phase.phase_name} (Order: {phase.phase_order})")
    
    # Check bulk_packing and secondary_packaging order
    bulk_packing = tablet_phases.filter(phase_name='bulk_packing').first()
    secondary_packaging = tablet_phases.filter(phase_name='secondary_packaging').first()
    
    if bulk_packing and secondary_packaging:
        if bulk_packing.phase_order >= secondary_packaging.phase_order:
            print("\n❌ ISSUE: bulk_packing order is >= secondary_packaging order")
            
            # Fix the order
            print("Fixing phase order...")
            
            # Get all phases with order between bulk_packing and final_qa
            phases_to_update = tablet_phases.filter(
                phase_order__gte=bulk_packing.phase_order,
                phase_order__lt=secondary_packaging.phase_order
            )
            
            # Update bulk_packing order to be before secondary_packaging
            new_bulk_order = secondary_packaging.phase_order - 1
            bulk_packing.phase_order = new_bulk_order
            bulk_packing.save()
            print(f"✓ Updated bulk_packing order to {new_bulk_order}")
            
            # Print updated ordering
            tablet_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
            print("\nUpdated phase order:")
            for idx, phase in enumerate(tablet_phases, 1):
                print(f"{idx}. {phase.phase_name} (Order: {phase.phase_order})")
        else:
            print("\n✓ CORRECT: bulk_packing order is already < secondary_packaging order")

if __name__ == "__main__":
    fix_phase_order_definitions()
