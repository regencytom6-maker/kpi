from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from products.models import Product
from decimal import Decimal

@receiver(m2m_changed, sender=Product.raw_materials.through)
def sync_raw_materials_on_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Signal handler to sync raw_materials M2M relationship with ProductMaterial model
    when raw_materials are added or removed from a product.
    """
    if action == 'post_add' and not reverse:
        # Materials added to a product
        from products.models_material import ProductMaterial
        
        for material_id in pk_set:
            raw_material = model.objects.get(pk=material_id)
            # Get the unit of measure with fallback
            unit = getattr(raw_material, 'unit_of_measure', 'units')
            
            # Create ProductMaterial if it doesn't exist
            ProductMaterial.objects.get_or_create(
                product=instance,
                raw_material=raw_material,
                defaults={
                    'required_quantity': Decimal('1.0'),
                    'unit_of_measure': unit,
                    'is_active_ingredient': raw_material.category == 'active'
                }
            )
    
    elif action == 'post_remove' and not reverse:
        # Materials removed from a product
        from products.models_material import ProductMaterial
        
        for material_id in pk_set:
            # Delete ProductMaterial entries for removed materials
            ProductMaterial.objects.filter(
                product=instance,
                raw_material_id=material_id
            ).delete()
