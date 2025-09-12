from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService

@login_required
def store_dashboard_sidebar(request):
    """Store Manager Dashboard with Sidebar Navigation - Raw Material Release Phase"""
    if request.user.role != 'store_manager':
        messages.error(request, 'Access denied. Store Manager role required.')
        return redirect('dashboards:dashboard_home')
    
    if request.method == 'POST':
        bmr_id = request.POST.get('bmr_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        try:
            bmr = BMR.objects.get(pk=bmr_id)
            
            # Get the raw material release phase
            phase_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name='raw_material_release'
            )
            
            if action == 'start':
                # Check if all required materials have passed QC
                if not all_materials_qc_approved(bmr):
                    messages.error(request, f'Cannot start raw material release for batch {bmr.batch_number}. Some materials have not passed QC.')
                    return redirect('dashboards:store_dashboard_sidebar')
                
                phase_execution.status = 'in_progress'
                phase_execution.started_by = request.user
                phase_execution.started_date = timezone.now()
                phase_execution.operator_comments = f"Raw material release started by {request.user.get_full_name()}. Notes: {notes}"
                phase_execution.save()
                
                messages.success(request, f'Raw material release started for batch {bmr.batch_number}.')
                
            elif action == 'complete':
                phase_execution.status = 'completed'
                phase_execution.completed_by = request.user
                phase_execution.completed_date = timezone.now()
                phase_execution.operator_comments = f"Raw materials released by {request.user.get_full_name()}. Notes: {notes}"
                phase_execution.save()
                
                # Trigger next phase in workflow (material_dispensing)
                WorkflowService.trigger_next_phase(bmr, phase_execution.phase)
                
                messages.success(request, f'Raw materials released for batch {bmr.batch_number}. Material dispensing is now available.')
                
        except Exception as e:
            messages.error(request, f'Error processing raw material release: {str(e)}')
    
        return redirect('dashboards:store_dashboard_sidebar')
    
    # Get all BMRs
    all_bmrs = BMR.objects.select_related('product', 'created_by').all()
    
    # Import raw materials models
    from raw_materials.models import RawMaterial, RawMaterialBatch, RawMaterialQC, MaterialDispensing
    
    # Get raw materials inventory statistics
    total_materials = RawMaterial.objects.count()
    total_batches = RawMaterialBatch.objects.count()
    
    # Get pending QC materials
    pending_qc_count = RawMaterialBatch.objects.filter(status='pending_qc').count()
    pending_qc_batches = RawMaterialBatch.objects.filter(
        status='pending_qc'
    ).select_related('material').order_by('-received_date')[:10]
    
    # Get QC approved materials
    approved_materials = RawMaterialBatch.objects.filter(
        status='approved',
        quantity_remaining__gt=0
    ).select_related('material').order_by('-received_date')[:10]
    
    # Get all materials for the dropdown
    all_materials = RawMaterial.objects.all().order_by('material_name')
    
    # Get raw material release phases that are pending or in-progress
    my_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='raw_material_release',
        status__in=['pending', 'in_progress']
    ).select_related('bmr', 'bmr__product')

    # Stats
    stats = {
        'pending_phases': BatchPhaseExecution.objects.filter(phase__phase_name='raw_material_release', status='pending').count(),
        'in_progress_phases': BatchPhaseExecution.objects.filter(phase__phase_name='raw_material_release', status='in_progress').count(),
        'completed_today': BatchPhaseExecution.objects.filter(
            phase__phase_name='raw_material_release',
            status='completed',
            completed_date__date=timezone.now().date()
        ).count(),
        'total_batches': total_batches
    }

    # Get recent material activity
    recent_activity = []  # Placeholder - to be implemented with raw materials module

    return render(request, 'dashboards/store_dashboard_sidebar_simple.html', {
        'my_phases': my_phases,
        'stats': stats,
        'recent_activity': recent_activity,
        'all_materials': all_materials,
        'total_materials': total_materials,
        'total_batches': total_batches,
        'pending_qc_count': pending_qc_count,
        'pending_qc_batches': pending_qc_batches,
        'approved_materials': approved_materials,
        'today': timezone.now(),
    })

def test_sidebar(request):
    """Simple sidebar test view to verify sidebar rendering works"""
    return render(request, 'dashboards/test_sidebar.html')


def all_materials_qc_approved(bmr):
    """Check if all materials for a BMR have passed QC"""
    from raw_materials.models import RawMaterialBMRAssociation, RawMaterialQC
    
    # Get all raw materials associated with this BMR
    material_associations = RawMaterialBMRAssociation.objects.filter(bmr=bmr)
    
    for assoc in material_associations:
        # Check if material has a QC approval
        qc_tests = RawMaterialQC.objects.filter(
            raw_material_batch=assoc.raw_material_batch,
            status='approved'
        )
        
        if not qc_tests.exists():
            return False
    
    return True

@login_required
def sidebar_test(request):
    """Simple test for sidebar layout"""
    return render(request, 'dashboards/sidebar_test.html')

@login_required
def qc_dashboard_sidebar(request):
    """Quality Control Dashboard with Sidebar Navigation"""
    if request.user.role != 'qc_analyst':
        messages.error(request, 'Access denied. Quality Control role required.')
        return redirect('dashboards:dashboard_home')
    
    from raw_materials.models import RawMaterialQC
    
    # Process QC test results submission
    if request.method == 'POST':
        qc_test_id = request.POST.get('qc_test_id')
        action = request.POST.get('action')
        
        try:
            qc_test = RawMaterialQC.objects.get(pk=qc_test_id)
            
            if action == 'approve':
                qc_test.status = 'approved'
                qc_test.completed_date = timezone.now()
                qc_test.completed_by = request.user
                qc_test.save()
                
                messages.success(request, f'QC Test for {qc_test.raw_material_batch} approved successfully.')
                
            elif action == 'reject':
                qc_test.status = 'rejected'
                qc_test.completed_date = timezone.now()
                qc_test.completed_by = request.user
                qc_test.save()
                
                messages.warning(request, f'QC Test for {qc_test.raw_material_batch} rejected.')
                
        except Exception as e:
            messages.error(request, f'Error processing QC test result: {str(e)}')
            
        return redirect('dashboards:qc_dashboard_sidebar')
    
    # Get pending QC tests for raw materials
    pending_tests = RawMaterialQC.objects.filter(
        status='pending'
    ).select_related('raw_material_batch', 'raw_material_batch__raw_material')
    
    # Get recent QC activity
    recent_activity = RawMaterialQC.objects.filter(
        completed_date__isnull=False
    ).order_by('-completed_date')[:10].select_related(
        'raw_material_batch', 
        'raw_material_batch__raw_material',
        'created_by', 
        'completed_by'
    )
    
    # Stats
    stats = {
        'pending_tests': RawMaterialQC.objects.filter(status='pending').count(),
        'approved_today': RawMaterialQC.objects.filter(
            status='approved',
            completed_date__date=timezone.now().date()
        ).count(),
        'rejected_today': RawMaterialQC.objects.filter(
            status='rejected',
            completed_date__date=timezone.now().date()
        ).count(),
        'total_tests': RawMaterialQC.objects.count(),
    }
    
    return render(request, 'dashboards/qc_dashboard_sidebar_simple.html', {
        'pending_tests': pending_tests,
        'recent_activity': recent_activity,
        'stats': stats,
        'today': timezone.now(),
    })
