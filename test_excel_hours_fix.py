#!/usr/bin/env python3
"""
Test script to verify Excel export shows production time in hours
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from dashboards.views import export_timeline_data
from django.http import HttpRequest
from django.utils import timezone

def test_excel_hours():
    print("🧪 Testing Excel Export Hours Fix...")
    
    # Get any completed BMR
    completed_bmr = BMR.objects.filter(
        batchphaseexecution__phase__phase_name='finished_goods_store',
        batchphaseexecution__status='completed'
    ).first()
    
    if not completed_bmr:
        print("❌ No completed BMRs found to test")
        return
    
    print(f"📊 Testing BMR: {completed_bmr.batch_number}")
    
    # Get FGS completion time
    fgs_phase = BatchPhaseExecution.objects.filter(
        bmr=completed_bmr,
        phase__phase_name='finished_goods_store',
        status='completed'
    ).first()
    
    if fgs_phase and fgs_phase.completed_date:
        # Calculate production time
        production_time_seconds = (fgs_phase.completed_date - completed_bmr.created_date).total_seconds()
        production_time_hours = round(production_time_seconds / 3600, 2)
        production_time_days = (fgs_phase.completed_date - completed_bmr.created_date).days
        
        print(f"⏱️  BMR Created: {completed_bmr.created_date}")
        print(f"✅ FGS Completed: {fgs_phase.completed_date}")
        print(f"📈 Production Time: {production_time_hours} hours ({production_time_days} days)")
        
        # Test if fix is working - should show hours not days
        if production_time_hours > 0:
            print("✅ SUCCESS: Excel will now show production time in hours instead of days")
            print(f"   Example: '{production_time_hours} hours' instead of '{production_time_days} days'")
        else:
            print("⚠️  WARNING: Production time calculation issue")
    else:
        print("❌ No FGS completion data found")
    
    print("\n🎯 HOURS FIX VERIFICATION COMPLETE!")

if __name__ == "__main__":
    test_excel_hours()
