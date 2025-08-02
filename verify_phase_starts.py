#!/usr/bin/env python
"""
Quick verification that operators can now start phases
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

def verify_phase_starts():
    print("🔍 PHASE START VERIFICATION")
    print("=" * 30)
    
    # Show startable phases by role
    roles = {
        'mixing_operator': 'mixing',
        'granulation_operator': 'granulation', 
        'blending_operator': 'blending',
        'compression_operator': 'compression'
    }
    
    for role, expected_phase in roles.items():
        print(f"\n👤 {role.replace('_', ' ').title()}:")
        
        # Find phases this operator can start
        startable = []
        bmrs = BMR.objects.filter(status='approved')
        
        for bmr in bmrs:
            try:
                phases = WorkflowService.get_phases_for_user_role(bmr, role)
                for phase in phases:
                    if (phase.status == 'pending' and 
                        WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)):
                        startable.append(phase)
            except:
                pass
        
        if startable:
            print(f"   ✅ Can start {len(startable)} phase(s):")
            for phase in startable:
                print(f"      🚀 {phase.phase.phase_name} on BMR {phase.bmr.batch_number}")
        else:
            print(f"   ❌ No startable phases")
    
    print(f"\n📊 SUMMARY:")
    total_pending = BatchPhaseExecution.objects.filter(status='pending').count()
    total_startable = 0
    
    for phase in BatchPhaseExecution.objects.filter(status='pending'):
        if WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name):
            total_startable += 1
    
    print(f"   • Pending phases: {total_pending}")
    print(f"   • Actually startable: {total_startable}")
    print(f"   • Success rate: {(total_startable/total_pending*100):.1f}%" if total_pending > 0 else "   • No pending phases")

if __name__ == '__main__':
    verify_phase_starts()
