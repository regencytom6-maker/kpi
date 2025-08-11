import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.template.loader import render_to_string
from django.template import RequestContext
from django.test.client import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

def render_admin_dashboard_with_user():
    print("\n🔍 DEBUGGING ADMIN DASHBOARD TEMPLATE RENDERING\n")
    
    try:
        # Get admin user
        admin_user = User.objects.filter(is_staff=True).first()
        if admin_user:
            print(f"✅ Found admin user: {admin_user.username}")
        else:
            print("❌ No admin user found, creating mock user")
            admin_user = User(username="admin_test", is_staff=True)
        
        # Create request with user
        factory = RequestFactory()
        request = factory.get('/')
        request.user = admin_user
        
        # Render the admin dashboard template
        try:
            # Try rendering with request context
            from django.template import engines
            django_engine = engines['django']
            
            admin_template = django_engine.get_template('dashboards/admin_dashboard_clean.html')
            print("✅ Successfully loaded template")
            
            context = {'user': admin_user}  # Basic context
            rendered_html = admin_template.render(context, request)
            
            # Check if userDropdown exists
            if 'id="userDropdown"' in rendered_html:
                print("✅ userDropdown element found in the rendered template")
            else:
                print("❌ userDropdown element NOT found in rendered template")
                
            # Check if any blocks were skipped/overridden
            if "{% block" in rendered_html:
                print("❌ Template tags found in rendered output - this indicates template not rendering properly")
            else:
                print("✅ No raw template tags in rendered output")
            
            # Find what's actually in the navbar area
            if '<nav class="navbar' in rendered_html:
                start_idx = rendered_html.find('<nav class="navbar')
                end_idx = rendered_html.find('</nav>', start_idx)
                if end_idx > start_idx:
                    navbar_html = rendered_html[start_idx:end_idx+6]
                    print("\n📋 NAVBAR HTML SNIPPET:")
                    print(navbar_html[:500] + "..." if len(navbar_html) > 500 else navbar_html)
                else:
                    print("❌ Navbar tag found but couldn't extract complete HTML")
            else:
                print("❌ No navbar found in the rendered HTML")
            
            print("\n💡 SOLUTION STRATEGY:")
            print("1. Fix the admin_dashboard_clean.html template structure:")
            print("   - Ensure it extends 'dashboards/dashboard_base.html'")
            print("   - Make sure content block doesn't override navbar")
            print("   - Check for custom blocks that conflict with base template")
            print("\n2. Add a custom block in dashboard_base.html for the navbar:")
            print("   {% block navbar %}... navbar code ...{% endblock %}")
            print("   Then make sure admin_dashboard_clean.html doesn't override this block")
            
            print("\n3. Fix the issue with one direct update:")
            print("   Create a fix_admin_dropdown.py script that adds the correct navbar")
            
        except Exception as e:
            print(f"❌ Error rendering template: {e}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    render_admin_dashboard_with_user()
