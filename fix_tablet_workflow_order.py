#!/usr/bin/env python
"""
Repair script: Ensures all coated tablet BMRs have correct workflow order:
... -> sorting -> coating -> packaging_material_release -> packing
Uncoated tablets skip coating.
Run with: python fix_tablet_workflow_order.py
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from products.models import Product
from django.db import transaction

def fix_tablet_bmr_workflow():
    print("\n=== Repairing tablet BMR workflows ===")
    bmr_qs = BMR.objects.filter(product__product_type='tablet')
    for bmr in bmr_qs:
        is_coated = getattr(bmr.product, 'is_coated', False)
        tablet_type = getattr(bmr.product, 'tablet_type', None)
        print(f"\nBMR {bmr.batch_number}: {bmr.product.product_name} (Coated: {is_coated}, Type: {tablet_type})")
        # Build correct phase list
        phase_names = [
            'bmr_creation', 'regulatory_approval', 'material_dispensing',
            'granulation', 'blending', 'compression', 'post_compression_qc', 'sorting'
        ]
        if is_coated:
            phase_names.append('coating')
        phase_names.append('packaging_material_release')
        if tablet_type == 'tablet_2':
            phase_names.append('bulk_packing')
        else:
            phase_names.append('blister_packing')
        phase_names += ['secondary_packaging', 'final_qa', 'finished_goods_store']
        # Remove duplicates
        seen = set()
        phase_names = [x for x in phase_names if not (x in seen or seen.add(x))]
        # Get all phase objects in correct order
        phases = [ProductionPhase.objects.get(product_type='tablet', phase_name=pn) for pn in phase_names]
        # Update phase_order in ProductionPhase if needed
        for idx, phase in enumerate(phases, 1):
            if phase.phase_order != idx:
                phase.phase_order = idx
                phase.save()
        # Update or create BatchPhaseExecution for each phase
        with transaction.atomic():
            for idx, phase in enumerate(phases, 1):
                bpe, created = BatchPhaseExecution.objects.get_or_create(bmr=bmr, phase=phase)
                # Set status for first phase(s)
                if phase.phase_name == 'bmr_creation':
                    bpe.status = 'completed'
                elif phase.phase_name == 'regulatory_approval':
                    bpe.status = 'pending'
                elif phase.phase_name == 'coating' and not is_coated:
                    bpe.status = 'skipped'
                elif idx == 1 or (idx == 2 and phases[0].phase_name == 'bmr_creation'):
                    bpe.status = 'pending'
                else:
                    bpe.status = 'not_ready'
                bpe.save()
            # Remove any extra phases not in the correct list
            BatchPhaseExecution.objects.filter(bmr=bmr).exclude(phase__in=phases).delete()
        print(f"  ✔ Workflow phases repaired for {bmr.batch_number}")

if __name__ == '__main__':
    fix_tablet_bmr_workflow()
    print("\nDone. All tablet BMRs now have correct workflow order and statuses.")
