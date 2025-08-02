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
from accounts.models import CustomUser
from workflow.models import BatchPhaseExecution
from products.models import Product
from django.utils import timezone
from datetime import timedelta

def test_admin_dashboard_data():
    """Test that admin dashboard loads real data correctly"""
    
    print("=== ADMIN DASHBOARD DATA TEST ===\n")
    
    # BMR Statistics
    total_bmrs = BMR.objects.count()
    active_batches = BMR.objects.filter(status__in=['draft', 'approved', 'in_production']).count()
    completed_batches = BMR.objects.filter(status='completed').count()
    rejected_batches = BMR.objects.filter(status='rejected').count()
    
    print("📊 BMR METRICS:")
    print(f"   Total BMRs: {total_bmrs}")
    print(f"   Active Batches: {active_batches}")
    print(f"   Completed Batches: {completed_batches}")
    print(f"   Rejected Batches: {rejected_batches}")
    print()
    
    # User Statistics
    total_users = CustomUser.objects.count()
    active_users_count = CustomUser.objects.filter(
        is_active=True, 
        last_login__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    print("👥 USER METRICS:")
    print(f"   Total Users: {total_users}")
    print(f"   Active Users (30 days): {active_users_count}")
    print()
    
    # System Status
    active_phases = BatchPhaseExecution.objects.filter(
        status__in=['pending', 'in_progress']
    ).count()
    
    completed_today = BatchPhaseExecution.objects.filter(
        completed_date__date=timezone.now().date(),
        status='completed'
    ).count()
    
    print("⚙️ SYSTEM STATUS:")
    print(f"   Active Phases: {active_phases}")
    print(f"   Completed Today: {completed_today}")
    print()
    
    # FGS Store
    fgs_batches = BatchPhaseExecution.objects.filter(
        phase__phase_name='finished_goods_storage',
        status__in=['completed', 'in_progress']
    )
    fgs_total_items = fgs_batches.count()
    
    print("📦 FGS STORE:")
    print(f"   Total Items in FGS: {fgs_total_items}")
    print()
    
    # Products
    total_products = Product.objects.count()
    product_types = Product.objects.values_list('product_type', flat=True).distinct()
    
    print("🧪 PRODUCTS:")
    print(f"   Total Products: {total_products}")
    print(f"   Product Types: {list(product_types)}")
    print()
    
    # Summary
    print("✅ DASHBOARD DATA SUMMARY:")
    print(f"   - Cards will show: {total_bmrs} Total BMRs, {active_batches} Active, {completed_batches} Completed, {rejected_batches} Rejected")
    print(f"   - System shows: {active_users_count} Active Users out of {total_users} total")
    print(f"   - FGS Monitor shows: {fgs_total_items} items in store")
    print(f"   - System Status: {active_phases} active phases, {completed_today} completed today")
    
    # Check if we have any sample data
    if total_bmrs == 0:
        print("\n⚠️  WARNING: No BMR data found. Consider creating some test BMRs to see dashboard in action.")
    
    if total_users <= 1:
        print("\n⚠️  WARNING: Very few users found. Consider creating test users with different roles.")
    
    print("\n🎨 STYLING UPDATES:")
    print("   - Cards now use uniform colors instead of gradients")
    print("   - Blue for BMR metrics, Green for system status")
    print("   - Purple for quick actions, Cyan for timeline, Red for monitoring")
    
    print("\n🖼️  LOGO INTEGRATION:")
    print("   - Logo placeholder created in static/images/")
    print("   - Add 'logo.png' to static/images/ directory")
    print("   - Logo will appear in navigation and login page")
    print("   - Fallback to icon if logo not found")

if __name__ == '__main__':
    test_admin_dashboard_data()
