from django.core.management.base import BaseCommand
from django.utils import timezone
from products.models import Product
from raw_materials.models import RawMaterial
from products.models_material import ProductMaterial

class Command(BaseCommand):
    help = 'List all product materials with their approval status and available quantities'
    
    def add_arguments(self, parser):
        parser.add_argument('--product', type=str, help='Filter by product name (partial match)')
        parser.add_argument('--material', type=str, help='Filter by material code or name (partial match)')
        parser.add_argument('--show-all', action='store_true', help='Show all materials including sufficient ones')
        parser.add_argument('--show-approved-only', action='store_true', help='Show only approved materials')
        parser.add_argument('--show-issues-only', action='store_true', help='Show only materials with issues (not approved or insufficient)')
        
    def handle(self, *args, **options):
        product_filter = options.get('product')
        material_filter = options.get('material')
        show_all = options.get('show_all')
        show_approved_only = options.get('show_approved_only')
        show_issues_only = options.get('show_issues_only')
        
        # Get all product materials with filtering
        product_materials = ProductMaterial.objects.all()
        
        if product_filter:
            product_materials = product_materials.filter(product__product_name__icontains=product_filter)
        
        if material_filter:
            product_materials = product_materials.filter(
                raw_material__material_name__icontains=material_filter) | product_materials.filter(
                raw_material__material_code__icontains=material_filter)
        
        # Apply status filters if requested
        if show_approved_only:
            # This requires Python-side filtering as it uses a property
            filtered_materials = []
            for pm in product_materials:
                if pm.is_approved():
                    filtered_materials.append(pm)
            product_materials = filtered_materials
        
        if show_issues_only:
            # This requires Python-side filtering as it uses properties
            filtered_materials = []
            for pm in product_materials:
                if not pm.is_approved() or not pm.has_sufficient_quantity():
                    filtered_materials.append(pm)
            product_materials = filtered_materials
        
        # Display results
        self.stdout.write("\nPRODUCT MATERIALS WITH APPROVAL STATUS AND AVAILABLE QUANTITIES")
        self.stdout.write("--------------------------------------------------------------\n")
        
        if not product_materials:
            self.stdout.write("No product materials found in the database.")
            self.stdout.write("Use the associate_material command to add product materials:")
            self.stdout.write('python manage.py associate_material "Product Name" "Material-Code" Quantity "unit"')
            return
            
        # Group by product for better readability
        products_map = {}
        for pm in product_materials:
            if pm.product not in products_map:
                products_map[pm.product] = []
            products_map[pm.product].append(pm)
        
        # Print grouped by product
        for product, materials in products_map.items():
            self.stdout.write(self.style.SUCCESS(f"Product: {product.product_name} ({product.product_type})"))
            
            for pm in materials:
                approved = pm.is_approved()
                approved_str = "✓ Approved" if approved else "✗ Not approved"
                sufficient = pm.has_sufficient_quantity()
                sufficient_str = "✓ Yes" if sufficient else "✗ No"
                
                self.stdout.write(f"  Material: {pm.raw_material.material_name} ({pm.raw_material.material_code})")
                self.stdout.write(f"  Required: {pm.required_quantity} {pm.unit_of_measure} per unit")
                self.stdout.write(f"  QC Status: {approved_str}")
                self.stdout.write(f"  Available: {pm.available_quantity()} {pm.raw_material.unit_of_measure}")
                self.stdout.write(f"  Sufficient: {sufficient_str}")
                self.stdout.write("")
