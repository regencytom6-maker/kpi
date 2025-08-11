import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution

batch_number = '0032025'  # Change to '0032025' for the other batch

print(f"\n=== BMR {batch_number} ===")
bmr = BMR.objects.filter(batch_number=batch_number).first()
if not bmr:
    print("❌ BMR not found!")
else:
    print(f"Product: {bmr.product.product_name}")
    print(f"Product type: {bmr.product.product_type}")
    is_coated = getattr(bmr.product, 'is_coated', False)
    tablet_type = getattr(bmr.product, 'tablet_type', None)
    print(f"Is coated: {is_coated}")
    print(f"Tablet type: {tablet_type}")

    phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
    print("\nAll phases:")
    for phase in phases:
        print(f"  {phase.phase.phase_order:2d}. {phase.phase.phase_name:25} {phase.status}")

    packing_phases = [p for p in phases if p.phase.phase_name in ['blister_packing', 'bulk_packing', 'secondary_packaging'] and p.status == 'pending']
    if not packing_phases:
        print("No pending packing phases found.")
    else:
        for packing in packing_phases:
            print(f"\n🚩 Blocked Packing Phase: {packing.phase.phase_name}")
            prereqs = [p for p in phases if p.phase.phase_order < packing.phase.phase_order]
            blocking = [p for p in prereqs if p.status not in ['completed', 'skipped']]
            if blocking:
                print("Blocking prerequisite(s):")
                for block in blocking:
                    print(f"  - {block.phase.phase_name}: {block.status}")
            else:
                print("All prerequisites completed/skipped. Should be startable!")