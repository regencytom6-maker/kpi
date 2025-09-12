from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Creates sample products for testing'

    def handle(self, *args, **options):
        # Check existing products
        existing_count = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Current product count: {existing_count}'))
        
        # Create sample products
        products_to_create = [
            {
                'product_name': 'Paracetamol 500mg Tablets',
                'product_type': 'tablet',
                'coating_type': 'uncoated',
                'tablet_type': 'normal',
                'standard_batch_size': 10000,
                'batch_size_unit': 'tablets'
            },
            {
                'product_name': 'Amoxicillin 250mg Capsules',
                'product_type': 'capsule',
                'capsule_type': 'normal',
                'standard_batch_size': 5000,
                'batch_size_unit': 'capsules'
            },
            {
                'product_name': 'Hydrocortisone Cream 1%',
                'product_type': 'ointment',
                'standard_batch_size': 500,
                'batch_size_unit': 'tubes'
            },
            {
                'product_name': 'Ibuprofen 400mg Tablets',
                'product_type': 'tablet',
                'coating_type': 'coated',
                'tablet_type': 'tablet_2',
                'standard_batch_size': 8000,
                'batch_size_unit': 'tablets'
            }
        ]
        
        created_count = 0
        for product_data in products_to_create:
            # Check if product already exists
            if not Product.objects.filter(product_name=product_data['product_name']).exists():
                Product.objects.create(**product_data)
                created_count += 1
                self.stdout.write(f"Created: {product_data['product_name']}")
            else:
                self.stdout.write(f"Already exists: {product_data['product_name']}")
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new products'))
        self.stdout.write(self.style.SUCCESS(f'Total products now: {Product.objects.count()}'))
