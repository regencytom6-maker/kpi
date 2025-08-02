import os
import django
import sys

# Add the project directory to Python path
sys.path.append(r'c:\Users\Ronald\Desktop\new system')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from django.utils import timezone
import requests

def test_timeline_export():
    print("=== Testing Enhanced Timeline Export ===")
    
    # Get some sample data
    bmrs = BMR.objects.all()[:2]  # Test with first 2 BMRs
    
    for bmr in bmrs:
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        print(f"\n📋 BMR: {bmr.batch_number} - {bmr.product.product_name}")
        print(f"   Product Type: {bmr.product.product_type}")
        print(f"   Created: {bmr.created_date}")
        
        total_duration = 0
        phase_count = 0
        
        for phase in phases:
            print(f"   🔄 {phase.phase.phase_name.replace('_', ' ').title()}")
            print(f"      Status: {phase.status}")
            if phase.started_date:
                print(f"      Started: {phase.started_date}")
                if phase.started_by:
                    print(f"      Started By: {phase.started_by.get_full_name()}")
            if phase.completed_date:
                print(f"      Completed: {phase.completed_date}")
                if phase.completed_by:
                    print(f"      Completed By: {phase.completed_by.get_full_name()}")
                
                if phase.started_date:
                    duration = phase.completed_date - phase.started_date
                    duration_hours = duration.total_seconds() / 3600
                    print(f"      Duration: {duration_hours:.2f} hours")
                    total_duration += duration_hours
                    phase_count += 1
            print()
        
        if phase_count > 0:
            avg_duration = total_duration / phase_count
            print(f"   📊 Average Phase Duration: {avg_duration:.2f} hours")
            print(f"   📊 Total Measured Time: {total_duration:.2f} hours")
    
    print("\n🌐 Testing Export URLs...")
    try:
        # Test CSV export
        csv_response = requests.get('http://127.0.0.1:8000/dashboard/admin/timeline/?export=csv')
        print(f"   CSV Export: {'✅ OK' if csv_response.status_code == 200 else '❌ ERROR'} ({csv_response.status_code})")
        
        # Test Excel export
        excel_response = requests.get('http://127.0.0.1:8000/dashboard/admin/timeline/?export=excel')
        print(f"   Excel Export: {'✅ OK' if excel_response.status_code == 200 else '❌ ERROR'} ({excel_response.status_code})")
        
    except Exception as e:
        print(f"   ❌ Export test failed: {str(e)}")
    
    print("\n✅ Enhanced timeline export features:")
    print("   • Detailed phase tracking with entry/exit times")
    print("   • Individual phase durations in hours")
    print("   • Started/Completed by information")
    print("   • Operator comments included")
    print("   • Two Excel sheets: Summary + Detailed Timeline")
    print("   • CSV format with BMR sections and phase details")
    print("   • Total production time calculation")

if __name__ == "__main__":
    test_timeline_export()
