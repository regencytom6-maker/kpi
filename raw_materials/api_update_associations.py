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
