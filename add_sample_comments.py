#!/usr/bin/env python
"""
Simple test script to generate sample comments for testing the report system
"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR, BMRSignature
from workflow.models import BatchPhaseExecution
from accounts.models import CustomUser

def create_sample_comments():
    """Add some sample comments to existing data for testing"""
    print("🧪 ADDING SAMPLE COMMENTS FOR TESTING")
    print("=" * 40)
    
    # Get some existing BMRs
    bmrs = BMR.objects.all()[:3]
    if not bmrs:
        print("❌ No BMRs found. Please create some BMRs first.")
        return
    
    # Add QA comments to BMRs
    for i, bmr in enumerate(bmrs):
        if not bmr.qa_comments:
            bmr.qa_comments = f"Quality assurance review completed for batch {bmr.batch_number}. All specifications met. Sample #{i+1} comment."
            bmr.save()
            print(f"✅ Added QA comments to BMR {bmr.batch_number}")
        
        if not bmr.regulatory_comments and bmr.status in ['approved', 'submitted']:
            bmr.regulatory_comments = f"Regulatory review for {bmr.batch_number}: Documentation complete and compliant with guidelines. Approved for production."
            bmr.save()
            print(f"✅ Added regulatory comments to BMR {bmr.batch_number}")
    
    # Add operator comments to some phases
    phases = BatchPhaseExecution.objects.filter(status__in=['completed', 'in_progress'])[:5]
    for i, phase in enumerate(phases):
        if not phase.operator_comments:
            phase.operator_comments = f"Phase {phase.phase.phase_name} completed successfully. Temperature maintained at optimal levels. Quality checks passed. Operator note #{i+1}."
            phase.save()
            print(f"✅ Added operator comments to {phase.bmr.batch_number} - {phase.phase.phase_name}")
    
    # Add some rejection reasons
    failed_phases = BatchPhaseExecution.objects.filter(status='failed')[:2]
    for i, phase in enumerate(failed_phases):
        if not phase.rejection_reason:
            phase.rejection_reason = f"Quality control failed: pH levels outside acceptable range. Batch returned for rework. Rejection #{i+1}."
            phase.save()
            print(f"❌ Added rejection reason to {phase.bmr.batch_number} - {phase.phase.phase_name}")
    
    print(f"\n📊 Sample comments added successfully!")
    print("You can now test the comments report system with sample data.")

if __name__ == "__main__":
    create_sample_comments()
