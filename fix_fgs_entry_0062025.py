#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution

batch_number = '0062025'

bmr = BMR.objects.filter(batch_number=batch_number).first()
if not bmr:
    print(f"❌ BMR {batch_number} not found.")
    sys.exit(1)

print(f"=== Diagnosing Packing & FGS Entry for BMR {batch_number} ===\n")

packing_executions = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name__icontains='packing').order_by('phase__phase_order')
for pe in packing_executions:
    print(f"Packing phase: {pe.phase.phase_name} | Status: {pe.status}")

# Fix: Set the latest packing phase to completed if not already
def fix_packing():
    latest_packing = packing_executions.last()
    if latest_packing and latest_packing.status != 'completed':
        latest_packing.status = 'completed'
        latest_packing.save()
        print(f"✅ Fixed: Set {latest_packing.phase.phase_name} to completed.")
    else:
        print("No fix needed. Latest packing phase already completed.")

fix_packing()

# Show FGS phase status
def show_fgs():
    fgs = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='finished_goods_store').first()
    if fgs:
        print(f"FGS phase status: {fgs.status}")
    else:
        print("No FGS phase found for this BMR.")

show_fgs()

print("\nDone.")
