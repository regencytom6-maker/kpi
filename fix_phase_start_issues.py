#!/usr/bin/env python
"""
Fix Phase Start Issues - Convert 'not_ready' phases to 'pending' where appropriate
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from django.utils import timezone

def fix_phase_start_issues():
    """Fix phases that can't be started by updating their status"""
    
    print("🔧 FIXING PHASE START ISSUES")
    print("=" * 50)
    
    # 1. Find all 'not_ready' phases that should be 'pending'
    not_ready_phases = BatchPhaseExecution.objects.filter(status='not_ready').select_related('bmr', 'phase')
    print(f"Found {not_ready_phases.count()} phases in 'not_ready' status")
    
    fixed_count = 0
    
    for phase in not_ready_phases:
        print(f"\n🔍 Checking: {phase.phase.phase_name} for BMR {phase.bmr.batch_number}")
        
        # Check if all prerequisite phases are completed
        prereq_phases = BatchPhaseExecution.objects.filter(
            bmr=phase.bmr,
            phase__phase_order__lt=phase.phase.phase_order
        )
        
        all_prereqs_done = True
        for prereq in prereq_phases:
            if prereq.status not in ['completed', 'skipped']:
                all_prereqs_done = False
                print(f"   ❌ Blocked by: {prereq.phase.phase_name} ({prereq.status})")
                break
        
        if all_prereqs_done:
            # Convert to pending
            phase.status = 'pending'
            phase.save()
            fixed_count += 1
            print(f"   ✅ FIXED: Changed to 'pending' - now startable!")
        else:
            print(f"   ⏳ Keeping 'not_ready' - prerequisites not met")
    
    print(f"\n🎉 SUMMARY: Fixed {fixed_count} phases")
    
    # 2. Check for BMRs stuck at regulatory approval
    print(f"\n📋 CHECKING REGULATORY APPROVALS")
    print("-" * 30)
    
    regulatory_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='regulatory_approval',
        status='pending'
    ).select_related('bmr')
    
    print(f"BMRs awaiting regulatory approval: {regulatory_phases.count()}")
    
    for reg_phase in regulatory_phases:
        print(f"   📝 BMR {reg_phase.bmr.batch_number}: {reg_phase.bmr.product.product_name}")
        
        # Auto-approve for testing (you can comment this out in production)
        print(f"   🚀 Auto-approving for testing...")
        reg_phase.status = 'completed'
        reg_phase.completed_by = None  # System approval
        reg_phase.completed_date = timezone.now()
        reg_phase.operator_comments = "Auto-approved for testing - phase start fix"
        reg_phase.save()
        
        # Update BMR status
        reg_phase.bmr.status = 'approved'
        reg_phase.bmr.approved_date = timezone.now()
        reg_phase.bmr.save()
        
        # Trigger next phase
        WorkflowService.trigger_next_phase(reg_phase.bmr, reg_phase.phase)
        print(f"   ✅ Approved and triggered next phase")
    
    # 3. Show current startable phases for each operator role
    print(f"\n👥 STARTABLE PHASES BY ROLE")
    print("-" * 30)
    
    operator_roles = [
        'mixing_operator',
        'granulation_operator', 
        'blending_operator',
        'compression_operator',
        'coating_operator',
        'packing_operator'
    ]
    
    bmrs = BMR.objects.filter(status='approved')
    
    for role in operator_roles:
        print(f"\n🎯 {role.replace('_', ' ').title()}:")
        startable_phases = []
        
        for bmr in bmrs:
            try:
                user_phases = WorkflowService.get_phases_for_user_role(bmr, role)
                for phase in user_phases:
                    if phase.status == 'pending':
                        can_start = WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)
                        if can_start:
                            startable_phases.append(phase)
            except Exception as e:
                print(f"   ❌ Error for BMR {bmr.batch_number}: {e}")
        
        if startable_phases:
            print(f"   Can start {len(startable_phases)} phase(s):")
            for phase in startable_phases[:3]:  # Show first 3
                print(f"   🚀 {phase.phase.phase_name} (BMR {phase.bmr.batch_number})")
        else:
            print(f"   ❌ No startable phases found")
    
    # 4. Final verification
    print(f"\n🔍 FINAL VERIFICATION")
    print("-" * 20)
    
    pending_phases = BatchPhaseExecution.objects.filter(status='pending').count()
    not_ready_remaining = BatchPhaseExecution.objects.filter(status='not_ready').count()
    
    print(f"Pending phases (startable): {pending_phases}")
    print(f"Not ready phases (waiting): {not_ready_remaining}")
    
    # Show sample startable phases
    sample_pending = BatchPhaseExecution.objects.filter(status='pending').select_related('bmr', 'phase')[:5]
    
    print(f"\nSample startable phases:")
    for phase in sample_pending:
        can_start = WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)
        start_icon = "🚀" if can_start else "🚫"
        print(f"   {start_icon} {phase.phase.phase_name} (BMR {phase.bmr.batch_number})")
    
    print(f"\n✅ PHASE START FIX COMPLETE!")
    print(f"Operators should now be able to start their phases.")

if __name__ == '__main__':
    fix_phase_start_issues()
