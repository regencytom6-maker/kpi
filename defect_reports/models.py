from django.db import models
from django.conf import settings
from bmr.models import BMR
from django.utils import timezone

class DefectReport(models.Model):
    """
    Model for storing defect reports from operators during production.
    Allows operators to upload images and descriptions of defective products.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_required', 'Action Required'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic information
    title = models.CharField(max_length=100, help_text="Short title describing the defect")
    batch = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='defect_reports')
    reported_date = models.DateTimeField(default=timezone.now)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reported_defects'
    )
    
    # Defect details
    description = models.TextField(help_text="Detailed description of the defect")
    image = models.ImageField(upload_to='defect_reports/%Y/%m/%d/', blank=True, null=True)
    production_phase = models.CharField(max_length=50, help_text="Phase where defect was observed")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    
    # Review information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_defects'
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Notes from the QA review")
    
    # Corrective actions
    corrective_action = models.TextField(blank=True, help_text="Actions taken to address the defect")
    action_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-reported_date']
        verbose_name = "Defect Report"
        verbose_name_plural = "Defect Reports"
        
    def __str__(self):
        return f"Defect: {self.title} - Batch {self.batch.batch_number}"
    
    def save(self, *args, **kwargs):
        # If status changes to reviewed, update the review date
        if self.status == 'reviewed' and not self.reviewed_date:
            self.reviewed_date = timezone.now()
        super().save(*args, **kwargs)
