import os
import django
import json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kampala_pharma.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from django.test import RequestFactory
from dashboards.views import admin_dashboard

print("=== ADMIN DASHBOARD CHART DATA TEST ===\n")

# Get an existing admin user
User = get_user_model()
try:
    # Try to get any superuser
    user = User.objects.filter(is_superuser=True).first()
    if user:
        print(f"Using existing superuser: {user.username}")
    else:
        # If no superuser exists, try to get a staff user
        user = User.objects.filter(is_staff=True).first()
        if user:
            print(f"Using existing staff user: {user.username}")
        else:
            # If no staff user exists, use any user
            user = User.objects.first()
            if user:
                print(f"Using existing user: {user.username}")
                user.is_staff = True
                user.save()
                print(f"Granted staff permissions to user: {user.username}")
            else:
                print("No users found in the database.")
                import sys
                sys.exit(1)
except Exception as e:
    print(f"Error finding user: {str(e)}")
    import sys
    sys.exit(1)

# Test the admin dashboard view
print("\nTesting chart data in admin dashboard...")
factory = RequestFactory()
request = factory.get(reverse('dashboards:admin_dashboard'))
request.user = user

try:
    # Execute the view and get the response
    response = admin_dashboard(request)
    
    # Get context data
    context = {}
    if hasattr(response, 'context_data'):
        context = response.context_data
    elif hasattr(response, 'context'):
        context = response.context
    
    # Chart data - Product Types
    print("\n📊 PRODUCT TYPE DATA:")
    tablet_count = context.get('tablet_count', 0)
    capsule_count = context.get('capsule_count', 0)
    ointment_count = context.get('ointment_count', 0)
    print(f"   Tablets: {tablet_count}")
    print(f"   Capsules: {capsule_count}")
    print(f"   Ointments: {ointment_count}")
    
    # Phase completion data
    print("\n🔄 PHASE COMPLETION DATA:")
    phase_data = {}
    for key in context:
        if key.endswith('_completed') or key.endswith('_inprogress'):
            phase_data[key] = context[key]
    
    phases = ['mixing', 'drying', 'granulation', 'compression', 'packing']
    for phase in phases:
        completed = phase_data.get(f"{phase}_completed", 0)
        in_progress = phase_data.get(f"{phase}_inprogress", 0)
        print(f"   {phase.title()}: {completed} completed, {in_progress} in progress")
    
    # Weekly production trend data
    print("\n📈 WEEKLY PRODUCTION TREND:")
    weekly_data = context.get('weekly_data', {})
    if weekly_data:
        for i in range(1, 5):
            started = weekly_data.get(f"started_week{i}", 0)
            completed = weekly_data.get(f"completed_week{i}", 0)
            print(f"   Week {i}: {started} batches started, {completed} batches completed")
    else:
        print("   No weekly data available")
    
    # Quality Control data
    print("\n🧪 QUALITY CONTROL STATUS:")
    qc_data = context.get('qc_data', {})
    if qc_data:
        passed = qc_data.get('passed', 0)
        failed = qc_data.get('failed', 0)
        pending = qc_data.get('pending', 0)
        total = passed + failed + pending
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"   Passed: {passed} ({pass_rate:.1f}%)")
        print(f"   Failed: {failed} ({(failed / total * 100) if total > 0 else 0:.1f}%)")
        print(f"   Pending: {pending} ({(pending / total * 100) if total > 0 else 0:.1f}%)")
    else:
        print("   No QC data available")
    
    print("\n✅ CHART DATA VERIFICATION:")
    all_data_present = True
    
    # Check product type data
    if tablet_count == 0 and capsule_count == 0 and ointment_count == 0:
        print("   ❌ Missing product type data")
        all_data_present = False
    else:
        print("   ✓ Product type data available")
    
    # Check phase data
    if not phase_data:
        print("   ❌ Missing phase completion data")
        all_data_present = False
    else:
        print("   ✓ Phase completion data available")
    
    # Check weekly data
    if not weekly_data:
        print("   ❌ Missing weekly trend data")
        all_data_present = False
    else:
        print("   ✓ Weekly trend data available")
    
    # Check QC data
    if not qc_data:
        print("   ❌ Missing quality control data")
        all_data_present = False
    else:
        print("   ✓ Quality control data available")
    
    if all_data_present:
        print("\n🎉 All chart data is available for rendering!")
    else:
        print("\n⚠️  Some chart data is missing. Check for template or JavaScript errors.")
    
except Exception as e:
    print(f"\n❌ Error testing admin dashboard: {str(e)}")
    import traceback
    traceback.print_exc()

print("\nTest completed.")
