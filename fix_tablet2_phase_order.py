"""
Fix phase ordering for tablet type 2 products to ensure the correct sequence:
1. For coated tablets: coating → material release → bulk packing → secondary packing
2. For uncoated tablets: sorting → material release → bulk packing → secondary packing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db import transaction
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from django.utils import timezone

def fix_production_phase_order():
    """Fix the ordering of phases for tablet type 2 in the ProductionPhase model"""
    print("\n=== Fixing production phase ordering for tablet type 2 ===")
    
    # Get all tablet phases
    tablet_phases = ProductionPhase.objects.filter(product_type='tablet').order_by('phase_order')
    
    print("Current tablet phase ordering:")
    for i, phase in enumerate(tablet_phases, 1):
        print(f"{i:2d}. {phase.phase_name} (order: {phase.phase_order})")
    
    # Get critical phases
    sorting = tablet_phases.filter(phase_name='sorting').first()
    coating = tablet_phases.filter(phase_name='coating').first()
    packaging_material_release = tablet_phases.filter(phase_name='packaging_material_release').first()
    bulk_packing = tablet_phases.filter(phase_name='bulk_packing').first()
    blister_packing = tablet_phases.filter(phase_name='blister_packing').first()
    secondary_packaging = tablet_phases.filter(phase_name='secondary_packaging').first()
    
    if not all([sorting, coating, packaging_material_release, bulk_packing, secondary_packaging]):
        print("❌ ERROR: Some required phases are missing")
        return False
    
    # Current ordering issues:
    # - coating and packaging_material_release have the same phase_order
    # - bulk_packing and secondary_packaging have the same phase_order
    
    with transaction.atomic():
        # Set correct ordering:
        # 1. Sorting should be before coating
        sorting_order = sorting.phase_order
        
        # 2. Coating should be next
        coating_order = sorting_order + 1
        coating.phase_order = coating_order
        coating.save()
        
        # 3. Packaging material release should be after coating
        packaging_order = coating_order + 1
        packaging_material_release.phase_order = packaging_order
        packaging_material_release.save()
        
        # 4. Packing phases (bulk or blister) should be next
        packing_order = packaging_order + 1
        blister_packing.phase_order = packing_order
        bulk_packing.phase_order = packing_order
        blister_packing.save()
        bulk_packing.save()
        
        # 5. Secondary packaging should follow
        secondary_order = packing_order + 1
        secondary_packaging.phase_order = secondary_order
        secondary_packaging.save()
        
        print("\nUpdated phase ordering:")
        print(f"sorting: {sorting_order}")
        print(f"coating: {coating_order}")
        print(f"packaging_material_release: {packaging_order}")
        print(f"blister_packing: {packing_order}")
        print(f"bulk_packing: {packing_order}")
        print(f"secondary_packaging: {secondary_order}")
        
    return True

def fix_batch_phase_ordering():
    """Fix the ordering of phases for existing BMRs"""
    print("\n=== Fixing batch phase ordering for existing BMRs ===")
    
    # Find all tablet type 2 batches
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    print(f"Found {tablet2_bmrs.count()} tablet type 2 BMRs to fix")
    
    fixed_count = 0
    for bmr in tablet2_bmrs:
        print(f"\nFixing BMR {bmr.batch_number}: {bmr.product.product_name}")
        print(f"Product is {'coated' if bmr.product.is_coated else 'uncoated'}")
        
        with transaction.atomic():
            # Get all batch phase executions for this BMR
            executions = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
            
            # Get critical phases
            sorting = executions.filter(phase__phase_name='sorting').first()
            coating = executions.filter(phase__phase_name='coating').first() if bmr.product.is_coated else None
            packaging_material_release = executions.filter(phase__phase_name='packaging_material_release').first()
            bulk_packing = executions.filter(phase__phase_name='bulk_packing').first()
            secondary_packaging = executions.filter(phase__phase_name='secondary_packaging').first()
            
            if not all([sorting, packaging_material_release, bulk_packing, secondary_packaging]):
                print("❌ ERROR: Some required phases are missing")
                continue
                
            # Get updated phase orders from production phases
            sorting_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='sorting')
            coating_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='coating') if bmr.product.is_coated else None
            packaging_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='packaging_material_release')
            bulk_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='bulk_packing')
            secondary_phase = ProductionPhase.objects.get(product_type='tablet', phase_name='secondary_packaging')
            
            # Update phase orders
            sorting.phase = sorting_phase
            sorting.save()
            
            if coating and coating_phase:
                coating.phase = coating_phase
                coating.save()
                
            packaging_material_release.phase = packaging_phase
            packaging_material_release.save()
            
            bulk_packing.phase = bulk_phase
            bulk_packing.save()
            
            secondary_packaging.phase = secondary_phase
            secondary_packaging.save()
            
            # Fix status progression issues
            fixed = False
            
            # Case: secondary_packaging is pending but bulk_packing isn't completed yet
            if secondary_packaging.status in ['pending', 'in_progress'] and bulk_packing.status not in ['completed', 'in_progress']:
                if packaging_material_release.status == 'completed':
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    print(f"✅ Set bulk_packing to pending as material release is completed")
                    fixed = True
                    
                # Set secondary packaging back to not_ready as it should come after bulk packing
                if secondary_packaging.status == 'pending':
                    secondary_packaging.status = 'not_ready'
                    secondary_packaging.save()
                    print(f"✅ Set secondary_packaging back to not_ready until bulk_packing completes")
                    fixed = True
            
            if fixed:
                fixed_count += 1
                print(f"✅ Fixed workflow for BMR {bmr.batch_number}")
            else:
                print(f"✓ No workflow status changes needed for BMR {bmr.batch_number}")
    
    print(f"\nFixed workflow for {fixed_count} out of {tablet2_bmrs.count()} BMRs")

def verify_fixed_workflow():
    """Verify the fixed workflow for tablet type 2 batches"""
    print("\n=== Verifying fixed workflow ===")
    
    # Find all tablet type 2 batches
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    if tablet2_bmrs.count() == 0:
        print("No tablet type 2 BMRs found")
        return
        
    test_bmr = tablet2_bmrs.first()
    print(f"Verifying BMR {test_bmr.batch_number}: {test_bmr.product.product_name}")
    print(f"Product is {'coated' if test_bmr.product.is_coated else 'uncoated'}")
    
    # Get phases in order
    phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).select_related('phase').order_by('phase__phase_order')
    
    # Print complete phase sequence
    print("\nComplete phase sequence:")
    for i, phase in enumerate(phases, 1):
        print(f"{i:2d}. {phase.phase.phase_name} (Order: {phase.phase.phase_order}, Status: {phase.status})")
    
    # Verify critical phases
    critical_phases = []
    if test_bmr.product.is_coated:
        critical_phases = ['sorting', 'coating', 'packaging_material_release', 'bulk_packing', 'secondary_packaging']
    else:
        critical_phases = ['sorting', 'packaging_material_release', 'bulk_packing', 'secondary_packaging']
    
    print("\nVerifying critical phase ordering:")
    previous_order = 0
    for phase_name in critical_phases:
        phase = phases.filter(phase__phase_name=phase_name).first()
        if not phase:
            print(f"❌ ERROR: Missing critical phase: {phase_name}")
            continue
            
        print(f"- {phase_name}: order {phase.phase.phase_order}")
        
        if phase.phase.phase_order <= previous_order:
            print(f"❌ ERROR: Phase {phase_name} order should be greater than previous phase")
            return False
            
        previous_order = phase.phase.phase_order
    
    print("✅ Critical phase ordering is correct")
    return True

if __name__ == "__main__":
    print("===== FIXING TABLET TYPE 2 PHASE ORDERING =====")
    
    # Fix production phase ordering first
    if fix_production_phase_order():
        # Then fix batch phase ordering
        fix_batch_phase_ordering()
        
        # Verify the fixes
        if verify_fixed_workflow():
            print("\n✨ TABLET TYPE 2 PHASE ORDERING SUCCESSFULLY FIXED")
            print("The correct workflow sequence is now enforced:")
            print("- For coated tablets: sorting → coating → material release → bulk packing → secondary packing")
            print("- For uncoated tablets: sorting → material release → bulk packing → secondary packing")
        else:
            print("\n⚠️ TABLET TYPE 2 PHASE ORDERING STILL HAS ISSUES")
            print("Please check the details above")
    else:
        print("\n❌ FAILED TO FIX TABLET TYPE 2 PHASE ORDERING")
        print("Please check the error messages above")
