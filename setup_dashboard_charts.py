"""
Test script to verify the admin dashboard charts are working
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from products.models import Product
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase

def setup_test_data():
    """Set up test data for dashboard charts"""
    print("Setting up test data for dashboard charts...")
    
    # 1. Check Product counts
    product_types = Product.objects.values('product_type').annotate(count=Count('product_type'))
    print("\nProduct types in system:")
    for pt in product_types:
        print(f"- {pt['product_type']}: {pt['count']} products")
    
    # 2. Check batch phases
    phase_names = BatchPhaseExecution.objects.values_list('phase__phase_name', flat=True).distinct()
    print("\nPhase types in system:")
    for phase_name in sorted(set(phase_names)):
        total = BatchPhaseExecution.objects.filter(phase__phase_name=phase_name).count()
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name=phase_name,
            status='completed'
        ).count()
        inprogress = BatchPhaseExecution.objects.filter(
            phase__phase_name=phase_name,
            status='in_progress'
        ).count()
        print(f"- {phase_name}: {completed} completed, {inprogress} in progress, {total} total")
    
    # 3. Weekly data
    print("\nSetting up weekly production data...")
    today = timezone.now().date()
    
    # Get FGS phases
    fgs_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_store',
        status='completed'
    ).order_by('completed_date')
    
    if fgs_phases.exists():
        # Distribute them over the last 4 weeks
        week_count = min(4, fgs_phases.count())
        phases_per_week = max(1, fgs_phases.count() // week_count)
        
        for i, phase in enumerate(fgs_phases):
            week_offset = min(3, i // phases_per_week)
            days_ago = 7 * week_offset + (i % 7)
            completion_date = today - timedelta(days=days_ago)
            
            phase.completed_date = timezone.make_aware(
                timezone.datetime.combine(completion_date, timezone.datetime.min.time())
            )
            phase.save()
        
        print(f"Updated {fgs_phases.count()} FGS phases with dates over the last {week_count} weeks")
    
    # 4. QC data
    print("\nSetting up QC data...")
    qc_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name__icontains='qc'
    )
    
    passed_count = qc_phases.filter(status='completed').count()
    failed_count = qc_phases.filter(status='failed').count()
    pending_count = qc_phases.filter(status__in=['pending', 'in_progress']).count()
    
    # If no failed QC phases, mark some as failed
    if failed_count == 0 and passed_count > 0:
        phases_to_fail = min(3, passed_count)
        for phase in qc_phases.filter(status='completed')[:phases_to_fail]:
            phase.status = 'failed'
            phase.save()
        print(f"Marked {phases_to_fail} QC phases as failed for chart data")
    
    # Final QC stats
    qc_passed = qc_phases.filter(status='completed').count()
    qc_failed = qc_phases.filter(status='failed').count()
    qc_pending = qc_phases.filter(status__in=['pending', 'in_progress']).count()
    
    print(f"QC Stats: {qc_passed} passed, {qc_failed} failed, {qc_pending} pending")
    
    print("\nDashboard test data setup complete!")
    print("Visit: http://127.0.0.1:8000/dashboard/admin-overview/")

if __name__ == "__main__":
    setup_test_data()
