from django.contrib import admin
from .models import ProductionPhase, BatchPhaseExecution

@admin.register(ProductionPhase)
class ProductionPhaseAdmin(admin.ModelAdmin):
    list_display = ['phase_name', 'product_type', 'phase_order', 'is_mandatory', 'requires_approval']
    list_filter = ['product_type', 'is_mandatory', 'requires_approval']
    search_fields = ['phase_name', 'description']
    ordering = ['product_type', 'phase_order']

@admin.register(BatchPhaseExecution)
class BatchPhaseExecutionAdmin(admin.ModelAdmin):
    list_display = ['bmr', 'phase', 'status', 'started_by', 'completed_by', 'started_date', 'completed_date']
    list_filter = ['status', 'phase__product_type', 'phase__phase_name', 'started_date', 'completed_date']
    search_fields = ['bmr__batch_number', 'phase__phase_name', 'operator_comments']
    readonly_fields = ['created_date']
    ordering = ['-started_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bmr', 'phase', 'started_by', 'completed_by')
