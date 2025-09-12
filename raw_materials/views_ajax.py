from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from raw_materials.models import RawMaterial

@staff_member_required
def get_raw_material_unit(request):
    """
    AJAX view to get the unit of measure for a raw material
    Used by the product_material_admin.js script
    """
    raw_material_id = request.GET.get('raw_material_id')
    if not raw_material_id:
        return JsonResponse({'success': False, 'error': 'No raw material ID provided'})
    
    try:
        raw_material = RawMaterial.objects.get(id=raw_material_id)
        return JsonResponse({
            'success': True,
            'unit_of_measure': raw_material.unit_of_measure
        })
    except RawMaterial.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Raw material not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
