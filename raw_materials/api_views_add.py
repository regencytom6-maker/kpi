@login_required
def api_inventory_by_product(request):
    """API endpoint to get inventory organized by product"""
    try:
        from products.models import Product
        
        # Get all products
        products = Product.objects.all()
        
        product_inventory = []
        
        for product in products:
            # Get raw materials for this product
            materials = product.raw_materials.all()
            
            # Calculate total approved inventory for each material
            material_data = []
            for material in materials:
                # Get approved batches
                approved_batches = RawMaterialBatch.objects.filter(
                    material=material,
                    status='approved'
                )
                
                # Calculate total approved quantity
                approved_quantity = sum(batch.quantity_remaining for batch in approved_batches)
                
                # Get pending QC batches
                pending_qc_batches = RawMaterialBatch.objects.filter(
                    material=material,
                    status='pending_qc'
                )
                
                # Calculate total pending quantity
                pending_quantity = sum(batch.quantity_received for batch in pending_qc_batches)
                
                # Add material info
                material_data.append({
                    'id': material.id,
                    'material_code': material.material_code,
                    'material_name': material.material_name,
                    'unit_of_measure': material.unit_of_measure,
                    'approved_quantity': float(approved_quantity),
                    'pending_quantity': float(pending_quantity),
                    'reorder_level': float(material.reorder_level),
                    'status': 'low_stock' if approved_quantity < material.reorder_level else 'in_stock'
                })
            
            # Add product info with its materials
            product_inventory.append({
                'id': product.id,
                'product_name': product.product_name,
                'product_type': product.get_product_type_display(),
                'materials': material_data,
                'material_count': len(material_data)
            })
        
        return JsonResponse({'success': True, 'product_inventory': product_inventory})
        
    except Exception as e:
        import logging
        logging.error(f"Error in api_inventory_by_product: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
