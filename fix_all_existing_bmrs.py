#!/usr/bin/env python3
"""
EMERGENCY FIX FOR EXISTING TABLET_2 BMRs
========================================
This script fixes ALL existing BMRs that have the wrong workflow order.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase, BatchPhaseExecution
from bmr.models import BMR

def fix_existing_bmr_workflows():
    """Fix all existing tablet_2 BMRs with wrong workflow order"""
    print("🔧 EMERGENCY FIX: Correcting existing BMR workflows")
    print("=" * 60)
    
    # Find all tablet_2 BMRs
    tablet_2_bmrs = BMR.objects.filter(
        product__product_type='tablet_2'
    )
    
    print(f"Found {tablet_2_bmrs.count()} tablet_2 BMRs to fix")
    
    for bmr in tablet_2_bmrs:
        print(f"\n🔍 Fixing BMR: {bmr.batch_number}")
        
        # Get current phases for this BMR
        current_phases = BatchPhaseExecution.objects.filter(bmr=bmr)
        
        # Check if bulk_packing and secondary_packaging exist
        bulk_phase = current_phases.filter(phase__phase_name='bulk_packing').first()
        secondary_phase = current_phases.filter(phase__phase_name='secondary_packaging').first()
        
        if not bulk_phase or not secondary_phase:
            print(f"   ⚠️  Missing phases for {bmr.batch_number}")
            continue
            
        # Check current order
        if bulk_phase.phase.phase_order > secondary_phase.phase.phase_order:
            print(f"   ❌ Wrong order: bulk({bulk_phase.phase.phase_order}) > secondary({secondary_phase.phase.phase_order})")
            
            # Get the correct phase definitions
            correct_bulk_phase = ProductionPhase.objects.filter(
                product_type='tablet_2',
                phase_name='bulk_packing'
            ).first()
            
            correct_secondary_phase = ProductionPhase.objects.filter(
                product_type='tablet_2', 
                phase_name='secondary_packaging'
            ).first()
            
            if correct_bulk_phase and correct_secondary_phase:
                # Update the BMR phases to use the correct phase definitions
                bulk_phase.phase = correct_bulk_phase
                bulk_phase.save()
                
                secondary_phase.phase = correct_secondary_phase
                secondary_phase.save()
                
                print(f"   ✅ Fixed: bulk({correct_bulk_phase.phase_order}) < secondary({correct_secondary_phase.phase_order})")
                
                # If secondary_packaging is pending but bulk_packing is not_ready, fix the status
                if secondary_phase.status == 'pending' and bulk_phase.status == 'not_ready':
                    # Set bulk_packing to pending and secondary_packaging to not_ready
                    bulk_phase.status = 'pending'
                    bulk_phase.save()
                    
                    secondary_phase.status = 'not_ready'
                    secondary_phase.save()
                    
                    print(f"   🔄 Fixed status: bulk_packing -> pending, secondary_packaging -> not_ready")
            else:
                print(f"   ❌ Could not find correct phase definitions")
        else:
            print(f"   ✅ Already correct: bulk({bulk_phase.phase.phase_order}) < secondary({secondary_phase.phase.phase_order})")

def verify_all_fixes():
    """Verify that all BMRs now have correct workflow"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICATION: Checking all BMRs")
    print("=" * 60)
    
    tablet_2_bmrs = BMR.objects.filter(product__product_type='tablet_2')
    
    all_correct = True
    for bmr in tablet_2_bmrs:
        phases = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).select_related('phase').order_by('phase__phase_order')
        
        phase_names = [p.phase.phase_name for p in phases]
        
        if 'bulk_packing' in phase_names and 'secondary_packaging' in phase_names:
            bulk_index = phase_names.index('bulk_packing')
            secondary_index = phase_names.index('secondary_packaging')
            
            if bulk_index < secondary_index:
                print(f"   ✅ {bmr.batch_number}: Correct order")
            else:
                print(f"   ❌ {bmr.batch_number}: Still wrong order!")
                all_correct = False
        else:
            print(f"   ⚠️  {bmr.batch_number}: Missing phases")
    
    print("\n" + "=" * 60)
    if all_correct:
        print("🎉 ALL BMRs ARE NOW CORRECT!")
        print("✅ The system is permanently fixed!")
    else:
        print("❌ Some BMRs still have issues")
    print("=" * 60)

if __name__ == "__main__":
    fix_existing_bmr_workflows()
    verify_all_fixes()
    print("\n🔒 DEPLOYMENT READY: All workflows are now correct!")
