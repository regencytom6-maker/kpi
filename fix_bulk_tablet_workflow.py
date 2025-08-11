"""
Diagnosis and fix script for bulk tablet workflow issues
- Identifies tablets of type 'tablet_2' that should go to bulk packing 
- Fixes workflow phases to ensure proper progression for bulk tablets
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from django.db.models import Q

def diagnose_bulk_tablet_workflow():
    """Check tablets that should use bulk packing instead of blister packing"""
    
    print("=== DIAGNOSING BULK TABLET WORKFLOW ISSUES ===")
    
    # 1. Find all tablet type 2 products
    tablet2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).select_related('product')
    
    print(f"Found {tablet2_bmrs.count()} BMRs with tablet type 2 products")
    
    issues_found = 0
    bmrs_to_fix = []
    
    for bmr in tablet2_bmrs:
        print(f"\nAnalyzing BMR {bmr.batch_number}: {bmr.product.product_name}")
        print(f"  Product Type: {bmr.product.product_type}")
        print(f"  Tablet Type: {bmr.product.tablet_type}")
        print(f"  Is Coated: {bmr.product.is_coated}")
        
        # Get phase executions for this BMR
        phase_executions = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).select_related('phase').order_by('phase__phase_order')
        
        phases = [f"{p.phase.phase_name} ({p.status})" for p in phase_executions]
        print(f"  Phases: {', '.join(phases)}")
        
        # Check if bulk_packing exists
        bulk_packing = phase_executions.filter(phase__phase_name='bulk_packing').first()
        blister_packing = phase_executions.filter(phase__phase_name='blister_packing').first()
        
        if not bulk_packing and blister_packing:
            print(f"  ❌ ERROR: BMR {bmr.batch_number} has blister_packing instead of bulk_packing")
            issues_found += 1
            bmrs_to_fix.append(bmr)
        elif not bulk_packing:
            print(f"  ❌ ERROR: BMR {bmr.batch_number} doesn't have bulk_packing phase")
            issues_found += 1
            bmrs_to_fix.append(bmr)
        else:
            # Check phase order: coating -> bulk_packing -> secondary_packaging
            coating = phase_executions.filter(phase__phase_name='coating').first() if bmr.product.is_coated else None
            secondary_packaging = phase_executions.filter(phase__phase_name='secondary_packaging').first()
            
            if coating and bulk_packing and coating.phase.phase_order >= bulk_packing.phase.phase_order:
                print(f"  ❌ ERROR: Coating phase order ({coating.phase.phase_order}) >= Bulk Packing phase order ({bulk_packing.phase.phase_order})")
                issues_found += 1
                bmrs_to_fix.append(bmr)
            elif bulk_packing and secondary_packaging and bulk_packing.phase.phase_order >= secondary_packaging.phase.phase_order:
                print(f"  ❌ ERROR: Bulk Packing phase order ({bulk_packing.phase.phase_order}) >= Secondary Packaging phase order ({secondary_packaging.phase.phase_order})")
                issues_found += 1
                bmrs_to_fix.append(bmr)
            else:
                print(f"  ✓ Phases for BMR {bmr.batch_number} are correctly ordered")
                
                # Check status progression
                if coating and coating.status == 'completed' and bulk_packing.status == 'not_ready':
                    print(f"  ❌ ERROR: Coating completed but Bulk Packing not activated")
                    issues_found += 1
                    bmrs_to_fix.append(bmr)
    
    print(f"\nFound {issues_found} issues across {len(bmrs_to_fix)} BMRs")
    return bmrs_to_fix

def fix_bulk_tablet_workflow(bmrs_to_fix):
    """Fix workflow issues for bulk tablet BMRs"""
    
    if not bmrs_to_fix:
        print("No BMRs to fix")
        return
        
    print("\n=== FIXING BULK TABLET WORKFLOW ISSUES ===")
    
    for bmr in bmrs_to_fix:
        print(f"\nFixing BMR {bmr.batch_number}: {bmr.product.product_name}")
        
        # Get phase executions for this BMR
        phase_executions = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).select_related('phase').order_by('phase__phase_order')
        
        # 1. Check if bulk_packing exists
        bulk_packing = phase_executions.filter(phase__phase_name='bulk_packing').first()
        blister_packing = phase_executions.filter(phase__phase_name='blister_packing').first()
        
        # If there's blister packing instead of bulk packing, we need to replace it
        if blister_packing and not bulk_packing:
            print(f"  Replacing blister_packing with bulk_packing for BMR {bmr.batch_number}")
            
            # Get production phase
            bulk_phase = ProductionPhase.objects.filter(
                product_type='tablet', phase_name='bulk_packing').first()
            
            if not bulk_phase:
                print("  Creating bulk_packing production phase")
                bulk_phase = ProductionPhase.objects.create(
                    product_type='tablet',
                    phase_name='bulk_packing',
                    phase_order=blister_packing.phase.phase_order,
                    is_mandatory=True
                )
            
            # Update the blister phase execution to use bulk_packing
            blister_packing.phase = bulk_phase
            blister_packing.save()
            print(f"  Updated phase to bulk_packing")
            
        # If there's no bulk_packing at all, we need to create it
        elif not bulk_packing:
            print(f"  Creating bulk_packing phase execution for BMR {bmr.batch_number}")
            
            # Get production phase
            bulk_phase = ProductionPhase.objects.filter(
                product_type='tablet', phase_name='bulk_packing').first()
            
            if not bulk_phase:
                print("  Creating bulk_packing production phase")
                # Find where it should go in order
                packaging_material_release = phase_executions.filter(
                    phase__phase_name='packaging_material_release').first()
                secondary_packaging = phase_executions.filter(
                    phase__phase_name='secondary_packaging').first()
                
                if packaging_material_release and secondary_packaging:
                    new_order = packaging_material_release.phase.phase_order + 1
                    bulk_phase = ProductionPhase.objects.create(
                        product_type='tablet',
                        phase_name='bulk_packing',
                        phase_order=new_order,
                        is_mandatory=True
                    )
                    
                    # Update secondary packaging order if needed
                    if secondary_packaging.phase.phase_order <= new_order:
                        sec_phase = secondary_packaging.phase
                        sec_phase.phase_order = new_order + 1
                        sec_phase.save()
                
            # Create the batch phase execution
            packaging_material_release = phase_executions.filter(
                phase__phase_name='packaging_material_release').first()
                
            new_status = 'pending' if packaging_material_release and packaging_material_release.status == 'completed' else 'not_ready'
            
            BatchPhaseExecution.objects.create(
                bmr=bmr,
                phase=bulk_phase,
                status=new_status
            )
            print(f"  Created bulk_packing phase with status {new_status}")
        
        # 3. Ensure correct ordering: coating -> bulk_packing -> secondary_packaging
        coating = phase_executions.filter(phase__phase_name='coating').first() if bmr.product.is_coated else None
        bulk_packing = phase_executions.filter(phase__phase_name='bulk_packing').first()
        secondary_packaging = phase_executions.filter(phase__phase_name='secondary_packaging').first()
        packaging_material_release = phase_executions.filter(phase__phase_name='packaging_material_release').first()
        
        # Update phase ordering if necessary
        if packaging_material_release and bulk_packing:
            correct_order = packaging_material_release.phase.phase_order + 1
            if bulk_packing.phase.phase_order != correct_order:
                bulk_phase = bulk_packing.phase
                bulk_phase.phase_order = correct_order
                bulk_phase.save()
                print(f"  Updated bulk_packing order to {correct_order}")
        
        if bulk_packing and secondary_packaging:
            if secondary_packaging.phase.phase_order <= bulk_packing.phase.phase_order:
                sec_phase = secondary_packaging.phase
                sec_phase.phase_order = bulk_packing.phase.phase_order + 1
                sec_phase.save()
                print(f"  Updated secondary_packaging order to {sec_phase.phase_order}")
        
        # 4. Fix status progression if coating is completed but bulk_packing isn't activated
        if coating and coating.status == 'completed' and bulk_packing and bulk_packing.status == 'not_ready':
            bulk_packing.status = 'pending'
            bulk_packing.save()
            print(f"  Updated bulk_packing status from 'not_ready' to 'pending'")
    
    print("\nFixes applied successfully!")

if __name__ == "__main__":
    bmrs_to_fix = diagnose_bulk_tablet_workflow()
    
    fix_it = input("\nWould you like to fix these issues? (y/n): ")
    if fix_it.lower() in ['y', 'yes']:
        fix_bulk_tablet_workflow(bmrs_to_fix)
    else:
        print("No changes were made")
