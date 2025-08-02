#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmaceutical_operations.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from bmr.models import BMR
from accounts.models import CustomUser

def test_qa_two_step_workflow():
    print("=== Testing QA Two-Step Workflow ===\n")
    
    # Find Final QA phases
    final_qa_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='final_qa'
    ).select_related('bmr', 'phase', 'started_by', 'completed_by')
    
    if not final_qa_phases.exists():
        print("❌ No Final QA phases found")
        return
    
    print(f"📊 Found {final_qa_phases.count()} Final QA phases\n")
    
    # Group phases by status
    pending_phases = final_qa_phases.filter(status='pending')
    in_progress_phases = final_qa_phases.filter(status='in_progress')
    completed_phases = final_qa_phases.filter(status='completed')
    failed_phases = final_qa_phases.filter(status='failed')
    
    print(f"📋 Status Summary:")
    print(f"   • Pending (Ready to Start): {pending_phases.count()}")
    print(f"   • In Progress (Ready to Complete): {in_progress_phases.count()}")
    print(f"   • Completed (Approved): {completed_phases.count()}")
    print(f"   • Failed (Rejected): {failed_phases.count()}\n")
    
    # Show phases ready to start
    if pending_phases.exists():
        print("🟡 PHASES READY TO START:")
        for i, phase in enumerate(pending_phases, 1):
            print(f"   {i}. BMR: {phase.bmr.batch_number}")
            print(f"      Product: {phase.bmr.product.product_name}")
            print(f"      Product Type: {phase.bmr.product.product_type}")
            print(f"      Status: {phase.status.upper()}")
            print(f"      Action: Can click 'Start Review' button")
            print()
    
    # Show phases in progress (ready to approve/reject)
    if in_progress_phases.exists():
        print("🔵 PHASES IN PROGRESS (Ready to Complete):")
        for i, phase in enumerate(in_progress_phases, 1):
            print(f"   {i}. BMR: {phase.bmr.batch_number}")
            print(f"      Product: {phase.bmr.product.product_name}")
            print(f"      Product Type: {phase.bmr.product.product_type}")
            print(f"      Status: {phase.status.upper()}")
            print(f"      Started By: {phase.started_by.get_full_name() if phase.started_by else 'Unknown'}")
            print(f"      Started Date: {phase.started_date}")
            print(f"      Actions: Can click 'Approve' or 'Reject' buttons")
            print()
    
    # Show completed phases
    if completed_phases.exists():
        print("✅ COMPLETED PHASES (Approved):")
        for i, phase in enumerate(completed_phases, 1):
            print(f"   {i}. BMR: {phase.bmr.batch_number}")
            print(f"      Product: {phase.bmr.product.product_name}")
            print(f"      Completed By: {phase.completed_by.get_full_name() if phase.completed_by else 'Unknown'}")
            print(f"      Completed Date: {phase.completed_date}")
            print(f"      Status: APPROVED ✅")
            print()
    
    # Show rejected phases
    if failed_phases.exists():
        print("❌ REJECTED PHASES:")
        for i, phase in enumerate(failed_phases, 1):
            print(f"   {i}. BMR: {phase.bmr.batch_number}")
            print(f"      Product: {phase.bmr.product.product_name}")
            print(f"      Rejected By: {phase.completed_by.get_full_name() if phase.completed_by else 'Unknown'}")
            print(f"      Rejected Date: {phase.completed_date}")
            print(f"      Status: REJECTED ❌")
            if phase.operator_comments:
                print(f"      Comments: {phase.operator_comments}")
            print()
    
    # Check QA users
    qa_users = CustomUser.objects.filter(role='qa', is_active=True)
    print(f"👥 Available QA Users: {qa_users.count()}")
    for qa_user in qa_users:
        print(f"   • {qa_user.get_full_name()} ({qa_user.username})")
    
    print("\n" + "="*50)
    print("WORKFLOW EXPLANATION:")
    print("1. Pending phases show 'Start Review' button")
    print("2. After starting, phases move to 'In Progress'")
    print("3. In Progress phases show 'Approve' and 'Reject' buttons")
    print("4. QA Officer can only approve/reject after starting the review")
    print("5. Comments are required for approval/rejection")
    print("="*50)

if __name__ == "__main__":
    test_qa_two_step_workflow()
