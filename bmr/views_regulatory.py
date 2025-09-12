from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import BMR
from dashboards.utils import all_materials_qc_approved

@login_required
def start_bmr_production(request, bmr_id):
    """
    Approves materials for a BMR and marks it ready for production.
    This is called from the QC material report page.
    """
    if request.user.role != 'qc' and request.user.role != 'regulatory':
        messages.error(request, 'Access denied. QC or Regulatory role required.')
        return redirect('dashboards:dashboard_home')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('dashboards:qc_dashboard')
    
    action = request.POST.get('action', '')
    if action != 'qc_approve':
        messages.error(request, 'Invalid action specified.')
        return redirect('dashboards:qc_dashboard')
    
    try:
        # Get the BMR
        bmr = get_object_or_404(BMR, pk=bmr_id)
        
        # Check if all materials are QC approved
        if all_materials_qc_approved(bmr):
            # Update BMR status if not already in production or completed
            if bmr.status not in ['in_production', 'completed']:
                bmr.materials_approved = True
                bmr.materials_approved_by = request.user
                bmr.materials_approved_date = timezone.now()
                bmr.save()
                messages.success(request, f'Materials for BMR {bmr.batch_number} approved successfully.')
            else:
                messages.info(request, f'BMR {bmr.batch_number} is already in production or completed.')
        else:
            messages.error(request, f'Cannot approve BMR {bmr.batch_number}. Some materials have not passed QC.')
        
        # Redirect back to the material report page
        return redirect('dashboards:qc_material_report', bmr_id=bmr_id)
        
    except Exception as e:
        messages.error(request, f'Error approving materials: {str(e)}')
        return redirect('dashboards:qc_dashboard')
