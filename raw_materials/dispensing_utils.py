"""
This module contains fixes for the raw materials dispensing functionality.
"""

from decimal import Decimal
from django.utils import timezone
from raw_materials.models import MaterialDispensingItem, InventoryTransaction


def update_material_quantities(dispensing_item):
    """
    Update material quantities properly for a dispensing item.
    
    Args:
        dispensing_item: The MaterialDispensingItem to process
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Skip if already processed
        if dispensing_item.is_dispensed:
            return True
            
        # Get the batch
        batch = dispensing_item.material_batch
        
        # Calculate the quantity to subtract
        # If dispensed_quantity is 0, use required_quantity instead
        if dispensing_item.dispensed_quantity == 0 and dispensing_item.required_quantity > 0:
            dispensing_item.dispensed_quantity = dispensing_item.required_quantity
            dispensing_item.save(update_fields=['dispensed_quantity'])
            
        dispensed_qty = Decimal(str(dispensing_item.dispensed_quantity))
        
        # Check if there's enough quantity
        if batch.quantity_remaining < dispensed_qty:
            return False
            
        # Update the batch quantity
        old_quantity = batch.quantity_remaining
        batch.quantity_remaining -= dispensed_qty
        batch.save()
        
        # Create transaction record
        InventoryTransaction.objects.create(
            material=batch.material,
            material_batch=batch,
            transaction_type='dispensed',
            quantity=dispensed_qty,
            reference_number=dispensing_item.dispensing.dispensing_reference,
            performed_by=dispensing_item.dispensing.dispensed_by,
            notes=f"Dispensed for BMR {dispensing_item.dispensing.bmr.bmr_number}"
        )
        
        # Mark as dispensed
        dispensing_item.is_dispensed = True
        dispensing_item.dispensed_date = timezone.now()
        dispensing_item.save(update_fields=['is_dispensed', 'dispensed_date'])
        
        return True
    
    except Exception:
        return False
