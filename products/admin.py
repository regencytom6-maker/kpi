from django.contrib import admin
from django import forms
from .models import Product, ProductIngredient, ProductSpecification
from .models_material import ProductMaterial
from raw_materials.models import RawMaterial

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'product_type': forms.Select(attrs={'id': 'id_product_type'}),
            'coating_type': forms.Select(attrs={'id': 'id_coating_type'}),
            'tablet_type': forms.Select(attrs={'id': 'id_tablet_type'}),
            'capsule_type': forms.Select(attrs={'id': 'id_capsule_type'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text
        self.fields['coating_type'].help_text = "Select coating type for tablets only"
        self.fields['tablet_type'].help_text = "Select tablet type for tablets only"
        self.fields['capsule_type'].help_text = "Select capsule type: normal (blister) or bulk"
        
        # Add empty option for product-specific fields
        self.fields['coating_type'].choices = [('', '---------')] + list(self.fields['coating_type'].choices)
        self.fields['tablet_type'].choices = [('', '---------')] + list(self.fields['tablet_type'].choices)
        self.fields['capsule_type'].choices = [('', '---------')] + list(self.fields['capsule_type'].choices)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = [
        'product_name', 'product_type', 'coating_type', 'tablet_type', 'capsule_type',
        'standard_batch_size', 'batch_size_unit', 'packaging_size_in_units', 'is_active'
    ]
    list_filter = ['product_type', 'coating_type', 'tablet_type', 'capsule_type', 'is_active']
    search_fields = ['product_name']
    
    fields = [
        'product_name', 'product_type', 'coating_type', 'tablet_type', 'capsule_type',
        'standard_batch_size', 'batch_size_unit', 'packaging_size_in_units',
        'raw_materials', 'is_active'
    ]
    filter_horizontal = ('raw_materials',)
    
    class Media:
        js = ('admin/js/product_conditional.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form
        
# Create an inline admin for ProductMaterial to use in both Product and RawMaterial admins
class ProductMaterialInline(admin.TabularInline):
    model = ProductMaterial
    extra = 1
    autocomplete_fields = ['raw_material', 'product']
    fields = ('raw_material', 'required_quantity', 'unit_of_measure', 'is_active_ingredient')
    
    class Media:
        js = ('admin/js/product_material_admin.js',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Show all raw materials regardless of whether they're already linked
        # This prevents "Select a valid choice" errors when editing
        if db_field.name == "raw_material":
            kwargs["queryset"] = RawMaterial.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Update the ProductAdmin to include the ProductMaterialInline
ProductAdmin.inlines = [ProductMaterialInline]

@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ('product', 'raw_material', 'required_quantity', 'unit_of_measure', 
                  'is_active_ingredient', 'material_approval_status', 'available_quantity_display', 'quantity_sufficient')
    list_filter = ('is_active_ingredient', 'product', 'raw_material')
    search_fields = ('product__product_name', 'raw_material__material_name', 'raw_material__material_code')
    autocomplete_fields = ['product', 'raw_material']
    
    def material_approval_status(self, obj):
        if obj.is_approved():
            return True
        return False
    material_approval_status.boolean = True
    material_approval_status.short_description = 'QC Approved'
    
    def available_quantity_display(self, obj):
        return obj.available_quantity_with_unit()
    available_quantity_display.short_description = 'Available Quantity'
    
    def quantity_sufficient(self, obj):
        return obj.has_sufficient_quantity()
    quantity_sufficient.boolean = True
    quantity_sufficient.short_description = 'Quantity Sufficient'

@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'ingredient_name', 'ingredient_type', 
        'quantity_per_unit', 'unit_of_measure'
    ]
    list_filter = ['ingredient_type', 'unit_of_measure']
    search_fields = ['ingredient_name', 'product__product_name']

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'parameter_name', 'specification', 'test_method']
    list_filter = ['parameter_name']
    search_fields = ['product__product_name', 'parameter_name']
