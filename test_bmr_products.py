#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from products.models import Product

def test_bmr_product_relationships():
    """Test BMR-Product relationships to see why products aren't showing"""
    
    print("=== BMR-PRODUCT RELATIONSHIP TEST ===\n")
    
    # Check total counts
    total_bmrs = BMR.objects.count()
    total_products = Product.objects.count()
    
    print(f"📊 COUNTS:")
    print(f"   Total BMRs: {total_bmrs}")
    print(f"   Total Products: {total_products}")
    print()
    
    # Check BMRs with products
    bmrs_with_products = BMR.objects.select_related('product').exclude(product__isnull=True).count()
    bmrs_without_products = BMR.objects.filter(product__isnull=True).count()
    
    print(f"🔗 RELATIONSHIPS:")
    print(f"   BMRs with Products: {bmrs_with_products}")
    print(f"   BMRs without Products: {bmrs_without_products}")
    print()
    
    # Show first 10 BMRs with their product details
    print("📋 SAMPLE BMR-PRODUCT DATA:")
    bmrs = BMR.objects.select_related('product').all()[:10]
    
    for bmr in bmrs:
        product_name = bmr.product.product_name if bmr.product else "NO PRODUCT"
        product_type = bmr.product.product_type if bmr.product else "N/A"
        print(f"   BMR {bmr.batch_number}: {product_name} ({product_type})")
    
    print()
    
    # Check for orphaned BMRs
    if bmrs_without_products > 0:
        print("⚠️  ORPHANED BMRs (No Product Assigned):")
        orphaned = BMR.objects.filter(product__isnull=True)
        for bmr in orphaned:
            print(f"   BMR {bmr.batch_number}: No product assigned")
        print()
    
    # Check products in database
    print("🧪 PRODUCTS IN DATABASE:")
    products = Product.objects.all()
    for product in products:
        bmr_count = BMR.objects.filter(product=product).count()
        print(f"   {product.product_name} ({product.product_type}): {bmr_count} BMRs")
    
    print()
    
    # Test the exact query used in dashboards
    print("🔍 DASHBOARD QUERY TEST:")
    recent_bmrs = BMR.objects.select_related('product', 'created_by').all()[:5]
    
    for bmr in recent_bmrs:
        try:
            product_name = bmr.product.product_name
            print(f"   ✅ BMR {bmr.batch_number}: {product_name}")
        except AttributeError as e:
            print(f"   ❌ BMR {bmr.batch_number}: Error accessing product - {e}")
        except Exception as e:
            print(f"   ❌ BMR {bmr.batch_number}: Unexpected error - {e}")
    
    print()
    
    # Recommendations
    if bmrs_without_products > 0:
        print("🔧 RECOMMENDATIONS:")
        print("   1. Assign products to orphaned BMRs")
        print("   2. Update BMR creation process to require product selection")
        print("   3. Add database constraint to prevent null products")
    else:
        print("✅ ALL BMRs HAVE PRODUCTS ASSIGNED")
        print("   The issue might be in template rendering or view context")

if __name__ == '__main__':
    test_bmr_product_relationships()
