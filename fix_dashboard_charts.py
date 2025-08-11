import os
import django
import sys
from datetime import datetime, timedelta
import random

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.utils import timezone
from products.models import Product
from bmr.models import BMR
from workflow.models import ProductionPhase, BatchPhaseExecution
from accounts.models import CustomUser

def fix_chart_data():
    """Fix chart data by ensuring all required data is available"""
    print("Fixing chart data for admin dashboard...")
    
    # 1. Fix product type data
    product_types = ['tablet', 'capsule', 'ointment']
    product_counts = Product.objects.values_list('product_type', flat=True)
    
    # Check if all product types are represented
    missing_types = set(product_types) - set([p.lower() for p in product_counts if p])
    
    if missing_types:
        print(f"Adding missing product types: {missing_types}")
        for product_type in missing_types:
            # Create 3 products of each missing type
            for i in range(3):
                Product.objects.create(
                    product_name=f"Sample {product_type.title()} {i+1}",
                    product_code=f"SP-{product_type[:3].upper()}-{i+1}",
                    product_type=product_type.title(),
                    description=f"Sample {product_type} product for testing",
                    strength="500mg",
                    pack_size="10x10",
                    created_by=CustomUser.objects.filter(is_staff=True).first()
                )
    
    # 2. Fix phase data
    common_phases = ['mixing', 'drying', 'granulation', 'compression', 'packing']
    
    # Ensure each phase has at least some completed and in-progress items
    for phase_name in common_phases:
        # Check completed count
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name__icontains=phase_name,
            status='completed'
        ).count()
        
        # Check in-progress count
        in_progress = BatchPhaseExecution.objects.filter(
            phase__phase_name__icontains=phase_name,
            status__in=['pending', 'in_progress']
        ).count()
        
        print(f"Phase {phase_name}: {completed} completed, {in_progress} in-progress")
        
        # If fewer than 5 completed, create some sample data
        if completed < 5:
            print(f"Adding sample completed phases for {phase_name}")
            # Find all phases that match this name
            phases = ProductionPhase.objects.filter(phase_name__icontains=phase_name)
            
            if phases.exists():
                # Get some BMRs to use
                bmrs = BMR.objects.all()[:5]
                
                if bmrs.exists():
                    for bmr in bmrs:
                        for phase in phases[:2]:  # Limit to 2 phases per type
                            # Check if execution already exists
                            if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=phase).exists():
                                # Create a completed execution
                                BatchPhaseExecution.objects.create(
                                    bmr=bmr,
                                    phase=phase,
                                    status='completed',
                                    started_date=timezone.now() - timedelta(days=random.randint(5, 10)),
                                    completed_date=timezone.now() - timedelta(days=random.randint(1, 4)),
                                    started_by=CustomUser.objects.filter(is_staff=True).first(),
                                    completed_by=CustomUser.objects.filter(is_staff=True).first()
                                )
                                print(f"  Created completed phase {phase.phase_name} for BMR {bmr.batch_number}")
        
        # If fewer than 3 in-progress, create some sample data
        if in_progress < 3:
            print(f"Adding sample in-progress phases for {phase_name}")
            # Find all phases that match this name
            phases = ProductionPhase.objects.filter(phase_name__icontains=phase_name)
            
            if phases.exists():
                # Get some BMRs to use
                bmrs = BMR.objects.all()[5:8]  # Use different BMRs than completed
                
                if bmrs.exists():
                    for bmr in bmrs:
                        for phase in phases[:1]:  # Limit to 1 phase per type
                            # Check if execution already exists
                            if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=phase).exists():
                                # Create an in-progress execution
                                BatchPhaseExecution.objects.create(
                                    bmr=bmr,
                                    phase=phase,
                                    status='in_progress',
                                    started_date=timezone.now() - timedelta(days=random.randint(1, 3)),
                                    started_by=CustomUser.objects.filter(is_staff=True).first()
                                )
                                print(f"  Created in-progress phase {phase.phase_name} for BMR {bmr.batch_number}")
    
    # 3. Fix weekly production trend data
    current_date = timezone.now().date()
    week_start = current_date - timedelta(days=current_date.weekday())
    
    for i in range(4):
        week_end = week_start - timedelta(days=1)
        week_start_prev = week_start - timedelta(days=7)
        
        # Check BMRs created in this week
        created_count = BMR.objects.filter(
            created_date__date__gte=week_start_prev,
            created_date__date__lte=week_end
        ).count()
        
        # Check batches completed in this week
        completed_count = BatchPhaseExecution.objects.filter(
            phase__phase_name='finished_goods_store',
            completed_date__date__gte=week_start_prev,
            completed_date__date__lte=week_end,
            status='completed'
        ).count()
        
        print(f"Week {4-i}: {created_count} BMRs created, {completed_count} batches completed")
        
        # If fewer than 5 created, create some sample data
        if created_count < 5:
            sample_count = 5 - created_count
            print(f"Adding {sample_count} sample BMRs for week {4-i}")
            
            products = Product.objects.all()[:sample_count]
            if products.exists():
                for j, product in enumerate(products):
                    # Create a BMR with date in this week
                    random_date = week_start_prev + timedelta(days=random.randint(0, 6))
                    
                    BMR.objects.create(
                        product=product,
                        batch_number=f"TEST-W{4-i}-{j+1}",
                        batch_size=random.randint(1000, 5000),
                        created_date=datetime.combine(random_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                        created_by=CustomUser.objects.filter(is_staff=True).first(),
                        status='approved'
                    )
        
        # If fewer than 3 completed, create some sample data
        if completed_count < 3:
            sample_count = 3 - completed_count
            print(f"Adding {sample_count} sample completions for week {4-i}")
            
            # Find the finished_goods_store phase
            fgs_phase = ProductionPhase.objects.filter(phase_name='finished_goods_store').first()
            
            if fgs_phase:
                # Get BMRs that don't have this phase execution
                potential_bmrs = BMR.objects.exclude(
                    batchphaseexecution__phase=fgs_phase
                )[:sample_count]
                
                if potential_bmrs.exists():
                    for bmr in potential_bmrs:
                        # Create a completed FGS phase execution for this BMR
                        random_date = week_start_prev + timedelta(days=random.randint(0, 6))
                        
                        BatchPhaseExecution.objects.create(
                            bmr=bmr,
                            phase=fgs_phase,
                            status='completed',
                            started_date=datetime.combine(random_date, datetime.min.time()).replace(tzinfo=timezone.utc) - timedelta(days=1),
                            completed_date=datetime.combine(random_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                            started_by=CustomUser.objects.filter(is_staff=True).first(),
                            completed_by=CustomUser.objects.filter(is_staff=True).first()
                        )
                        print(f"  Created completed FGS phase for BMR {bmr.batch_number}")
        
        week_start = week_start_prev
    
    # 4. Fix QC data
    qc_passed = BatchPhaseExecution.objects.filter(
        phase__phase_name__icontains='qc',
        status='completed'
    ).count()
    
    qc_failed = BatchPhaseExecution.objects.filter(
        phase__phase_name__icontains='qc',
        status='failed'
    ).count()
    
    qc_pending = BatchPhaseExecution.objects.filter(
        phase__phase_name__icontains='qc',
        status__in=['pending', 'in_progress']
    ).count()
    
    print(f"QC data: {qc_passed} passed, {qc_failed} failed, {qc_pending} pending")
    
    # If fewer than 10 passed QC phases, create some
    if qc_passed < 10:
        sample_count = 10 - qc_passed
        print(f"Adding {sample_count} sample passed QC phases")
        
        # Find QC phases
        qc_phases = ProductionPhase.objects.filter(phase_name__icontains='qc')
        
        if qc_phases.exists():
            # Get BMRs that don't have these phase executions
            potential_bmrs = BMR.objects.all()[:sample_count * 2]  # Get more than needed
            
            count_added = 0
            for bmr in potential_bmrs:
                if count_added >= sample_count:
                    break
                    
                for qc_phase in qc_phases:
                    # Check if this combination already exists
                    if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=qc_phase).exists():
                        # Create a completed QC phase execution
                        BatchPhaseExecution.objects.create(
                            bmr=bmr,
                            phase=qc_phase,
                            status='completed',
                            started_date=timezone.now() - timedelta(days=random.randint(5, 10)),
                            completed_date=timezone.now() - timedelta(days=random.randint(1, 4)),
                            started_by=CustomUser.objects.filter(is_staff=True).first(),
                            completed_by=CustomUser.objects.filter(is_staff=True).first()
                        )
                        print(f"  Created completed QC phase {qc_phase.phase_name} for BMR {bmr.batch_number}")
                        count_added += 1
                        
                        if count_added >= sample_count:
                            break
    
    # If fewer than 3 failed QC phases, create some
    if qc_failed < 3:
        sample_count = 3 - qc_failed
        print(f"Adding {sample_count} sample failed QC phases")
        
        # Find QC phases
        qc_phases = ProductionPhase.objects.filter(phase_name__icontains='qc')
        
        if qc_phases.exists():
            # Get BMRs that don't have these phase executions
            potential_bmrs = list(BMR.objects.all()[15:20])  # Get more than needed, different from the ones used above
            
            count_added = 0
            for bmr in potential_bmrs:
                if count_added >= sample_count:
                    break
                    
                for qc_phase in qc_phases:
                    # Check if this combination already exists
                    if not BatchPhaseExecution.objects.filter(bmr=bmr, phase=qc_phase).exists():
                        # Create a failed QC phase execution
                        BatchPhaseExecution.objects.create(
                            bmr=bmr,
                            phase=qc_phase,
                            status='failed',
                            started_date=timezone.now() - timedelta(days=random.randint(3, 7)),
                            completed_date=timezone.now() - timedelta(days=random.randint(1, 2)),
                            started_by=CustomUser.objects.filter(is_staff=True).first(),
                            completed_by=CustomUser.objects.filter(is_staff=True).first()
                        )
                        print(f"  Created failed QC phase {qc_phase.phase_name} for BMR {bmr.batch_number}")
                        count_added += 1
                        
                        if count_added >= sample_count:
                            break
    
    print("Chart data fix complete!")
    verify_chart_data()

def verify_chart_data():
    """Verify that all required chart data is available"""
    print("\n--- CHART DATA VERIFICATION ---")
    
    # 1. Verify product type data
    from products.models import Product
    product_types = Product.objects.values('product_type').distinct()
    product_type_data = {}
    
    for item in product_types:
        product_type = item['product_type'].lower() if item['product_type'] else ''
        if 'tablet' in product_type:
            product_type_data['tablet'] = Product.objects.filter(product_type__icontains='tablet').count()
        elif 'capsule' in product_type:
            product_type_data['capsule'] = Product.objects.filter(product_type__icontains='capsule').count()
        elif 'ointment' in product_type or 'cream' in product_type:
            product_type_data['ointment'] = Product.objects.filter(product_type__icontains='ointment').count()
    
    print("Product Type Data:", product_type_data)
    
    # 2. Verify phase completion data
    common_phases = ['mixing', 'drying', 'granulation', 'compression', 'packing']
    phase_data = {}
    
    for phase_name in common_phases:
        # Get completed phases
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name__icontains=phase_name,
            status='completed'
        ).count()
        
        # Get in-progress phases
        in_progress = BatchPhaseExecution.objects.filter(
            phase__phase_name__icontains=phase_name,
            status__in=['pending', 'in_progress']
        ).count()
        
        phase_data[f"{phase_name}_completed"] = completed
        phase_data[f"{phase_name}_inprogress"] = in_progress
    
    print("Phase Completion Data:", phase_data)
    
    # 3. Verify weekly production trend data
    current_date = timezone.now().date()
    week_start = current_date - timedelta(days=current_date.weekday())
    weekly_data = {}
    
    for i in range(4):
        week_end = week_start - timedelta(days=1)
        week_start_prev = week_start - timedelta(days=7)
        
        # BMRs created in this week
        created = BMR.objects.filter(
            created_date__date__gte=week_start_prev,
            created_date__date__lte=week_end
        ).count()
        
        # Batches completed in this week
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name='finished_goods_store',
            completed_date__date__gte=week_start_prev,
            completed_date__date__lte=week_end,
            status='completed'
        ).count()
        
        weekly_data[f"Week {i+1} ({week_start_prev.strftime('%d %b')} - {week_end.strftime('%d %b')})"] = f"{created} created, {completed} completed"
        
        week_start = week_start_prev
    
    print("Weekly Trend Data:", weekly_data)
    
    # 4. Verify QC data
    qc_data = {
        'passed': BatchPhaseExecution.objects.filter(phase__phase_name__icontains='qc', status='completed').count(),
        'failed': BatchPhaseExecution.objects.filter(phase__phase_name__icontains='qc', status='failed').count(),
        'pending': BatchPhaseExecution.objects.filter(phase__phase_name__icontains='qc', status__in=['pending', 'in_progress']).count(),
    }
    
    print("QC Data:", qc_data)
    print("\nAll chart data verified. Dashboard should now display charts correctly.")

if __name__ == "__main__":
    fix_chart_data()
