from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService

@login_required
def timeline_list_view(request):
    """Enhanced timeline list view showing all BMRs with visual progress"""
    # Check if user is admin/staff - they see all BMRs
    is_admin = request.user.is_staff or request.user.is_superuser or request.user.role == 'admin'
    
    if is_admin:
        bmrs = BMR.objects.all().select_related('product', 'created_by').order_by('-created_date')
    else:
        # Operators only see BMRs they were involved in
        bmrs = BMR.objects.filter(
            Q(created_by=request.user) | Q(approved_by=request.user)
        ).select_related('product', 'created_by').order_by('-created_date')
    
    # Add progress information to each BMR
    bmr_progress = []
    stats = {'completed': 0, 'in_progress': 0, 'partially_complete': 0, 'not_started': 0}
    
    for bmr in bmrs:
        phases = BatchPhaseExecution.objects.filter(bmr=bmr)
        total_phases = phases.count()
        completed_phases = phases.filter(status='completed').count()
        in_progress_phases = phases.filter(status='in_progress').count()
        
        progress_percentage = (completed_phases / total_phases * 100) if total_phases > 0 else 0
        
        # Determine status
        if completed_phases == total_phases and total_phases > 0:
            status = 'completed'
            status_class = 'success'
        elif in_progress_phases > 0:
            status = 'in_progress'
            status_class = 'primary'
        elif completed_phases > 0:
            status = 'partially_complete'
            status_class = 'warning'
        else:
            status = 'not_started'
            status_class = 'secondary'
        
        # Update stats
        stats[status] += 1
        
        bmr_progress.append({
            'bmr': bmr,
            'total_phases': total_phases,
            'completed_phases': completed_phases,
            'progress_percentage': progress_percentage,
            'status': status,
            'status_class': status_class
        })
    
    context = {
        'bmr_progress': bmr_progress,
        'is_admin': is_admin,
        'total_bmrs': len(bmr_progress),
        'stats': stats,
    }
    
    return render(request, 'reports/timeline_list.html', context)

@login_required
def enhanced_timeline_view(request, bmr_id):
    """Enhanced timeline view with visual progress tracking"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Check if user has access to this BMR
    is_admin = request.user.is_staff or request.user.is_superuser or request.user.role == 'admin'
    
    if not is_admin:
        # Check user access
        user_bmrs = BMR.objects.filter(
            Q(created_by=request.user) | Q(approved_by=request.user)
        )
        user_phases = BatchPhaseExecution.objects.filter(
            Q(started_by=request.user) | Q(completed_by=request.user),
            bmr=bmr
        )
        
        if not (bmr in user_bmrs or user_phases.exists()):
            from django.contrib import messages
            messages.error(request, 'Access denied. You can only view BMRs you were involved in.')
            return redirect('reports:comments_report')
    
    # Get all phases for this BMR
    phase_executions = BatchPhaseExecution.objects.filter(bmr=bmr).select_related(
        'phase', 'started_by', 'completed_by'
    ).order_by('phase__phase_order')
    
    # Calculate overall progress
    total_phases = phase_executions.count()
    completed_phases = phase_executions.filter(status='completed').count()
    overall_progress = (completed_phases / total_phases * 100) if total_phases > 0 else 0
    
    # Find current phase
    current_phase = None
    next_phase = None
    
    for phase in phase_executions:
        if phase.status in ['pending', 'in_progress']:
            if not current_phase:
                current_phase = phase
            elif phase.status == 'in_progress':
                current_phase = phase
                break
    
    # Find next phase
    if current_phase:
        next_phases = phase_executions.filter(
            phase__phase_order__gt=current_phase.phase.phase_order,
            status='pending'
        ).order_by('phase__phase_order')
        if next_phases.exists():
            next_phase = next_phases.first()
    
    # Group phases into implementation stages (like the diagram)
    phase_groups = []
    
    # Development Phase (Early phases)
    development_phases = phase_executions.filter(
        phase__phase_name__in=[
            'material_dispensing', 'mixing', 'granulation', 'blending'
        ]
    )
    
    # Quality Control Phase (QC phases)
    qc_phases = phase_executions.filter(
        phase__phase_name__in=[
            'post_mixing_qc', 'post_blending_qc', 'post_compression_qc'
        ]
    )
    
    # Production Phase (Main production)
    production_phases = phase_executions.filter(
        phase__phase_name__in=[
            'compression', 'coating', 'drying', 'filling', 'tube_filling'
        ]
    )
    
    # Packaging Phase (Packaging operations)
    packaging_phases = phase_executions.filter(
        phase__phase_name__in=[
            'sorting', 'bulk_packing', 'packaging_material_release', 
            'blister_packing', 'secondary_packaging'
        ]
    )
    
    # Final Phase (Final operations)
    final_phases = phase_executions.filter(
        phase__phase_name__in=[
            'final_qa', 'finished_goods_store'
        ]
    )
    
    # Calculate progress for each group
    def calculate_group_progress(phases):
        if not phases.exists():
            return 0, 'not-ready'
        completed = phases.filter(status='completed').count()
        in_progress = phases.filter(status='in_progress').count()
        total = phases.count()
        
        if completed == total:
            return 100, 'completed'
        elif in_progress > 0 or completed > 0:
            return (completed / total * 100), 'in-progress'
        else:
            return 0, 'pending'
    
    dev_progress, dev_status = calculate_group_progress(development_phases)
    qc_progress, qc_status = calculate_group_progress(qc_phases)
    prod_progress, prod_status = calculate_group_progress(production_phases)
    pack_progress, pack_status = calculate_group_progress(packaging_phases)
    final_progress, final_status = calculate_group_progress(final_phases)
    
    phase_groups = [
        {
            'name': 'Planning & Setup',
            'icon': 'fas fa-lightbulb',
            'color': 'warning',
            'phases': development_phases,
            'progress': dev_progress,
            'status': dev_status,
            'description': 'Material preparation and initial processing'
        },
        {
            'name': 'Quality Control',
            'icon': 'fas fa-microscope',
            'color': 'info',
            'phases': qc_phases,
            'progress': qc_progress,
            'status': qc_status,
            'description': 'Quality testing and validation'
        },
        {
            'name': 'Production',
            'icon': 'fas fa-cogs',
            'color': 'primary',
            'phases': production_phases,
            'progress': prod_progress,
            'status': prod_status,
            'description': 'Core manufacturing operations'
        },
        {
            'name': 'Packaging',
            'icon': 'fas fa-boxes',
            'color': 'success',
            'phases': packaging_phases,
            'progress': pack_progress,
            'status': pack_status,
            'description': 'Packaging and material handling'
        },
        {
            'name': 'Go Live!',
            'icon': 'fas fa-rocket',
            'color': 'dark',
            'phases': final_phases,
            'progress': final_progress,
            'status': final_status,
            'description': 'Final approval and storage'
        }
    ]
    
    context = {
        'bmr': bmr,
        'phase_executions': phase_executions,
        'overall_progress': overall_progress,
        'current_phase': current_phase,
        'next_phase': next_phase,
        'phase_groups': phase_groups,
        'total_phases': total_phases,
        'completed_phases': completed_phases,
        'remaining_phases': total_phases - completed_phases,
        'is_admin': is_admin
    }
    
    return render(request, 'reports/enhanced_timeline.html', context)
