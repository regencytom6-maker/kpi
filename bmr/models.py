from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from products.models import Product
from datetime import datetime
import re

def validate_batch_number(value):
    """Validate batch number format XXX-YYYY"""
    pattern = r'^\d{3}\d{4}$'  # 3 digits + 4 digits (e.g., 0012025)
    if not re.match(pattern, value):
        raise ValidationError(
            'Batch number must be in format XXXYYYY (e.g., 0012025)'
        )

class BMR(models.Model):
    """Batch Manufacturing Record - Core document for pharmaceutical production"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # BMR Header Information
    bmr_number = models.CharField(max_length=20, unique=True)
    batch_number = models.CharField(
        max_length=10, 
        unique=True,
        validators=[validate_batch_number],
        help_text="Enter batch number in format XXXYYYY (e.g., 0012025)"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_size = models.DecimalField(max_digits=10, decimal_places=2)
    batch_size_unit = models.CharField(max_length=20, default='units')
    
    # Dates
    created_date = models.DateTimeField(auto_now_add=True)
    planned_start_date = models.DateTimeField(null=True, blank=True)
    planned_completion_date = models.DateTimeField(null=True, blank=True)
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Personnel
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_bmrs'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_bmrs'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Manufacturing Instructions
    manufacturing_instructions = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Quality Parameters
    in_process_controls = models.TextField(blank=True)
    quality_checks_required = models.TextField(blank=True)
    
    # Comments and Notes
    qa_comments = models.TextField(blank=True)
    regulatory_comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Batch Manufacturing Record'
        verbose_name_plural = 'Batch Manufacturing Records'
    
    def __str__(self):
        return f"BMR-{self.bmr_number} | Batch: {self.batch_number} | {self.product.product_name}"
    
    def save(self, *args, **kwargs):
        if not self.bmr_number:
            self.bmr_number = self.generate_bmr_number()
        super().save(*args, **kwargs)
    
    def generate_bmr_number(self):
        """Generate unique BMR number"""
        year = datetime.now().year
        count = BMR.objects.filter(created_date__year=year).count() + 1
        return f"BMR{year}{count:04d}"

class BMRMaterial(models.Model):
    """Materials required for BMR production"""
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='materials')
    material_name = models.CharField(max_length=200)
    material_code = models.CharField(max_length=50)
    required_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    unit_of_measure = models.CharField(max_length=20)
    batch_lot_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    
    # Dispensing information
    dispensed_quantity = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    dispensed_date = models.DateTimeField(null=True, blank=True)
    is_dispensed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.bmr.bmr_number} - {self.material_name}"

class BMRSignature(models.Model):
    """Electronic signatures for BMR approval and sign-offs"""
    
    SIGNATURE_TYPE_CHOICES = [
        ('created', 'Created'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('dispensed', 'Materials Dispensed'),
        ('production_started', 'Production Started'),
        ('production_completed', 'Production Completed'),
        ('qc_approved', 'QC Approved'),
        ('final_approval', 'Final Approval'),
    ]
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='signatures')
    signature_type = models.CharField(max_length=30, choices=SIGNATURE_TYPE_CHOICES)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signed_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['bmr', 'signature_type', 'signed_by']
    
    def __str__(self):
        return f"{self.bmr.bmr_number} - {self.get_signature_type_display()} by {self.signed_by.username}"
