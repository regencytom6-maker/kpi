"""
Machine API endpoints for dashboards
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from workflow.models import Machine, BatchPhaseExecution

@login_required
def machine_overview_api(request):
    """API endpoint to get machine data for the dashboard"""
    all_machines = Machine.objects.all().order_by('machine_type', 'name')
    machines_data = []

    for machine in all_machines:
        usage_count = BatchPhaseExecution.objects.filter(machine_used=machine).count()
        breakdown_count = BatchPhaseExecution.objects.filter(
            machine_used=machine,
            breakdown_occurred=True
        ).count()
        changeover_count = BatchPhaseExecution.objects.filter(
            machine_used=machine,
            changeover_occurred=True
        ).count()
        
        # Check if machine is currently in use
        current_usage = BatchPhaseExecution.objects.filter(
            machine_used=machine,
            status='in_progress'
        ).order_by('-created_date').first()
        
        current_usage_str = 'Not in use'
        if current_usage:
            current_usage_str = current_usage.phase.name
            
        # Add machine data to the list
        machines_data.append({
            'id': machine.id,
            'name': machine.name,
            'machine_type': machine.machine_type,
            'is_active': machine.is_active,
            'usage_count': usage_count,
            'breakdown_count': breakdown_count,
            'changeover_count': changeover_count,
            'breakdown_rate': round((breakdown_count / usage_count * 100), 1) if usage_count > 0 else 0,
            'current_usage': current_usage_str
        })
    
    return JsonResponse({
        'status': 'success',
        'machines': machines_data
    })
