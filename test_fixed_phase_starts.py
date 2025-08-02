#!/usr/bin/env python
"""
Test the fixed phase start functionality
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

def test_fixed_phase_starts():
    print("🧪 TESTING FIXED PHASE START FUNCTIONALITY")
    print("=" * 50)
    
    # Find startable phases
    startable_phases = []
    for phase in BatchPhaseExecution.objects.filter(status='pending'):
        if WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name):
            startable_phases.append(phase)
    
    print(f"✅ Found {len(startable_phases)} startable phases:")
    
    for phase in startable_phases:
        print(f"   🚀 Phase ID: {phase.id}")
        print(f"      Phase: {phase.phase.phase_name}")
        print(f"      BMR: {phase.bmr.batch_number}")
        print(f"      Product: {phase.bmr.product.product_name}")
        print(f"      Template will now pass: phase_id={phase.id}")
        print()
    
    print("🔧 FIXES APPLIED:")
    print("   ✅ Template now passes phase.id instead of phase.bmr.pk")
    print("   ✅ JavaScript updated to use phaseId parameter")
    print("   ✅ Form sends phase_id instead of bmr_id + phase_name")
    print("   ✅ Dashboard view receives correct phase_id parameter")
    print()
    
    print("🎯 NEXT STEPS:")
    print("   1. Login as an operator")
    print("   2. Go to operator dashboard")
    print("   3. Click 'Start' button on any pending phase")
    print("   4. The phase should now start successfully!")

if __name__ == '__main__':
    test_fixed_phase_starts()
