# Migration Instructions

## Handling the "standard_batch_size" Migration

When you run `python manage.py makemigrations products`, you'll get a prompt:

```
It is impossible to add a non-nullable field 'standard_batch_size' to product without specifying a default.
Please select a fix:
 1) Provide a one-off default now (will be set on all existing rows with a null value for this column)
 2) Quit and manually define a default value in models.py.
Select an option:
```

## Recommended Solution:

### Option 1: Quick Fix (Use this)
1. Select option **1** 
2. When prompted for a default value, enter: **1000**
3. This will set all existing products to have a standard batch size of 1000 units

### Steps:
1. Run: `python manage.py makemigrations products`
2. When prompted, type: `1` and press Enter
3. When asked for default value, type: `1000` and press Enter

## After Migration:
You can then manually update each product's batch size through the admin interface:

1. Go to Django Admin → Products
2. Edit each product to set the correct batch sizes:
   - **Tablets**: Usually 10,000-50,000 units
   - **Ointments**: Usually 100-500 kg
   - **Capsules**: Usually 5,000-25,000 units

## Alternative: Script to Set Realistic Defaults

If you want to set more realistic defaults based on product type, you can run this after migration:

```python
from products.models import Product

# Update batch sizes based on product type
for product in Product.objects.all():
    if product.product_type == 'tablet':
        product.standard_batch_size = 25000
        product.batch_size_unit = 'units'
    elif product.product_type == 'ointment':
        product.standard_batch_size = 250
        product.batch_size_unit = 'kg'
    elif product.product_type == 'capsule':
        product.standard_batch_size = 15000
        product.batch_size_unit = 'units'
    else:
        product.standard_batch_size = 1000
        product.batch_size_unit = 'units'
    
    product.save()
    print(f"Updated {product.product_name}: {product.standard_batch_size} {product.batch_size_unit}")
```

## Complete Migration Sequence:

1. **Products migration**: `python manage.py makemigrations products`
2. **BMR migration**: `python manage.py makemigrations bmr`
3. **Accounts migration**: `python manage.py makemigrations accounts`
4. **Apply all migrations**: `python manage.py migrate`
5. **Update batch sizes** using admin or script above
