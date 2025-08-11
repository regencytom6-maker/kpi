#!/usr/bin/env python
"""
Verify that database migrations have been applied correctly
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase

def verify_migration():
    print("🔍 VERIFYING DATABASE MIGRATION RESULTS...")
    
    # Check the phase order for tablet type workflows
    phases = ProductionPhase.objects.filter(
        phase_name__in=['bulk_packing', 'secondary_packaging'],
        product_type__in=['tablet', 'tablet_2']
    ).order_by('phase_order')
    
    print("\n📦 Phase Order Verification:")
    for phase in phases:
        print(f"   {phase.phase_name}: order {phase.phase_order} (product_type: {phase.product_type})")
    
    # Check if we have the correct order
    bulk_phases = [p for p in phases if p.phase_name == 'bulk_packing']
    secondary_phases = [p for p in phases if p.phase_name == 'secondary_packaging']
    
    if bulk_phases and secondary_phases:
        bulk_order = bulk_phases[0].phase_order
        secondary_order = secondary_phases[0].phase_order
        
        if bulk_order < secondary_order:
            print(f"   ✅ CORRECT: bulk_packing (order {bulk_order}) comes before secondary_packaging (order {secondary_order})")
            print("   ✅ Migration applied successfully!")
            return True
        else:
            print(f"   ❌ ERROR: Incorrect order - bulk_packing: {bulk_order}, secondary_packaging: {secondary_order}")
            return False
    else:
        print("   ❌ ERROR: Could not find required phases")
        return False

if __name__ == "__main__":
    verify_migration()
    print("\n🎉 Database migration verification complete!")
