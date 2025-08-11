#!/usr/bin/env python
"""
Debug script to check admin settings and actual database state
Find why bulk packing is being skipped for new batches
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from bmr.models import BMR
from products.models import Product
from workflow.models import BatchPhaseExecution, WorkflowPhase
from workflow.services import WorkflowService

User = get_user_model()

def check_admin_settings():
    """Check admin settings and database state"""
    print("="*80)
    print("DEBUGGING ADMIN SETTINGS AND DATABASE STATE")
    print("="*80)
    
    # 1. Check WorkflowPhase definitions in admin
    print("\n🔍 1. CHECKING WORKFLOW PHASE DEFINITIONS")
    print("-" * 50)
    
    all_phases = WorkflowPhase.objects.all().order_by('phase_order')
    print(f"Total phases defined: {all_phases.count()}")
    
    bulk_packing_phases = WorkflowPhase.objects.filter(phase_name='bulk_packing')
    print(f"Bulk packing phases found: {bulk_packing_phases.count()}")
    
    if bulk_packing_phases.exists():
        for phase in bulk_packing_phases:
            print(f"  ✅ Phase: {phase.phase_name}")
            print(f"     Order: {phase.phase_order}")
            print(f"     Display: {phase.get_phase_name_display()}")
            print(f"     User Role: {phase.user_role}")
            print(f"     Active: {getattr(phase, 'is_active', 'N/A')}")
    else:
        print("  ❌ NO BULK_PACKING PHASE FOUND IN DATABASE!")
        print("     This is the root cause - the phase doesn't exist!")
    
    # 2. Check all phases for tablet workflows
    print(f"\n🔍 2. ALL WORKFLOW PHASES (showing order)")
    print("-" * 50)
    for phase in all_phases:
        print(f"  {phase.phase_order:2d}. {phase.phase_name} ({phase.get_phase_name_display()}) - Role: {phase.user_role}")
    
    # 3. Check Product configurations
    print(f"\n🔍 3. CHECKING PRODUCT CONFIGURATIONS")
    print("-" * 50)
    
    tablet2_products = Product.objects.filter(
        product_type='tablet',
        tablet_type='tablet_2'
    )
    
    print(f"Tablet Type 2 products: {tablet2_products.count()}")
    for product in tablet2_products:
        print(f"  📦 {product.product_name}")
        print(f"     Type: {product.product_type}")
        print(f"     Tablet Type: {product.tablet_type}")
        print(f"     Coating: {getattr(product, 'coating_type', 'N/A')}")
        print()
    
    # 4. Check recent BMRs and their phases
    print(f"\n🔍 4. CHECKING RECENT BMRs AND THEIR PHASES")
    print("-" * 50)
    
    recent_bmrs = BMR.objects.select_related('product').order_by('-created_date')[:5]
    
    for bmr in recent_bmrs:
        print(f"\n📋 BMR: {bmr.batch_number} - {bmr.product.product_name}")
        print(f"   Product Type: {bmr.product.product_type}")
        print(f"   Tablet Type: {getattr(bmr.product, 'tablet_type', 'N/A')}")
        print(f"   Created: {bmr.created_date}")
        
        # Get phases for this BMR
        bmr_phases = BatchPhaseExecution.objects.filter(bmr=bmr).order_by('phase__phase_order')
        print(f"   Phases: {bmr_phases.count()}")
        
        has_bulk_packing = False
        for i, phase_exec in enumerate(bmr_phases, 1):
            phase_name = phase_exec.phase.phase_name
            if phase_name == 'bulk_packing':
                has_bulk_packing = True
                print(f"     {i:2d}. ✅ {phase_name} - {phase_exec.status}")
            else:
                print(f"     {i:2d}.    {phase_name} - {phase_exec.status}")
        
        if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2':
            if not has_bulk_packing:
                print(f"     ❌ PROBLEM: Tablet Type 2 missing bulk_packing!")
            else:
                print(f"     ✅ Tablet Type 2 has bulk_packing")
    
    # 5. Check workflow service method
    print(f"\n🔍 5. TESTING WORKFLOW SERVICE DIRECTLY")
    print("-" * 50)
    
    # Get a tablet type 2 product
    tablet2_product = Product.objects.filter(
        product_type='tablet',
        tablet_type='tablet_2'
    ).first()
    
    if tablet2_product:
        print(f"Testing with product: {tablet2_product.product_name}")
        
        # Test the workflow phases creation
        try:
            print("Calling WorkflowService.get_workflow_phases_for_product...")
            phases = WorkflowService.get_workflow_phases_for_product(tablet2_product)
            
            print(f"Phases returned: {len(phases)}")
            for i, phase in enumerate(phases, 1):
                if phase.phase_name == 'bulk_packing':
                    print(f"  {i:2d}. ✅ {phase.phase_name} (Order: {phase.phase_order})")
                else:
                    print(f"  {i:2d}.    {phase.phase_name} (Order: {phase.phase_order})")
            
            # Check if bulk_packing is in the list
            bulk_packing_found = any(p.phase_name == 'bulk_packing' for p in phases)
            if not bulk_packing_found:
                print("❌ BULK_PACKING NOT IN WORKFLOW PHASES LIST!")
            else:
                print("✅ bulk_packing found in workflow phases")
                
        except Exception as e:
            print(f"❌ Error calling WorkflowService: {e}")
    
    # 6. Check if there are any admin configurations affecting this
    print(f"\n🔍 6. CHECKING FOR CONFIGURATION ISSUES")
    print("-" * 50)
    
    # Check if there are duplicate or conflicting phases
    phase_names = WorkflowPhase.objects.values_list('phase_name', flat=True)
    duplicate_names = []
    seen = set()
    for name in phase_names:
        if name in seen:
            duplicate_names.append(name)
        seen.add(name)
    
    if duplicate_names:
        print(f"❌ DUPLICATE PHASE NAMES FOUND: {duplicate_names}")
    else:
        print("✅ No duplicate phase names")
    
    # Check for phases with same order
    phase_orders = WorkflowPhase.objects.values_list('phase_order', flat=True)
    duplicate_orders = []
    seen_orders = set()
    for order in phase_orders:
        if order in seen_orders:
            duplicate_orders.append(order)
        seen_orders.add(order)
    
    if duplicate_orders:
        print(f"❌ DUPLICATE PHASE ORDERS FOUND: {duplicate_orders}")
        print("   This could cause phases to be skipped!")
    else:
        print("✅ No duplicate phase orders")
    
    # 7. Create a test BMR and trace the workflow creation
    print(f"\n🔍 7. CREATING TEST BMR TO TRACE WORKFLOW")
    print("-" * 50)
    
    if tablet2_product:
        qa_user = User.objects.filter(role='qa').first()
        if qa_user:
            try:
                # Create test BMR
                test_batch = f"DEBUG{datetime.now().strftime('%H%M%S')}"
                test_bmr = BMR.objects.create(
                    batch_number=test_batch,
                    product=tablet2_product,
                    batch_size=1000,
                    created_by=qa_user,
                    status='draft'
                )
                
                print(f"✅ Created test BMR: {test_bmr.batch_number}")
                
                # Initialize workflow and trace
                print("Initializing workflow...")
                WorkflowService.initialize_workflow_for_bmr(test_bmr)
                
                # Check what phases were created
                test_phases = BatchPhaseExecution.objects.filter(bmr=test_bmr).order_by('phase__phase_order')
                print(f"Phases created: {test_phases.count()}")
                
                has_bulk = False
                for phase_exec in test_phases:
                    if phase_exec.phase.phase_name == 'bulk_packing':
                        has_bulk = True
                        print(f"  ✅ {phase_exec.phase.phase_name} (Order: {phase_exec.phase.phase_order})")
                    else:
                        print(f"     {phase_exec.phase.phase_name} (Order: {phase_exec.phase.phase_order})")
                
                if not has_bulk:
                    print("❌ TEST FAILED: bulk_packing not created for test BMR!")
                    print("   This confirms the issue exists in workflow initialization")
                else:
                    print("✅ TEST PASSED: bulk_packing created for test BMR")
                
                # Clean up test BMR
                test_bmr.delete()
                print(f"🗑️  Cleaned up test BMR")
                
            except Exception as e:
                print(f"❌ Error creating test BMR: {e}")
        else:
            print("❌ No QA user found for testing")
    
    print("\n" + "="*80)
    print("SUMMARY AND RECOMMENDATIONS")
    print("="*80)
    
    # Check critical issues
    critical_issues = []
    
    if not bulk_packing_phases.exists():
        critical_issues.append("❌ CRITICAL: bulk_packing phase not defined in WorkflowPhase table")
    
    if duplicate_orders:
        critical_issues.append("❌ CRITICAL: Duplicate phase orders causing workflow conflicts")
    
    if not tablet2_products.exists():
        critical_issues.append("❌ CRITICAL: No Tablet Type 2 products found")
    
    if critical_issues:
        print("🚨 CRITICAL ISSUES FOUND:")
        for issue in critical_issues:
            print(f"   {issue}")
        print("\nRECOMMENDED ACTIONS:")
        print("1. Check Django admin for WorkflowPhase table")
        print("2. Ensure bulk_packing phase exists with correct order")
        print("3. Verify no duplicate phase orders")
        print("4. Check product tablet_type field values")
    else:
        print("✅ No critical configuration issues found")
        print("   The problem may be in the workflow logic code")
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    success = check_admin_settings()
    if not success:
        print("\n🔧 Run this script to identify the exact admin configuration problem.")
        sys.exit(1)
    else:
        print("\n✅ Admin configuration appears correct. Issue may be in code logic.")
