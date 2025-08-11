import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import ProductionPhase, BatchPhaseExecution
from bmr.models import BMR

def verify_tablet_workflow():
    print("\n✨ WORKFLOW SEQUENCE VERIFICATION\n")
    
    # Check all BMRs for tablet type 2
    tablet_bmrs = BMR.objects.filter(product__product_type='tablet', product__tablet_type='tablet_2')
    
    print(f"Found {tablet_bmrs.count()} tablet type 2 BMRs")
    
    for bmr in tablet_bmrs:
        print(f"\n📋 BMR: {bmr.bmr_number}")
        print(f"Product: {bmr.product.product_name}")
        print(f"Is Coated: {bmr.product.is_coated}")
        
        # Get phases in order
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        print("\nPhase Sequence:")
        for idx, phase in enumerate(phases, 1):
            status_emoji = "✅" if phase.status == 'completed' else "⏳" if phase.status == 'pending' else "🔄" if phase.status == 'in_progress' else "⏹️"
            print(f"{idx:2d}. {status_emoji} {phase.phase.phase_name} ({phase.status})")
        
        # Verify specific order for tablet type 2
        material_release = phases.filter(phase__phase_name='packaging_material_release').first()
        bulk_packing = phases.filter(phase__phase_name='bulk_packing').first()
        secondary_packing = phases.filter(phase__phase_name='secondary_packaging').first()
        
        if material_release and bulk_packing and secondary_packing:
            mr_order = material_release.phase.phase_order
            bp_order = bulk_packing.phase.phase_order
            sp_order = secondary_packing.phase.phase_order
            
            if mr_order < bp_order < sp_order:
                print("\n✅ CORRECT SEQUENCE: Material Release → Bulk Packing → Secondary Packaging")
            else:
                print("\n❌ INCORRECT SEQUENCE:")
                print(f"Material Release order: {mr_order}")
                print(f"Bulk Packing order: {bp_order}")
                print(f"Secondary Packaging order: {sp_order}")
        else:
            print("\n❌ Missing required phases")
    
    # Check notification display
    print("\n🔍 CHECKING NOTIFICATION TEMPLATES\n")
    
    notification_path = 'dashboards/templates/notifications/phase_notification.html'
    if os.path.exists(notification_path):
        print(f"✅ Notification template exists at: {notification_path}")
    else:
        print(f"❌ Notification template not found at: {notification_path}")
    
    # Check if packaging dashboard includes the notification template
    packaging_path = 'templates/dashboards/packaging_dashboard.html'
    if os.path.exists(packaging_path):
        with open(packaging_path, 'r') as f:
            content = f.read()
        if "{% include 'notifications/phase_notification.html' %}" in content:
            print("✅ Packaging dashboard includes the notification template")
        else:
            print("❌ Packaging dashboard does not include the notification template")
    
    # Check cursor fix
    print("\n🔍 CHECKING DROPDOWN CURSOR FIX\n")
    
    base_path = 'templates/dashboards/dashboard_base.html'
    if os.path.exists(base_path):
        with open(base_path, 'r') as f:
            content = f.read()
        if "cursor: pointer" in content:
            print("✅ Dropdown cursor fix is applied")
        else:
            print("❌ Dropdown cursor fix is not applied")
    
    # Check login issues fix
    print("\n🔍 CHECKING LOGIN ISSUES FIX\n")
    
    middleware_path = 'accounts/middleware/session_timeout.py'
    if os.path.exists(middleware_path):
        print("✅ Session timeout middleware exists")
    else:
        print("❌ Session timeout middleware not found")
    
    settings_path = 'kampala_pharma/settings.py'
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            content = f.read()
        if "accounts.middleware.session_timeout" in content:
            print("✅ Session timeout middleware is included in settings")
        else:
            print("❌ Session timeout middleware is not included in settings")
        if "SESSION_TIMEOUT" in content:
            print("✅ Session timeout setting is configured")
        else:
            print("❌ Session timeout setting is not configured")

    print("\n✨ VERIFICATION COMPLETE\n")
    print("Please test the system with the following steps:")
    print("1. Try logging in to ensure session management works correctly")
    print("2. Complete a material release phase for a tablet type 2 product")
    print("3. Verify that the next phase is correctly shown as 'Bulk Packing'")
    print("4. Check that the user dropdown cursor changes to a pointer when hovering")

if __name__ == "__main__":
    verify_tablet_workflow()
