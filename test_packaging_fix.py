#!/usr/bin/env python3
"""
Test the fixed packaging transition logic
"""

import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from django.utils import timezone

def test_packaging_fix():
    print("🧪 TESTING FIXED PACKAGING TRANSITION LOGIC")
    print("=" * 50)
    
    # Get a tablet type 2 BMR that has reached packaging material release
    bmr = BMR.objects.filter(
        product__product_type='tablet',
        product__tablet_type='tablet_2'
    ).first()
    
    if not bmr:
        print("❌ No tablet type 2 BMR found!")
        return
    
    print(f"📋 Testing with BMR: {bmr.batch_number} - {bmr.product.product_name}")
    print(f"   Product Type: {bmr.product.product_type}")
    print(f"   Tablet Type: {getattr(bmr.product, 'tablet_type', 'N/A')}")
    
    # Get the packaging material release phase
    packaging_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='packaging_material_release'
    ).first()
    
    if not packaging_phase:
        print("❌ No packaging material release phase found!")
        return
    
    print(f"\n📊 Current Status:")
    print(f"   📦 Packaging Material Release: {packaging_phase.status}")
    
    # Get bulk packing phase
    bulk_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='bulk_packing'
    ).first()
    
    if bulk_phase:
        print(f"   📦 Bulk Packing: {bulk_phase.status}")
    
    # Get secondary packaging phase
    secondary_phase = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='secondary_packaging'
    ).first()
    
    if secondary_phase:
        print(f"   📦 Secondary Packaging: {secondary_phase.status}")
    
    # Simulate completing the packaging material release
    print(f"\n🎬 SIMULATING: Completing packaging material release...")
    
    # Store original status
    original_packaging_status = packaging_phase.status
    original_bulk_status = bulk_phase.status if bulk_phase else 'N/A'
    original_secondary_status = secondary_phase.status if secondary_phase else 'N/A'
    
    # Temporarily complete the packaging phase
    packaging_phase.status = 'completed'
    packaging_phase.completed_date = timezone.now()
    packaging_phase.save()
    
    print(f"   ✅ Set packaging_material_release to 'completed'")
    
    # Test the trigger_next_phase method
    print(f"   🚀 Calling WorkflowService.trigger_next_phase...")
    result = WorkflowService.trigger_next_phase(bmr, packaging_phase.phase)
    
    # Check the results
    bulk_phase.refresh_from_db()
    secondary_phase.refresh_from_db()
    
    print(f"\n📈 RESULTS:")
    print(f"   trigger_next_phase returned: {result}")
    print(f"   📦 Bulk Packing: {original_bulk_status} → {bulk_phase.status}")
    print(f"   📦 Secondary Packaging: {original_secondary_status} → {secondary_phase.status}")
    
    if bulk_phase.status == 'pending':
        print(f"   ✅ SUCCESS: bulk_packing was correctly activated!")
    else:
        print(f"   ❌ FAILED: bulk_packing should be 'pending' but is '{bulk_phase.status}'")
    
    if secondary_phase.status == 'not_ready':
        print(f"   ✅ SUCCESS: secondary_packaging correctly remains 'not_ready'")
    else:
        print(f"   ⚠️  WARNING: secondary_packaging is '{secondary_phase.status}' (should be 'not_ready')")
    
    # Test the notification logic
    print(f"\n💬 TESTING NOTIFICATION LOGIC:")
    if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2':
        next_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()
        if next_phase:
            print(f"   ✅ Next phase for notification: {next_phase.phase.get_phase_name_display()}")
            print(f"   📋 This should appear in the dashboard notification!")
        else:
            print(f"   ❌ No bulk_packing phase found for notification!")
    
    # Restore original status
    print(f"\n🔄 RESTORING ORIGINAL STATUS...")
    packaging_phase.status = original_packaging_status
    packaging_phase.completed_date = None
    packaging_phase.save()
    bulk_phase.status = original_bulk_status
    bulk_phase.save()
    secondary_phase.status = original_secondary_status
    secondary_phase.save()
    print(f"   ✅ Restored original phases status")

if __name__ == '__main__':
    test_packaging_fix()
