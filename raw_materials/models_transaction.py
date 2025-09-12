from django.db import models
from django.conf import settings
from django.utils import timezone

class InventoryTransaction(models.Model):
    """Tracks all inventory transactions for raw materials"""
    TRANSACTION_TYPES = [
        ('received', 'Material Received'),
        ('dispensed', 'Material Dispensed'),
        ('returned', 'Material Returned'),
        ('adjusted', 'Quantity Adjusted'),
        ('expired', 'Material Expired'),
        ('rejected', 'Material Rejected'),
    ]
    
    material_batch = models.ForeignKey('raw_materials.RawMaterialBatch', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=4)
    transaction_date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    reference_bmr = models.ForeignKey('bmr.BMR', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_transactions')
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.material_batch.material.material_name} ({self.transaction_date.strftime('%Y-%m-%d %H:%M')})"
