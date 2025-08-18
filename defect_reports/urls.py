from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_defect, name='report_defect'),
    path('list/', views.defect_list, name='defect_list'),
    path('<int:pk>/', views.defect_detail, name='defect_detail'),
]
