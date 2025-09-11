from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from django.http import JsonResponse, HttpResponse
from decimal import Decimal, InvalidOperation
from datetime import timedelta
import csv
from .models import RawMaterial, RawMaterialBatch, RawMaterialQC, MaterialDispensing, MaterialDispensingItem


@login_required
def inventory_monitor(request):
    """Raw Materials Inventory Monitor"""
    # Allow access for store managers or any admin/staff user
    if not (request.user.role == 'store_manager' or request.user.is_staff or request.user.role in ['admin', 'superadmin']):
        messages.error(request, 'Access denied. Store Manager or Admin role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get all materials with their stock information
    materials = RawMaterial.objects.all().order_by('material_code')
    
    # Calculate summary stats
    total_materials = materials.count()
    
    # Calculate materials with low stock
    low_stock = 0
    for material in materials:
        if hasattr(material, 'current_stock') and material.current_stock <= material.reorder_level:
            low_stock += 1
    
    # Get QC pending count
    pending_qc = RawMaterialBatch.objects.filter(status='pending_qc').count()
    
    # Calculate approved materials
    approved_materials = RawMaterialBatch.objects.filter(status='approved').values('material').distinct().count()
    
    # Get last 30 days transactions
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_batches = RawMaterialBatch.objects.filter(created_at__gte=thirty_days_ago)
    
    transactions_summary = {
        'received': recent_batches.filter(status='received').count(),
        'dispensed': MaterialDispensing.objects.filter(
            status='completed',
            completed_date__gte=thirty_days_ago
        ).count(),
        'returned': MaterialDispensing.objects.filter(
            status='returned',
            completed_date__gte=thirty_days_ago
        ).count(),
        'adjusted': recent_batches.filter(status='adjusted').count(),
    }
    
    # Debug print statements
    print(f"Total materials: {total_materials}")
    print(f"Low stock: {low_stock}")
    print(f"Pending QC: {pending_qc}")
    print(f"Materials queryset: {materials.query}")
    
    # Prepare context with all required data
    context = {
        'total_materials': total_materials,
        'low_stock': low_stock,
        'pending_qc': pending_qc,
        'approved_materials': approved_materials,
        'transactions_summary': transactions_summary,
        'materials': materials.prefetch_related('inventory_batches'),  # Optimize queries
    }
    
    print(f"Rendering template with context: {context}")
    return render(request, 'raw_materials/inventory_monitor.html', context)

@login_required
def raw_materials_dashboard(request):
    """Raw Materials Store Dashboard"""
    if request.user.role not in ['store_manager', 'admin']:
        messages.error(request, 'Access denied. Store Manager role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get raw materials statistics
    total_materials = RawMaterial.objects.count()
    total_batches = RawMaterialBatch.objects.count()
    
    # Stock status
    out_of_stock = RawMaterial.objects.filter(inventory_batches__status='approved').annotate(
        total_stock=Sum('inventory_batches__quantity_remaining')
    ).filter(Q(total_stock__lte=0) | Q(total_stock__isnull=True)).count()
    
    low_stock = RawMaterial.objects.filter(inventory_batches__status='approved').annotate(
        total_stock=Sum('inventory_batches__quantity_remaining')
    ).filter(total_stock__gt=0, total_stock__lte=F('reorder_level')).count()
    
    # QC pending materials
    pending_qc = RawMaterialBatch.objects.filter(status='pending_qc').count()
    
    # Recent activity
    recent_batches = RawMaterialBatch.objects.all().order_by('-created_at')[:10]
    
    # Pending dispensing
    pending_dispensing = MaterialDispensing.objects.filter(status='pending').count()
    in_progress_dispensing = MaterialDispensing.objects.filter(status='in_progress').count()
    
    # Material expiry alerts
    expiring_soon = RawMaterialBatch.objects.filter(
        status='approved',
        expiry_date__lte=timezone.now().date() + timezone.timedelta(days=90),
        expiry_date__gt=timezone.now().date(),
        quantity_remaining__gt=0
    ).order_by('expiry_date')[:10]
    
    # Recent dispensing
    recent_dispensing = MaterialDispensing.objects.all().order_by('-requested_date')[:10]
    
    context = {
        'total_materials': total_materials,
        'total_batches': total_batches,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'pending_qc': pending_qc,
        'recent_batches': recent_batches,
        'pending_dispensing': pending_dispensing,
        'in_progress_dispensing': in_progress_dispensing,
        'expiring_soon': expiring_soon,
        'recent_dispensing': recent_dispensing,
    }
    
    return render(request, 'dashboards/store_dashboard.html', context)

@login_required
def material_detail(request, material_id):
    """View details of a raw material"""
    material = get_object_or_404(RawMaterial, id=material_id)
    
    # Get all batches for this material
    batches = RawMaterialBatch.objects.filter(material=material).order_by('-received_date')
    
    # Calculate total approved quantity
    approved_quantity = sum(batch.quantity_remaining for batch in batches if batch.status == 'approved')
    
    # Get recent QC tests
    qc_tests = RawMaterialQC.objects.filter(material_batch__material=material).order_by('-started_date')[:10]
    
    # Get recent dispensing
    dispensing_items = MaterialDispensingItem.objects.filter(
        material=material,
        dispensing__status__in=['completed', 'in_progress']
    ).order_by('-dispensing__started_date')[:10]
    
    context = {
        'material': material,
        'batches': batches,
        'approved_quantity': approved_quantity,
        'qc_tests': qc_tests,
        'dispensing_items': dispensing_items,
    }
    
    return render(request, 'raw_materials/material_detail.html', context)


@login_required
def export_inventory(request):
    """Export inventory data to CSV"""
    if not (request.user.role == 'store_manager' or request.user.is_staff or request.user.role in ['admin', 'superadmin']):
        messages.error(request, 'Access denied. Store Manager or Admin role required.')
        return redirect('dashboards:dashboard_home')

    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="inventory_export.csv"'},
    )

    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Material Code', 
        'Material Name', 
        'Category', 
        'Current Stock', 
        'Unit of Measure',
        'Reorder Level', 
        'Status'
    ])

    # Get all materials
    materials = RawMaterial.objects.all().order_by('material_code')

    # Write data rows
    for material in materials:
        writer.writerow([
            material.material_code,
            material.material_name,
            material.category,
            material.current_stock,
            material.unit_of_measure,
            material.reorder_level,
            material.stock_status
        ])

    return response


@login_required
def batch_list(request, status=None):
    """View filtered list of raw material batches based on status"""
    if request.user.role not in ['store_manager', 'admin', 'qc', 'regulatory']:
        messages.error(request, 'Access denied. Authorized role required.')
        return redirect('dashboards:dashboard_home')
    
    batches = RawMaterialBatch.objects.all().select_related('material')
    
    # Apply status filter if provided
    if status:
        batches = batches.filter(status=status)
    
    # Allow filtering by material if requested
    material_id = request.GET.get('material_id')
    if material_id:
        batches = batches.filter(material_id=material_id)
        material_name = RawMaterial.objects.get(id=material_id).material_name
    else:
        material_name = None
    
    # Order by newest first
    batches = batches.order_by('-received_date')
    
    # Get counts for sidebar
    pending_count = RawMaterialBatch.objects.filter(status='pending_qc').count()
    approved_count = RawMaterialBatch.objects.filter(status='approved').count()
    rejected_count = RawMaterialBatch.objects.filter(status='rejected').count()
    
    context = {
        'batches': batches,
        'status': status,
        'material_name': material_name,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'status_display': {
            'pending_qc': 'Pending QC',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'expired': 'Expired',
            'disposed': 'Disposed'
        }
    }
    
    return render(request, 'raw_materials/batch_list.html', context)

@login_required
def material_detail(request, material_id):
    """View details of a specific raw material"""
    if request.user.role not in ['store_manager', 'admin', 'qc']:
        messages.error(request, 'Access denied. Store Manager role required.')
        return redirect('dashboards:dashboard_home')
    
    material = get_object_or_404(RawMaterial, id=material_id)
    
    # Get all batches for this material
    batches = RawMaterialBatch.objects.filter(material=material).order_by('-received_date')
    
    # Usage history
    usage_history = MaterialDispensingItem.objects.filter(
        material_batch__material=material,
        is_dispensed=True
    ).order_by('-dispensed_date')[:20]
    
    context = {
        'material': material,
        'batches': batches,
        'usage_history': usage_history,
    }
    
    return render(request, 'raw_materials/material_detail.html', context)


@login_required
def qc_dashboard(request):
    """QC Dashboard for Raw Materials Testing"""
    if request.user.role != 'qc':
        messages.error(request, 'Access denied. QC role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get batches pending QC
    pending_raw_materials = RawMaterialBatch.objects.filter(status='pending_qc').order_by('received_date')
    
    # Get in-progress QC tests
    in_progress_raw_materials = RawMaterialQC.objects.filter(status='in_progress').order_by('-started_date')
    
    # Get pending QC phases for production
    from bmr.models import BatchPhaseExecution, PhaseDefinition
    pending_phases = BatchPhaseExecution.objects.filter(
        phase__phase_type='qc',
        status='pending'
    ).order_by('bmr__created_date')
    
    # Get in-progress QC phases for production
    in_progress_phases = BatchPhaseExecution.objects.filter(
        phase__phase_type='qc',
        status='in_progress'
    ).order_by('-started_date')
    
    # Recent QC tests
    recent_tests = RawMaterialQC.objects.all().order_by('-test_date')[:10]
    
    # Get QC activity
    from itertools import chain
    from django.db.models import Count
    
    # Stats for counters
    stats = {
        'pending_tests': pending_phases.count(),
        'in_progress_tests': in_progress_phases.count(),
        'pending_raw_materials': pending_raw_materials.count(),
        'completed_today': RawMaterialQC.objects.filter(completed_date__date=timezone.now().date()).count()
    }
    
    context = {
        'pending_raw_materials': pending_raw_materials,
        'in_progress_raw_materials': in_progress_raw_materials,
        'pending_phases': pending_phases,
        'in_progress_phases': in_progress_phases,
        'recent_tests': recent_tests,
        'stats': stats
    }
    
    return render(request, 'dashboards/qc_dashboard.html', context)
    
    return render(request, 'dashboards/qc_dashboard.html', context)


@login_required
def perform_qc_test(request, batch_id):
    """Perform QC test on a raw material batch - redirects to QC dashboard with modal testing"""
    if request.user.role != 'qc':
        messages.error(request, 'Access denied. QC role required.')
        return redirect('dashboards:dashboard_home')
    
    batch = get_object_or_404(RawMaterialBatch, id=batch_id)
    
    # Check if already tested
    existing_test = RawMaterialQC.objects.filter(material_batch=batch).first()
    if existing_test:
        messages.info(request, f'QC test already exists for this batch. You can update it in the QC dashboard.')
        return redirect('raw_materials:qc_dashboard')
    
    # Redirect to QC dashboard with batch ID to trigger the modal
    # The AJAX modal approach will be used for all QC testing
    response = redirect('raw_materials:qc_dashboard')
    response['Location'] += f'?open_qc_test={batch_id}'
    return response


@login_required
def dispensing_detail(request, dispensing_id):
    """View and manage a material dispensing record"""
    if request.user.role != 'dispensing_operator':
        messages.error(request, 'Access denied. Dispensing Operator role required.')
        return redirect('dashboards:dashboard_home')
    
    dispensing = get_object_or_404(MaterialDispensing, id=dispensing_id)
    
    # Get all items for this dispensing
    items = MaterialDispensingItem.objects.filter(dispensing=dispensing)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            dispensing.status = 'in_progress'
            dispensing.dispensed_by = request.user
            dispensing.started_date = timezone.now()
            dispensing.save()
            messages.success(request, f'Started dispensing for BMR {dispensing.bmr.batch_number}')
            
        elif action == 'complete':
            # Check if all items are dispensed
            all_dispensed = True
            for item in items:
                if not item.is_dispensed:
                    all_dispensed = False
                    break
            
            if all_dispensed:
                dispensing.status = 'completed'
                dispensing.completed_date = timezone.now()
                dispensing.save()
                
                # Trigger next phase in workflow
                from workflow.services import WorkflowService
                WorkflowService.trigger_next_phase(dispensing.bmr, 'raw_material_release')
                
                messages.success(request, f'Completed dispensing for BMR {dispensing.bmr.batch_number}')
            else:
                messages.error(request, 'Cannot complete. Some items are not yet dispensed.')
                
        elif action == 'dispense_item':
            item_id = request.POST.get('item_id')
            dispensed_qty = request.POST.get('dispensed_quantity')
            
            if item_id and dispensed_qty:
                try:
                    item = MaterialDispensingItem.objects.get(id=item_id, dispensing=dispensing)
                    item.dispensed_quantity = float(dispensed_qty)
                    item.is_dispensed = True
                    item.dispensed_date = timezone.now()
                    item.save()
                    messages.success(request, f'Dispensed {dispensed_qty} {item.bmr_material.unit_of_measure} of {item.bmr_material.material_name}')
                except Exception as e:
                    messages.error(request, f'Error dispensing item: {str(e)}')
            else:
                messages.error(request, 'Missing item ID or quantity.')
        
        return redirect('raw_materials:dispensing_detail', dispensing_id)
    
    context = {
        'dispensing': dispensing,
        'items': items,
    }
    
    return render(request, 'raw_materials/dispensing_detail.html', context)


@login_required
def dispensing_dashboard(request):
    """Dispensing Operator Dashboard"""
    if request.user.role != 'dispensing_operator':
        messages.error(request, 'Access denied. Dispensing Operator role required.')
        return redirect('dashboards:dashboard_home')
    
    # Get pending dispensing
    pending_dispensing = MaterialDispensing.objects.filter(status='pending').order_by('requested_date')
    
    # Get in-progress dispensing
    in_progress_dispensing = MaterialDispensing.objects.filter(
        status='in_progress',
        dispensed_by=request.user
    ).order_by('started_date')
    
    # Recent completed dispensing
    recent_completed = MaterialDispensing.objects.filter(
        status='completed',
        dispensed_by=request.user
    ).order_by('-completed_date')[:10]
    
    # Count dispensing completed today
    from django.utils import timezone
    import datetime
    today = timezone.now().date()
    total_dispensed_today = MaterialDispensing.objects.filter(
        status='completed',
        completed_date__date=today
    ).count()
    
    # Prefetch related data for better performance
    recent_completed = recent_completed.prefetch_related(
        'items__bmr_material__material',
        'items__material_batch',
        'bmr__product'
    )
    
    context = {
        'pending_dispensing': pending_dispensing,
        'in_progress_dispensing': in_progress_dispensing,
        'recent_completed': recent_completed,
        'total_dispensed_today': total_dispensed_today,
    }
    
    return render(request, 'raw_materials/dispensing_dashboard.html', context)

@login_required
def start_dispensing(request, dispensing_id):
    """Start dispensing process for a BMR"""
    if request.user.role != 'dispensing_operator':
        messages.error(request, 'Access denied. Only dispensing operators can perform this action.')
        return redirect('dashboards:dashboard_home')
    
    try:
        dispensing = MaterialDispensing.objects.get(id=dispensing_id)
        
        # Check if it's in a valid state
        if dispensing.status != 'pending':
            messages.error(request, f'Cannot start dispensing. Current status: {dispensing.status}')
            return redirect('raw_materials:dispensing_dashboard')
        
        # Update the status
        dispensing.status = 'in_progress'
        dispensing.dispensed_by = request.user
        dispensing.started_date = timezone.now()
        dispensing.save()
        
        messages.success(request, f'Started dispensing for BMR {dispensing.bmr.batch_number}')
    except MaterialDispensing.DoesNotExist:
        messages.error(request, 'Dispensing record not found')
    except Exception as e:
        messages.error(request, f'Error starting dispensing: {str(e)}')
    
    return redirect('raw_materials:dispensing_dashboard')

@login_required
def complete_dispensing(request, dispensing_id):
    """Complete dispensing process for a BMR"""
    if request.user.role != 'dispensing_operator':
        messages.error(request, 'Access denied. Only dispensing operators can perform this action.')
        return redirect('dashboards:dashboard_home')
    
    try:
        dispensing = MaterialDispensing.objects.get(id=dispensing_id)
        
        # Check if it's in a valid state
        if dispensing.status != 'in_progress':
            messages.error(request, f'Cannot complete dispensing. Current status: {dispensing.status}')
            return redirect('raw_materials:dispensing_dashboard')
        
        # Update the status
        dispensing.status = 'completed'
        dispensing.completed_date = timezone.now()
        dispensing._complete_dispensing = True  # This flag will trigger process_dispensing_completion in save()
        dispensing.save()
        
        messages.success(request, f'Completed dispensing for BMR {dispensing.bmr.batch_number}')
    except MaterialDispensing.DoesNotExist:
        messages.error(request, 'Dispensing record not found')
    except Exception as e:
        messages.error(request, f'Error completing dispensing: {str(e)}')
    
    return redirect('raw_materials:dispensing_dashboard')

@login_required
def dispensing_detail(request, dispensing_id):
    """View details of a specific dispensing record"""
    if request.user.role not in ['dispensing_operator', 'qa', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('dashboards:dashboard_home')
    
    try:
        dispensing = MaterialDispensing.objects.get(id=dispensing_id)
        dispensing_items = dispensing.items.all().select_related('bmr_material', 'material_batch')
        
        context = {
            'dispensing': dispensing,
            'items': dispensing_items,
        }
        
        return render(request, 'raw_materials/dispensing_detail.html', context)
    except MaterialDispensing.DoesNotExist:
        messages.error(request, 'Dispensing record not found')
        return redirect('raw_materials:dispensing_dashboard')

@login_required
def qc_test_detail(request, test_id):
    """View QC test details"""
    if request.user.role not in ['qc', 'admin', 'store_manager']:
        messages.error(request, 'Access denied. QC or Store Manager role required.')
        return redirect('dashboards:dashboard_home')
    
    test = get_object_or_404(RawMaterialQC, id=test_id)
    
    context = {
        'test': test,
        'material': test.material_batch.material,
        'batch': test.material_batch
    }
    
    return render(request, 'raw_materials/qc_test_detail.html', context)

@login_required
def receive_material(request):
    """API endpoint for receiving new raw materials"""
    if request.user.role not in ['store_manager', 'admin']:
        return JsonResponse({'success': False, 'error': 'Access denied. Store Manager role required.'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'})
    
    try:
        # Extract form data
        material_id = request.POST.get('material_id')
        batch_number = request.POST.get('batch_number')
        quantity = request.POST.get('quantity')
        supplier = request.POST.get('supplier')
        received_date = request.POST.get('received_date')
        manufacturing_date = request.POST.get('manufacturing_date')
        expiry_date = request.POST.get('expiry_date')
        
        # Validate data
        if not all([material_id, batch_number, quantity, supplier, received_date, expiry_date]):
            return JsonResponse({'success': False, 'error': 'All fields are required'})
        
        # Convert quantity to Decimal
        try:
            quantity = Decimal(quantity)
            if quantity <= 0:
                return JsonResponse({'success': False, 'error': 'Quantity must be greater than zero'})
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Invalid quantity format'})
        
        # Validate dates
        try:
            received_date = timezone.datetime.strptime(received_date, '%Y-%m-%d').date()
            expiry_date = timezone.datetime.strptime(expiry_date, '%Y-%m-%d').date()
            
            # Handle manufacturing date if present
            if manufacturing_date:
                manufacturing_date = timezone.datetime.strptime(manufacturing_date, '%Y-%m-%d').date()
            
            if expiry_date <= received_date:
                return JsonResponse({'success': False, 'error': 'Expiry date must be after received date'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Get material
        material = get_object_or_404(RawMaterial, id=material_id)
        
        # Check if batch number already exists
        if RawMaterialBatch.objects.filter(material=material, batch_number=batch_number).exists():
            return JsonResponse({'success': False, 'error': 'Batch number already exists for this material'})
        
        # Create new batch
        batch = RawMaterialBatch.objects.create(
            material=material,
            batch_number=batch_number,
            quantity_received=quantity,
            quantity_remaining=quantity,
            supplier=supplier,
            received_date=received_date,
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            received_by=request.user,
            status='pending_qc'  # New batches start in pending QC status
        )
        
        # Update material stock
        material.current_stock += quantity
        material.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Material batch {batch_number} received successfully',
            'batch_id': batch.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
