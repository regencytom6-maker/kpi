from django.contrib import admin
from .models import DefectReport

@admin.register(DefectReport)
class DefectReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'batch', 'reported_by', 'reported_date', 'severity', 'status')
    list_filter = ('status', 'severity', 'reported_date')
    search_fields = ('title', 'description', 'batch__batch_number')
    date_hierarchy = 'reported_date'
    readonly_fields = ('reported_date',)
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'batch', 'reported_by', 'reported_date', 'production_phase')
        }),
        ('Defect Details', {
            'fields': ('description', 'image', 'severity')
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_date', 'review_notes')
        }),
        ('Corrective Actions', {
            'fields': ('corrective_action', 'action_date')
        }),
    )
