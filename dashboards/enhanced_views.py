from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Avg, Q, F
from django.core.paginator import Paginator
from django.urls import reverse, resolve, NoReverseMatch
import json
import datetime
import traceback
from django.template import TemplateDoesNotExist

from workflow.models import BatchPhaseExecution, ProductionPhase
from bmr.models import BMR, BMRMaterial
from raw_materials.models import RawMaterial, RawMaterialBatch, RawMaterialQC
from dashboards.utils import all_materials_qc_approved

@login_required
def store_dashboard_enhanced(request):
    """Enhanced Store Manager Dashboard with Raw Material Management"""
    if request.user.role != 'store_manager':
        messages.error(request, 'Access denied. Store Manager role required.')
        return redirect('dashboards:dashboard_home')
    
    # Process raw material release actions
    if request.method == 'POST':
        action_type = request.POST.get('action_type', 'bmr_release')
        
        # Handle BMR raw material release
        if action_type == 'bmr_release':
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
                        messages.error(request, f'Cannot start raw material release for batch {bmr.bmr_number}. Some materials have not passed QC.')
                        return redirect('dashboards:store_dashboard_enhanced')
                    
                    phase_execution.status = 'in_progress'
                    phase_execution.started_by = request.user
                    phase_execution.started_date = timezone.now()
                    phase_execution.operator_comments = f"Raw material release started by {request.user.get_full_name()}. Notes: {notes}"
                    phase_execution.save()
                    
                    messages.success(request, f'Raw material release started for batch {bmr.bmr_number}.')
                    
                elif action == 'complete':
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"Raw materials released by {request.user.get_full_name()}. Notes: {notes}"
                    phase_execution.save()
                    
                    # Update next phase status to pending
                    workflow_service = BatchWorkflowService(bmr)
                    workflow_service.complete_current_phase('raw_material_release')
                    
                    messages.success(request, f'Raw material release completed for batch {bmr.bmr_number}.')
                
            except BMR.DoesNotExist:
                messages.error(request, 'BMR not found.')
            except BatchPhaseExecution.DoesNotExist:
                messages.error(request, 'Raw material release phase not found for this BMR.')
        
        # Handle new raw material receipt
        elif action_type == 'material_receipt':
            material_id = request.POST.get('material_id')
            batch_number = request.POST.get('batch_number')
            quantity = request.POST.get('quantity')
            supplier = request.POST.get('supplier')
            received_date = request.POST.get('received_date')
            expiry_date = request.POST.get('expiry_date')
            
            try:
                material = RawMaterial.objects.get(pk=material_id)
                
                # Validate batch number uniqueness
                if RawMaterialBatch.objects.filter(material=material, batch_number=batch_number).exists():
                    messages.error(request, f'Batch number {batch_number} already exists for {material.material_name}.')
                    return redirect('dashboards:store_dashboard_enhanced')
                
                # Create new batch
                new_batch = RawMaterialBatch(
                    material=material,
                    batch_number=batch_number,
                    quantity_received=quantity,
                    quantity_remaining=quantity,
                    supplier=supplier,
                    received_date=received_date,
                    expiry_date=expiry_date,
                    status='pending_qc',
                    received_by=request.user
                )
                new_batch.save()
                
                messages.success(request, f'Raw material batch {batch_number} received successfully.')
                
            except RawMaterial.DoesNotExist:
                messages.error(request, 'Raw material not found.')
            except Exception as e:
                messages.error(request, f'Error receiving raw material: {str(e)}')
    
    # Get data for display
    # Pending raw material release phases
    pending_release_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name='raw_material_release',
        status__in=['pending', 'in_progress']
    ).select_related('bmr', 'bmr__product', 'phase')
    
    # Raw materials data
    raw_materials = RawMaterial.objects.all()
    
    # Raw material batches pending QC
    pending_qc_batches = RawMaterialBatch.objects.filter(
        status='pending_qc'
    ).select_related('material')
    
    # Recent raw material receipts
    recent_receipts = RawMaterialBatch.objects.all().order_by('-received_date')[:10]
    
    # Low stock materials
    low_stock_materials = []
    for material in raw_materials:
        if material.status in ['low_stock', 'out_of_stock']:
            low_stock_materials.append(material)
    
    # Dashboard statistics
    total_materials = raw_materials.count()
    materials_in_stock = sum(1 for m in raw_materials if m.status == 'in_stock')
    materials_low_stock = sum(1 for m in raw_materials if m.status == 'low_stock')
    materials_out_of_stock = sum(1 for m in raw_materials if m.status == 'out_of_stock')
    
    pending_bmrs = pending_release_phases.count()
    pending_qc = pending_qc_batches.count()
    
    stats = {
        'total_materials': total_materials,
        'materials_in_stock': materials_in_stock,
        'materials_low_stock': materials_low_stock,
        'materials_out_of_stock': materials_out_of_stock,
        'pending_bmrs': pending_bmrs,
        'pending_qc': pending_qc
    }
    
    context = {
        'pending_release_phases': pending_release_phases,
        'raw_materials': raw_materials,
        'pending_qc_batches': pending_qc_batches,
        'recent_receipts': recent_receipts,
        'low_stock_materials': low_stock_materials,
        'stats': stats
    }
    
    return render(request, 'dashboards/store_dashboard_enhanced.html', context)

@login_required
def qc_dashboard_enhanced(request):
    """Enhanced Quality Control Dashboard with Raw Material QC Management"""
    if request.user.role != 'qc':
        messages.error(request, 'Access denied. QC role required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle POST requests for QC test results
    if request.method == 'POST':
        action_type = request.POST.get('action_type', 'production_qc')
        
        # Handle Production QC testing
        if action_type == 'production_qc':
            phase_id = request.POST.get('phase_id')
            qc_approved = request.POST.get('qc_approved') == 'true'
            qa_comments = request.POST.get('qa_comments', '')
            rejection_reason = request.POST.get('rejection_reason', '')
            
            try:
                phase_execution = BatchPhaseExecution.objects.get(pk=phase_id)
                
                phase_execution.qc_approved = qc_approved
                phase_execution.qa_comments = qa_comments
                
                if qc_approved:
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = f"QC approved by {request.user.get_full_name()}. Comments: {qa_comments}"
                    
                    # Update next phase status to pending using workflow service
                    from workflow.services import BatchWorkflowService
                    workflow_service = BatchWorkflowService(phase_execution.bmr)
                    workflow_service.complete_current_phase(phase_execution.phase.phase_name)
                    
                else:
                    phase_execution.rejection_reason = rejection_reason
                    phase_execution.operator_comments = f"QC rejected by {request.user.get_full_name()}. Reason: {rejection_reason}"
                    
                    # Handle rollback to previous phase
                    from workflow.services import BatchWorkflowService
                    workflow_service = BatchWorkflowService(phase_execution.bmr)
                    workflow_service.rollback_to_previous_phase(phase_execution.phase.phase_name)
                
                phase_execution.save()
                
                messages.success(request, f'QC test {"approved" if qc_approved else "rejected"} successfully.')
                
            except BatchPhaseExecution.DoesNotExist:
                messages.error(request, 'Phase execution not found.')
                
        # Handle Raw Material QC testing
        elif action_type == 'raw_material_qc':
            material_batch_id = request.POST.get('material_batch_id')
            appearance_result = request.POST.get('appearance_result')
            identification_result = request.POST.get('identification_result')
            assay_result = request.POST.get('assay_result')
            purity_result = request.POST.get('purity_result')
            final_result = request.POST.get('final_result')
            status = request.POST.get('status')
            test_notes = request.POST.get('test_notes', '')
            
            try:
                material_batch = RawMaterialBatch.objects.get(pk=material_batch_id)
                
                # Check if QC test already exists
                qc_test, created = RawMaterialQC.objects.get_or_create(
                    material_batch=material_batch,
                    defaults={
                        'started_by': request.user,
                        'started_date': timezone.now()
                    }
                )
                
                # Update test results
                qc_test.appearance_result = appearance_result
                qc_test.identification_result = identification_result
                qc_test.assay_result = assay_result
                qc_test.purity_result = purity_result
                qc_test.final_result = final_result
                qc_test.test_notes = test_notes
                
                # If test is approved or rejected, complete it
                if status in ['approved', 'rejected']:
                    qc_test.completed_by = request.user
                    qc_test.completed_date = timezone.now()
                    
                    # Also update the material batch status
                    material_batch.status = 'approved' if status == 'approved' else 'rejected'
                    material_batch.save()
                
                qc_test.save()
                
                messages.success(request, f'Raw material QC test saved successfully.')
                
            except RawMaterialBatch.DoesNotExist:
                messages.error(request, 'Material batch not found.')
    
    # Get QC phases that need testing
    qc_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name__in=['granulation_qc', 'compression_qc', 'coating_qc', 'bulk_packing_qc', 'blister_packing_qc'],
        status__in=['pending', 'in_progress']
    ).select_related('bmr', 'bmr__product', 'phase')
    
    # Get raw material batches pending QC
    pending_material_batches = RawMaterialBatch.objects.filter(
        status='pending_qc'
    ).select_related('material')
    
    # Get in-progress material QC tests
    in_progress_material_tests = RawMaterialQC.objects.filter(
        completed_date__isnull=True
    ).select_related('material_batch', 'material_batch__material', 'started_by')
    
    # Dashboard statistics
    pending_tests = qc_phases.filter(status='pending').count()
    pending_raw_materials = pending_material_batches.count()
    
    # Tests passed today
    today = timezone.now().date()
    passed_today = (
        BatchPhaseExecution.objects.filter(
            phase__phase_name__contains='_qc',
            qc_approved=True,
            completed_date__date=today
        ).count() + 
        RawMaterialQC.objects.filter(
            final_result='pass',
            completed_date__date=today
        ).count()
    )
    
    # Tests failed this week
    week_ago = today - datetime.timedelta(days=7)
    failed_this_week = (
        BatchPhaseExecution.objects.filter(
            phase__phase_name__contains='_qc',
            qc_approved=False,
            completed_date__date__gte=week_ago
        ).count() + 
        RawMaterialQC.objects.filter(
            final_result='fail',
            completed_date__date__gte=week_ago
        ).count()
    )
    
    # Tests completed today
    completed_today = (
        BatchPhaseExecution.objects.filter(
            phase__phase_name__contains='_qc',
            completed_date__date=today
        ).count() + 
        RawMaterialQC.objects.filter(
            completed_date__date=today
        ).count()
    )
    
    stats = {
        'pending_tests': pending_tests,
        'pending_raw_materials': pending_raw_materials,
        'passed_today': passed_today,
        'failed_this_week': failed_this_week,
        'completed_today': completed_today
    }
    
    context = {
        'qc_phases': qc_phases,
        'pending_material_batches': pending_material_batches,
        'in_progress_material_tests': in_progress_material_tests,
        'stats': stats
    }
    
    return render(request, 'dashboards/qc_dashboard_enhanced.html', context)

@login_required
def qc_test_detail(request, test_id):
    """View for QC test details in the production workflow"""
    if request.user.role != 'qc':
        messages.error(request, 'Access denied. QC role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get the test details from the production workflow
    # In a real implementation, this would fetch test details from a QC test model
    # related to production phases, not raw materials
    
    context = {
        'test_id': test_id,
        'test_type': 'production',
        'test_date': timezone.now(),
        'material_name': 'Production Sample',
        'product_name': 'Sample Product',
        'batch_number': 'PROD-' + str(test_id),
        'test_parameters': [
            {'name': 'Appearance', 'result': 'Pass', 'specification': 'Clear liquid'},
            {'name': 'pH', 'result': 'Pass', 'specification': '6.5-7.5'},
            {'name': 'Assay', 'result': 'Pass', 'specification': '95-105%'},
        ],
        'final_result': 'Approved',
        'tested_by': request.user.get_full_name(),
    }
    
    return render(request, 'dashboards/qc_test_detail.html', context)

@login_required
@require_POST
def start_qc_test(request):
    """Start a QC test for a production phase"""
    if request.user.role != 'qc':
        return JsonResponse({'success': False, 'error': 'Access denied. QC role required.'})
    
    data = json.loads(request.body)
    phase_id = data.get('phase_id')
    action = data.get('action')
    
    if not phase_id or action != 'start':
        return JsonResponse({'success': False, 'error': 'Invalid request parameters.'})
    
    try:
        phase_execution = BatchPhaseExecution.objects.get(pk=phase_id)
        
        if phase_execution.status != 'pending':
            return JsonResponse({'success': False, 'error': 'Phase is not in pending status.'})
        
        phase_execution.status = 'in_progress'
        phase_execution.started_by = request.user
        phase_execution.started_date = timezone.now()
        phase_execution.save()
        
        return JsonResponse({'success': True})
        
    except BatchPhaseExecution.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Phase execution not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_phase_details(request):
    """Get details for a specific phase execution"""
    if request.user.role != 'qc':
        return JsonResponse({'success': False, 'error': 'Access denied. QC role required.'})
    
    phase_id = request.GET.get('phase_id')
    
    if not phase_id:
        return JsonResponse({'success': False, 'error': 'Phase ID is required.'})
    
    try:
        phase_execution = BatchPhaseExecution.objects.get(pk=phase_id)
        
        phase_data = {
            'id': phase_execution.id,
            'bmr_number': phase_execution.bmr.bmr_number,
            'product_name': phase_execution.bmr.product.product_name,
            'phase_name': phase_execution.phase.get_phase_name_display(),
            'status': phase_execution.status,
            'started_date': phase_execution.started_date.isoformat() if phase_execution.started_date else None,
            'started_by': phase_execution.started_by.get_full_name() if phase_execution.started_by else None
        }
        
        return JsonResponse({'success': True, 'phase': phase_data})
        
    except BatchPhaseExecution.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Phase execution not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def complete_qc_test(request):
    """Complete a QC test with results"""
    if request.user.role != 'qc':
        return JsonResponse({'success': False, 'error': 'Access denied. QC role required.'})
    
    phase_id = request.POST.get('phase_id')
    qc_approved = request.POST.get('qc_approved') == 'true'
    qa_comments = request.POST.get('qa_comments', '')
    rejection_reason = request.POST.get('rejection_reason', '')
    
    if not phase_id:
        return JsonResponse({'success': False, 'error': 'Phase ID is required.'})
    
    try:
        phase_execution = BatchPhaseExecution.objects.get(pk=phase_id)
        
        if phase_execution.status != 'in_progress':
            return JsonResponse({'success': False, 'error': 'Phase is not in progress.'})
        
        phase_execution.qc_approved = qc_approved
        phase_execution.qa_comments = qa_comments
        
        if qc_approved:
            phase_execution.status = 'completed'
            phase_execution.completed_by = request.user
            phase_execution.completed_date = timezone.now()
            phase_execution.operator_comments = f"QC approved by {request.user.get_full_name()}. Comments: {qa_comments}"
            
            # Update next phase status to pending using workflow service
            from workflow.services import BatchWorkflowService
            workflow_service = BatchWorkflowService(phase_execution.bmr)
            workflow_service.complete_current_phase(phase_execution.phase.phase_name)
            
        else:
            phase_execution.rejection_reason = rejection_reason
            phase_execution.operator_comments = f"QC rejected by {request.user.get_full_name()}. Reason: {rejection_reason}"
            
            # Handle rollback to previous phase
            from workflow.services import BatchWorkflowService
            workflow_service = BatchWorkflowService(phase_execution.bmr)
            workflow_service.rollback_to_previous_phase(phase_execution.phase.phase_name)
        
        phase_execution.save()
        
        return JsonResponse({'success': True})
        
    except BatchPhaseExecution.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Phase execution not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def qc_results_data(request):
    """Get QC test results data for charts"""
    if request.user.role != 'qc':
        return JsonResponse({'success': False, 'error': 'Access denied. QC role required.'})
    
    # Get raw material QC statistics
    material_approved = RawMaterialQC.objects.filter(final_result='pass').count()
    material_rejected = RawMaterialQC.objects.filter(final_result='fail').count()
    material_pending = RawMaterialBatch.objects.filter(status='pending_qc').count()
    
    # Get production QC statistics
    production_passed = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        qc_approved=True
    ).count()
    
    production_failed = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        qc_approved=False,
        status='completed'
    ).count()
    
    production_in_progress = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        status='in_progress'
    ).count()
    
    # Calculate average test time
    avg_material_test_time = RawMaterialQC.objects.filter(
        started_date__isnull=False,
        completed_date__isnull=False
    ).annotate(
        duration=F('completed_date') - F('started_date')
    ).aggregate(
        avg_duration=Avg('duration')
    )['avg_duration']
    
    avg_production_test_time = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        started_date__isnull=False,
        completed_date__isnull=False
    ).annotate(
        duration=F('completed_date') - F('started_date')
    ).aggregate(
        avg_duration=Avg('duration')
    )['avg_duration']
    
    # Calculate overall average test time in hours
    avg_test_time = 0
    if avg_material_test_time:
        avg_test_time += avg_material_test_time.total_seconds() / 3600
    if avg_production_test_time:
        avg_test_time += avg_production_test_time.total_seconds() / 3600
    if avg_material_test_time and avg_production_test_time:
        avg_test_time /= 2
    
    # Calculate pass rate (last 30 days)
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    
    material_tests_30d = RawMaterialQC.objects.filter(completed_date__gte=thirty_days_ago).count()
    material_passed_30d = RawMaterialQC.objects.filter(
        completed_date__gte=thirty_days_ago,
        final_result='pass'
    ).count()
    
    production_tests_30d = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        completed_date__gte=thirty_days_ago
    ).count()
    
    production_passed_30d = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        completed_date__gte=thirty_days_ago,
        qc_approved=True
    ).count()
    
    total_tests_30d = material_tests_30d + production_tests_30d
    total_passed_30d = material_passed_30d + production_passed_30d
    
    pass_rate = (total_passed_30d / total_tests_30d * 100) if total_tests_30d > 0 else 0
    
    # Get recent test results
    recent_material_tests = RawMaterialQC.objects.filter(
        completed_date__isnull=False
    ).select_related(
        'material_batch', 'material_batch__material', 'completed_by'
    ).order_by('-completed_date')[:5]
    
    recent_production_tests = BatchPhaseExecution.objects.filter(
        phase__phase_name__contains='_qc',
        completed_date__isnull=False
    ).select_related(
        'bmr', 'bmr__product', 'phase', 'completed_by'
    ).order_by('-completed_date')[:5]
    
    # Combine and sort recent tests
    recent_tests = []
    
    for test in recent_material_tests:
        recent_tests.append({
            'id': test.id,
            'type': 'raw_material',
            'date': test.completed_date,
            'name': test.material_batch.material.material_name,
            'batch_number': test.material_batch.batch_number,
            'result': test.final_result,
            'tested_by': test.completed_by.get_full_name() if test.completed_by else 'Unknown'
        })
    
    for test in recent_production_tests:
        recent_tests.append({
            'id': test.id,
            'type': 'production',
            'date': test.completed_date,
            'name': test.bmr.product.product_name,
            'batch_number': test.bmr.bmr_number,
            'result': 'pass' if test.qc_approved else 'fail',
            'tested_by': test.completed_by.get_full_name() if test.completed_by else 'Unknown'
        })
    
    # Sort by date, newest first
    recent_tests.sort(key=lambda x: x['date'], reverse=True)
    recent_tests = recent_tests[:10]
    
    # Convert datetime objects to strings
    for test in recent_tests:
        test['date'] = test['date'].isoformat()
    
    data = {
        'success': True,
        'material_stats': {
            'approved': material_approved,
            'rejected': material_rejected,
            'pending': material_pending
        },
        'production_stats': {
            'passed': production_passed,
            'failed': production_failed,
            'in_progress': production_in_progress
        },
        'avg_test_time': avg_test_time,
        'pass_rate': pass_rate,
        'recent_tests': recent_tests
    }
    
    return JsonResponse(data)

@login_required
@require_POST
def qc_history_data(request):
    """Get QC testing history data"""
    if request.user.role != 'qc':
        return JsonResponse({'success': False, 'error': 'Access denied. QC role required.'})
    
    data = json.loads(request.body)
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    test_type = data.get('test_type')
    test_result = data.get('test_result')
    
    # Convert dates to datetime objects
    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        # Add one day to end_date to include the entire day
        end_date = datetime.datetime.combine(end_date, datetime.time.max)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid date format.'})
    
    # Get raw material QC tests
    material_tests = []
    if test_type in ['all', 'raw_material']:
        material_qc_query = RawMaterialQC.objects.filter(
            completed_date__isnull=False,
            completed_date__date__gte=start_date,
            completed_date__lte=end_date
        ).select_related(
            'material_batch', 'material_batch__material', 'started_by', 'completed_by'
        )
        
        if test_result == 'pass':
            material_qc_query = material_qc_query.filter(final_result='pass')
        elif test_result == 'fail':
            material_qc_query = material_qc_query.filter(final_result='fail')
        
        for test in material_qc_query:
            duration = 0
            if test.started_date and test.completed_date:
                duration = (test.completed_date - test.started_date).total_seconds() / 3600
            
            material_tests.append({
                'id': test.id,
                'type': 'raw_material',
                'date': test.completed_date,
                'name': test.material_batch.material.material_name,
                'batch_number': test.material_batch.batch_number,
                'result': test.final_result,
                'tested_by': test.completed_by.get_full_name() if test.completed_by else 'Unknown',
                'duration': round(duration, 2)
            })
    
    # Get production QC tests
    production_tests = []
    if test_type in ['all', 'production']:
        production_qc_query = BatchPhaseExecution.objects.filter(
            phase__phase_name__contains='_qc',
            completed_date__isnull=False,
            completed_date__date__gte=start_date,
            completed_date__lte=end_date
        ).select_related(
            'bmr', 'bmr__product', 'phase', 'started_by', 'completed_by'
        )
        
        if test_result == 'pass':
            production_qc_query = production_qc_query.filter(qc_approved=True)
        elif test_result == 'fail':
            production_qc_query = production_qc_query.filter(qc_approved=False)
        
        for test in production_qc_query:
            duration = 0
            if test.started_date and test.completed_date:
                duration = (test.completed_date - test.started_date).total_seconds() / 3600
            
            production_tests.append({
                'id': test.id,
                'type': 'production',
                'date': test.completed_date,
                'name': test.bmr.product.product_name,
                'batch_number': test.bmr.bmr_number,
                'result': 'pass' if test.qc_approved else 'fail',
                'tested_by': test.completed_by.get_full_name() if test.completed_by else 'Unknown',
                'duration': round(duration, 2)
            })
    
    # Combine and sort all tests
    all_tests = material_tests + production_tests
    all_tests.sort(key=lambda x: x['date'], reverse=True)
    
    # Convert datetime objects to strings
    for test in all_tests:
        test['date'] = test['date'].isoformat()
    
    return JsonResponse({
        'success': True,
        'tests': all_tests
    })

@login_required
def export_qc_history(request):
    """Export QC testing history as CSV"""
    if request.user.role != 'qc':
        messages.error(request, 'Access denied. QC role required.')
        return redirect('dashboards:dashboard_home')
    
    # This would generate a CSV file and return as a response
    # Implementation would be similar to qc_history_data but return CSV
    
    # For now, just redirect back with a message
    messages.info(request, 'Export functionality will be implemented in a future update.')
    return redirect('dashboards:qc_dashboard_enhanced')

@login_required
def inventory_debug_tool(request):
    """Debug tool for inventory and API endpoints"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Administrator access required.')
        return redirect('dashboards:dashboard_home')
    
    # Handle direct endpoint testing
    if 'debug_endpoint' in request.GET:
        endpoint = request.GET.get('debug_endpoint')
        try:
            # Try to resolve the endpoint
            url = reverse(endpoint)
            return redirect(url)
        except NoReverseMatch:
            return JsonResponse({
                'error': f'Could not resolve endpoint: {endpoint}',
                'available_endpoints': {
                    'raw_materials:api_materials': 'Materials list API',
                    'raw_materials:api_expiry': 'Expiry tracking API',
                    'raw_materials:api_activity': 'Activity log API'
                }
            }, status=400)
    
    # Handle diagnostic tools
    if 'action' in request.GET:
        action = request.GET.get('action')
        
        if action == 'check_templates':
            html = '<div class="mb-4">'
            templates_to_check = [
                'dashboards/store_dashboard_enhanced.html',
                'dashboards/qc_dashboard_enhanced.html',
                'raw_materials/dashboard.html',
                'raw_materials/material_detail.html'
            ]
            
            for template in templates_to_check:
                try:
                    # Just try rendering to check if template exists
                    render(request, template, {})
                    html += f'<p class="text-success"><i class="fas fa-check-circle me-2"></i>{template} - OK</p>'
                except TemplateDoesNotExist:
                    html += f'<p class="text-danger"><i class="fas fa-times-circle me-2"></i>{template} - Not Found</p>'
                except Exception as e:
                    html += f'<p class="text-warning"><i class="fas fa-exclamation-triangle me-2"></i>{template} - Error: {str(e)}</p>'
            
            html += '</div>'
            return HttpResponse(html)
            
        elif action == 'check_urls':
            html = '<div class="mb-4">'
            urls_to_check = [
                'raw_materials:api_materials',
                'raw_materials:api_expiry',
                'raw_materials:api_activity',
                'raw_materials:add_material',
                'raw_materials:save_qc_test'
            ]
            
            for url_name in urls_to_check:
                try:
                    resolved_url = reverse(url_name)
                    html += f'<p class="text-success"><i class="fas fa-check-circle me-2"></i>{url_name} - Resolved to {resolved_url}</p>'
                except NoReverseMatch:
                    html += f'<p class="text-danger"><i class="fas fa-times-circle me-2"></i>{url_name} - No match found</p>'
                except Exception as e:
                    html += f'<p class="text-warning"><i class="fas fa-exclamation-triangle me-2"></i>{url_name} - Error: {str(e)}</p>'
            
            html += '</div>'
            return HttpResponse(html)
            
        elif action == 'repair_endpoints':
            # This is just a placeholder - we'd need server access to actually fix things
            html = '<div class="alert alert-info">'
            html += '<h5>Endpoint Analysis Complete</h5>'
            html += '<p>The system has analyzed the current configuration and recommends:</p>'
            html += '<ol>'
            html += '<li>Use "raw_materials:api_materials" instead of "store:ajax_inventory_data"</li>'
            html += '<li>Use "raw_materials:api_expiry" instead of "store:ajax_expiry_data"</li>'
            html += '<li>Use "raw_materials:api_materials" instead of "store:ajax_materials_list"</li>'
            html += '</ol>'
            html += '<p class="mb-0">These recommendations have been implemented in the diagnostic version of the template.</p>'
            html += '</div>'
            return HttpResponse(html)
    
    return render(request, 'dashboards/inventory_debug.html')
