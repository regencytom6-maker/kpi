from django.db import models
from django.core.exceptions import ValidationError
# Import the new product material model
from products.models_material import ProductMaterial

class Product(models.Model):
    # Add back the raw_materials ManyToMany field
    raw_materials = models.ManyToManyField('raw_materials.RawMaterial', blank=True, related_name='products')
    
    """Product master data for pharmaceutical products"""
    
    def clean(self):
        # Only allow tablet_type for tablets, capsule_type for capsules
        if self.product_type == 'tablet' and self.capsule_type:
            raise ValidationError({'capsule_type': 'Tablet products cannot have a capsule type.'})
        if self.product_type == 'capsule' and self.tablet_type:
            raise ValidationError({'tablet_type': 'Capsule products cannot have a tablet type.'})
        # Optionally clear irrelevant fields
        if self.product_type != 'tablet':
            self.tablet_type = ''
        if self.product_type != 'capsule':
            self.capsule_type = ''
    """Product master data for pharmaceutical products"""
    
    PRODUCT_TYPE_CHOICES = [
        ('ointment', 'Ointment'),
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
    ]
    
    COATING_CHOICES = [
        ('uncoated', 'Uncoated'),
        ('coated', 'Coated'),
    ]
    
    TABLET_TYPE_CHOICES = [
        ('normal', 'Normal Tablet'),
        ('tablet_2', 'Tablet Type 2'),
    ]
    
    CAPSULE_TYPE_CHOICES = [
        ('normal', 'Normal Capsule (Blister)'),
        ('bulk', 'Bulk Capsule'),
    ]
    
    # Essential fields only
    product_name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    
    # Tablet specific fields (only show when product_type is 'tablet')
    coating_type = models.CharField(
        max_length=20,
        choices=COATING_CHOICES,
        blank=True,
        help_text="Only applicable for tablets - whether the tablet is coated or not"
    )
    tablet_type = models.CharField(
        max_length=20, 
        choices=TABLET_TYPE_CHOICES,
        blank=True,
        help_text="Only applicable for tablets - normal or tablet type 2"
    )
    
    # Capsule specific fields
    capsule_type = models.CharField(
        max_length=20, 
        choices=CAPSULE_TYPE_CHOICES,
        blank=True,
        default='normal',
        help_text="Only applicable for capsules - normal (blister) or bulk"
    )
    
    # Batch size configuration - moved from BMR to Product
    standard_batch_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=1000,  # Default batch size
        help_text="Standard batch size for this product"
    )
    batch_size_unit = models.CharField(
        max_length=20,
        default='units',
        help_text="Unit of measurement for batch size (automatically set based on product type)"
    )
    
    # New packaging size field
    packaging_size_in_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Size of individual packaging unit (e.g., tablets per blister, capsules per bottle, ml per tube)"
    )
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_coated(self):
        """Backward compatibility property"""
        return self.coating_type == 'coated'
    
    def __str__(self):
        if self.product_type == 'tablet':
            coating_status = self.get_coating_type_display() if self.coating_type else "Uncoated"
            tablet_display = self.get_tablet_type_display() if self.tablet_type else "Normal"
            return f"{self.product_name} ({tablet_display}, {coating_status})"
        return f"{self.product_name} ({self.get_product_type_display()})"
    
    def save(self, *args, **kwargs):
        # Always run clean() before saving
        self.clean()
        
        # Clear product-specific fields if they don't match the product type
        if self.product_type != 'tablet':
            self.coating_type = ''
            self.tablet_type = ''
            
        if self.product_type != 'capsule':
            self.capsule_type = ''
        
        # Set batch_size_unit based on product type
        if self.product_type == 'tablet':
            self.batch_size_unit = 'tablets'
        elif self.product_type == 'capsule':
            self.batch_size_unit = 'capsules'
        elif self.product_type == 'ointment':
            self.batch_size_unit = 'tubes'
        else:
            self.batch_size_unit = 'units'  # Default fallback
            
        super().save(*args, **kwargs)
        
        # After save, sync raw_materials if it's a real save (not a fixture load)
        # We check for a primary key to ensure it's an actual DB object
        if self.pk is not None:
            try:
                # Sync raw materials to ensure ProductMaterial entries exist
                self.sync_raw_materials()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in sync_raw_materials for product {self.product_name}: {str(e)}")
    
    class Meta:
        ordering = ['product_name']
    
    def sync_raw_materials(self):
        """
        Synchronize between raw_materials M2M relationship and ProductMaterial model
        This ensures both systems work correctly
        """
        from raw_materials.models import RawMaterial
        from decimal import Decimal
        
        # Add any raw_materials to ProductMaterial if they don't exist
        for material in self.raw_materials.all():
            try:
                # Get the unit of measure with fallback
                unit = getattr(material, 'unit_of_measure', 'units')
                
                # Use Decimal directly to avoid conversion issues
                required_qty = Decimal('1.0')
                
                ProductMaterial.objects.get_or_create(
                    product=self,
                    raw_material=material,
                    defaults={
                        'required_quantity': required_qty,
                        'unit_of_measure': unit,
                        'is_active_ingredient': material.category == 'active'
                    }
                )
            except Exception as e:
                # Log the error but continue processing other materials
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error synchronizing material {material.material_name} for product {self.product_name}: {str(e)}")
        
        # Add any ProductMaterials to raw_materials if they don't exist
        for product_material in self.product_materials.all():
            self.raw_materials.add(product_material.raw_material)

class ProductIngredient(models.Model):
    """Active and inactive ingredients for each product"""
    
    INGREDIENT_TYPE_CHOICES = [
        ('active', 'Active Ingredient'),
        ('inactive', 'Inactive Ingredient'),
        ('excipient', 'Excipient'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ingredients')
    ingredient_name = models.CharField(max_length=200)
    ingredient_type = models.CharField(max_length=20, choices=INGREDIENT_TYPE_CHOICES)
    quantity_per_unit = models.DecimalField(max_digits=10, decimal_places=4)
    unit_of_measure = models.CharField(max_length=20)  # mg, g, ml, %
    supplier = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.product.product_name} - {self.ingredient_name}"

class ProductSpecification(models.Model):
    """Product specifications and quality parameters"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    parameter_name = models.CharField(max_length=100)
    specification = models.CharField(max_length=200)
    test_method = models.CharField(max_length=200)
    acceptance_criteria = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.product.product_name} - {self.parameter_name}"
