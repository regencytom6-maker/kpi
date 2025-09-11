from django.urls import path
from . import views
from . import api_views
from . import debug_views
from . import views_ajax

app_name = 'raw_materials'

urlpatterns = [
    # Debug views
    path('debug/user-access/', debug_views.debug_user_access, name='debug_user_access'),
    # Raw materials store views
    path('dashboard/', views.raw_materials_dashboard, name='dashboard'),
    path('monitor/', views.inventory_monitor, name='inventory_monitor'),
    path('monitor/export/', views.export_inventory, name='export_inventory'),
    path('material/<int:material_id>/', views.material_detail, name='material_detail'),
    path('receive/', views.receive_material, name='receive_material'),
    
    # Filtered material batch lists
    path('batches/all/', views.batch_list, name='batch_list'),
    path('batches/pending/', views.batch_list, {'status': 'pending_qc'}, name='pending_batches'),
    path('batches/approved/', views.batch_list, {'status': 'approved'}, name='approved_batches'),
    path('batches/rejected/', views.batch_list, {'status': 'rejected'}, name='rejected_batches'),
    
    # QC testing views
    path('qc/dashboard/', views.qc_dashboard, name='qc_dashboard'),
    path('qc/test/<int:batch_id>/', views.perform_qc_test, name='perform_qc_test'),
    path('qc/test-detail/<int:test_id>/', views.qc_test_detail, name='qc_test_detail'),
    
    # Dispensing views
    path('dispensing/dashboard/', views.dispensing_dashboard, name='dispensing_dashboard'),
    path('dispensing/<int:dispensing_id>/', views.dispensing_detail, name='dispensing_detail'),
    path('dispensing/<int:dispensing_id>/start/', views.start_dispensing, name='start_dispensing'),
    path('dispensing/<int:dispensing_id>/complete/', views.complete_dispensing, name='complete_dispensing'),
    
    # AJAX views
    path('unit/', views_ajax.get_raw_material_unit, name='get_raw_material_unit'),
    path('dispensing/<int:dispensing_id>/', views.dispensing_detail, name='dispensing_detail'),
    
    # API endpoints
    path('api/materials/', api_views.api_materials, name='api_materials'),
    path('api/materials/<int:material_id>/', api_views.api_material_detail, name='api_material_detail'),
    path('api/batch-detail/', api_views.api_batch_detail, name='api_batch_detail'),
    path('api/qc-test-detail/', api_views.api_qc_test_detail, name='api_qc_test_detail'),
    path('api/start-qc-test/', api_views.start_qc_test, name='start_qc_test'),
    path('api/save-qc-test/', api_views.save_qc_test, name='save_qc_test'),
    path('api/activity/', api_views.api_activity, name='api_activity'),
    path('api/expiry/', api_views.api_expiry, name='api_expiry'),
    path('api/add-material/', api_views.add_material, name='add_material'),
    path('api/mark-for-disposal/', api_views.mark_for_disposal, name='mark_for_disposal'),
    path('api/update-associations/', api_views.api_update_associations, name='api_update_associations'),
    path('api/inventory-by-product/', api_views.api_inventory_by_product, name='api_inventory_by_product'),
]
