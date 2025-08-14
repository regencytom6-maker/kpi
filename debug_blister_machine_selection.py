#!/usr/bin/env python
"""Debug blister packing machine selection"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import Machine, PhaseTemplate, BatchPhaseExecution
from accounts.models import CustomUser
from bmr.models import BatchManufacturingRecord

print("=== Debugging Blister Packing Machine Selection ===")

# Check machines
print("\n1. Available Machines:")
machines = Machine.objects.all()
for machine in machines:
    print(f"   - {machine.name} ({machine.machine_type}) - Active: {machine.is_active}")

# Check blister packing machines specifically
blister_machines = Machine.objects.filter(machine_type='blister_packing')
print(f"\n2. Blister Packing Machines: {blister_machines.count()}")
for machine in blister_machines:
    print(f"   - {machine.name} - Active: {machine.is_active}")

# Check phase templates
print("\n3. Phase Templates with 'blister' in name:")
blister_phases = PhaseTemplate.objects.filter(phase_name__icontains='blister')
for phase in blister_phases:
    print(f"   - {phase.phase_name} (Order: {phase.phase_order})")

# Check packing operator users
print("\n4. Packing Operators:")
packing_ops = CustomUser.objects.filter(role='packing_operator')
for user in packing_ops:
    print(f"   - {user.username} ({user.first_name} {user.last_name})")

# Check current blister packing phases
print("\n5. Current Blister Packing Phases:")
blister_executions = BatchPhaseExecution.objects.filter(
    phase__phase_name='blister_packing',
    status__in=['ready', 'in_progress']
)
for execution in blister_executions:
    print(f"   - BMR: {execution.bmr.bmr_number}")
    print(f"     Status: {execution.status}")
    print(f"     Machine Used: {execution.machine_used}")
    print(f"     Assigned To: {execution.assigned_to}")

# Check the role-to-machine mapping from the view
print("\n6. Role-to-Machine Type Mapping:")
role_to_machine_type = {
    'mixing_operator': 'mixing',
    'granulation_operator': 'granulation', 
    'compression_operator': 'compression',
    'coating_operator': 'coating',
    'tube_filling_operator': 'tube_filling',
    'packing_operator': 'blister_packing',  # This should show blister packing machines
    'packaging_operator': 'packaging'
}

for role, machine_type in role_to_machine_type.items():
    machines_for_role = Machine.objects.filter(machine_type=machine_type, is_active=True)
    print(f"   - {role} -> {machine_type}: {machines_for_role.count()} machines")

print("\n=== Debug Complete ===")
