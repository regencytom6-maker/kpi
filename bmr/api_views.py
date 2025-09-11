from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from bmr.models import BMR

def bmr_materials_api(request, bmr_id):
    """API endpoint to get materials for a BMR"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Get all materials for this BMR
    bmr_materials = bmr.materials.all().prefetch_related('material', 'dispensing_items')
    
    materials_data = []
    
    for material in bmr_materials:
        # Check if it's been dispensed
        dispensed_item = material.dispensing_items.first()
        
        material_data = {
            'name': material.material.material_name if material.material else material.material_name,
            'code': material.material_code,
            'required': float(material.required_quantity),
            'unit': material.material.unit_of_measure if material.material else material.unit_of_measure,
            'is_dispensed': material.is_dispensed,
            'batch_lot': material.batch_lot_number if material.batch_lot_number else (dispensed_item.material_batch.batch_number if dispensed_item and dispensed_item.material_batch else ''),
            'dispensed': float(material.dispensed_quantity) if material.dispensed_quantity else None,
        }
        
        materials_data.append(material_data)
    
    return JsonResponse({
        'bmr_number': bmr.bmr_number,
        'batch_number': bmr.batch_number,
        'materials': materials_data
    })
