from django.contrib import admin
from .models import RawMaterial, RawMaterialBatch, RawMaterialQC, MaterialDispensing, MaterialDispensingItem
from .models_transaction import InventoryTransaction

class RawMaterialBatchInline(admin.TabularInline):
    model = RawMaterialBatch
    extra = 0
    fields = ('batch_number', 'quantity_received', 'quantity_remaining', 'supplier', 'received_date', 'expiry_date', 'status')
    readonly_fields = ('quantity_remaining', 'status')

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('material_code', 'material_name', 'category', 'unit_of_measure', 'current_stock', 'status')
    list_filter = ('category', )
    search_fields = ('material_code', 'material_name', 'description')
    fieldsets = (
        ('Material Information', {
            'fields': ('material_code', 'material_name', 'description', 'category', 'unit_of_measure')
        }),
        ('Inventory Settings', {
            'fields': ('reorder_level', 'default_supplier')
        }),
    )
    inlines = [RawMaterialBatchInline]
    
    def get_inlines(self, request, obj):
        # Import the ProductMaterialInline only when needed to avoid circular imports
        from products.admin import ProductMaterialInline
        return [RawMaterialBatchInline, ProductMaterialInline]


class RawMaterialQCInline(admin.StackedInline):
    model = RawMaterialQC
    can_delete = False
    fields = ('appearance_result', 'identification_result', 'assay_result', 'purity_result', 
              'final_result', 'comments', 'tested_by', 'approved_by')
    

@admin.register(RawMaterialBatch)
class RawMaterialBatchAdmin(admin.ModelAdmin):
    list_display = ('material', 'batch_number', 'quantity_received', 'quantity_remaining', 'expiry_date', 'status')
    list_filter = ('status', 'received_date', 'expiry_date')
    search_fields = ('batch_number', 'material__material_name', 'material__material_code')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Batch Information', {
            'fields': ('material', 'batch_number', 'supplier', 'received_date', 'expiry_date')
        }),
        ('Quantities', {
            'fields': ('quantity_received', 'quantity_remaining')
        }),
        ('Status', {
            'fields': ('status', 'received_by')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [RawMaterialQCInline]


@admin.register(RawMaterialQC)
class RawMaterialQCAdmin(admin.ModelAdmin):
    list_display = ('material_batch', 'test_date', 'final_result', 'tested_by')
    list_filter = ('final_result', 'test_date')
    search_fields = ('material_batch__batch_number', 'material_batch__material__material_name')
    readonly_fields = ('test_date',)
    fieldsets = (
        ('Batch Information', {
            'fields': ('material_batch', 'test_date')
        }),
        ('QC Results', {
            'fields': ('appearance_result', 'identification_result', 'assay_result', 'purity_result', 
                       'final_result', 'comments')
        }),
        ('Personnel', {
            'fields': ('tested_by', 'approved_by')
        }),
    )


class MaterialDispensingItemInline(admin.TabularInline):
    model = MaterialDispensingItem
    extra = 0
    fields = ('bmr_material', 'material_batch', 'required_quantity', 'dispensed_quantity', 'is_dispensed', 'dispensed_date')
    readonly_fields = ('dispensed_date',)


@admin.register(MaterialDispensing)
class MaterialDispensingAdmin(admin.ModelAdmin):
    list_display = ('dispensing_reference', 'bmr', 'status', 'requested_date', 'completed_date')
    list_filter = ('status', 'requested_date')
    search_fields = ('dispensing_reference', 'bmr__batch_number', 'bmr__bmr_number')
    readonly_fields = ('dispensing_reference', 'requested_date', 'started_date', 'completed_date')
    fieldsets = (
        ('Dispensing Information', {
            'fields': ('bmr', 'dispensing_reference', 'status', 'dispensing_notes')
        }),
        ('Personnel', {
            'fields': ('dispensed_by',)
        }),
        ('Dates', {
            'fields': ('requested_date', 'started_date', 'completed_date')
        }),
    )
    inlines = [MaterialDispensingItemInline]


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('material_batch', 'transaction_type', 'quantity', 'transaction_date', 'user')
    list_filter = ('transaction_type', 'transaction_date', 'user')
    search_fields = ('material_batch__batch_number', 'material_batch__material__material_name', 'notes')
    readonly_fields = ('transaction_date',)
    fieldsets = (
        ('Transaction Details', {
            'fields': ('material_batch', 'transaction_type', 'quantity', 'transaction_date', 'user')
        }),
        ('Reference', {
            'fields': ('reference_bmr', 'notes')
        }),
    )
