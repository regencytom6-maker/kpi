from django.db import models
from django.utils.translation import gettext_lazy as _

class ProductMaterial(models.Model):
    """
    This model connects products to raw materials with specific quantities required for production.
    It provides a more detailed relationship than the simple ManyToMany in the Product model.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='product_materials')
    raw_material = models.ForeignKey('raw_materials.RawMaterial', on_delete=models.CASCADE, related_name='product_materials')
    required_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    unit_of_measure = models.CharField(max_length=20)
    is_active_ingredient = models.BooleanField(default=False, help_text=_("Check if this is an active pharmaceutical ingredient"))
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('product', 'raw_material')
        verbose_name = _("Product Material")
        verbose_name_plural = _("Product Materials")
        ordering = ['product__product_name', 'is_active_ingredient']
    
    def __str__(self):
        return f"{self.raw_material.material_name} for {self.product.product_name}: {self.required_quantity} {self.unit_of_measure}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure raw_materials M2M relationship is also updated"""
        # Make sure required_quantity is properly formatted as a Decimal
        try:
            from decimal import Decimal
            # Convert directly to Decimal using string to avoid float precision issues
            if not isinstance(self.required_quantity, Decimal):
                self.required_quantity = Decimal(str(self.required_quantity))
        except Exception:
            # Use a safe default if conversion fails
            from decimal import Decimal
            self.required_quantity = Decimal('1.0')
        
        # Ensure unit_of_measure matches the raw material
        if self.raw_material_id:  # Only if we have a raw material
            if not self.unit_of_measure:
                self.unit_of_measure = self.raw_material.unit_of_measure
            elif self.unit_of_measure != self.raw_material.unit_of_measure:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Unit mismatch: Cannot use {self.unit_of_measure} for material that uses "
                    f"{self.raw_material.unit_of_measure}"
                )
        
        super().save(*args, **kwargs)
        # Ensure this raw material is also in the product's raw_materials
        self.product.raw_materials.add(self.raw_material)
    
    def delete(self, *args, **kwargs):
        """Override delete to check if we should also remove from raw_materials"""
        product = self.product
        raw_material = self.raw_material
        # Delete the ProductMaterial entry
        super().delete(*args, **kwargs)
        # If no other ProductMaterial exists for this material and product, remove from raw_materials
        if not ProductMaterial.objects.filter(product=product, raw_material=raw_material).exists():
            product.raw_materials.remove(raw_material)
    
    def is_approved(self):
        """Check if this material has approved batches"""
        return self.raw_material.inventory_batches.filter(status='approved').exists()
    
    def available_quantity(self):
        """Return the available quantity of this material"""
        return self.raw_material.current_stock
    
    def available_quantity_with_unit(self):
        """Return the available quantity with unit"""
        return f"{self.available_quantity()} {self.raw_material.unit_of_measure}"
    
    def has_sufficient_quantity(self):
        """Check if there is sufficient quantity for production"""
        # This is a simplified check - in reality would need to consider unit conversions
        return self.available_quantity() > self.required_quantity
