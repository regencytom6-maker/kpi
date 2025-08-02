#!/usr/bin/env python
"""
Test actual phase starting functionality - simulate what happens when clicking start button
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
from accounts.models import CustomUser
from django.utils import timezone

def test_actual_phase_start():
    print("🧪 TESTING ACTUAL PHASE START FUNCTIONALITY")
    print("=" * 50)
    
    # Find a startable phase
    startable_phases = []
    for phase in BatchPhaseExecution.objects.filter(status='pending'):
        if WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name):
            startable_phases.append(phase)
    
    if not startable_phases:
        print("❌ No startable phases found!")
        return
    
    # Test with the first available phase
    test_phase = startable_phases[0]
    print(f"🎯 Testing with: {test_phase.phase.phase_name} on BMR {test_phase.bmr.batch_number}")
    print(f"   Phase ID: {test_phase.id}")
    print(f"   Current status: {test_phase.status}")
    
    # Get or create a test user for the appropriate role
    phase_role_mapping = {
        'mixing': 'mixing_operator',
        'granulation': 'granulation_operator',
        'blending': 'blending_operator',
        'compression': 'compression_operator',
        'coating': 'coating_operator',
        'drying': 'drying_operator'
    }
    
    required_role = phase_role_mapping.get(test_phase.phase.phase_name, 'operator')
    
    # Try to find an existing user with the right role, or create one
    test_user = CustomUser.objects.filter(role=required_role).first()
    if not test_user:
        print(f"   Creating test user with role: {required_role}")
        test_user = CustomUser.objects.create_user(
            username=f"test_{required_role}",
            email=f"test_{required_role}@kampala.com",
            role=required_role,
            first_name="Test",
            last_name="User"
        )
    
    print(f"   Using user: {test_user.username} ({test_user.role})")
    
    # Test the WorkflowService.start_phase method directly
    print(f"\n🚀 Attempting to start phase...")
    
    # Store original state
    original_status = test_phase.status
    original_started_by = test_phase.started_by
    original_started_date = test_phase.started_date
    
    try:
        # Call the start_phase method
        result = WorkflowService.start_phase(test_phase.bmr, test_phase.phase.phase_name, test_user)
        
        if result:
            print(f"   ✅ SUCCESS! Phase started successfully")
            
            # Refresh from database
            test_phase.refresh_from_db()
            print(f"   New status: {test_phase.status}")
            print(f"   Started by: {test_phase.started_by}")
            print(f"   Started date: {test_phase.started_date}")
            
            # Now test completing the phase
            print(f"\n⏭️ Testing phase completion...")
            completion_result = WorkflowService.complete_phase(
                test_phase.bmr, 
                test_phase.phase.phase_name, 
                test_user,
                "Test completion"
            )
            
            if completion_result:
                print(f"   ✅ Phase completed successfully!")
                test_phase.refresh_from_db()
                print(f"   Final status: {test_phase.status}")
                print(f"   Completed by: {test_phase.completed_by}")
                print(f"   Next phase triggered: {completion_result.phase.phase_name if completion_result else 'None'}")
            else:
                print(f"   ❌ Failed to complete phase")
            
        else:
            print(f"   ❌ FAILED to start phase")
            
            # Check why it failed
            print(f"\n🔍 Diagnosing failure...")
            print(f"   Phase status: {test_phase.status}")
            print(f"   Can start check: {WorkflowService.can_start_phase(test_phase.bmr, test_phase.phase.phase_name)}")
            
            # Check if user has permission
            user_phases = WorkflowService.get_phases_for_user_role(test_phase.bmr, test_user.role)
            user_can_work_on_phase = any(p.id == test_phase.id for p in user_phases)
            print(f"   User can work on this phase: {user_can_work_on_phase}")
    
    except Exception as e:
        print(f"   ❌ ERROR starting phase: {e}")
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
    
    # Test the dashboard POST simulation
    print(f"\n🌐 Testing Dashboard POST Simulation...")
    
    # Reset phase for testing
    try:
        if test_phase.status != 'pending':
            test_phase.status = 'pending'
            test_phase.started_by = None
            test_phase.started_date = None
            test_phase.completed_by = None
            test_phase.completed_date = None
            test_phase.operator_comments = ''
            test_phase.save()
            print(f"   Reset phase to pending for testing")
    except:
        pass
    
    # Simulate what the dashboard view does
    try:
        print(f"   Simulating dashboard POST request...")
        
        # Check the same validation as dashboard
        user_phases = WorkflowService.get_phases_for_user_role(test_phase.bmr, test_user.role)
        phase_in_user_list = user_phases.filter(phase__phase_name=test_phase.phase.phase_name, status='pending').exists()
        
        print(f"   Phase in user's phase list: {phase_in_user_list}")
        
        if phase_in_user_list:
            # Check prerequisites
            can_start = WorkflowService.can_start_phase(test_phase.bmr, test_phase.phase.phase_name)
            print(f"   Prerequisites met: {can_start}")
            
            if can_start:
                # Simulate the dashboard action
                test_phase.status = 'in_progress'
                test_phase.started_by = test_user
                test_phase.started_date = timezone.now()
                test_phase.operator_comments = f"Started by {test_user.get_full_name()}. Notes: Test start"
                test_phase.save()
                
                print(f"   ✅ Dashboard simulation successful!")
                print(f"   Phase status: {test_phase.status}")
            else:
                print(f"   ❌ Prerequisites not met")
        else:
            print(f"   ❌ Phase not in user's available phases")
            
    except Exception as e:
        print(f"   ❌ Dashboard simulation failed: {e}")
    
    # Show final summary
    print(f"\n📋 FINAL STATUS:")
    test_phase.refresh_from_db()
    print(f"   Phase: {test_phase.phase.phase_name}")
    print(f"   Status: {test_phase.status}")
    print(f"   BMR: {test_phase.bmr.batch_number}")
    
    # Check what phases are available right now
    print(f"\n🔍 CURRENT AVAILABLE PHASES:")
    current_startable = []
    for phase in BatchPhaseExecution.objects.filter(status='pending'):
        if WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name):
            current_startable.append(phase)
    
    print(f"   Total startable phases: {len(current_startable)}")
    for phase in current_startable[:5]:  # Show first 5
        print(f"   🚀 {phase.phase.phase_name} (BMR {phase.bmr.batch_number}) - ID: {phase.id}")

if __name__ == '__main__':
    test_actual_phase_start()
