@login_required
def api_batch_detail(request):
    """Get detailed information for a specific batch"""
    try:
        batch_id = request.GET.get('batch_id')
        if not batch_id:
            return JsonResponse({'success': False, 'error': 'Batch ID is required'})
        
        batch = get_object_or_404(RawMaterialBatch, pk=batch_id)
        
        # Get QC info if available
        qc_info = {}
        try:
            qc = batch.qc_checks.first()  # Assuming one QC check per batch
            if qc:
                qc_info = {
                    'id': qc.id,
                    'status': qc.status,
                    'tested_by': qc.tested_by.username if qc.tested_by else None,
                    'test_date': qc.test_date.strftime('%Y-%m-%d') if qc.test_date else None,
                    'remarks': qc.remarks,
                }
        except Exception as e:
            import logging
            logging.error(f"Error accessing QC info: {str(e)}")
        
        # Format batch data
        batch_data = {
            'id': batch.id,
            'batch_number': batch.batch_number,
            'material': {
                'id': batch.material.id,
                'material_code': batch.material.material_code,
                'material_name': batch.material.material_name,
            },
            'quantity_received': float(batch.quantity_received),
            'quantity_remaining': float(batch.quantity_remaining),
            'status': batch.status,
            'date_received': batch.date_received.strftime('%Y-%m-%d'),
            'expiry_date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else None,
            'manufacturer': batch.manufacturer,
            'qc_info': qc_info,
        }
        
        return JsonResponse({'success': True, 'batch': batch_data})
        
    except Exception as e:
        import logging
        logging.error(f"Error in api_batch_detail: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def api_update_associations(request):
    """API endpoint to update product associations for a raw material"""
    try:
        material_id = request.POST.get('material_id')
        product_ids_json = request.POST.get('product_ids')
        
        if not material_id or not product_ids_json:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        try:
            import json
            product_ids = json.loads(product_ids_json)
            
            # Get the material
            material = RawMaterial.objects.get(pk=material_id)
            
            # Import Product model
            from products.models import Product
            
            # Clear existing associations first
            material.products.clear()
            
            # Add new associations
            for product_id in product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    product.raw_materials.add(material)
                except Product.DoesNotExist:
                    # Skip products that don't exist
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Updated product associations for {material.material_name}'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid product IDs format'})
        except RawMaterial.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Material not found'})
            
    except Exception as e:
        import logging
        logging.error(f"Error updating product associations: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
