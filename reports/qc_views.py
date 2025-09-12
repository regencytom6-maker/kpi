from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import xlwt
from raw_materials.models import RawMaterial, RawMaterialQC

@login_required
def qc_test_report_view(request):
    """Generate a report of QC tests with filtering options"""
    # Get filter parameters
    material_id = request.GET.get('material', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    # Base query
    qc_tests = RawMaterialQC.objects.all().select_related(
        'material_batch', 
        'material_batch__material', 
        'tested_by'
    ).order_by('-test_date')
    
    # Apply filters
    if material_id:
        qc_tests = qc_tests.filter(material_batch__material_id=material_id)
        selected_material_name = RawMaterial.objects.get(pk=material_id).material_name
    else:
        selected_material_name = None
        
    if status:
        qc_tests = qc_tests.filter(status=status)
        
    if from_date:
        from_date_obj = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
        qc_tests = qc_tests.filter(test_date__gte=from_date_obj)
    
    if to_date:
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
        # Include the entire day
        to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)
        to_date_obj = timezone.make_aware(to_date_obj)
        qc_tests = qc_tests.filter(test_date__lte=to_date_obj)
    
    # Get all materials for filter dropdown
    materials = RawMaterial.objects.all().order_by('material_name')
    
    # Calculate stats
    stats = {
        'total': qc_tests.count(),
        'approved': qc_tests.filter(status='approved').count(),
        'rejected': qc_tests.filter(status='rejected').count(),
        'pending': qc_tests.filter(Q(status='pending') | Q(status='in_progress')).count(),
    }
    
    context = {
        'qc_tests': qc_tests,
        'materials': materials,
        'selected_material': material_id,
        'selected_material_name': selected_material_name,
        'selected_status': status,
        'from_date': from_date,
        'to_date': to_date,
        'stats': stats,
        'today': timezone.now(),
    }
    
    return render(request, 'reports/qc_test_report.html', context)

@login_required
def export_qc_tests_csv(request):
    """Export QC test data as CSV"""
    # Get same filter parameters as the report view
    material_id = request.GET.get('material', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    # Base query
    qc_tests = RawMaterialQC.objects.all().select_related(
        'material_batch', 
        'material_batch__material', 
        'tested_by'
    ).order_by('-test_date')
    
    # Apply filters
    if material_id:
        qc_tests = qc_tests.filter(material_batch__material_id=material_id)
        
    if status:
        qc_tests = qc_tests.filter(status=status)
        
    if from_date:
        from_date_obj = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
        qc_tests = qc_tests.filter(test_date__gte=from_date_obj)
    
    if to_date:
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
        to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)
        to_date_obj = timezone.make_aware(to_date_obj)
        qc_tests = qc_tests.filter(test_date__lte=to_date_obj)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="qc_tests_report.csv"'
    
    writer = csv.writer(response)
    # Write header
    writer.writerow([
        'Material', 'Batch Number', 'Test Date', 
        'Appearance', 'Identification', 'Assay', 'Purity',
        'Final Result', 'Status', 'Tested By', 'Comments'
    ])
    
    # Write data
    for test in qc_tests:
        writer.writerow([
            test.material_batch.material.material_name,
            test.material_batch.batch_number,
            test.test_date.strftime('%Y-%m-%d %H:%M'),
            test.get_appearance_result_display(),
            test.get_identification_result_display(),
            test.get_assay_result_display() if test.assay_result else 'N/A',
            test.get_purity_result_display() if test.purity_result else 'N/A',
            test.get_final_result_display(),
            test.get_status_display(),
            test.tested_by.get_full_name() if test.tested_by else 'N/A',
            test.comments or ''
        ])
    
    return response

@login_required
def export_qc_tests_excel(request):
    """Export QC test data as Excel file"""
    # Get same filter parameters as the report view
    material_id = request.GET.get('material', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    # Base query
    qc_tests = RawMaterialQC.objects.all().select_related(
        'material_batch', 
        'material_batch__material', 
        'tested_by'
    ).order_by('-test_date')
    
    # Apply filters
    if material_id:
        qc_tests = qc_tests.filter(material_batch__material_id=material_id)
        material_name = RawMaterial.objects.get(pk=material_id).material_name
        filename = f"qc_tests_{material_name.replace(' ', '_')}.xls"
    else:
        filename = "qc_tests_report.xls"
        
    if status:
        qc_tests = qc_tests.filter(status=status)
        
    if from_date:
        from_date_obj = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
        qc_tests = qc_tests.filter(test_date__gte=from_date_obj)
    
    if to_date:
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
        to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)
        to_date_obj = timezone.make_aware(to_date_obj)
        qc_tests = qc_tests.filter(test_date__lte=to_date_obj)
    
    # Create Excel workbook
    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet('QC Tests')
    
    # Style for headers
    header_style = xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour gray25;')
    date_style = xlwt.easyxf('font: bold off; align: horiz left;', num_format_str='YYYY-MM-DD HH:MM')
    
    # Write header
    headers = [
        'Material', 'Batch Number', 'Test Date', 
        'Appearance', 'Identification', 'Assay', 'Purity',
        'Final Result', 'Status', 'Tested By', 'Comments'
    ]
    
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_style)
        # Set column width
        worksheet.col(col_num).width = 256 * 20  # 20 characters wide
    
    # Write data
    for row_num, test in enumerate(qc_tests, 1):
        worksheet.write(row_num, 0, test.material_batch.material.material_name)
        worksheet.write(row_num, 1, test.material_batch.batch_number)
        # Convert test_date to a string to avoid timezone issues
        worksheet.write(row_num, 2, test.test_date.strftime('%Y-%m-%d %H:%M'))
        worksheet.write(row_num, 3, test.get_appearance_result_display())
        worksheet.write(row_num, 4, test.get_identification_result_display())
        worksheet.write(row_num, 5, test.get_assay_result_display() if test.assay_result else 'N/A')
        worksheet.write(row_num, 6, test.get_purity_result_display() if test.purity_result else 'N/A')
        worksheet.write(row_num, 7, test.get_final_result_display())
        worksheet.write(row_num, 8, test.get_status_display())
        worksheet.write(row_num, 9, test.tested_by.get_full_name() if test.tested_by else 'N/A')
        worksheet.write(row_num, 10, test.comments or '')
    
    # Create response
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    
    return response
