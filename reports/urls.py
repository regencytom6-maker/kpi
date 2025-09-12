from django.urls import path
from . import views
from . import timeline_views
from . import qc_views

app_name = 'reports'

urlpatterns = [
    path('timeline/', timeline_views.timeline_list_view, name='timeline_list'),
    path('comments/', views.comments_report_view, name='comments_report'),
    path('comments/export/csv/', views.export_comments_csv, name='export_comments_csv'),
    path('comments/export/word/', views.export_comments_word, name='export_comments_word'),
    path('comments/export/excel/', views.export_comments_excel, name='export_comments_excel'),
    path('comments/bmr/<int:bmr_id>/', views.bmr_comments_detail, name='bmr_comments_detail'),
    path('enhanced-timeline/<int:bmr_id>/', timeline_views.enhanced_timeline_view, name='enhanced_timeline'),
    
    # QC Test Reports
    path('qc-tests/', qc_views.qc_test_report_view, name='qc_test_report'),
    path('qc-tests/export/csv/', qc_views.export_qc_tests_csv, name='export_qc_tests_csv'),
    path('qc-tests/export/excel/', qc_views.export_qc_tests_excel, name='export_qc_tests_excel'),
]
