from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product

@login_required
def api_products(request):
    """API endpoint to return all products in JSON format"""
    products = Product.objects.all()
    
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'product_name': product.product_name,
            'product_type': product.product_type,
            'batch_size_unit': product.batch_size_unit,
            'is_active': product.is_active,
        })
    
    return JsonResponse({'success': True, 'products': products_data})

@login_required
def ajax_products_list(request):
    """Returns all products for AJAX dropdowns"""
    # Get all products, regardless of active status to ensure we have data
    products = Product.objects.all()
    
    product_list = []
    for product in products:
        # Use proper display names for product types
        product_type_display = dict(Product.PRODUCT_TYPE_CHOICES).get(product.product_type, product.product_type)
        
        product_list.append({
            'id': product.id,
            'product_name': product.product_name,
            'category': product_type_display
        })
    
    # Log how many products were found for debugging
    print(f"Found {len(product_list)} products for dropdown")
    
    return JsonResponse({'products': product_list})
