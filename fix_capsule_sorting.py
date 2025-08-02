#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from django.utils import timezone

# Fix the capsule sorting issue for BMR 0012025
bmr = BMR.objects.get(batch_number='0012025')
print(f"=== Fixing Capsule Sorting Issue for {bmr.batch_number} ===")

try:
    # Get the problematic phases
    sorting_phase = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='sorting')
    packaging_phase = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='packaging_material_release')
    
    print(f"Current status:")
    print(f"  Sorting: {sorting_phase.status} (order {sorting_phase.phase.phase_order})")
    print(f"  Packaging: {packaging_phase.status} (order {packaging_phase.phase.phase_order})")
    
    # If packaging is completed but sorting is still pending, we need to fix this
    if packaging_phase.status == 'completed' and sorting_phase.status == 'pending':
        print(f"\n⚠️  Issue detected: Packaging completed but sorting still pending!")
        print(f"This means sorting was bypassed in the workflow.")
        
        # Option 1: Mark sorting as skipped since packaging is already done
        print(f"\n🔧 Solution: Marking sorting as 'skipped' since packaging is already completed")
        
        sorting_phase.status = 'skipped'
        sorting_phase.completed_date = timezone.now()
        sorting_phase.operator_comments = "Phase skipped - packaging materials were already released. Fixed by system."
        sorting_phase.save()
        
        print(f"✅ Sorting phase marked as skipped")
        
        # Now check if packing phases are available
        print(f"\n=== Checking Packing Phases ===")
        try:
            blister_packing = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='blister_packing')
            secondary_packaging = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='secondary_packaging')
            
            print(f"Blister packing: {blister_packing.status}")
            print(f"Secondary packaging: {secondary_packaging.status}")
            
            # These should be pending since packaging material release is completed
            if blister_packing.status == 'not_ready':
                blister_packing.status = 'pending'
                blister_packing.save()
                print(f"✅ Blister packing activated")
                
            if secondary_packaging.status == 'not_ready':
                secondary_packaging.status = 'pending'
                secondary_packaging.save()
                print(f"✅ Secondary packaging activated")
                
        except BatchPhaseExecution.DoesNotExist as e:
            print(f"❌ Packing phase not found: {e}")
    
    elif sorting_phase.status == 'pending' and packaging_phase.status == 'pending':
        print(f"\n✅ Both phases are pending - normal state")
        print(f"Sorting should be completed before packaging material release")
        
    else:
        print(f"\n✅ No issue detected with current status")
    
    # Final status check
    print(f"\n=== Final Status ===")
    all_phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    
    for phase in all_phases:
        status_icon = {
            'completed': '✅',
            'in_progress': '🔄', 
            'pending': '⏳',
            'not_ready': '⚫',
            'failed': '❌',
            'skipped': '⏭️'
        }.get(phase.status, '❓')
        
        print(f"  {status_icon} {phase.phase.phase_name} (order {phase.phase.phase_order}): {phase.status}")

except BatchPhaseExecution.DoesNotExist as e:
    print(f"❌ Phase not found: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n=== Testing WorkflowService Logic ===")
# Test the WorkflowService to make sure it handles capsule workflow correctly
workflow = WorkflowService.PRODUCT_WORKFLOWS.get('capsule', [])
print(f"Capsule workflow: {workflow}")

filling_index = workflow.index('filling') if 'filling' in workflow else -1
sorting_index = workflow.index('sorting') if 'sorting' in workflow else -1
packaging_index = workflow.index('packaging_material_release') if 'packaging_material_release' in workflow else -1

print(f"Filling index: {filling_index}")
print(f"Sorting index: {sorting_index}")
print(f"Packaging index: {packaging_index}")

if filling_index >= 0 and sorting_index == filling_index + 1:
    print(f"✅ Sorting should come immediately after filling")
else:
    print(f"❌ Workflow order issue!")

print(f"\n=== Done ===")
