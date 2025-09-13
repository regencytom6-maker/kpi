from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import BMR

@login_required
def materials_detail_view(request, bmr_id):
    """View to display exact details of materials for a BMR"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Get all materials for this BMR
    bmr_materials = bmr.materials.all().select_related('material').prefetch_related('dispensing_items')
    
    # Process materials data
    materials = []
    for material in bmr_materials:
        # Check if it's been dispensed
        dispensed_item = material.dispensing_items.first()
        
        material_data = {
            'name': material.material.material_name if material.material else material.material_name,
            'code': material.material_code,
            'required': float(material.required_quantity),
            'unit': material.material.unit_of_measure if material.material else material.unit_of_measure,
            'is_dispensed': material.is_dispensed,
            'batch_lot': material.batch_lot_number if material.batch_lot_number else (dispensed_item.material_batch.batch_number if dispensed_item and hasattr(dispensed_item, 'material_batch') and dispensed_item.material_batch else ''),
            'dispensed': float(material.dispensed_quantity) if material.dispensed_quantity else None,
        }
        materials.append(material_data)

    # Create a simple HTML response directly
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Materials for {bmr.batch_number} - Kampala Pharmaceutical Industries</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ padding-top: 20px; }}
            .material-row:hover {{ background-color: #f8f9fa; }}
        </style>
    </head>
    <body>
        <div class="container-fluid mt-4">
            <!-- Header -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center">
                        <h2 class="text-primary">
                            <i class="fas fa-boxes me-2"></i>Materials for {bmr.batch_number}
                        </h2>
                        <a href="/bmr/{bmr.id}/" class="btn btn-primary">
                            <i class="fas fa-arrow-left me-1"></i>Back to BMR
                        </a>
                    </div>
                </div>
            </div>
            
            <!-- BMR Information Card -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-info-circle me-2"></i>BMR Information
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <p class="mb-1"><strong>BMR Number:</strong></p>
                                    <p>{bmr.bmr_number}</p>
                                </div>
                                <div class="col-md-3">
                                    <p class="mb-1"><strong>Batch Number:</strong></p>
                                    <p>{bmr.batch_number}</p>
                                </div>
                                <div class="col-md-3">
                                    <p class="mb-1"><strong>Product:</strong></p>
                                    <p>{bmr.product.product_name}</p>
                                </div>
                                <div class="col-md-3">
                                    <p class="mb-1"><strong>Batch Size:</strong></p>
                                    <p>{bmr.batch_size}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Materials Table -->
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-clipboard-list me-2"></i>Exact Material Details
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped table-bordered">
                                    <thead class="table-dark">
                                        <tr>
                                            <th style="width: 25%">Material</th>
                                            <th style="width: 15%">Code</th>
                                            <th style="width: 15%">Required Quantity</th>
                                            <th style="width: 15%">Dispensed Quantity</th>
                                            <th style="width: 15%">Batch/Lot Number</th>
                                            <th style="width: 15%">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
    """
    
    # Add material rows
    if materials:
        for material in materials:
            status_badge = '<span class="badge bg-success">Dispensed</span>' if material['is_dispensed'] else '<span class="badge bg-warning">Pending</span>'
            dispensed_qty = f"{material['dispensed']} {material['unit']}" if material['dispensed'] else '-'
            
            html_content += f"""
                                        <tr class="material-row">
                                            <td><strong>{material['name']}</strong></td>
                                            <td>{material['code']}</td>
                                            <td>{material['required']} {material['unit']}</td>
                                            <td>{dispensed_qty}</td>
                                            <td>{material['batch_lot'] or '-'}</td>
                                            <td>{status_badge}</td>
                                        </tr>
            """
    else:
        html_content += """
                                        <tr>
                                            <td colspan="6" class="text-center">
                                                <p class="text-muted">No materials found for this BMR.</p>
                                            </td>
                                        </tr>
        """
        
    # Complete the HTML structure
    html_content += """
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="card-footer">
                            <small class="text-muted">
                                <i class="fas fa-info-circle me-1"></i>
                                This page shows the exact details of materials required for this BMR.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content)
