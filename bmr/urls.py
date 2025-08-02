from django.urls import path
from .views import (
    create_bmr_view, bmr_list_view, bmr_detail_view,
    start_phase_view, complete_phase_view, reject_phase_view
)

app_name = 'bmr'

urlpatterns = [
    path('create/', create_bmr_view, name='create'),
    path('list/', bmr_list_view, name='list'),
    path('<int:bmr_id>/', bmr_detail_view, name='detail'),
    path('<int:bmr_id>/start-phase/<str:phase_name>/', start_phase_view, name='start_phase'),
    path('<int:bmr_id>/complete-phase/<str:phase_name>/', complete_phase_view, name='complete_phase'),
    path('<int:bmr_id>/reject-phase/<str:phase_name>/', reject_phase_view, name='reject_phase'),
]
