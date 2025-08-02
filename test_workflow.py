#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.services import WorkflowService
from accounts.models import CustomUser

def test_workflow():
    print("Testing Workflow Service...")
    
    # Get a sample BMR
    bmr = BMR.objects.first()
    if not bmr:
        print("No BMR found. Please create one first.")
        return
    
    print(f"Testing with BMR: {bmr.batch_number} - {bmr.product.product_name}")
    
    # Test different user roles
    roles = ['mixing_operator', 'qc', 'regulatory_affairs', 'store_manager']
    
    for role in roles:
        phases = WorkflowService.get_phases_for_user_role(bmr, role)
        print(f"\n{role}: {len(phases)} phases")
        for phase in phases:
            print(f"  - {phase.phase.phase_name}: {phase.status}")
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_workflow()
