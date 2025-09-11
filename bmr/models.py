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
    # Batch size now comes from Product model - these fields are for actual batch size if different from standard
    actual_batch_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual batch size (if different from standard product batch size)"
    )
    actual_batch_size_unit = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Unit for actual batch size (inherits from product if not specified)"
    )
    
    # Dates
    created_date = models.DateTimeField(auto_now_add=True)
    planned_start_date = models.DateTimeField(null=True, blank=True)
    planned_completion_date = models.DateTimeField(null=True, blank=True)
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Manufacturing and Expiry Dates
    manufacture_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date of manufacture for this batch"
    )
    expiry_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Expiry date for this batch"
    )
    
    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Material Status
    MATERIAL_STATUS_CHOICES = [
        ('pending', 'Pending Dispensing'),
        ('dispensing', 'Dispensing in Progress'),
        ('dispensed', 'Materials Dispensed'),
        ('returned', 'Materials Returned')
    ]
    material_status = models.CharField(
        max_length=20, 
        choices=MATERIAL_STATUS_CHOICES, 
        default='pending'
    )
    
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
    
    # Materials QC Approval
    materials_approved = models.BooleanField(default=False)
    materials_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='materials_approved_bmrs'
    )
    materials_approved_date = models.DateTimeField(null=True, blank=True)
    
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
    
    @property
    def batch_size(self):
        """Get batch size - actual if specified, otherwise standard from product"""
        return self.actual_batch_size or self.product.standard_batch_size
    
    @property
    def batch_size_unit(self):
        """Get batch size unit - actual if specified, otherwise from product"""
        return self.actual_batch_size_unit or self.product.batch_size_unit
    
    def save(self, *args, **kwargs):
        # Check if this is a status change to approved
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = BMR.objects.get(pk=self.pk)
                old_status = old_instance.status
            except BMR.DoesNotExist:
                pass
        
        if not self.bmr_number:
            self.bmr_number = self.generate_unique_bmr_number()
        
        # Save the BMR first
        super().save(*args, **kwargs)
        
        # Create BMR materials from product materials if this is a new BMR with a product
        if is_new and self.product:
            self.create_materials_from_product()
        
        # Initialize workflow when BMR is created or when status changes to approved
        if is_new or (old_status != 'approved' and self.status == 'approved'):
            from workflow.services import WorkflowService
            try:
                WorkflowService.initialize_workflow_for_bmr(self)
                print(f"Workflow initialized for BMR {self.bmr_number}")
                
                # If status is approved, activate the raw material release phase
                if self.status == 'approved':
                    from workflow.models import BatchPhaseExecution
                    raw_material_phase = BatchPhaseExecution.objects.filter(
                        bmr=self,
                        phase__phase_name='raw_material_release'
                    ).first()
                    
                    if raw_material_phase and raw_material_phase.status == 'not_ready':
                        raw_material_phase.status = 'pending'
                        raw_material_phase.save()
                        print(f"Activated raw material release phase for BMR {self.bmr_number}")
                        
            except Exception as e:
                print(f"Error initializing workflow for BMR {self.bmr_number}: {e}")

    def generate_unique_bmr_number(self):
        """Generate a truly unique BMR number for the year, even if BMRs are deleted or created concurrently."""
        from django.db.models import Max
        from datetime import datetime
        year = datetime.now().year
        prefix = f"BMR{year}"
        # Find the max number used so far for this year
        max_bmr = BMR.objects.filter(bmr_number__startswith=prefix).aggregate(Max('bmr_number'))['bmr_number__max']
        if max_bmr:
            # Extract the numeric part and increment
            try:
                last_num = int(max_bmr.replace(prefix, ""))
            except Exception:
                last_num = 0
            next_num = last_num + 1
        else:
            next_num = 1
        # Loop to ensure uniqueness in case of race condition
        while True:
            candidate = f"{prefix}{next_num:04d}"
            if not BMR.objects.filter(bmr_number=candidate).exists():
                return candidate
            next_num += 1

    def create_materials_from_product(self):
        """Create BMR materials from product materials"""
        if not self.product:
            return
            
        from products.models import ProductMaterial
        
        # Get product materials
        product_materials = ProductMaterial.objects.filter(product=self.product)
        if not product_materials.exists():
            return
            
        print(f"Creating {product_materials.count()} BMR materials for BMR {self.bmr_number}")
        
        # Create BMR materials
        for pm in product_materials:
            try:
                material = pm.raw_material
                
                # Skip if this material already exists for this BMR
                if BMRMaterial.objects.filter(bmr=self, material_code=material.material_code).exists():
                    continue
                    
                bmr_material = BMRMaterial.objects.create(
                    bmr=self,
                    material_code=material.material_code,
                    material_name=material.material_name,
                    required_quantity=pm.required_quantity,
                    unit_of_measure=pm.unit_of_measure
                )
                print(f"Created BMR material {bmr_material.id} for {material.material_name}")
            except Exception as e:
                print(f"Error creating BMR material: {str(e)}")

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
    
    def get_suitable_batch(self):
        """Find a suitable raw material batch for this BMR material"""
        try:
            # Import here to avoid circular imports
            from raw_materials.models import RawMaterial, RawMaterialBatch
            
            # Find the raw material by code
            raw_material = RawMaterial.objects.get(material_code=self.material_code)
            
            # Find a suitable batch with enough quantity
            suitable_batch = RawMaterialBatch.objects.filter(
                material=raw_material,
                status='approved',
                quantity_remaining__gte=self.required_quantity
            ).order_by('expiry_date').first()
            
            return suitable_batch
        except Exception as e:
            print(f"Error finding suitable batch for {self.material_name}: {str(e)}")
            return None
    
    def __str__(self):
        return f"{self.bmr.bmr_number} - {self.material_name}"

class RawMaterialRelease(models.Model):
    """Track raw material releases from Store to Dispensing Store"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Release'),
        ('released', 'Released to Dispensing'),
        ('received', 'Received by Dispensing'),
        ('cancelled', 'Cancelled'),
    ]
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='material_releases')
    release_number = models.CharField(max_length=20, unique=True)
    
    # Release details
    release_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Personnel
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='released_materials'
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_materials'
    )
    
    # Dates
    release_started_date = models.DateTimeField(null=True, blank=True)
    release_completed_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
    # Comments
    release_comments = models.TextField(blank=True)
    receiving_comments = models.TextField(blank=True)
    
    def __str__(self):
        return f"Release-{self.release_number} for {self.bmr.batch_number}"
    
    def save(self, *args, **kwargs):
        if not self.release_number:
            self.release_number = self.generate_release_number()
        super().save(*args, **kwargs)
    
    def generate_release_number(self):
        """Generate unique release number"""
        from django.db.models import Max
        from datetime import datetime
        year = datetime.now().year
        prefix = f"REL{year}"
        max_release = RawMaterialRelease.objects.filter(release_number__startswith=prefix).aggregate(Max('release_number'))['release_number__max']
        if max_release:
            try:
                last_num = int(max_release.replace(prefix, ""))
            except Exception:
                last_num = 0
            next_num = last_num + 1
        else:
            next_num = 1
        while True:
            candidate = f"{prefix}{next_num:04d}"
            if not RawMaterialRelease.objects.filter(release_number=candidate).exists():
                return candidate
            next_num += 1
    
    class Meta:
        ordering = ['-release_date']

class RawMaterialReleaseItem(models.Model):
    """Individual material items in a release"""
    
    release = models.ForeignKey(RawMaterialRelease, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(BMRMaterial, on_delete=models.CASCADE)
    
    # Release quantities
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    released_quantity = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Material details at time of release
    batch_lot_number = models.CharField(max_length=50)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status
    is_released = models.BooleanField(default=False)
    release_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.release.release_number} - {self.material.material_name}"

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
