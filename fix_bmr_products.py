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

def fix_bmr_product_relationships():
    """Fix missing product relationships in BMRs"""
    
    print("=== BMR-PRODUCT RELATIONSHIP FIX ===\n")
    
    # Check for BMRs without products
    bmrs_without_products = BMR.objects.filter(product__isnull=True)
    print(f"📋 BMRs without products: {bmrs_without_products.count()}")
    
    if bmrs_without_products.count() > 0:
        # Get a default product to assign
        default_product = Product.objects.first()
        
        if default_product:
            print(f"🔧 Assigning default product: {default_product.product_name}")
            
            for bmr in bmrs_without_products:
                bmr.product = default_product
                bmr.save()
                print(f"   ✅ Fixed BMR {bmr.batch_number}")
            
            print(f"\n✅ Fixed {bmrs_without_products.count()} BMR records")
        else:
            print("❌ No products available to assign!")
            return
    
    # Verify fix
    print("\n📊 FINAL STATUS:")
    total_bmrs = BMR.objects.count()
    bmrs_with_products = BMR.objects.exclude(product__isnull=True).count()
    
    print(f"   Total BMRs: {total_bmrs}")
    print(f"   BMRs with Products: {bmrs_with_products}")
    
    if bmrs_with_products == total_bmrs:
        print("✅ All BMRs now have products assigned!")
    else:
        print(f"⚠️  Still {total_bmrs - bmrs_with_products} BMRs without products")
    
    # Show sample data
    print("\n📋 SAMPLE BMR-PRODUCT DATA:")
    sample_bmrs = BMR.objects.select_related('product').all()[:5]
    
    for bmr in sample_bmrs:
        product_name = bmr.product.product_name if bmr.product else "NO PRODUCT"
        print(f"   BMR {bmr.batch_number}: {product_name}")

if __name__ == '__main__':
    fix_bmr_product_relationships()
