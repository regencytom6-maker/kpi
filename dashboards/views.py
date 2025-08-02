# Basic workflow_chart view to resolve missing view error
from django.contrib.auth.decorators import login_required

@login_required
def workflow_chart(request):
    """Workflow Chart View (placeholder)"""
    return render(request, 'dashboards/workflow_chart.html', {'dashboard_title': 'Workflow Chart'})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Min, Max, F, ExpressionWrapper, DateTimeField, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
import csv
import xlwt
from bmr.models import BMR
from workflow.models import BatchPhaseExecution
from workflow.services import WorkflowService
from products.models import Product
from accounts.models import CustomUser

def dashboard_home(request):
    """Route users to their role-specific dashboard or show welcome page"""
    if not request.user.is_authenticated:
        # Show welcome page for anonymous users
        return render(request, 'dashboards/welcome.html')
    
    user_role = request.user.role
    
    role_dashboard_map = {
        'qa': 'dashboards:qa_dashboard',
        'regulatory': 'dashboards:regulatory_dashboard',
        'store_manager': 'dashboards:store_dashboard',
        'packaging_store': 'dashboards:packaging_dashboard',
        'finished_goods_store': 'dashboards:finished_goods_dashboard',
        'mixing_operator': 'dashboards:mixing_dashboard',
        'qc': 'dashboards:qc_dashboard',
        'tube_filling_operator': 'dashboards:tube_filling_dashboard',
        'packing_operator': 'dashboards:packing_dashboard',
        'granulation_operator': 'dashboards:granulation_dashboard',
        'blending_operator': 'dashboards:blending_dashboard',
        'compression_operator': 'dashboards:compression_dashboard',
        'sorting_operator': 'dashboards:sorting_dashboard',
        'coating_operator': 'dashboards:coating_dashboard',
        'drying_operator': 'dashboards:drying_dashboard',
        'filling_operator': 'dashboards:filling_dashboard',
        'dispensing_operator': 'dashboards:operator_dashboard',
        'equipment_operator': 'dashboards:operator_dashboard',
        'cleaning_operator': 'dashboards:operator_dashboard',
        'admin': 'dashboards:admin_dashboard',
    }
    
    dashboard_url = role_dashboard_map.get(user_role, 'dashboards:admin_dashboard')
    return redirect(dashboard_url)

@login_required
def admin_dashboard(request):
    """Admin Dashboard for system overview and user management"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboards:dashboard_home')
    
    # Get comprehensive BMR statistics
    total_bmrs = BMR.objects.count()
    active_batches = BMR.objects.filter(status__in=['draft', 'approved', 'in_production']).count()
    completed_batches = BMR.objects.filter(status='completed').count()
    rejected_batches = BMR.objects.filter(status='rejected').count()
    
    # Get system metrics
    total_users = CustomUser.objects.count()
    active_users_count = CustomUser.objects.filter(is_active=True, last_login__gte=timezone.now() - timedelta(days=30)).count()
    
    # Get FGS Store data
    fgs_batches = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_storage',
        status__in=['completed', 'in_progress']
    )
    fgs_total_items = fgs_batches.count()
    fgs_low_stock = fgs_batches.filter(
        bmr__product__product_name__icontains='tablet'
    ).count()  # This is a placeholder - you'd need proper inventory tracking
    
    bmrs_this_month = BMR.objects.filter(
        created_date__month=timezone.now().month,
        created_date__year=timezone.now().year
    ).count()
    
    total_products = Product.objects.count()
    products_by_type = Product.objects.values('product_type').annotate(count=Count('product_type'))
    
    # Active workflow phases
    active_phases = BatchPhaseExecution.objects.filter(
        status__in=['pending', 'in_progress']
    ).count()
    
    completed_today = BatchPhaseExecution.objects.filter(
        completed_date__date=timezone.now().date(),
        status='completed'
    ).count()
    
    # Recent activity
    recent_bmrs = BMR.objects.select_related('product', 'created_by').order_by('-created_date')[:10]
    recent_users = CustomUser.objects.filter(is_active=True).order_by('-date_joined')[:10]
    
    # System health metrics
    pending_approvals = BatchPhaseExecution.objects.filter(
        phase__phase_name='regulatory_approval',
        status='pending'
    ).count()
    
    failed_phases = BatchPhaseExecution.objects.filter(
        status='failed',
        completed_date__date=timezone.now().date()
    ).count()
    
    # Production metrics
    production_stats = {
        'in_production': BatchPhaseExecution.objects.filter(
            status='in_progress'
        ).count(),
        'quality_hold': BatchPhaseExecution.objects.filter(
            phase__phase_name__contains='qc',
            status='pending'
        ).count(),
        'awaiting_packaging': BatchPhaseExecution.objects.filter(
            phase__phase_name='packaging_material_release',
            status='pending'
        ).count(),
        'final_qa_pending': BatchPhaseExecution.objects.filter(
            phase__phase_name='final_qa',
            status='pending'
        ).count(),
        'in_fgs': BatchPhaseExecution.objects.filter(
            phase__phase_name='finished_goods_storage',
            status__in=['completed', 'in_progress']
        ).count(),
    }
    
    # Performance metrics - Average cycle time
    completed_bmrs = BMR.objects.filter(status='approved').annotate(
        cycle_time=ExpressionWrapper(
            F('approved_date') - F('created_date'),
            output_field=DateTimeField()
        )
    )
    
    context = {
        'user': request.user,
        'dashboard_title': 'System Administration Dashboard',
        # Key Metrics for cards
        'total_bmrs': total_bmrs,
        'active_batches': active_batches,
        'completed_batches': completed_batches,
        'rejected_batches': rejected_batches,
        # System Status
        'active_users_count': active_users_count,
        # FGS Store data
        'fgs_total_items': fgs_total_items,
        'fgs_low_stock': fgs_low_stock,
        # Detailed stats for other components
        'stats': {
            'total_users': total_users,
            'active_users': active_users_count,
            'total_bmrs': total_bmrs,
            'bmrs_this_month': bmrs_this_month,
            'total_products': total_products,
            'active_phases': active_phases,
            'completed_today': completed_today,
            'pending_approvals': pending_approvals,
            'failed_phases': failed_phases,
        },
        'production_stats': production_stats,
        'users_by_role': CustomUser.objects.values('role').annotate(count=Count('role')).order_by('role'),
        'products_by_type': products_by_type,
        'recent_bmrs': recent_bmrs,
        'recent_users': recent_users,
        'completed_bmrs_count': completed_bmrs.count(),
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def qa_dashboard(request):
    """Quality Assurance Dashboard"""
    if request.user.role != 'qa':
        messages.error(request, 'Access denied. QA role required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle POST requests for Final QA workflow
    if request.method == 'POST':
        action = request.POST.get('action')
        phase_id = request.POST.get('phase_id')
        comments = request.POST.get('comments', '')
        
        if phase_id and action in ['start', 'approve', 'reject']:
            try:
                phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_id)
                
                if action == 'start':
                    # Start the Final QA review process
                    phase_execution.status = 'in_progress'
                    phase_execution.started_by = request.user
                    phase_execution.started_date = timezone.now()
                    phase_execution.operator_comments = f"Final QA review started by {request.user.get_full_name()}. Notes: {comments}"
                    phase_execution.save()
                    
                    messages.success(request, f'Final QA review started for batch {phase_execution.bmr.batch_number}. You can now complete the review.')
                
                elif action == 'approve':
                    # Complete Final QA with approval
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments += f"\nFinal QA Approved by {request.user.get_full_name()}. Comments: {comments}"
                    phase_execution.save()
                    
                    # Trigger next phase in workflow (should be finished goods store)
                    WorkflowService.trigger_next_phase(phase_execution.bmr, phase_execution.phase)
                    
                    messages.success(request, f'Final QA approved for batch {phase_execution.bmr.batch_number}. Batch is ready for finished goods storage.')
                    
                elif action == 'reject':
                    # Complete Final QA with rejection
                    phase_execution.status = 'failed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments += f"\nFinal QA Rejected by {request.user.get_full_name()}. Rejection Reason: {comments}"
                    phase_execution.save()
                    
                    # Rollback to appropriate packing phase based on product type
                    bmr = phase_execution.bmr
                    product_type = bmr.product.product_type
                    
                    # Determine which packing phase to rollback to based on product type
                    if product_type == 'tablet':
                        if hasattr(bmr.product, 'tablet_type') and bmr.product.tablet_type == 'tablet_2':
                            rollback_phase = 'bulk_packing'
                        else:
                            rollback_phase = 'blister_packing'
                    elif product_type == 'capsule':
                        rollback_phase = 'blister_packing'
                    elif product_type == 'ointment':
                        rollback_phase = 'secondary_packaging'
                    else:
                        rollback_phase = 'secondary_packaging'  # default
                    
                    # Find and activate the appropriate packing phase for rework
                    rollback_execution = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name=rollback_phase
                    ).first()
                    
                    if rollback_execution:
                        rollback_execution.status = 'pending'
                        rollback_execution.operator_comments = f"Returned for rework due to Final QA rejection. Reason: {comments}. Original comments: {rollback_execution.operator_comments}"
                        rollback_execution.save()
                        
                        messages.warning(request, f'Final QA rejected for batch {bmr.batch_number}. Batch has been sent back to {rollback_phase.replace("_", " ").title()} for rework.')
                    else:
                        messages.error(request, f'Could not find {rollback_phase} phase to rollback to for batch {bmr.batch_number}.')
                    
            except Exception as e:
                messages.error(request, f'Error processing Final QA: {str(e)}')
        
        return redirect('dashboards:qa_dashboard')
    
    # Get QA-specific data
    total_bmrs = BMR.objects.count()
    draft_bmrs = BMR.objects.filter(status='draft').count()
    submitted_bmrs = BMR.objects.filter(status='submitted').count()
    my_bmrs = BMR.objects.filter(created_by=request.user).count()
    
    # Recent BMRs created by this user
    recent_bmrs = BMR.objects.filter(created_by=request.user).select_related('product').order_by('-created_date')[:5]
    
    # BMRs needing final QA review
    final_qa_pending = BatchPhaseExecution.objects.filter(
        phase__phase_name='final_qa',
        status='pending'
    ).select_related('bmr', 'phase')[:10]
    
    # Final QA reviews in progress (started but not completed)
    final_qa_in_progress = BatchPhaseExecution.objects.filter(
        phase__phase_name='final_qa',
        status='in_progress'
    ).select_related('bmr', 'phase')[:10]
    
    # Build operator history for this user: phases where user created the BMR or was QA (started_by or completed_by)
    recent_phases = BatchPhaseExecution.objects.filter(
        Q(started_by=request.user) | Q(completed_by=request.user) |
        Q(bmr__created_by=request.user)
    ).order_by('-started_date', '-completed_date')[:10]
    operator_history = [
        {
            'date': (p.completed_date or p.started_date or p.created_date).strftime('%Y-%m-%d %H:%M'),
            'batch': p.bmr.batch_number,
            'phase': p.phase.get_phase_name_display(),
        }
        for p in recent_phases
    ]

    context = {
        'user': request.user,
        'total_bmrs': total_bmrs,
        'draft_bmrs': draft_bmrs,
        'submitted_bmrs': submitted_bmrs,
        'my_bmrs': my_bmrs,
        'recent_bmrs': recent_bmrs,
        'final_qa_pending': final_qa_pending,
        'final_qa_in_progress': final_qa_in_progress,
        'dashboard_title': 'Quality Assurance Dashboard',
        'operator_history': operator_history,
    }
    return render(request, 'dashboards/qa_dashboard.html', context)

@login_required
def regulatory_dashboard(request):
    """Regulatory Dashboard"""
    if request.user.role != 'regulatory':
        messages.error(request, 'Access denied. Regulatory role required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle POST requests for approval/rejection
    if request.method == 'POST':
        action = request.POST.get('action')
        bmr_id = request.POST.get('bmr_id')
        comments = request.POST.get('comments', '')
        
        if bmr_id and action in ['approve', 'reject']:
            try:
                bmr = get_object_or_404(BMR, pk=bmr_id)
                
                # Find the regulatory approval phase for this BMR
                regulatory_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='regulatory_approval',
                    status='pending'
                ).first()
                
                if regulatory_phase:
                    if action == 'approve':
                        regulatory_phase.status = 'completed'
                        regulatory_phase.completed_by = request.user
                        regulatory_phase.completed_date = timezone.now()
                        regulatory_phase.operator_comments = f"Approved by {request.user.get_full_name()}. Comments: {comments}"
                        regulatory_phase.save()
                        
                        # Update BMR status
                        bmr.status = 'approved'
                        bmr.approved_by = request.user
                        bmr.approved_date = timezone.now()
                        bmr.save()
                        
                        # Trigger next phase in workflow
                        WorkflowService.trigger_next_phase(bmr, regulatory_phase.phase)
                        
                        messages.success(request, f'BMR {bmr.batch_number} has been approved successfully.')
                        
                    elif action == 'reject':
                        regulatory_phase.status = 'failed'
                        regulatory_phase.completed_by = request.user
                        regulatory_phase.completed_date = timezone.now()
                        regulatory_phase.operator_comments = f"Rejected by {request.user.get_full_name()}. Reason: {comments}"
                        regulatory_phase.save()
                        
                        # Update BMR status
                        bmr.status = 'rejected'
                        bmr.approved_by = request.user
                        bmr.approved_date = timezone.now()
                        bmr.save()
                        
                        messages.warning(request, f'BMR {bmr.batch_number} has been rejected and sent back to QA.')
                else:
                    messages.error(request, 'No pending regulatory approval found for this BMR.')
                    
            except Exception as e:
                messages.error(request, f'Error processing request: {str(e)}')
        
        return redirect('dashboards:regulatory_dashboard')
    
    # BMRs waiting for regulatory approval (pending regulatory_approval phase)
    pending_approvals = BatchPhaseExecution.objects.filter(
        phase__phase_name='regulatory_approval',
        status='pending'
    ).select_related('bmr__product', 'phase').order_by('bmr__created_date')
    
    # Statistics
    stats = {
        'pending_approvals': pending_approvals.count(),
        'approved_today': BMR.objects.filter(
            status='approved',
            approved_date__date=timezone.now().date()
        ).count(),
        'rejected_this_week': BMR.objects.filter(
            status='rejected',
            approved_date__gte=timezone.now().date() - timedelta(days=7)
        ).count(),
        'total_bmrs': BMR.objects.count(),
    }
    
    context = {
        'user': request.user,
        'pending_approvals': pending_approvals,
        'stats': stats,
        'dashboard_title': 'Regulatory Dashboard'
    }
    return render(request, 'dashboards/regulatory_dashboard.html', context)

@login_required
def store_dashboard(request):
    """Store Manager Dashboard - Material Dispensing Only"""
    if request.user.role != 'store_manager':
        messages.error(request, 'Access denied. Store Manager role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get all BMRs
    all_bmrs = BMR.objects.select_related('product', 'created_by').all()
    
    # Get material dispensing phases this user can work on
    my_phases = []
    for bmr in all_bmrs:
        user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
        my_phases.extend(user_phases)
    
    # Statistics
    stats = {
        'pending_phases': len([p for p in my_phases if p.status == 'pending']),
        'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
        'completed_today': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date=timezone.now().date()
        ).count(),
        'total_batches': len(set([p.bmr for p in my_phases])),
    }
    
    daily_progress = min(100, (stats['completed_today'] / max(1, stats['pending_phases'] + stats['completed_today'])) * 100)
    
    context = {
        'user': request.user,
        'my_phases': my_phases,
        'stats': stats,
        'daily_progress': daily_progress,
        'dashboard_title': 'Store Manager Dashboard'
    }
    
    return render(request, 'dashboards/store_dashboard.html', context)

@login_required
def operator_dashboard(request):
    """Generic operator dashboard for production phases"""
    
    # Handle POST requests for phase completion
    if request.method == 'POST':
        action = request.POST.get('action')
        phase_id = request.POST.get('phase_id')
        comments = request.POST.get('comments', '')
        
        if phase_id and action in ['start', 'complete']:
            try:
                phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_id)
                
                if action == 'start':
                    # Validate that the phase can actually be started
                    if not WorkflowService.can_start_phase(phase_execution.bmr, phase_execution.phase.phase_name):
                        messages.error(request, f'Cannot start {phase_execution.phase.phase_name} for batch {phase_execution.bmr.batch_number} - prerequisites not met.')
                        return redirect(request.path)
                    
                    phase_execution.status = 'in_progress'
                    phase_execution.started_by = request.user
                    phase_execution.started_date = timezone.now()
                    phase_execution.operator_comments = f"Started by {request.user.get_full_name()}. Notes: {comments}"
                    phase_execution.save()
                    
                    messages.success(request, f'Phase {phase_execution.phase.phase_name} started for batch {phase_execution.bmr.batch_number}.')
                    
                elif action == 'complete':
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"Completed by {request.user.get_full_name()}. Notes: {comments}"
                    phase_execution.save()
                    
                    # Trigger next phase in workflow
                    WorkflowService.trigger_next_phase(phase_execution.bmr, phase_execution.phase)
                    
                    messages.success(request, f'Phase {phase_execution.phase.phase_name} completed for batch {phase_execution.bmr.batch_number}.')
                    
            except Exception as e:
                messages.error(request, f'Error processing phase: {str(e)}')
        
        return redirect(request.path)  # Redirect to same dashboard
    
    # Get phases this user can work on
    all_bmrs = BMR.objects.select_related('product', 'created_by').all()
    my_phases = []
    
    for bmr in all_bmrs:
        user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
        my_phases.extend(user_phases)
    
    # Statistics
    stats = {
        'pending_phases': len([p for p in my_phases if p.status == 'pending']),
        'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
        'completed_today': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date=timezone.now().date()
        ).count(),
        'total_batches': len(set([p.bmr for p in my_phases])),
    }
    
    # Determine the primary phase name for this role
    role_phase_mapping = {
        'mixing_operator': 'mixing',
        'granulation_operator': 'granulation',
        'blending_operator': 'blending',
        'compression_operator': 'compression',
        'coating_operator': 'coating',
        'drying_operator': 'drying',
        'filling_operator': 'filling',
        'tube_filling_operator': 'tube_filling',
        'packing_operator': 'packing',
        'sorting_operator': 'sorting',
    }
    
    phase_name = role_phase_mapping.get(request.user.role, 'production')
    daily_progress = min(100, (stats['completed_today'] / max(1, stats['pending_phases'] + stats['completed_today'])) * 100)
    
    context = {
        'user': request.user,
        'my_phases': my_phases,
        'stats': stats,
        'phase_name': phase_name,
        'daily_progress': daily_progress,
        'dashboard_title': f'{request.user.get_role_display()} Dashboard'
    }
    
    return render(request, 'dashboards/operator_dashboard.html', context)

# Specific operator dashboards
@login_required
def mixing_dashboard(request):
    return operator_dashboard(request)

@login_required
def granulation_dashboard(request):
    return operator_dashboard(request)

@login_required
def blending_dashboard(request):
    return operator_dashboard(request)

@login_required
def compression_dashboard(request):
    return operator_dashboard(request)

@login_required
def coating_dashboard(request):
    return operator_dashboard(request)

@login_required
def drying_dashboard(request):
    return operator_dashboard(request)

@login_required
def filling_dashboard(request):
    return operator_dashboard(request)

@login_required
def tube_filling_dashboard(request):
    return operator_dashboard(request)

@login_required
def sorting_dashboard(request):
    return operator_dashboard(request)

@login_required
def qc_dashboard(request):
    """Quality Control Dashboard"""
    if request.user.role != 'qc':
        messages.error(request, 'Access denied. QC role required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle POST requests for QC test results
    if request.method == 'POST':
        action = request.POST.get('action')
        phase_id = request.POST.get('phase_id')
        test_results = request.POST.get('test_results', '')
        
        if phase_id and action in ['start', 'pass', 'fail']:
            try:
                phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_id)
                
                if action == 'start':
                    # Start QC testing
                    phase_execution.status = 'in_progress'
                    phase_execution.started_by = request.user
                    phase_execution.started_date = timezone.now()
                    phase_execution.operator_comments = f"QC Testing started by {request.user.get_full_name()}. Notes: {test_results}"
                    phase_execution.save()
                    
                    messages.success(request, f'QC testing started for batch {phase_execution.bmr.batch_number}.')
                
                elif action == 'pass':
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"QC Test Passed by {request.user.get_full_name()}. Results: {test_results}"
                    phase_execution.save()
                    
                    # Trigger next phase in workflow
                    WorkflowService.trigger_next_phase(phase_execution.bmr, phase_execution.phase)
                    
                    messages.success(request, f'QC test passed for batch {phase_execution.bmr.batch_number}.')
                    
                elif action == 'fail':
                    phase_execution.status = 'failed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"QC Test Failed by {request.user.get_full_name()}. Results: {test_results}"
                    phase_execution.save()
                    
                    # Rollback to previous phase
                    WorkflowService.rollback_to_previous_phase(phase_execution.bmr, phase_execution.phase)
                    
                    messages.warning(request, f'QC test failed for batch {phase_execution.bmr.batch_number}. Rolled back to previous phase.')
                    
            except Exception as e:
                messages.error(request, f'Error processing QC test: {str(e)}')
        
        return redirect('dashboards:qc_dashboard')
    
    # Get all BMRs
    all_bmrs = BMR.objects.select_related('product', 'created_by').all()
    
    # Get QC phases this user can work on
    my_phases = []
    for bmr in all_bmrs:
        user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
        my_phases.extend(user_phases)
    
    # Statistics
    stats = {
        'pending_tests': len([p for p in my_phases if p.status == 'pending']),
        'in_testing': len([p for p in my_phases if p.status == 'in_progress']),
        'passed_today': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date=timezone.now().date(),
            status='completed'
        ).count(),
        'failed_this_week': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date__gte=timezone.now().date() - timedelta(days=7),
            status='failed'
        ).count(),
        'total_batches': len(set([p.bmr for p in my_phases])),
    }
    
    daily_progress = min(100, (stats['passed_today'] / max(1, stats['pending_tests'] + stats['passed_today'])) * 100)
    
    context = {
        'user': request.user,
        'my_phases': my_phases,
        'qc_phases': my_phases,  # Add this for template compatibility
        'stats': stats,
        'daily_progress': daily_progress,
        'dashboard_title': 'Quality Control Dashboard'
    }
    
    return render(request, 'dashboards/qc_dashboard.html', context)

@login_required
def packaging_dashboard(request):
    """Packaging Store Dashboard"""
    if request.user.role != 'packaging_store':
        messages.error(request, 'Access denied. Packaging Store role required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle POST requests for packaging material release
    if request.method == 'POST':
        action = request.POST.get('action')
        phase_id = request.POST.get('phase_id')
        notes = request.POST.get('notes', '')
        
        if phase_id and action in ['start', 'complete']:
            try:
                phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_id)
                
                if action == 'start':
                    # Validate that the phase can actually be started
                    if not WorkflowService.can_start_phase(phase_execution.bmr, phase_execution.phase.phase_name):
                        messages.error(request, f'Cannot start packaging material release for batch {phase_execution.bmr.batch_number} - prerequisites not met.')
                        return redirect('dashboards:packaging_dashboard')
                    
                    phase_execution.status = 'in_progress'
                    phase_execution.started_by = request.user
                    phase_execution.started_date = timezone.now()
                    phase_execution.operator_comments = f"Packaging material release started by {request.user.get_full_name()}. Notes: {notes}"
                    phase_execution.save()
                    
                    messages.success(request, f'Packaging material release started for batch {phase_execution.bmr.batch_number}.')
                    
                elif action == 'complete':
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"Packaging materials released by {request.user.get_full_name()}. Notes: {notes}"
                    phase_execution.save()
                    
                    # Trigger next phase in workflow (should be packing phases)
                    WorkflowService.trigger_next_phase(phase_execution.bmr, phase_execution.phase)
                    
                    messages.success(request, f'Packaging materials released for batch {phase_execution.bmr.batch_number}. Packing phases are now available.')
                    
            except Exception as e:
                messages.error(request, f'Error processing packaging material release: {str(e)}')
        
        return redirect('dashboards:packaging_dashboard')
    
    # Get all BMRs
    all_bmrs = BMR.objects.select_related('product', 'created_by').all()
    
    # Get packaging phases this user can work on
    my_phases = []
    for bmr in all_bmrs:
        user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
        my_phases.extend(user_phases)
    
    # Statistics
    stats = {
        'pending_phases': len([p for p in my_phases if p.status == 'pending']),
        'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
        'completed_today': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date=timezone.now().date()
        ).count(),
        'total_batches': len(set([p.bmr for p in my_phases])),
    }
    
    daily_progress = min(100, (stats['completed_today'] / max(1, stats['pending_phases'] + stats['completed_today'])) * 100)
    
    # Build operator history for this user (recent phases where user was started_by or completed_by)
    recent_phases = BatchPhaseExecution.objects.filter(
        Q(started_by=request.user) | Q(completed_by=request.user)
    ).order_by('-started_date', '-completed_date')[:10]
    operator_history = [
        {
            'date': (p.completed_date or p.started_date or p.created_date).strftime('%Y-%m-%d %H:%M'),
            'batch': p.bmr.batch_number,
            'phase': p.phase.get_phase_name_display(),
        }
        for p in recent_phases
    ]

    context = {
        'user': request.user,
        'my_phases': my_phases,
        'stats': stats,
        'daily_progress': daily_progress,
        'dashboard_title': 'Packaging Store Dashboard',
        'operator_history': operator_history,
    }
    return render(request, 'dashboards/packaging_dashboard.html', context)

@login_required
def packing_dashboard(request):
    """Packing Operator Dashboard"""
    if request.user.role != 'packing_operator':
        messages.error(request, 'Access denied. Packing Operator role required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle POST requests for packing phase completion
    if request.method == 'POST':
        action = request.POST.get('action')
        phase_id = request.POST.get('phase_id')
        notes = request.POST.get('notes', '')
        
        if phase_id and action in ['start', 'complete']:
            try:
                phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_id)
                
                if action == 'start':
                    # Validate that the phase can actually be started
                    if not WorkflowService.can_start_phase(phase_execution.bmr, phase_execution.phase.phase_name):
                        messages.error(request, f'Cannot start packing for batch {phase_execution.bmr.batch_number} - prerequisites not met.')
                        return redirect('dashboards:packing_dashboard')
                    
                    phase_execution.status = 'in_progress'
                    phase_execution.started_by = request.user
                    phase_execution.started_date = timezone.now()
                    phase_execution.operator_comments = f"Packing started by {request.user.get_full_name()}. Notes: {notes}"
                    phase_execution.save()
                    
                    messages.success(request, f'Packing started for batch {phase_execution.bmr.batch_number}.')
                    
                elif action == 'complete':
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"Packing completed by {request.user.get_full_name()}. Notes: {notes}"
                    phase_execution.save()
                    
                    # Trigger next phase in workflow
                    WorkflowService.trigger_next_phase(phase_execution.bmr, phase_execution.phase)
                    
                    messages.success(request, f'Packing completed for batch {phase_execution.bmr.batch_number}.')
                    
            except Exception as e:
                messages.error(request, f'Error processing packing phase: {str(e)}')
        
        return redirect('dashboards:packing_dashboard')
    
    # Get all BMRs
    all_bmrs = BMR.objects.all()
    
    # Get packing phases this user can work on
    my_phases = []
    for bmr in all_bmrs:
        user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
        my_phases.extend(user_phases)
    
    # Statistics
    stats = {
        'pending_phases': len([p for p in my_phases if p.status == 'pending']),
        'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
        'pending_packing': len([p for p in my_phases if p.status == 'pending']),  # For template compatibility
        'in_progress_packing': len([p for p in my_phases if p.status == 'in_progress']),  # For template compatibility
        'completed_today': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date=timezone.now().date()
        ).count(),
        'total_batches': len(set([p.bmr for p in my_phases])),
    }
    
    daily_progress = min(100, (stats['completed_today'] / max(1, stats['pending_phases'] + stats['completed_today'])) * 100)
    
    # Build operator history for this user (recent phases where user was started_by or completed_by)
    recent_phases = BatchPhaseExecution.objects.filter(
        Q(started_by=request.user) | Q(completed_by=request.user)
    ).order_by('-started_date', '-completed_date')[:10]
    operator_history = [
        {
            'date': (p.completed_date or p.started_date or p.created_date).strftime('%Y-%m-%d %H:%M'),
            'batch': p.bmr.batch_number,
            'phase': p.phase.get_phase_name_display(),
        }
        for p in recent_phases
    ]

    context = {
        'user': request.user,
        'my_phases': my_phases,
        'packing_phases': my_phases,  # Add this for template compatibility
        'stats': stats,
        'daily_progress': daily_progress,
        'dashboard_title': 'Packing Dashboard',
        'operator_history': operator_history,
    }
    
    return render(request, 'dashboards/packing_dashboard.html', context)

@login_required
def finished_goods_dashboard(request):
    """Finished Goods Store Dashboard"""
    if request.user.role != 'finished_goods_store':
        messages.error(request, 'Access denied. Finished Goods Store role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get all BMRs
    all_bmrs = BMR.objects.select_related('product', 'created_by').all()
    
    # Get finished goods phases this user can work on
    my_phases = []
    for bmr in all_bmrs:
        user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
        my_phases.extend(user_phases)
    
    # Statistics
    stats = {
        'pending_phases': len([p for p in my_phases if p.status == 'pending']),
        'in_progress_phases': len([p for p in my_phases if p.status == 'in_progress']),
        'completed_today': BatchPhaseExecution.objects.filter(
            completed_by=request.user,
            completed_date__date=timezone.now().date()
        ).count(),
        'total_batches': len(set([p.bmr for p in my_phases])),
    }
    
    daily_progress = min(100, (stats['completed_today'] / max(1, stats['pending_phases'] + stats['completed_today'])) * 100)
    
    context = {
        'user': request.user,
        'my_phases': my_phases,
        'stats': stats,
        'daily_progress': daily_progress,
        'dashboard_title': 'Finished Goods Store Dashboard'
    }
    
    return render(request, 'dashboards/finished_goods_dashboard.html', context)

@login_required
def admin_timeline_view(request):
    """Admin Timeline View - Track all BMRs through the system"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboards:dashboard_home')
    
    # Get export format if requested
    export_format = request.GET.get('export')
    
    # Get all BMRs with timeline data
    bmrs = BMR.objects.select_related('product', 'created_by', 'approved_by').all()
    
    # Add timeline data for each BMR
    timeline_data = []
    for bmr in bmrs:
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        # Calculate timeline metrics
        bmr_created = bmr.created_date
        fgs_completed = phases.filter(
            phase__phase_name='finished_goods_storage',
            status='completed'
        ).first()
        
        total_time_days = None
        if fgs_completed and fgs_completed.completed_date:
            total_time_days = (fgs_completed.completed_date - bmr_created).days
        
        # Get phase timeline with detailed information
        phase_timeline = []
        for phase in phases:
            phase_data = {
                'phase_name': phase.phase.phase_name.replace('_', ' ').title(),
                'status': phase.status.title(),
                'started_date': phase.started_date,
                'completed_date': phase.completed_date,
                'started_by': phase.started_by.get_full_name() if phase.started_by else None,
                'completed_by': phase.completed_by.get_full_name() if phase.completed_by else None,
                'duration_hours': None,
                'operator_comments': getattr(phase, 'operator_comments', '') or '',
                'phase_order': phase.phase.phase_order if hasattr(phase.phase, 'phase_order') else 0,
            }
            
            if phase.started_date and phase.completed_date:
                duration = phase.completed_date - phase.started_date
                phase_data['duration_hours'] = round(duration.total_seconds() / 3600, 2)
            elif phase.started_date and not phase.completed_date:
                # For ongoing phases, calculate current duration
                duration = timezone.now() - phase.started_date
                phase_data['duration_hours'] = round(duration.total_seconds() / 3600, 2)
            
            phase_timeline.append(phase_data)
        
        timeline_data.append({
            'bmr': bmr,
            'total_time_days': total_time_days,
            'phase_timeline': phase_timeline,
            'current_phase': phases.filter(status__in=['pending', 'in_progress']).first(),
            'is_completed': fgs_completed is not None,
        })
    
    # Handle exports
    if export_format in ['csv', 'excel']:
        return export_timeline_data(timeline_data, export_format)
    
    # Pagination
    paginator = Paginator(timeline_data, 10)  # 10 BMRs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'page_obj': page_obj,
        'timeline_data': page_obj.object_list,
        'dashboard_title': 'BMR Timeline Tracking',
        'total_bmrs': len(timeline_data),
    }
    
    return render(request, 'dashboards/admin_timeline.html', context)

@login_required
def admin_fgs_monitor(request):
    """Admin FGS Monitor - Track finished goods storage"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboards:dashboard_home')
    
    # Get finished goods storage phases
    fgs_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_storage'
    ).select_related('bmr__product', 'started_by', 'completed_by').order_by('-started_date')
    
    # Group by status
    fgs_pending = fgs_phases.filter(status='pending')
    fgs_in_progress = fgs_phases.filter(status='in_progress') 
    fgs_completed = fgs_phases.filter(status='completed')
    
    # Statistics
    fgs_stats = {
        'total_in_store': fgs_completed.count(),
        'pending_storage': fgs_pending.count(),
        'being_stored': fgs_in_progress.count(),
        'storage_capacity_used': min(100, (fgs_completed.count() / max(1000, 1)) * 100),  # Assuming 1000 batch capacity
    }
    
    # Recent storage activity
    recent_stored = fgs_completed[:10]
    
    # Products in FGS by type
    products_in_fgs = fgs_completed.values(
        'bmr__product__product_type',
        'bmr__product__product_name'
    ).annotate(
        batch_count=Count('bmr'),
        latest_storage=Max('completed_date')
    ).order_by('bmr__product__product_type', '-latest_storage')
    
    context = {
        'user': request.user,
        'fgs_pending': fgs_pending,
        'fgs_in_progress': fgs_in_progress,
        'recent_stored': recent_stored,
        'fgs_stats': fgs_stats,
        'products_in_fgs': products_in_fgs,
        'dashboard_title': 'Finished Goods Store Monitor',
    }
    
    return render(request, 'dashboards/admin_fgs_monitor.html', context)

def export_timeline_data(timeline_data, format_type):
    """Export detailed timeline data to CSV or Excel with all phases"""
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bmr_detailed_timeline_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write detailed phase information for each BMR
        for item in timeline_data:
            bmr = item['bmr']
            
            # BMR Header
            writer.writerow([])  # Empty row for separation
            writer.writerow([f"BMR: {bmr.batch_number} - {bmr.product.product_name}"])
            writer.writerow([f"Product Type: {bmr.product.product_type}"])
            writer.writerow([f"Created: {bmr.created_date.strftime('%Y-%m-%d %H:%M:%S')}"])
            writer.writerow([f"Total Production Time: {item['total_time_days']} days" if item['total_time_days'] else "In Progress"])
            writer.writerow([])  # Empty row
            
            # Phase details header
            writer.writerow([
                'Phase Name', 'Status', 'Started Date', 'Started By', 
                'Completed Date', 'Completed By', 'Duration (Hours)', 'Comments'
            ])
            
            # Phase data
            for phase_data in item['phase_timeline']:
                duration = phase_data.get('duration_hours', '')
                if duration:
                    duration = f"{duration:.2f}"
                    
                writer.writerow([
                    phase_data['phase_name'],
                    phase_data['status'],
                    phase_data['started_date'].strftime('%Y-%m-%d %H:%M:%S') if phase_data['started_date'] else '',
                    phase_data['started_by'] or '',
                    phase_data['completed_date'].strftime('%Y-%m-%d %H:%M:%S') if phase_data['completed_date'] else '',
                    phase_data['completed_by'] or '',
                    duration,
                    phase_data.get('operator_comments', '')
                ])
            
            writer.writerow([])  # Empty row for separation
        
        return response
    
    elif format_type == 'excel':
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        
        wb = openpyxl.Workbook()
        
        # Create summary sheet
        summary_ws = wb.active
        summary_ws.title = "Summary"
        
        # Summary headers
        summary_headers = [
            'BMR Number', 'Product Name', 'Product Type', 'Created Date', 
            'Total Time (Days)', 'Current Status', 'Current Phase',
            'Created By', 'Approved By', 'Approved Date'
        ]
        
        # Style summary headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for col, header in enumerate(summary_headers, 1):
            cell = summary_ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Summary data rows
        for row, item in enumerate(timeline_data, 2):
            bmr = item['bmr']
            summary_ws.cell(row=row, column=1, value=bmr.batch_number)
            summary_ws.cell(row=row, column=2, value=bmr.product.product_name)
            summary_ws.cell(row=row, column=3, value=bmr.product.product_type)
            summary_ws.cell(row=row, column=4, value=bmr.created_date.strftime('%Y-%m-%d %H:%M:%S'))
            summary_ws.cell(row=row, column=5, value=item['total_time_days'] or 'In Progress')
            summary_ws.cell(row=row, column=6, value=bmr.get_status_display())
            summary_ws.cell(row=row, column=7, value=item['current_phase'].phase.phase_name.replace('_', ' ').title() if item['current_phase'] else 'Completed')
            summary_ws.cell(row=row, column=8, value=bmr.created_by.get_full_name() if bmr.created_by else '')
            summary_ws.cell(row=row, column=9, value=bmr.approved_by.get_full_name() if bmr.approved_by else '')
            summary_ws.cell(row=row, column=10, value=bmr.approved_date.strftime('%Y-%m-%d %H:%M:%S') if bmr.approved_date else '')
        
        # Create detailed timeline sheet
        detail_ws = wb.create_sheet("Detailed Timeline")
        
        # Detailed timeline headers
        detail_headers = [
            'BMR Number', 'Product Name', 'Phase Name', 'Status', 
            'Started Date', 'Started By', 'Completed Date', 'Completed By',
            'Duration (Hours)', 'Phase Order', 'Comments'
        ]
        
        for col, header in enumerate(detail_headers, 1):
            cell = detail_ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Detailed timeline data
        row_num = 2
        for item in timeline_data:
            bmr = item['bmr']
            
            for phase_data in item['phase_timeline']:
                detail_ws.cell(row=row_num, column=1, value=bmr.batch_number)
                detail_ws.cell(row=row_num, column=2, value=bmr.product.product_name)
                detail_ws.cell(row=row_num, column=3, value=phase_data['phase_name'])
                detail_ws.cell(row=row_num, column=4, value=phase_data['status'])
                detail_ws.cell(row=row_num, column=5, value=phase_data['started_date'].strftime('%Y-%m-%d %H:%M:%S') if phase_data['started_date'] else '')
                detail_ws.cell(row=row_num, column=6, value=phase_data['started_by'] or '')
                detail_ws.cell(row=row_num, column=7, value=phase_data['completed_date'].strftime('%Y-%m-%d %H:%M:%S') if phase_data['completed_date'] else '')
                detail_ws.cell(row=row_num, column=8, value=phase_data['completed_by'] or '')
                detail_ws.cell(row=row_num, column=9, value=f"{phase_data['duration_hours']:.2f}" if phase_data.get('duration_hours') else '')
                detail_ws.cell(row=row_num, column=10, value=phase_data.get('phase_order', ''))
                detail_ws.cell(row=row_num, column=11, value=phase_data.get('operator_comments', ''))
                
                row_num += 1
        
        # Auto-adjust column widths for both sheets
        for ws in [summary_ws, detail_ws]:
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="bmr_detailed_timeline_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        wb.save(response)
        return response
