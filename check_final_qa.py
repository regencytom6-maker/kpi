#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from bmr.models import BMR

# Check which BMRs have Final QA phases ready
final_qa_phases = BatchPhaseExecution.objects.filter(
    phase__phase_name='final_qa',
    status='pending'
).select_related('bmr', 'phase')

print(f"Final QA phases ready for QA dashboard: {final_qa_phases.count()}")

for phase in final_qa_phases:
    print(f"  BMR {phase.bmr.batch_number}: {phase.bmr.product.product_name} - Status: {phase.status}")
    
    # Check if QA can work on this
    qa_phases = WorkflowService.get_phases_for_user_role(phase.bmr, 'qa')
    qa_final_qa = [p for p in qa_phases if p.phase.phase_name == 'final_qa']
    
    if qa_final_qa:
        print(f"    ✅ This phase will show on QA dashboard")
    else:
        print(f"    ❌ This phase will NOT show on QA dashboard")

# Also check if the logic is correctly triggering the next phases
print(f"\n=== Testing next phase trigger for BMR 0042025 ===")
bmr = BMR.objects.get(batch_number='0042025')

# Get secondary packaging phase
secondary_phase = BatchPhaseExecution.objects.filter(
    bmr=bmr,
    phase__phase_name='secondary_packaging'
).first()

if secondary_phase:
    print(f"Secondary packaging status: {secondary_phase.status}")
    
    if secondary_phase.status == 'completed':
        print("Secondary packaging is completed - Final QA should be available")
        
        # Check Final QA status
        final_qa = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name='final_qa'
        ).first()
        
        if final_qa:
            print(f"Final QA status: {final_qa.status}")
            if final_qa.status == 'pending':
                print("✅ Final QA is ready and should appear on QA dashboard!")
            else:
                print(f"❌ Final QA is not ready yet: {final_qa.status}")
        else:
            print("❌ Final QA phase not found")
    else:
        print(f"Secondary packaging not completed yet: {secondary_phase.status}")
else:
    print("Secondary packaging phase not found")
