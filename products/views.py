from django.shortcuts import render
from .models import Product

def product_list(request):
    """View to display list of products"""
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

def product_detail(request, product_id):
    """View to display details of a specific product"""
    product = Product.objects.get(pk=product_id)
    return render(request, 'products/product_detail.html', {'product': product})
