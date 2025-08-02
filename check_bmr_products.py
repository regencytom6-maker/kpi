from bmr.models import BMR
from products.models import Product

# Check BMRs and their products
bmrs = BMR.objects.select_related('product').all()
print(f'Total BMRs: {bmrs.count()}')

for bmr in bmrs[:5]:
    product_name = bmr.product.name if bmr.product else "None"
    print(f'BMR {bmr.batch_number}: Product = {product_name}')

# Check if there are any products
products = Product.objects.all()
print(f'\nTotal Products: {products.count()}')
for product in products[:3]:
    print(f'Product: {product.name}')
