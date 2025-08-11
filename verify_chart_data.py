"""
Script to verify that the admin dashboard charts are working correctly
"""

import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db.models import Count
from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from django.utils import timezone
from datetime import datetime, timedelta

def verify_chart_data():
    """Verify that chart data is correctly populated"""
    print("\n--- ANALYTICS PANEL DATA VERIFICATION ---\n")
    
    # 1. Verify Product Type Data
    print("1. PRODUCT TYPE DATA:")
    completed_bmrs = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_store',
        status='completed'
    ).select_related('bmr__product')
    
    product_type_data = {}
    for execution in completed_bmrs:
        product_type = execution.bmr.product.product_type
        if product_type not in product_type_data:
            product_type_data[product_type] = 0
        product_type_data[product_type] += 1
    
    print(f"   Product type data found: {product_type_data}")
    
    # 2. Verify Phase Completion
    print("\n2. PHASE COMPLETION DATA:")
    all_phases = BatchPhaseExecution.objects.values('phase__phase_name').distinct()
    for phase_dict in all_phases:
        phase_name = phase_dict['phase__phase_name']
        if phase_name:
            total = BatchPhaseExecution.objects.filter(phase__phase_name=phase_name).count()
            completed = BatchPhaseExecution.objects.filter(
                phase__phase_name=phase_name,
                status='completed'
            ).count()
            if total > 0:  # Avoid division by zero
                completion_rate = (completed / total) * 100
            else:
                completion_rate = 0
            print(f"   {phase_name}: {completed}/{total} ({round(completion_rate, 1)}%)")
    
    # 3. Weekly Production Trend
    print("\n3. WEEKLY PRODUCTION TREND:")
    today = timezone.now().date()
    start_date = today - timezone.timedelta(days=28)  # Last 4 weeks
    
    for i in range(4):  # 4 weeks
        week_start = start_date + timezone.timedelta(days=i*7)
        week_end = week_start + timezone.timedelta(days=6)
        week_label = f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}"
        
        count = BatchPhaseExecution.objects.filter(
            phase__phase_name='finished_goods_store',
            status='completed',
            completed_date__date__range=[week_start, week_end]
        ).count()
        print(f"   {week_label}: {count} batches completed")
    
    # 4. QC Statistics
    print("\n4. QC STATISTICS:")
    qc_passed = BatchPhaseExecution.objects.filter(
        phase__phase_name__in=['post_compression_qc', 'post_mixing_qc', 'post_blending_qc'],
        status='completed'
    ).count()
    
    qc_failed = BatchPhaseExecution.objects.filter(
        phase__phase_name__in=['post_compression_qc', 'post_mixing_qc', 'post_blending_qc'],
        status='failed'
    ).count()
    
    print(f"   QC Tests Passed: {qc_passed}")
    print(f"   QC Tests Failed: {qc_failed}")
    print(f"   Pass Rate: {round((qc_passed / (qc_passed + qc_failed or 1)) * 100, 1)}%")
    
    # Summary
    print("\n--- DATA VERIFICATION SUMMARY ---")
    if product_type_data:
        print("✅ Product Type Chart: Data available")
    else:
        print("❌ Product Type Chart: No data available")
        
    if all_phases:
        print("✅ Phase Completion Chart: Data available")
    else:
        print("❌ Phase Completion Chart: No data available")
    
    weekly_total = sum(BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_store',
        status='completed',
        completed_date__date__range=[start_date, today]
    ).count() for _ in range(4))
    
    if weekly_total > 0:
        print("✅ Weekly Trend Chart: Data available")
    else:
        print("❌ Weekly Trend Chart: No data available")
    
    if qc_passed > 0 or qc_failed > 0:
        print("✅ QC Statistics Chart: Data available")
    else:
        print("❌ QC Statistics Chart: No data available")
    
    print("\nVisit the admin FGS monitor page to verify all charts are displaying correctly")
    print("URL: http://127.0.0.1:8000/dashboards/admin/fgs-monitor/")

if __name__ == "__main__":
    verify_chart_data()
