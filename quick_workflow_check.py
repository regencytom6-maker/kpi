#!/usr/bin/env python3
"""
QUICK WORKFLOW VERIFICATION
===========================
Run this script anytime to verify the tablet_2 workflow fix is still working.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase

def quick_verify():
    print("🔍 Quick Workflow Verification")
    print("=" * 40)
    
    # Check tablet_2 phase order
    phases = ProductionPhase.objects.filter(
        product_type='tablet_2',
        phase_name__in=['bulk_packing', 'secondary_packaging']
    ).order_by('phase_order')
    
    if len(phases) != 2:
        print("❌ Missing phases!")
        return False
    
    bulk = phases.filter(phase_name='bulk_packing').first()
    secondary = phases.filter(phase_name='secondary_packaging').first()
    
    print(f"bulk_packing order: {bulk.phase_order}")
    print(f"secondary_packaging order: {secondary.phase_order}")
    
    if bulk.phase_order < secondary.phase_order:
        print("✅ WORKFLOW IS CORRECT!")
        print("✅ bulk_packing comes before secondary_packaging")
        return True
    else:
        print("❌ WORKFLOW IS BROKEN!")
        print("❌ Need to run emergency fix again")
        return False

if __name__ == "__main__":
    success = quick_verify()
    if success:
        print("\n🎉 Your workflow is working perfectly!")
    else:
        print("\n⚠️  Workflow needs attention!")
    
    sys.exit(0 if success else 1)
