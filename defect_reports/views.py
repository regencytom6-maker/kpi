from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import DefectReport
from .forms import DefectReportForm, DefectReviewForm
from bmr.models import BMR

@login_required
def report_defect(request):
    """View for operators to submit defect reports"""
    
    # Only show active batches for the dropdown
    active_batches = BMR.objects.filter(
        Q(status='in_production') | Q(status='completed')
    )
    
    if request.method == 'POST':
        form = DefectReportForm(request.POST, request.FILES)
        if form.is_valid():
            defect_report = form.save(commit=False)
            defect_report.reported_by = request.user
            defect_report.save()
            messages.success(request, "Defect report submitted successfully!")
            return redirect('defect_list')
    else:
        form = DefectReportForm()
    
    # Customize the batch queryset to only show active batches
    form.fields['batch'].queryset = active_batches
    
    context = {
        'form': form,
        'title': 'Report Quality Defect'
    }
    return render(request, 'defect_reports/report_form.html', context)

@login_required
def defect_list(request):
    """View to list all defect reports"""
    
    # Determine if user is QA staff (has permission to review)
    is_qa = request.user.groups.filter(name__in=['qa', 'qc']).exists()
    
    if is_qa:
        # QA staff see all reports
        defects = DefectReport.objects.all()
    else:
        # Operators only see their own reports
        defects = DefectReport.objects.filter(reported_by=request.user)
        
    context = {
        'defects': defects,
        'is_qa': is_qa,
        'title': 'Quality Defect Reports'
    }
    return render(request, 'defect_reports/defect_list.html', context)

@login_required
def defect_detail(request, pk):
    """View defect report details"""
    
    defect = get_object_or_404(DefectReport, pk=pk)
    is_qa = request.user.groups.filter(name__in=['qa', 'qc']).exists()
    
    # Only creator or QA staff can view details
    if defect.reported_by != request.user and not is_qa:
        messages.error(request, "You don't have permission to view this report.")
        return redirect('defect_list')
        
    # Handle review form submission for QA staff
    if is_qa and request.method == 'POST':
        review_form = DefectReviewForm(request.POST, instance=defect)
        if review_form.is_valid():
            updated_defect = review_form.save(commit=False)
            updated_defect.reviewed_by = request.user
            updated_defect.reviewed_date = timezone.now()
            
            # Set action date if status changes to resolved
            if updated_defect.status == 'resolved' and not updated_defect.action_date:
                updated_defect.action_date = timezone.now()
                
            updated_defect.save()
            messages.success(request, "Defect report reviewed successfully!")
    else:
        review_form = DefectReviewForm(instance=defect)
        
    context = {
        'defect': defect,
        'review_form': review_form if is_qa else None,
        'is_qa': is_qa,
        'title': f"Defect: {defect.title}"
    }
    return render(request, 'defect_reports/defect_detail.html', context)
