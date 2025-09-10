from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from bmr.models import BMR, BMRMaterial
from .models import MaterialDispensing, MaterialDispensingItem, RawMaterial, RawMaterialBatch
from products.models_material import ProductMaterial


@receiver(post_save, sender=BMR)
def create_material_dispensing(sender, instance, created, **kwargs):
    """Create material dispensing record when BMR is approved"""
    if instance.status == 'approved':
        # Check if dispensing already exists
        if not hasattr(instance, 'material_dispensing'):
            # Create new dispensing record
            MaterialDispensing.objects.create(
                bmr=instance,
                status='pending'
            )


@receiver(post_save, sender=BMRMaterial)
def link_to_raw_material(sender, instance, created, **kwargs):
    """Link BMR materials to raw materials system"""
    if created:
        # Try to find a matching raw material by code
        try:
            raw_material = RawMaterial.objects.get(material_code=instance.material_code)
            
            # If BMR is already approved and has a material dispensing record
            if instance.bmr.status == 'approved' and hasattr(instance.bmr, 'material_dispensing'):
                # Find suitable batch with enough quantity
                suitable_batch = RawMaterialBatch.objects.filter(
                    material=raw_material,
                    status='approved',
                    quantity_remaining__gte=instance.required_quantity
                ).order_by('expiry_date').first()
                
                if suitable_batch:
                    # Create dispensing item with null dispensed quantity
                    MaterialDispensingItem.objects.create(
                        dispensing=instance.bmr.material_dispensing,
                        bmr_material=instance,
                        material_batch=suitable_batch,
                        required_quantity=instance.required_quantity
                    )
        except RawMaterial.DoesNotExist:
            # No matching raw material found
            pass


@receiver(pre_save, sender=ProductMaterial)
def validate_material_quantities(sender, instance, **kwargs):
    """Validate units and quantities when updating material associations"""
    
    # Ensure the units match
    if instance.unit_of_measure != instance.raw_material.unit_of_measure:
        raise ValidationError(
            f"Unit mismatch: Product requires {instance.unit_of_measure} but material {instance.raw_material.material_name} "
            f"uses {instance.raw_material.unit_of_measure}"
        )

@receiver(post_save, sender=ProductMaterial)
def sync_material_requirements(sender, instance, created, **kwargs):
    """Keep raw material requirements in sync across the system"""
    from django.db import connection
    
    # Update all related BMR materials to use the same quantity if they exist
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE bmr_bmrmaterial
            SET required_quantity = %s
            WHERE material_code = %s
            AND required_quantity != %s
        """, [
            instance.required_quantity,
            instance.raw_material.material_code,
            instance.required_quantity
        ])