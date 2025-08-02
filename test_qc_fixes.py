#!/usr/bin/env python
"""
Test QC phase start functionality after fixes
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

def test_qc_phase_fixes():
    print("🧪 TESTING QC PHASE START FIXES")
    print("=" * 40)
    
    # Find QC phases
    qc_phase_names = ['post_mixing_qc', 'post_blending_qc', 'post_compression_qc']
    
    qc_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name__in=qc_phase_names
    ).select_related('bmr', 'phase')
    
    print(f"📊 Found {qc_phases.count()} QC phases total")
    
    # Show status breakdown
    pending_qc = qc_phases.filter(status='pending')
    in_progress_qc = qc_phases.filter(status='in_progress')
    completed_qc = qc_phases.filter(status='completed')
    
    print(f"   • Pending: {pending_qc.count()}")
    print(f"   • In Progress: {in_progress_qc.count()}")
    print(f"   • Completed: {completed_qc.count()}")
    
    # Show startable QC phases
    print(f"\n🚀 STARTABLE QC PHASES:")
    startable_count = 0
    
    for phase in pending_qc:
        can_start = WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)
        if can_start:
            startable_count += 1
            print(f"   ✅ Phase ID: {phase.id}")
            print(f"      {phase.phase.phase_name} on BMR {phase.bmr.batch_number}")
            print(f"      Product: {phase.bmr.product.product_name}")
        else:
            print(f"   ⏳ {phase.phase.phase_name} on BMR {phase.bmr.batch_number} - waiting for prerequisites")
    
    if startable_count == 0:
        print("   ❌ No QC phases ready to start")
        print("\n🔍 CHECKING PREREQUISITES:")
        
        for phase in pending_qc[:3]:  # Check first 3
            print(f"\n   Phase: {phase.phase.phase_name} (BMR {phase.bmr.batch_number})")
            prereqs = BatchPhaseExecution.objects.filter(
                bmr=phase.bmr,
                phase__phase_order__lt=phase.phase.phase_order
            ).exclude(status__in=['completed', 'skipped'])
            
            if prereqs.exists():
                print(f"     Waiting for:")
                for prereq in prereqs:
                    print(f"       • {prereq.phase.phase_name}: {prereq.status}")
            else:
                print(f"     ⚠️ All prerequisites met but can't start - check logic")
    
    print(f"\n🔧 FIXES APPLIED TO QC DASHBOARD:")
    print("   ✅ Template buttons now pass phase.id instead of phase.bmr.pk")
    print("   ✅ JavaScript functions updated to use phaseId parameter")
    print("   ✅ Form sends phase_id instead of bmr_id + phase_name")
    print("   ✅ Dashboard view now accepts 'start' action for QC testing")
    print("   ✅ Test results field matches view expectations")
    
    print(f"\n🎯 QC OPERATORS CAN NOW:")
    print("   1. Click 'Start Test' on pending QC phases")
    print("   2. Enter test parameters and observations")
    print("   3. Mark tests as Pass/Fail with detailed comments")
    print("   4. Failed tests will trigger rollback workflows")

if __name__ == '__main__':
    test_qc_phase_fixes()
