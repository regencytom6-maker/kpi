from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import RawMaterial, RawMaterialBatch, RawMaterialQC
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
import json
import logging
from datetime import datetime, timedelta

@login_required
def api_materials(request):
    """API endpoint for raw materials data"""
    material_id = request.GET.get('material_id')
    include_all_products = request.GET.get('include_all_products') == 'true'
    
    if material_id:
        # Return detail for a specific material
        try:
            material = RawMaterial.objects.get(pk=material_id)
            
            # Initialize product_names outside the try block to ensure it always exists
            product_names = []
            product_ids = []
            all_products_data = []
            
            # Get associated products safely with more debug info
            try:
                from products.models import Product
                import logging
                
                # Print debug information
                logging.info(f"Looking up products for material: {material.material_name} (ID: {material_id})")
                
                # Check if any products exist at all
                all_products_count = Product.objects.all().count()
                logging.info(f"Total products in database: {all_products_count}")
                
                # Get products that have this material in their many-to-many relationship
                products = Product.objects.filter(raw_materials=material)
                product_names = [f"{p.product_name} ({p.get_product_type_display()})" for p in products]
                product_ids = [p.id for p in products]
                
                # Log what we found
                logging.info(f"Found {len(products)} products for material {material_id}")
                for p in products:
                    logging.info(f"Product: {p.product_name} ({p.get_product_type_display()})")
                
                # If include_all_products is true, also return a list of all products
                if include_all_products:
                    all_products = Product.objects.all()
                    all_products_data = [
                        {
                            'id': p.id,
                            'name': p.product_name,
                            'type': p.get_product_type_display()
                        }
                        for p in all_products
                    ]
                
                # If no products found, add a sample one for testing
                if len(products) == 0 and all_products_count > 0 and not include_all_products:
                    logging.info("No products associated, checking for available products to associate")
                    # Get a sample product
                    sample_product = Product.objects.first()
                    if sample_product:
                        logging.info(f"Adding association to product: {sample_product.product_name}")
                        sample_product.raw_materials.add(material)
                        sample_product.save()
                        product_names = [f"{sample_product.product_name} ({sample_product.get_product_type_display()}) (auto-associated)"]
                        product_ids = [sample_product.id]
                
            except Exception as e:
                import logging
                logging.error(f"Error accessing products for material {material_id}: {str(e)}")
                # product_names is already initialized to [] outside the try block
            
            material_data = {
                'id': material.id,
                'material_code': material.material_code,
                'material_name': material.material_name,
                'category': material.category,
                'category_display': material.get_category_display(),
                'unit_of_measure': material.unit_of_measure,
                'current_stock': float(material.current_stock),
                'reorder_level': float(material.reorder_level),
                'status': material.status,
                'default_supplier': material.default_supplier,
                'pending_qc_batches': material.pending_qc_batches,
                'products': product_names,
                'product_ids': product_ids
            }
            
            response_data = {'success': True, 'material': material_data}
            
            # Add all_products to the response if requested
            if include_all_products and all_products_data:
                response_data['all_products'] = all_products_data
                
            return JsonResponse(response_data)
            
        except RawMaterial.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Material not found'})
    
    # Return list of all materials
    materials = RawMaterial.objects.all()
    
    materials_data = []
    for material in materials:
        # Get associated products for each material
        try:
            products = material.products.all()
            product_names = [f"{p.product_name} ({p.get_product_type_display()})" for p in products]
        except Exception as e:
            import logging
            logging.error(f"Error accessing products for material {material.id}: {str(e)}")
            product_names = []
            
        materials_data.append({
            'id': material.id,
            'material_code': material.material_code,
            'material_name': material.material_name,
            'category': material.category,
            'category_display': material.get_category_display(),
            'unit_of_measure': material.unit_of_measure,
            'current_stock': float(material.current_stock),
            'reorder_level': float(material.reorder_level),
            'status': material.status,
            'default_supplier': material.default_supplier,
            'pending_qc_batches': material.pending_qc_batches,
            'products': product_names  # Include associated products
        })
    
    return JsonResponse({'success': True, 'materials': materials_data})

@login_required
def api_material_detail(request, material_id):
    """Get detailed information for a specific material including batches"""
    try:
        material = get_object_or_404(RawMaterial, pk=material_id)
        
        # Get batches for this material
        batches = RawMaterialBatch.objects.filter(material=material)
        
        # Format batch data
        batches_data = []
        for batch in batches:
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
                    }
            except Exception as e:
                pass
                
            batches_data.append({
                'id': batch.id,
                'batch_number': batch.batch_number,
                'quantity_received': float(batch.quantity_received),
                'quantity_remaining': float(batch.quantity_remaining),
                'status': batch.status,
                'date_received': batch.date_received.strftime('%Y-%m-%d'),
                'qc_status': batch.qc_status,
                'expiry_date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else None,
                'manufacturer': batch.manufacturer,
                'qc_info': qc_info,
            })
        
        # Get products that use this material
        product_names = []
        try:
            # Find products that have this material in their many-to-many field
            from products.models import Product
            products = Product.objects.filter(raw_materials=material)
            product_names = [f"{p.product_name} ({p.get_product_type_display()})" for p in products]
        except Exception as e:
            logging.error(f"Error accessing products: {str(e)}")
        
        # Build response
        material_data = {
            'id': material.id,
            'material_code': material.material_code,
            'material_name': material.material_name,
            'category': material.category,
            'category_display': material.get_category_display(),
            'unit_of_measure': material.unit_of_measure,
            'current_stock': float(material.current_stock),
            'reorder_level': float(material.reorder_level),
            'batches': batches_data,
            'products': product_names
        }
        
        return JsonResponse({'success': True, 'material': material_data})
    
    except Exception as e:
        logging.error(f"Error in api_material_detail: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_material_batches(request, material_id):
    """Get batches for a specific material"""
    try:
        material = get_object_or_404(RawMaterial, pk=material_id)
        
        # Get batches for this material
        batches = RawMaterialBatch.objects.filter(material=material)
        
        # Format batch data
        batches_data = []
        for batch in batches:
            batches_data.append({
                'id': batch.id,
                'batch_number': batch.batch_number,
                'quantity_received': float(batch.quantity_received),
                'quantity_remaining': float(batch.quantity_remaining),
                'status': batch.status,
                'date_received': batch.date_received.strftime('%Y-%m-%d'),
                'expiry_date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else None,
            })
        
        return JsonResponse({'success': True, 'batches': batches_data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_qc_results(request, batch_id):
    """Get QC results for a specific batch"""
    try:
        batch = get_object_or_404(RawMaterialBatch, pk=batch_id)
        
        # Get QC checks for this batch
        qc_checks = RawMaterialQC.objects.filter(batch=batch)
        
        # Format QC data
        qc_data = []
        for qc in qc_checks:
            qc_data.append({
                'id': qc.id,
                'status': qc.status,
                'tested_by': qc.tested_by.username if qc.tested_by else 'N/A',
                'test_date': qc.test_date.strftime('%Y-%m-%d') if qc.test_date else 'N/A',
                'remarks': qc.remarks,
                'parameters': qc.parameters
            })
        
        return JsonResponse({'success': True, 'qc_checks': qc_data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def api_add_material(request):
    """API endpoint to add a new raw material"""
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
def save_qc_test_old(request):
    """OLD VERSION - This function is obsolete. See the new save_qc_test below."""
    try:
        batch_id = request.POST.get('batch_id')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        parameters = request.POST.get('parameters', '{}')
        
        if not all([batch_id, status]):
            return JsonResponse({'success': False, 'error': 'Using obsolete function - Missing required fields'})
        
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

@login_required
def api_inventory_by_product(request):
    """API endpoint to get inventory organized by product"""
    try:
        from products.models import Product
        
        # Check if a specific product ID was requested
        product_id = request.GET.get('product_id')
        
        if product_id:
            # Get specific product
            try:
                products = [Product.objects.get(pk=product_id)]
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Product not found'})
        else:
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
        
@login_required
def api_qc_test_detail(request):
    """API endpoint to get QC test details"""
    try:
        test_id = request.GET.get('test_id')
        
        if not test_id:
            return JsonResponse({'success': False, 'error': 'Test ID is required'})
            
        qc_test = RawMaterialQC.objects.get(pk=test_id)
        
        test_data = {
            'id': qc_test.id,
            'material_batch_id': qc_test.material_batch.id,
            'material_name': qc_test.material_batch.material.material_name,
            'batch_number': qc_test.material_batch.batch_number,
            'test_date': qc_test.test_date.strftime('%Y-%m-%d %H:%M') if qc_test.test_date else None,
            'status': qc_test.status,
            'appearance_result': qc_test.appearance_result,
            'identification_result': qc_test.identification_result,
            'assay_result': qc_test.assay_result,
            'purity_result': qc_test.purity_result,
            'final_result': qc_test.final_result,
            'comments': qc_test.comments,
            'tested_by': qc_test.tested_by.username if qc_test.tested_by else None
        }
        
        return JsonResponse({'success': True, 'test': test_data})
        
    except RawMaterialQC.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'QC test not found'})
    except Exception as e:
        import logging
        logging.error(f"Error in api_qc_test_detail: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def save_qc_test(request):
    """API endpoint to save QC test results"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"QC Test Save Function Called - Method: {request.method}")
    logger.info(f"Request headers: {request.headers}")
    
    # Print to console as well for immediate feedback
    print("======= QC TEST SAVE FUNCTION CALLED =======")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    
    # Ensure we're processing a POST request
    if request.method != 'POST':
        print("ERROR: Not a POST request")
        return JsonResponse({'success': False, 'error': 'POST method required'})
        
    try:
        # Log incoming data
        logger.info(f"Received form data: {request.POST}")
        print(f"POST Data: {request.POST}")
        
        # Extract basic form fields
        test_id = request.POST.get('test_id')
        batch_id = request.POST.get('batch_id')
        appearance = request.POST.get('appearance_result')
        identification = request.POST.get('identification_result')
        assay = request.POST.get('assay_result')
        purity = request.POST.get('purity_result')
        ph_value = request.POST.get('ph_value')
        loss_on_drying = request.POST.get('loss_on_drying')
        final_result = request.POST.get('final_result')
        comments = request.POST.get('comments', '')
        
        # Validate required fields
        if not batch_id:
            return JsonResponse({'success': False, 'error': 'Batch ID is required'})
            
        # Validate required fields only when completing the test (not when starting)
        status_indicator = request.POST.get('status')
        
        # If this is just to start a test (status='in_progress'), don't require test results
        if status_indicator == 'in_progress':
            # This is just starting a test - no validation needed
            pass
        else:
            # This is completing a test - validate required fields
            if not appearance or not identification or not final_result:
                return JsonResponse({'success': False, 'error': 'Missing required test results'})
        
        # Only validate final_result if it's provided
        if final_result:
            # Ensure final_result is normalized
            final_result = final_result.lower()
            if 'pass' in final_result:
                final_result = 'pass'
            elif 'fail' in final_result:
                final_result = 'fail'
            else:
                return JsonResponse({'success': False, 'error': 'Invalid final result value'})
            
        logger.info(f"Processing QC test - Batch: {batch_id}, Final Result: {final_result}")
        
        # Find or create QC test record
        if test_id:
            # Update existing test
            try:
                qc_test = RawMaterialQC.objects.get(pk=test_id)
                logger.info(f"Found existing QC test with ID: {test_id}")
            except RawMaterialQC.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'QC Test with ID {test_id} not found'})
        else:
            # Find the batch
            try:
                batch = RawMaterialBatch.objects.get(pk=batch_id)
                logger.info(f"Found batch: {batch.batch_number} for material: {batch.material.material_name}")
            except RawMaterialBatch.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Batch with ID {batch_id} not found'})
                
            # Check for existing test
            existing_test = RawMaterialQC.objects.filter(material_batch=batch).first()
            if existing_test:
                qc_test = existing_test
                logger.info(f"Found existing QC test for batch: {qc_test.id}")
            else:
                # Create new test
                qc_test = RawMaterialQC(material_batch=batch)
                logger.info(f"Creating new QC test for batch {batch.batch_number}")
        
        # Update test fields
        qc_test.appearance_result = appearance
        qc_test.identification_result = identification
        qc_test.assay_result = assay
        qc_test.purity_result = purity
        qc_test.final_result = final_result
        qc_test.comments = comments
        qc_test.tested_by = request.user
        qc_test.test_date = timezone.now()
        
        # Handle the new fields - pH value and loss on drying
        from decimal import Decimal, InvalidOperation
        if ph_value:
            try:
                qc_test.ph_value = Decimal(ph_value)
            except InvalidOperation:
                logger.warning(f"Invalid pH value received: {ph_value}")
                
        if loss_on_drying:
            try:
                qc_test.loss_on_drying = Decimal(loss_on_drying)
            except InvalidOperation:
                logger.warning(f"Invalid loss on drying value received: {loss_on_drying}")
        
        # Set status based on final result or explicit status
        if final_result == 'pass':
            logger.info(f"QC TEST PASSED - Marking batch as approved")
            qc_test.status = 'approved'
            qc_test.completed_date = timezone.now()
            qc_test.completed_by = request.user
            
            # Update batch status to approved (ready for store manager to release)
            qc_test.material_batch.status = 'approved'
            qc_test.material_batch.approved_date = timezone.now()
            qc_test.material_batch.approved_by = request.user
            
        elif final_result == 'fail':
            logger.info(f"QC TEST FAILED - Marking batch as rejected")
            qc_test.status = 'rejected'
            qc_test.completed_date = timezone.now()
            qc_test.completed_by = request.user
            
            # Update batch status to rejected
            qc_test.material_batch.status = 'rejected'
            qc_test.material_batch.rejection_date = timezone.now()
            qc_test.material_batch.rejected_by = request.user
            
        elif status_indicator == 'in_progress' or not final_result:
            logger.info(f"QC TEST IN PROGRESS")
            qc_test.status = 'in_progress'
            if not qc_test.started_date:
                qc_test.started_date = timezone.now()
                qc_test.started_by = request.user
            
        # Save both records
        qc_test.save()
        qc_test.material_batch.save()
        
        logger.info(f"QC Test saved successfully with ID: {qc_test.id}, Status: {qc_test.status}")
        print(f"SUCCESS: QC Test saved with ID: {qc_test.id}, Status: {qc_test.status}")
        print(f"  - Final Result: {qc_test.final_result}")
        print(f"  - Appearance: {qc_test.appearance_result}")
        print(f"  - Identification: {qc_test.identification_result}")
        
        # Return success response with detailed data
        return JsonResponse({
            'success': True,
            'test_id': qc_test.id,
            'status': qc_test.status,
            'final_result': qc_test.final_result,
            'message': 'QC Test saved successfully',
            'batch_status': qc_test.material_batch.status
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error in save_qc_test: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def start_qc_test(request):
    """API endpoint to initiate a QC test without saving results yet"""
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
        
    try:
        batch_id = request.POST.get('batch_id')
        
        if not batch_id:
            return JsonResponse({'success': False, 'error': 'Batch ID is required'})
            
        # Find the batch
        try:
            batch = RawMaterialBatch.objects.get(pk=batch_id)
            logger.info(f"Starting QC test for batch: {batch.batch_number}")
        except RawMaterialBatch.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Batch with ID {batch_id} not found'})
            
        # Check for existing test
        existing_test = RawMaterialQC.objects.filter(material_batch=batch).first()
        if existing_test:
            # Return existing test
            logger.info(f"Found existing QC test: {existing_test.id}")
            test_id = existing_test.id
        else:
            # Create new test without results
            new_test = RawMaterialQC(
                material_batch=batch,
                status='in_progress',
                started_by=request.user,
                started_date=timezone.now()
            )
            new_test.save()
            test_id = new_test.id
            logger.info(f"Created new QC test with ID: {test_id}")
            
        return JsonResponse({
            'success': True,
            'test_id': test_id,
            'message': 'QC test initiated'
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error in start_qc_test: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_batch_detail(request):
    """API endpoint to get batch details"""
    try:
        batch_id = request.GET.get('batch_id')
        material_id = request.GET.get('material_id')
        
        if batch_id:
            # Get details for a specific batch
            batch = RawMaterialBatch.objects.get(pk=batch_id)
            
            # Format batch data
            batch_data = {
                'id': batch.id,
                'material_id': batch.material.id,
                'material_name': batch.material.material_name,
                'material_code': batch.material.material_code,
                'batch_number': batch.batch_number,
                'quantity_received': float(batch.quantity_received),
                'quantity_remaining': float(batch.quantity_remaining),
                'unit_of_measure': batch.material.unit_of_measure,
                'supplier': batch.supplier,
                'received_date': batch.received_date.strftime('%Y-%m-%d'),
                'manufacturing_date': batch.manufacturing_date.strftime('%Y-%m-%d') if batch.manufacturing_date else None,
                'expiry_date': batch.expiry_date.strftime('%Y-%m-%d'),
                'status': batch.status,
                'received_by': batch.received_by.username if batch.received_by else None
            }
            
            return JsonResponse({'success': True, 'batch': batch_data})
        
        elif material_id:
            # Get all batches for a material
            material = RawMaterial.objects.get(pk=material_id)
            
            # Get batches for this material, with focus on approved batches
            all_batches = RawMaterialBatch.objects.filter(material=material).order_by('-status', '-received_date')
            
            # Format batches data
            batches_data = []
            for batch in all_batches:
                batch_data = {
                    'id': batch.id,
                    'batch_number': batch.batch_number,
                    'quantity_received': float(batch.quantity_received),
                    'quantity_remaining': float(batch.quantity_remaining),
                    'received_date': batch.received_date.strftime('%Y-%m-%d'),
                    'expiry_date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else None,
                    'status': batch.status,
                    'supplier': batch.supplier
                }
                batches_data.append(batch_data)
            
            # Format material data
            material_data = {
                'id': material.id,
                'material_name': material.material_name,
                'material_code': material.material_code,
                'unit_of_measure': material.unit_of_measure
            }
            
            return JsonResponse({'success': True, 'material': material_data, 'batches': batches_data})
        
        else:
            return JsonResponse({'success': False, 'error': 'Either batch_id or material_id is required'})
        
    except RawMaterialBatch.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Batch not found'})
    except Exception as e:
        import logging
        logging.error(f"Error in api_batch_detail: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
