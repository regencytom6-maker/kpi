from django.urls import path
from . import views
from . import api_views

app_name = 'products'

urlpatterns = [
    # Product views
    path('', views.product_list, name='product_list'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    
    # API endpoints
    path('api/products/', api_views.api_products, name='api_products'),
    path('api/products-list/', api_views.ajax_products_list, name='ajax_products_list'),
]
