@login_required
def api_qc_test_detail(request):
    """Get detailed information for a specific QC test"""
    try:
        test_id = request.GET.get('test_id')
        if not test_id:
            return JsonResponse({'success': False, 'error': 'Test ID is required'})
        
        qc_test = get_object_or_404(RawMaterialQC, pk=test_id)
        
        # Format test data
        test_data = {
            'id': qc_test.id,
            'batch': {
                'id': qc_test.batch.id,
                'batch_number': qc_test.batch.batch_number,
                'material': {
                    'id': qc_test.batch.material.id,
                    'material_name': qc_test.batch.material.material_name,
                    'material_code': qc_test.batch.material.material_code,
                },
            },
            'status': qc_test.status,
            'tested_by': qc_test.tested_by.username if qc_test.tested_by else None,
            'test_date': qc_test.test_date.strftime('%Y-%m-%d') if qc_test.test_date else None,
            'remarks': qc_test.remarks,
            'parameters': qc_test.parameters,
        }
        
        return JsonResponse({'success': True, 'test': test_data})
        
    except Exception as e:
        import logging
        logging.error(f"Error in api_qc_test_detail: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def save_qc_test(request):
    """Save QC test results"""
    try:
        batch_id = request.POST.get('batch_id')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        parameters = request.POST.get('parameters', '{}')
        
        if not all([batch_id, status]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Get the batch
        batch = get_object_or_404(RawMaterialBatch, pk=batch_id)
        
        # Check if a QC test already exists for this batch
        qc_test = batch.qc_checks.first()
        if not qc_test:
            # Create a new QC test
            qc_test = RawMaterialQC(
                batch=batch,
                status=status,
                tested_by=request.user,
                test_date=timezone.now(),
                remarks=remarks,
                parameters=parameters
            )
        else:
            # Update existing QC test
            qc_test.status = status
            qc_test.tested_by = request.user
            qc_test.test_date = timezone.now()
            qc_test.remarks = remarks
            qc_test.parameters = parameters
        
        qc_test.save()
        
        # Update the batch status based on QC results
        if status == 'approved':
            batch.status = 'approved'
        elif status == 'rejected':
            batch.status = 'rejected'
        else:
            batch.status = 'pending_qc'
        
        batch.save()
        
        return JsonResponse({
            'success': True,
            'qc_test': {
                'id': qc_test.id,
                'status': qc_test.status,
                'batch_id': batch.id,
                'test_date': qc_test.test_date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        import logging
        logging.error(f"Error saving QC test: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_activity(request):
    """Get recent activity data for materials"""
    try:
        # Get batches received in the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        recent_batches = RawMaterialBatch.objects.filter(
            date_received__range=(start_date, end_date)
        ).order_by('-date_received')[:20]
        
        # Format batch data
        activity_data = []
        for batch in recent_batches:
            activity_data.append({
                'id': batch.id,
                'batch_number': batch.batch_number,
                'material': {
                    'id': batch.material.id,
                    'material_name': batch.material.material_name,
                },
                'quantity_received': float(batch.quantity_received),
                'date_received': batch.date_received.strftime('%Y-%m-%d'),
                'status': batch.status,
            })
        
        return JsonResponse({'success': True, 'activity': activity_data})
        
    except Exception as e:
        import logging
        logging.error(f"Error in api_activity: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_expiry(request):
    """Get expiry data for materials"""
    try:
        # Get batches that will expire in the next 90 days
        today = timezone.now().date()
        expiry_cutoff = today + timedelta(days=90)
        
        expiring_batches = RawMaterialBatch.objects.filter(
            expiry_date__lte=expiry_cutoff,
            expiry_date__gte=today,
            status='approved',
            quantity_remaining__gt=0
        ).order_by('expiry_date')
        
        # Format batch data
        expiry_data = []
        for batch in expiring_batches:
            days_remaining = (batch.expiry_date - today).days
            expiry_data.append({
                'id': batch.id,
                'batch_number': batch.batch_number,
                'material': {
                    'id': batch.material.id,
                    'material_name': batch.material.material_name,
                },
                'quantity_remaining': float(batch.quantity_remaining),
                'expiry_date': batch.expiry_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
            })
        
        return JsonResponse({'success': True, 'expiry': expiry_data})
        
    except Exception as e:
        import logging
        logging.error(f"Error in api_expiry: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def add_material(request):
    """Add a new raw material"""
    try:
        # Get parameters
        material_code = request.POST.get('material_code')
        material_name = request.POST.get('material_name')
        category = request.POST.get('category')
        unit_of_measure = request.POST.get('unit_of_measure')
        reorder_level = request.POST.get('reorder_level')
        default_supplier = request.POST.get('default_supplier', '')
        
        # Check for required fields
        if not all([material_code, material_name, category, unit_of_measure]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Check if material code already exists
        if RawMaterial.objects.filter(material_code=material_code).exists():
            return JsonResponse({'success': False, 'error': 'Material code already exists'})
        
        # Create new material
        material = RawMaterial(
            material_code=material_code,
            material_name=material_name,
            category=category,
            unit_of_measure=unit_of_measure,
            reorder_level=float(reorder_level) if reorder_level else 0,
            default_supplier=default_supplier
        )
        material.save()
        
        # Handle associated products if provided
        associated_products = request.POST.get('associated_products', '[]')
        import json
        try:
            products = json.loads(associated_products)
            from products.models import Product
            for product_id in products:
                try:
                    product = Product.objects.get(pk=product_id)
                    product.raw_materials.add(material)
                except Product.DoesNotExist:
                    continue
        except json.JSONDecodeError:
            pass
        
        return JsonResponse({
            'success': True,
            'material': {
                'id': material.id,
                'material_code': material.material_code,
                'material_name': material.material_name
            }
        })
        
    except Exception as e:
        import logging
        logging.error(f"Error adding material: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def mark_for_disposal(request):
    """Mark a batch for disposal"""
    try:
        batch_id = request.POST.get('batch_id')
        if not batch_id:
            return JsonResponse({'success': False, 'error': 'Batch ID is required'})
        
        # Get the batch
        batch = get_object_or_404(RawMaterialBatch, pk=batch_id)
        
        # Mark as disposed
        batch.status = 'disposed'
        batch.quantity_remaining = 0
        batch.save()
        
        # Log activity
        try:
            from activity_log.models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                activity_type='disposal',
                object_type='raw_material_batch',
                object_id=batch.id,
                description=f"Marked batch {batch.batch_number} of {batch.material.material_name} for disposal"
            )
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'message': f"Batch {batch.batch_number} marked for disposal successfully"
        })
        
    except Exception as e:
        import logging
        logging.error(f"Error marking for disposal: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
