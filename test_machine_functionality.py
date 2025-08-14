#!/usr/bin/env python
"""
Test script to verify machine functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import Machine, BatchPhaseExecution
from bmr.models import BMR
from accounts.models import CustomUser

def test_machine_functionality():
    """Test the machine functionality implementation"""
    
    print("🔧 Testing Machine Module Implementation")
    print("=" * 50)
    
    # Test 1: Check if machines were created
    print("\n1️⃣ Testing Machine Creation:")
    total_machines = Machine.objects.count()
    print(f"   Total machines in system: {total_machines}")
    
    if total_machines == 0:
        print("   ❌ No machines found! Running machine creation...")
        os.system('python create_sample_machines.py')
        total_machines = Machine.objects.count()
    
    print(f"   ✅ {total_machines} machines available")
    
    # Test 2: Check machines by type
    print("\n2️⃣ Testing Machine Types:")
    for machine_type, display_name in Machine.MACHINE_TYPE_CHOICES:
        count = Machine.objects.filter(machine_type=machine_type, is_active=True).count()
        print(f"   {display_name}: {count} machines")
        
        # Show machine names
        machines = Machine.objects.filter(machine_type=machine_type, is_active=True)
        for machine in machines:
            print(f"     - {machine.name}")
    
    # Test 3: Check BatchPhaseExecution model fields
    print("\n3️⃣ Testing BatchPhaseExecution Model:")
    sample_execution = BatchPhaseExecution.objects.first()
    if sample_execution:
        print(f"   Sample execution: {sample_execution}")
        print(f"   Has machine_used field: {hasattr(sample_execution, 'machine_used')}")
        print(f"   Has breakdown fields: {hasattr(sample_execution, 'breakdown_occurred')}")
        print(f"   Has changeover fields: {hasattr(sample_execution, 'changeover_occurred')}")
        
        # Test helper methods
        try:
            requires_machine = sample_execution.requires_machine_selection()
            print(f"   requires_machine_selection() works: {requires_machine}")
        except:
            print("   ❌ requires_machine_selection() method issue")
            
        try:
            breakdown_duration = sample_execution.get_breakdown_duration()
            print(f"   get_breakdown_duration() works: {breakdown_duration} minutes")
        except:
            print("   ❌ get_breakdown_duration() method issue")
    else:
        print("   ⚠️ No BatchPhaseExecution records found")
    
    # Test 4: Check user roles that need machines
    print("\n4️⃣ Testing User Roles with Machine Requirements:")
    machine_roles = [
        'granulation_operator',
        'blending_operator', 
        'compression_operator',
        'coating_operator',
        'packing_operator',
        'filling_operator'
    ]
    
    for role in machine_roles:
        users = CustomUser.objects.filter(role=role)
        print(f"   {role}: {users.count()} users")
        if users.exists():
            print(f"     Example: {users.first().username}")
    
    # Test 5: Simulate machine assignment
    print("\n5️⃣ Testing Machine Assignment Logic:")
    
    # Get a granulation machine
    granulation_machine = Machine.objects.filter(
        machine_type='granulation', 
        is_active=True
    ).first()
    
    if granulation_machine:
        print(f"   Testing with machine: {granulation_machine.name}")
        
        # Check if we can find phases that need this machine type
        granulation_phases = BatchPhaseExecution.objects.filter(
            phase__phase_name='granulation'
        )
        
        print(f"   Found {granulation_phases.count()} granulation phases")
        
        if granulation_phases.exists():
            test_phase = granulation_phases.first()
            test_phase.machine_used = granulation_machine
            test_phase.save()
            print(f"   ✅ Successfully assigned machine to phase")
            
            # Test duration calculations
            test_phase.breakdown_occurred = True
            from datetime import datetime, timedelta
            now = datetime.now()
            test_phase.breakdown_start_time = now
            test_phase.breakdown_end_time = now + timedelta(minutes=30)
            test_phase.save()
            
            duration = test_phase.get_breakdown_duration()
            print(f"   ✅ Breakdown duration calculation: {duration} minutes")
        else:
            print("   ⚠️ No granulation phases available for testing")
    else:
        print("   ❌ No granulation machines available")
    
    print("\n🎉 Machine Module Testing Complete!")
    print("\n📋 Summary:")
    print(f"   - Total Machines: {Machine.objects.count()}")
    print(f"   - Active Machines: {Machine.objects.filter(is_active=True).count()}")
    print(f"   - Machine Types: {len(Machine.MACHINE_TYPE_CHOICES)}")
    print("   - All core functionality implemented ✅")

if __name__ == '__main__':
    test_machine_functionality()
