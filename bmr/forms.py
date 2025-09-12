from django import forms
from django.db import models
from .models import BMR, BMRMaterial
from products.models import Product

class BMRCreateForm(forms.ModelForm):
    """Form for QA to create BMR - batch size comes from product definition"""
    
    class Meta:
        model = BMR
        fields = [
            'product', 'batch_number', 'manufacture_date', 'expiry_date'
        ]
        widgets = {
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control batch-number',
                'placeholder': 'Enter batch number (e.g., 0012025)',
                'pattern': r'\d{7}',
                'title': 'Enter 7 digits: XXX (batch) + YYYY (year)'
            }),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'manufacture_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': 'required'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': 'required'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active products that have batch size configured
        self.fields['product'].queryset = Product.objects.filter(
            is_active=True,
            standard_batch_size__isnull=False
        )
        
        # Customize product field to show only product names
        self.fields['product'].empty_label = "Select a product..."
        choices = [('', 'Select a product...')]
        for product in self.fields['product'].queryset:
            choices.append((product.pk, product.product_name))
        self.fields['product'].choices = choices
        
        # Add help text
        self.fields['batch_number'].help_text = (
            "Enter batch number manually in format XXXYYYY (e.g., 0012025 for 1st batch of 2025)"
        )
        self.fields['product'].help_text = (
            "Select product - batch size will be automatically set from product configuration"
        )
    
    def clean_batch_number(self):
        """Validate batch number format"""
        batch_number = self.cleaned_data.get('batch_number')
        if batch_number:
            import re
            if not re.match(r'^\d{7}$', batch_number):
                raise forms.ValidationError(
                    "Batch number must be exactly 7 digits in format XXXYYYY (e.g., 0012025)"
                )
            
            # Check if batch number already exists
            if BMR.objects.filter(batch_number=batch_number).exists():
                raise forms.ValidationError(
                    f"Batch number {batch_number} already exists. Please use a different number."
                )
        
        return batch_number
        
    def clean(self):
        """Validate that the product has raw materials with sufficient quantities"""
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        
        if product:
            # Check if product has raw materials
            from products.models import ProductMaterial
            product_materials = ProductMaterial.objects.filter(product=product)
            
            if not product_materials.exists():
                self.add_error('product', 
                    f"The selected product '{product.product_name}' has no raw materials associated with it. "
                    f"Please add raw materials to this product before creating a BMR."
                )
                return cleaned_data
            
            # Check if sufficient quantities of raw materials are available
            from raw_materials.models import RawMaterialBatch
            
            insufficient_materials = []
            for pm in product_materials:
                material = pm.raw_material
                required_qty = pm.required_quantity
                
                # Get total available quantity from approved batches
                available_qty = RawMaterialBatch.objects.filter(
                    material=material,
                    status='approved'
                ).aggregate(total=models.Sum('quantity_remaining'))['total'] or 0
                
                if available_qty < required_qty:
                    insufficient_materials.append({
                        'name': material.material_name,
                        'required': required_qty,
                        'available': available_qty,
                        'unit': material.unit_of_measure
                    })
            
            if insufficient_materials:
                error_msg = "Insufficient quantities of the following raw materials:\n"
                for material in insufficient_materials:
                    error_msg += f"- {material['name']}: Required {material['required']} {material['unit']}, Available {material['available']} {material['unit']}\n"
                self.add_error('product', error_msg)
        
        return cleaned_data
