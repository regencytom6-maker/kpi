#!/usr/bin/env python3
"""
DIRECT FIX FOR BMR 0152025
==========================
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase, BatchPhaseExecution
from bmr.models import BMR

# Get BMR 0152025
bmr = BMR.objects.get(batch_number='0152025')
print(f"Fixing BMR: {bmr.batch_number}")

# Get the phases
bulk_phase_exec = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='bulk_packing')
secondary_phase_exec = BatchPhaseExecution.objects.get(bmr=bmr, phase__phase_name='secondary_packaging')

print(f"Current bulk_packing order: {bulk_phase_exec.phase.phase_order}")
print(f"Current secondary_packaging order: {secondary_phase_exec.phase.phase_order}")

# Get the correct phase definitions
correct_bulk = ProductionPhase.objects.get(product_type='tablet_2', phase_name='bulk_packing')
correct_secondary = ProductionPhase.objects.get(product_type='tablet_2', phase_name='secondary_packaging')

print(f"Correct bulk_packing order: {correct_bulk.phase_order}")
print(f"Correct secondary_packaging order: {correct_secondary.phase_order}")

# Update the phase executions to use the correct phases
bulk_phase_exec.phase = correct_bulk
bulk_phase_exec.save()

secondary_phase_exec.phase = correct_secondary
secondary_phase_exec.save()

# Fix the status - bulk should be pending, secondary should be not_ready
if secondary_phase_exec.status == 'pending' and bulk_phase_exec.status == 'not_ready':
    bulk_phase_exec.status = 'pending'
    bulk_phase_exec.save()
    
    secondary_phase_exec.status = 'not_ready'
    secondary_phase_exec.save()
    
    print("✅ Fixed status: bulk_packing -> pending, secondary_packaging -> not_ready")

print("✅ BMR 0152025 has been fixed!")

# Verify
phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
print("\nVerification - Current workflow order:")
for phase in phases:
    print(f"  {phase.phase.phase_order:2d}. {phase.phase.phase_name:25} {phase.status}")
