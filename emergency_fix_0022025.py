#!/usr/bin/env python
"""
EMERGENCY FIX: Repair existing BMR 0022025 workflow to show bulk packing instead of secondary
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase

def fix_existing_bmr_0022025():
    print("🚨 EMERGENCY FIX: BMR 0022025 workflow repair")
    
    try:
        # Get the specific BMR that's shown in the screenshot
        bmr = BMR.objects.get(batch_number='0022025')
        print(f"📋 Found BMR: {bmr.batch_number} - {bmr.product.product_name}")
        print(f"   Product Type: {bmr.product.product_type}")
        print(f"   Tablet Type: {getattr(bmr.product, 'tablet_type', 'N/A')}")
        
        # Get current phases
        packaging_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr, 
            phase__phase_name='packaging_material_release'
        ).first()
        
        bulk_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr, 
            phase__phase_name='bulk_packing'
        ).first()
        
        secondary_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr, 
            phase__phase_name='secondary_packaging'
        ).first()
        
        print(f"\n🔍 CURRENT STATE:")
        if packaging_phase:
            print(f"   📦 Packaging Material Release: {packaging_phase.status}")
        if bulk_phase:
            print(f"   📦 Bulk Packing: {bulk_phase.status}")
        if secondary_phase:
            print(f"   📦 Secondary Packaging: {secondary_phase.status}")
        
        # Fix the workflow: if packaging is completed, bulk should be pending, secondary should be not_ready
        if packaging_phase and packaging_phase.status == 'completed':
            print(f"\n🔧 FIXING WORKFLOW...")
            
            # Make bulk packing pending (next in line)
            if bulk_phase:
                bulk_phase.status = 'pending'
                bulk_phase.save()
                print(f"   ✅ Set bulk_packing to PENDING")
            
            # Make secondary packaging not ready (comes after bulk)
            if secondary_phase:
                secondary_phase.status = 'not_ready'
                secondary_phase.save()
                print(f"   ✅ Set secondary_packaging to NOT_READY")
                
            print(f"\n🎯 FIXED! BMR 0022025 workflow corrected")
            print(f"   Next phase should now be: BULK PACKING")
            
            return True
        else:
            print(f"   ❌ Packaging material release not completed yet")
            return False
            
    except BMR.DoesNotExist:
        print(f"   ❌ BMR 0022025 not found")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def fix_all_tablet_2_bmrs():
    print(f"\n🔧 FIXING ALL TABLET TYPE 2 BMRs...")
    
    # Find all tablet type 2 BMRs where packaging is done but workflow is wrong
    tablet_2_bmrs = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    )
    
    fixed_count = 0
    for bmr in tablet_2_bmrs:
        packaging_phase = BatchPhaseExecution.objects.filter(
            bmr=bmr, 
            phase__phase_name='packaging_material_release',
            status='completed'
        ).first()
        
        if packaging_phase:
            bulk_phase = BatchPhaseExecution.objects.filter(
                bmr=bmr, 
                phase__phase_name='bulk_packing'
            ).first()
            
            secondary_phase = BatchPhaseExecution.objects.filter(
                bmr=bmr, 
                phase__phase_name='secondary_packaging'
            ).first()
            
            # Fix if secondary is pending but bulk is not ready
            if (secondary_phase and secondary_phase.status == 'pending' and 
                bulk_phase and bulk_phase.status == 'not_ready'):
                
                print(f"   🔧 Fixing BMR {bmr.batch_number}")
                bulk_phase.status = 'pending'
                bulk_phase.save()
                secondary_phase.status = 'not_ready'  
                secondary_phase.save()
                fixed_count += 1
                
    print(f"   ✅ Fixed {fixed_count} BMRs")
    return fixed_count

if __name__ == "__main__":
    print("=" * 60)
    print("🚨 EMERGENCY WORKFLOW REPAIR")
    print("=" * 60)
    
    # Fix the specific BMR shown in screenshot
    fix_existing_bmr_0022025()
    
    # Fix all tablet type 2 BMRs with the same issue
    fix_all_tablet_2_bmrs()
    
    print("\n" + "=" * 60)
    print("🎉 EMERGENCY FIX COMPLETED!")
    print("💡 Refresh your browser to see the changes")
    print("=" * 60)
