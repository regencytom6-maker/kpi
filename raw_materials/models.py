from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import the transaction model
from raw_materials.models_transaction import InventoryTransaction

class RawMaterial(models.Model):
    """Raw material base information"""
    MATERIAL_CATEGORIES = [
        ('active', 'Active Pharmaceutical Ingredient'),
        ('excipient', 'Excipient'),
        ('packaging', 'Packaging Material'),
        ('other', 'Other')
    ]
    
    material_code = models.CharField(max_length=50, unique=True)
    material_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=MATERIAL_CATEGORIES)
    unit_of_measure = models.CharField(max_length=20)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Supplier information
    default_supplier = models.CharField(max_length=200, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.material_name} ({self.material_code})"
    
    @property
    def current_stock(self):
        """Get current available stock"""
        total_received = self.inventory_batches.filter(
            status='approved'
        ).aggregate(
            models.Sum('quantity_remaining')
        )['quantity_remaining__sum'] or 0
        
        return total_received
    
    @property
    def pending_qc_batches(self):
        """Get number of batches pending QC"""
        return self.inventory_batches.filter(status='pending_qc').count()
    
    @property
    def status(self):
        """Get stock status"""
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.reorder_level:
            return 'low_stock'
        else:
            return 'in_stock'


class RawMaterialBatch(models.Model):
    """Specific batch of raw material received"""
    STATUS_CHOICES = [
        ('pending_qc', 'Pending QC'),
        ('approved', 'QC Approved'),
        ('rejected', 'QC Rejected'),
        ('expired', 'Expired'),
        ('depleted', 'Depleted')
    ]
    
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='inventory_batches')
    batch_number = models.CharField(max_length=50)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=4)
    quantity_remaining = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Batch details
    supplier = models.CharField(max_length=200)
    received_date = models.DateField()
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    
    # Status and QC
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_qc')
    
    # QC approval/rejection tracking
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_raw_materials',
        blank=True
    )
    rejection_date = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rejected_raw_materials',
        blank=True
    )
    
    # Tracking
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_raw_materials'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.material.material_name} - {self.batch_number}"
    
    def save(self, *args, **kwargs):
        # Import utility for safe decimal conversion
        from .utils import safe_decimal_conversion
        from decimal import Decimal
        
        # Ensure quantity values are proper Decimal objects
        self.quantity_received = safe_decimal_conversion(self.quantity_received)
        self.quantity_remaining = safe_decimal_conversion(self.quantity_remaining)
        
        # Track if this is a new record or changes to quantity
        is_new = not self.pk
        quantity_changed = False
        old_quantity = Decimal('0')
        
        if not is_new:
            try:
                old_instance = RawMaterialBatch.objects.get(pk=self.pk)
                old_quantity = safe_decimal_conversion(old_instance.quantity_remaining)
                quantity_changed = old_quantity != self.quantity_remaining
            except RawMaterialBatch.DoesNotExist:
                pass
        
        # First save
        if is_new:
            self.quantity_remaining = self.quantity_received
        
        # Check for expired status
        if self.expiry_date < timezone.now().date():
            self.status = 'expired'
        
        # Check for depleted status
        if self.quantity_remaining <= Decimal('0'):
            self.status = 'depleted'
            
        super().save(*args, **kwargs)
        
        # Create transaction records
        if is_new:
            # Record the initial receipt
            InventoryTransaction.objects.create(
                material_batch=self,
                transaction_type='received',
                quantity=self.quantity_received,
                user=self.received_by,
                notes=f"Initial receipt of material batch {self.batch_number}"
            )
        elif quantity_changed and self.quantity_remaining < old_quantity:
            # Record a dispensing transaction when quantity is reduced
            from .utils import safe_decimal_conversion
            
            # Use safe conversion to ensure valid decimals
            difference = safe_decimal_conversion(old_quantity) - safe_decimal_conversion(self.quantity_remaining)
            
            InventoryTransaction.objects.create(
                material_batch=self,
                transaction_type='dispensed',
                quantity=difference,
                user=None,  # Will be updated by the specific operation
                notes=f"Quantity reduced from {old_quantity} to {self.quantity_remaining}"
            )


class RawMaterialQC(models.Model):
    """Quality Control testing for raw materials"""
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    material_batch = models.OneToOneField(RawMaterialBatch, on_delete=models.CASCADE, related_name='qc_test')
    test_date = models.DateTimeField(auto_now_add=True)
    
    # QC Parameters
    appearance_result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    identification_result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    assay_result = models.CharField(max_length=10, choices=RESULT_CHOICES, blank=True, null=True)
    purity_result = models.CharField(max_length=10, choices=RESULT_CHOICES, blank=True, null=True)
    ph_value = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, help_text='pH value measurement')
    loss_on_drying = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='Percentage loss on drying test')
    
    # Overall result
    final_result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    comments = models.TextField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='started_raw_material_qc',
        blank=True
    )
    started_date = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='completed_raw_material_qc',
        blank=True
    )
    completed_date = models.DateTimeField(null=True, blank=True)
    test_notes = models.TextField(blank=True)
    
    # Personnel
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='raw_material_qc_tests'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_raw_material_qc'
    )
    
    def save(self, *args, **kwargs):
        # Track if this is a status change
        is_new = not self.pk
        status_changed = False
        
        if not is_new:
            try:
                old_instance = RawMaterialQC.objects.get(pk=self.pk)
                status_changed = old_instance.status != self.status or old_instance.final_result != self.final_result
            except RawMaterialQC.DoesNotExist:
                pass
        
        # Ensure status and result are consistent
        if self.final_result == 'pass' and self.status != 'approved':
            self.status = 'approved'
        elif self.final_result == 'fail' and self.status != 'rejected':
            self.status = 'rejected'
        
        # Update batch status based on QC result
        if self.status == 'approved' and self.final_result == 'pass':
            self.material_batch.status = 'approved'
        elif self.status == 'rejected' or self.final_result == 'fail':
            self.material_batch.status = 'rejected'
        
        # Update the batch status
        self.material_batch.save()
        
        # Log the QC action
        import logging
        logger = logging.getLogger(__name__)
        if is_new:
            logger.info(f"New QC test created for {self.material_batch.material.material_name} batch {self.material_batch.batch_number} with status {self.status}")
        elif status_changed:
            logger.info(f"QC test updated for {self.material_batch.material.material_name} batch {self.material_batch.batch_number}: Status changed to {self.status}")
        
        super().save(*args, **kwargs)


class MaterialDispensing(models.Model):
    """Track material dispensing for BMRs"""
    STATUS_CHOICES = [
        ('pending', 'Pending Dispensing'),
        ('in_progress', 'Dispensing In Progress'),
        ('completed', 'Dispensing Complete'),
        ('cancelled', 'Dispensing Cancelled')
    ]
    
    bmr = models.OneToOneField('bmr.BMR', on_delete=models.CASCADE, related_name='material_dispensing')
    dispensing_reference = models.CharField(max_length=20, unique=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Personnel
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispensed_materials'
    )
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    started_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Comments
    dispensing_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Dispensing {self.dispensing_reference} for {self.bmr.batch_number}"
    
    def generate_dispensing_reference(self):
        """Generate unique dispensing reference"""
        from django.db.models import Max
        from datetime import datetime
        year = datetime.now().year
        prefix = f"DISP{year}"
        max_ref = MaterialDispensing.objects.filter(
            dispensing_reference__startswith=prefix
        ).aggregate(Max('dispensing_reference'))['dispensing_reference__max']
        
        if max_ref:
            try:
                last_num = int(max_ref.replace(prefix, ""))
            except Exception:
                last_num = 0
            next_num = last_num + 1
        else:
            next_num = 1
            
        while True:
            candidate = f"{prefix}{next_num:04d}"
            if not MaterialDispensing.objects.filter(dispensing_reference=candidate).exists():
                return candidate
            next_num += 1
    
    def process_dispensing_completion(self):
        """Process the completion of dispensing by updating inventory quantities"""
        from decimal import Decimal
        from django.db import transaction
        
        print(f"DEBUG: Starting process_dispensing_completion for dispensing {self.dispensing_reference}")
        
        with transaction.atomic():
            # Get all dispensing items
            dispensing_items = self.items.all()
            print(f"DEBUG: Found {dispensing_items.count()} dispensing items")
            
            for item in dispensing_items:
                print(f"DEBUG: Processing item for material {item.bmr_material}, is_dispensed={item.is_dispensed}")
                if not item.is_dispensed:
                    # Mark the item as dispensed
                    item.is_dispensed = True
                    item.dispensed_date = timezone.now()
                    
                    # Get the material batch
                    batch = item.material_batch
                    print(f"DEBUG: Material batch {batch.batch_number}, current quantity: {batch.quantity_remaining}")
                    
                    # Calculate the quantity to subtract
                    quantity_to_subtract = Decimal(str(item.dispensed_quantity))
                    print(f"DEBUG: Quantity to subtract: {quantity_to_subtract}")
                    
                    # Update the batch quantity
                    if batch.quantity_remaining >= quantity_to_subtract:
                        old_quantity = batch.quantity_remaining
                        batch.quantity_remaining -= quantity_to_subtract
                        print(f"DEBUG: Updating batch quantity from {old_quantity} to {batch.quantity_remaining}")
                        batch.save()
                        print(f"DEBUG: Batch saved with new quantity")
                        
                        # Create inventory transaction record
                        try:
                            transaction_record = InventoryTransaction.objects.create(
                                material=batch.material,
                                material_batch=batch,
                                transaction_type='dispensed',
                                quantity=quantity_to_subtract,
                                reference_number=self.dispensing_reference,
                                performed_by=self.dispensed_by,
                                notes=f"Dispensed for BMR {self.bmr.bmr_number}"
                            )
                            print(f"DEBUG: Created inventory transaction {transaction_record.id}")
                        except Exception as e:
                            print(f"DEBUG ERROR: Failed to create transaction record: {str(e)}")
                        
                        # Save the dispensing item
                        item.save()
                        print(f"DEBUG: Dispensing item saved with is_dispensed=True")
                    else:
                        error_msg = f"Insufficient quantity in batch {batch.batch_number}"
                        print(f"DEBUG ERROR: {error_msg}")
                        raise ValidationError(error_msg)
                else:
                    print(f"DEBUG: Skipping already dispensed item")
            
            # Update BMR status to indicate materials are dispensed
            self.bmr.material_status = 'dispensed'
            self.bmr.save()
            print(f"DEBUG: Updated BMR {self.bmr.bmr_number} status to dispensed")

    def save(self, *args, **kwargs):
        print(f"DEBUG: Saving MaterialDispensing {self.pk}, status={self.status}")
        
        if not self.dispensing_reference:
            self.dispensing_reference = self.generate_dispensing_reference()
            print(f"DEBUG: Generated new dispensing reference: {self.dispensing_reference}")
            
        # Update dates based on status changes
        if self.status == 'in_progress' and not self.started_date:
            self.started_date = timezone.now()
            print(f"DEBUG: Set started_date to {self.started_date}")
        elif self.status == 'completed' and not self.completed_date:
            self.completed_date = timezone.now()
            # Process the dispensing completion after saving
            self._complete_dispensing = True
            print(f"DEBUG: Set completed_date to {self.completed_date} and _complete_dispensing=True")
            
        # Check if _complete_dispensing is already set (e.g. from view)
        if hasattr(self, '_complete_dispensing'):
            print(f"DEBUG: _complete_dispensing was already set to {self._complete_dispensing}")
            
        super().save(*args, **kwargs)
        print(f"DEBUG: MaterialDispensing saved with ID {self.pk}")
        
        # Handle dispensing completion
        if hasattr(self, '_complete_dispensing') and self._complete_dispensing:
            print(f"DEBUG: Calling process_dispensing_completion")
            self.process_dispensing_completion()
        else:
            print(f"DEBUG: NOT calling process_dispensing_completion because _complete_dispensing flag not set")


class MaterialDispensingItem(models.Model):
    """Individual material items dispensed"""
    dispensing = models.ForeignKey(MaterialDispensing, on_delete=models.CASCADE, related_name='items')
    bmr_material = models.ForeignKey('bmr.BMRMaterial', on_delete=models.CASCADE, related_name='dispensing_items')
    
    # Material batch allocation
    material_batch = models.ForeignKey(
        RawMaterialBatch, 
        on_delete=models.PROTECT,
        related_name='dispensing_usages'
    )
    
    # Quantities
    required_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    dispensed_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Status
    is_dispensed = models.BooleanField(default=False)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # First save
        is_new = not self.pk
        print(f"DEBUG: Saving MaterialDispensingItem, is_new={is_new}, is_dispensed={self.is_dispensed}")
        
        # Ensure quantities are Decimal objects
        from decimal import Decimal
        from raw_materials.utils import safe_decimal_conversion
        
        try:
            self.required_quantity = safe_decimal_conversion(self.required_quantity)
            self.dispensed_quantity = safe_decimal_conversion(self.dispensed_quantity)
            print(f"DEBUG: Converted quantities - required: {self.required_quantity}, dispensed: {self.dispensed_quantity}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error converting quantities to Decimal: {str(e)}")
            print(f"DEBUG ERROR: Failed to convert quantities: {str(e)}")
            # Use default values if conversion fails
            self.required_quantity = Decimal('0.0') 
            self.dispensed_quantity = Decimal('0.0')
        
        super().save(*args, **kwargs)
        print(f"DEBUG: MaterialDispensingItem saved with ID {self.pk}")
        
        # NOTE: We are NOT updating quantities here as it will be handled by process_dispensing_completion
        # Instead, just update BMR material references
        if self.is_dispensed:
            print(f"DEBUG: Updating BMR material references for dispensed item")
            # Update BMR material
            self.bmr_material.dispensed_quantity = self.dispensed_quantity
            self.bmr_material.dispensed_by = self.dispensing.dispensed_by
            self.bmr_material.dispensed_date = timezone.now()
            self.bmr_material.is_dispensed = True
            self.bmr_material.batch_lot_number = self.material_batch.batch_number
            self.bmr_material.supplier = self.material_batch.supplier
            self.bmr_material.expiry_date = self.material_batch.expiry_date
            self.bmr_material.save()
            print(f"DEBUG: BMR material updated")
