from django import forms
from .models import BMR, BMRMaterial
from products.models import Product

class BMRCreateForm(forms.ModelForm):
    """Form for QA to create BMR - batch size comes from product definition"""
    
    class Meta:
        model = BMR
        fields = [
            'product', 'batch_number'
        ]
        widgets = {
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control batch-number',
                'placeholder': 'Enter batch number (e.g., 0012025)',
                'pattern': r'\d{7}',
                'title': 'Enter 7 digits: XXX (batch) + YYYY (year)'
            }),
            'product': forms.Select(attrs={'class': 'form-control'}),
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
