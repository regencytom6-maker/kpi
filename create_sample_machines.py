#!/usr/bin/env python
"""
Create sample machines for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import Machine

def create_sample_machines():
    """Create sample machines for each phase type"""
    
    machines_data = [
        # Granulation machines
        {'name': 'Granulator M-01', 'machine_type': 'granulation'},
        {'name': 'Granulator M-02', 'machine_type': 'granulation'},
        {'name': 'High Shear Mixer G-03', 'machine_type': 'granulation'},
        
        # Blending machines
        {'name': 'V-Blender B-01', 'machine_type': 'blending'},
        {'name': 'V-Blender B-02', 'machine_type': 'blending'},
        {'name': 'Octagonal Blender B-03', 'machine_type': 'blending'},
        
        # Compression machines
        {'name': 'Tablet Press TP-01', 'machine_type': 'compression'},
        {'name': 'Tablet Press TP-02', 'machine_type': 'compression'},
        {'name': 'Rotary Press TP-03', 'machine_type': 'compression'},
        
        # Coating machines
        {'name': 'Coating Pan CP-01', 'machine_type': 'coating'},
        {'name': 'Coating Pan CP-02', 'machine_type': 'coating'},
        
        # Blister packing machines
        {'name': 'Blister Pack BP-01', 'machine_type': 'blister_packing'},
        {'name': 'Blister Pack BP-02', 'machine_type': 'blister_packing'},
        {'name': 'Auto Blister BP-03', 'machine_type': 'blister_packing'},
        
        # Capsule filling machines
        {'name': 'Capsule Filler CF-01', 'machine_type': 'filling'},
        {'name': 'Capsule Filler CF-02', 'machine_type': 'filling'},
        {'name': 'Auto Capsule Filler CF-03', 'machine_type': 'filling'},
    ]
    
    print("Creating sample machines...")
    created_count = 0
    
    for machine_data in machines_data:
        machine, created = Machine.objects.get_or_create(
            name=machine_data['name'],
            defaults={
                'machine_type': machine_data['machine_type'],
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created: {machine.name} ({machine.get_machine_type_display()})")
            created_count += 1
        else:
            print(f"⚠️  Already exists: {machine.name}")
    
    print(f"\n🎉 Successfully created {created_count} new machines!")
    print(f"📊 Total machines in system: {Machine.objects.count()}")
    
    # Show summary by type
    print("\n📋 Machines by type:")
    for machine_type, display_name in Machine.MACHINE_TYPE_CHOICES:
        count = Machine.objects.filter(machine_type=machine_type, is_active=True).count()
        print(f"  {display_name}: {count} machines")

if __name__ == '__main__':
    create_sample_machines()
