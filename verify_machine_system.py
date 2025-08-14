#!/usr/bin/env python
"""
Quick verification of machine system components
"""

import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import Machine, BatchPhaseExecution
from django.db import models

def check_machine_system():
    print("🔧 MACHINE SYSTEM VERIFICATION")
    print("=" * 40)
    
    # Check Machine model
    print("1. Machine Model:")
    try:
        machine_count = Machine.objects.count()
        print(f"   ✓ Machine model accessible, count: {machine_count}")
        
        if machine_count > 0:
            sample_machine = Machine.objects.first()
            print(f"   ✓ Sample machine: {sample_machine.name} ({sample_machine.machine_type})")
    except Exception as e:
        print(f"   ❌ Machine model error: {e}")
    
    # Check BatchPhaseExecution model fields
    print("\n2. BatchPhaseExecution Model:")
    try:
        # Check if the new fields exist
        fields = [field.name for field in BatchPhaseExecution._meta.fields]
        machine_fields = ['machine_used', 'breakdown_occurred', 'breakdown_start_time', 
                         'breakdown_end_time', 'breakdown_reason', 'changeover_occurred', 
                         'changeover_start_time', 'changeover_end_time', 'changeover_reason']
        
        for field in machine_fields:
            has_field = field in fields
            print(f"   {'✓' if has_field else '❌'} {field}: {'Present' if has_field else 'Missing'}")
            
    except Exception as e:
        print(f"   ❌ BatchPhaseExecution model error: {e}")
    
    # Check duration properties
    print("\n3. Duration Properties:")
    try:
        execution = BatchPhaseExecution.objects.first()
        if execution:
            has_breakdown_duration = hasattr(execution, 'breakdown_duration')
            has_changeover_duration = hasattr(execution, 'changeover_duration')
            print(f"   {'✓' if has_breakdown_duration else '❌'} breakdown_duration property")
            print(f"   {'✓' if has_changeover_duration else '❌'} changeover_duration property")
        else:
            print("   ⚠ No BatchPhaseExecution records to test")
    except Exception as e:
        print(f"   ❌ Duration properties error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ VERIFICATION COMPLETE")

if __name__ == '__main__':
    check_machine_system()
