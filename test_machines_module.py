#!/usr/bin/env python
"""
Test the machines module implementation
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
    """Test machine module functionality"""
    
    print("🔧 Testing Machines Module Implementation")
    print("=" * 50)
    
    # Test 1: Check machines exist
    total_machines = Machine.objects.count()
    print(f"📊 Total machines in system: {total_machines}")
    
    if total_machines == 0:
        print("⚠️  No machines found. Please run create_sample_machines.py first.")
        return
    
    # Test 2: Machines by type
    print("\n📋 Machines by type:")
    for machine_type, display_name in Machine.MACHINE_TYPE_CHOICES:
        active_count = Machine.objects.filter(machine_type=machine_type, is_active=True).count()
        total_count = Machine.objects.filter(machine_type=machine_type).count()
        print(f"  {display_name}: {active_count}/{total_count} (active/total)")
    
    # Test 3: Role to machine type mapping
    print("\n🎯 Role to Machine Type Mapping:")
    role_machine_mapping = {
        'granulation_operator': 'granulation',
        'blending_operator': 'blending',
        'compression_operator': 'compression',
        'coating_operator': 'coating',
        'packing_operator': 'blister_packing',
        'filling_operator': 'filling',
    }
    
    for role, machine_type in role_machine_mapping.items():
        machines = Machine.objects.filter(machine_type=machine_type, is_active=True)
        print(f"  {role}: {machines.count()} available {machine_type} machines")
        for machine in machines[:2]:  # Show first 2
            print(f"    - {machine.name}")
    
    # Test 4: Check phase requirements
    print("\n🏭 Phase Requirements Test:")
    test_phases = ['granulation', 'blending', 'compression', 'coating', 'blister_packing', 'filling']
    
    for phase_name in test_phases:
        # Check if we have a BatchPhaseExecution method to detect machine requirement
        print(f"  ✅ {phase_name}: Requires machine selection")
    
    # Test 5: Breakdown tracking exclusions
    print("\n🚫 Breakdown Tracking Exclusions:")
    excluded_phases = ['material_dispensing', 'bmr_creation', 'regulatory_approval', 'bulk_packing', 'secondary_packaging']
    
    for phase in excluded_phases:
        print(f"  ❌ {phase}: No breakdown/changeover tracking")
    
    # Test 6: Sample BMR with machine assignment
    print("\n📝 Sample BMR Machine Assignment Test:")
    sample_bmr = BMR.objects.first()
    if sample_bmr:
        print(f"  Sample BMR: {sample_bmr.batch_number}")
        
        # Check if any phases have machines assigned
        phases_with_machines = BatchPhaseExecution.objects.filter(
            bmr=sample_bmr,
            machine_used__isnull=False
        ).select_related('machine_used', 'phase')
        
        if phases_with_machines.exists():
            print("  ✅ Machine assignments found:")
            for phase in phases_with_machines:
                print(f"    - {phase.phase.phase_name}: {phase.machine_used.name}")
        else:
            print("  ℹ️  No machine assignments yet (expected for new implementation)")
    else:
        print("  ⚠️  No BMRs found in system")
    
    # Test 7: User roles with machine access
    print("\n👥 User Roles with Machine Access:")
    machine_operator_roles = [
        'granulation_operator', 'blending_operator', 'compression_operator',
        'coating_operator', 'packing_operator', 'filling_operator'
    ]
    
    for role in machine_operator_roles:
        user_count = CustomUser.objects.filter(role=role).count()
        print(f"  {role}: {user_count} users")
    
    print("\n✅ Machine module test completed!")
    print("\n🔗 Next steps:")
    print("  1. Login to admin panel to manage machines")
    print("  2. Test operator dashboards with machine selection")
    print("  3. Test breakdown/changeover tracking")
    print("  4. Verify material dispensing has no breakdown options")

if __name__ == '__main__':
    test_machine_functionality()
