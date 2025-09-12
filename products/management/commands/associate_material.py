from django.core.management.base import BaseCommand
from products.models import Product
from raw_materials.models import RawMaterial
from products.models_material import ProductMaterial

class Command(BaseCommand):
    help = 'Associate raw materials with products'
    
    def add_arguments(self, parser):
        parser.add_argument('--product', type=str, help='Product name')
        parser.add_argument('--material', type=str, help='Material code')
        parser.add_argument('--quantity', type=float, default=1.0, help='Required quantity')
        parser.add_argument('--unit', type=str, help='Unit of measure (if not specified, uses material default)')
        parser.add_argument('--active', action='store_true', help='Mark as active ingredient')
        parser.add_argument('--notes', type=str, help='Optional notes')
        parser.add_argument('--list-products', action='store_true', help='List all products with their materials')
        parser.add_argument('--list-materials', action='store_true', help='List all materials with their products')
    
    def handle(self, *args, **options):
        if options['list_products']:
            self.list_products_with_materials()
            return
        
        if options['list_materials']:
            self.list_materials_with_products()
            return
        
        if not options['product'] or not options['material']:
            self.stdout.write(self.style.ERROR('Both --product and --material are required'))
            return
        
        self.associate_material_to_product(
            options['product'],
            options['material'],
            options['quantity'],
            options['unit'],
            options['active'],
            options['notes']
        )
    
    def associate_material_to_product(self, product_name, material_code, quantity=1.0, unit_of_measure=None, is_active=False, notes=None):
        try:
            # Find the product and material
            product = Product.objects.get(product_name=product_name)
            material = RawMaterial.objects.get(material_code=material_code)
            
            # Use the material's unit if none provided
            if not unit_of_measure:
                unit_of_measure = material.unit_of_measure
            
            # Create or update the relationship
            product_material, created = ProductMaterial.objects.update_or_create(
                product=product,
                raw_material=material,
                defaults={
                    'required_quantity': quantity,
                    'unit_of_measure': unit_of_measure,
                    'is_active_ingredient': is_active,
                    'notes': notes
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new relationship: {product_material}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated existing relationship: {product_material}"))
                
            # Display approval status and available quantity
            self.stdout.write("\nMaterial Status:")
            self.stdout.write(f"- Approved: {'Yes' if product_material.is_approved() else 'No'}")
            self.stdout.write(f"- Available Quantity: {product_material.available_quantity()} {material.unit_of_measure}")
            self.stdout.write(f"- Sufficient for production: {'Yes' if product_material.has_sufficient_quantity() else 'No'}")
            
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Product '{product_name}' not found"))
        except RawMaterial.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Material '{material_code}' not found"))
    
    def list_products_with_materials(self):
        products = Product.objects.prefetch_related('product_materials__raw_material').all()
        
        self.stdout.write(self.style.SUCCESS(f"Found {products.count()} products"))
        self.stdout.write("=" * 80)
        
        for product in products:
            self.stdout.write(self.style.SUCCESS(f"{product.product_name} ({product.product_type}):"))
            materials = product.product_materials.all()
            
            if materials:
                self.stdout.write("  Materials:")
                for pm in materials:
                    active_str = " (ACTIVE)" if pm.is_active_ingredient else ""
                    approved_str = "✓ Approved" if pm.is_approved() else "✗ Not approved"
                    available_str = f"Available: {pm.available_quantity()} {pm.raw_material.unit_of_measure}"
                    sufficient = "✓ Yes" if pm.has_sufficient_quantity() else "✗ No"
                    self.stdout.write(f"  - {pm.raw_material.material_name} ({pm.raw_material.material_code}): {pm.required_quantity} {pm.unit_of_measure}{active_str}")
                    self.stdout.write(f"    • QC Status: {approved_str}")
                    self.stdout.write(f"    • {available_str}")
                    self.stdout.write(f"    • Sufficient: {sufficient}")
            else:
                self.stdout.write("  No materials associated")
            
            self.stdout.write("-" * 80)
    
    def list_materials_with_products(self):
        materials = RawMaterial.objects.prefetch_related('product_materials__product').all()
        
        self.stdout.write(self.style.SUCCESS(f"Found {materials.count()} raw materials"))
        self.stdout.write("=" * 80)
        
        for material in materials:
            self.stdout.write(self.style.SUCCESS(f"{material.material_name} ({material.material_code}):"))
            product_materials = material.product_materials.all()
            
            if product_materials:
                self.stdout.write("  Used in products:")
                for pm in product_materials:
                    self.stdout.write(f"  - {pm.product.product_name}: {pm.required_quantity} {pm.unit_of_measure}")
            else:
                self.stdout.write("  Not used in any products")
            
            self.stdout.write("-" * 80)
