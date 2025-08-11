import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.template import Context, Template

User = get_user_model()

# Check if we can find the userDropdown element in admin dashboard
def check_admin_dropdown():
    print("\n🔍 CHECKING ADMIN DASHBOARD DROPDOWN CONFIGURATION\n")
    
    # Load the admin_dashboard_clean.html template
    try:
        template_path = "dashboards/admin_dashboard_clean.html"
        # This will use Django's template loader with all template directories
        rendered_html = render_to_string(template_path, {})
        
        print(f"✅ Successfully loaded template: {template_path}")
        
        # Check if userDropdown exists in the rendered template
        if 'id="userDropdown"' in rendered_html:
            print("✅ Found userDropdown element in the template")
        else:
            print("❌ userDropdown element NOT found in the template")
            print("\nProblem detected: The admin dashboard is missing the userDropdown element.")
            print("This could be caused by:")
            print("1. The navbar section in dashboard_base.html is being overridden")
            print("2. The template hierarchy isn't extending properly")
            
        # Check for bootstrap dropdown JavaScript
        bootstrap_script_check = 'bootstrap.bundle.min.js' in rendered_html or 'bootstrap.min.js' in rendered_html
        if bootstrap_script_check:
            print("✅ Bootstrap JS is included")
        else:
            print("❌ Bootstrap JS is NOT found in the rendered HTML")
        
        # Check for jQuery
        jquery_check = 'jquery' in rendered_html.lower()
        if jquery_check:
            print("✅ jQuery is included")
        else:
            print("❌ jQuery is NOT found in the rendered HTML")
        
        # Check for dropdown initialization script
        dropdown_init = 'bootstrap.Dropdown' in rendered_html
        if dropdown_init:
            print("✅ Dropdown initialization code is present")
        else:
            print("❌ Dropdown initialization code is NOT found")
            
        # Check if the admin dashboard is extending the base template correctly
        if '{% extends' in rendered_html or 'extends' in rendered_html:
            print("❓ Template extension syntax may be rendered as text - unexpected")
        
        # Look at the actual HTML structure of the dropdown menu
        import re
        dropdown_pattern = re.compile(r'<div class="dropdown".*?</div>', re.DOTALL)
        dropdown_matches = dropdown_pattern.findall(rendered_html)
        
        if dropdown_matches:
            print("\n📋 Found dropdown structure(s):")
            for i, match in enumerate(dropdown_matches):
                print(f"\nDropdown #{i+1}:")
                print(match[:200] + "..." if len(match) > 200 else match)
        else:
            print("\n❌ No dropdown structure found in the HTML")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Now check the base template
    print("\n🔍 CHECKING BASE TEMPLATE\n")
    try:
        base_template_path = "dashboards/dashboard_base.html"
        base_html = render_to_string(base_template_path, {})
        
        print(f"✅ Successfully loaded base template: {base_template_path}")
        
        # Check if userDropdown exists in the base template
        if 'id="userDropdown"' in base_html:
            print("✅ Found userDropdown element in the base template")
        else:
            print("❌ userDropdown element NOT found in the base template")
            
        # Check for scripts section in the base template
        if '<script>' in base_html:
            print("✅ Found script tags in base template")
        else:
            print("❌ No script tags found in base template")
            
        print("\n📋 SOLUTION RECOMMENDATIONS:")
        print("1. Make sure admin_dashboard_clean.html correctly extends dashboard_base.html")
        print("2. Ensure {% block content %} isn't overriding the navbar section")
        print("3. Check for conflicting JavaScript in the admin template")
        print("4. Verify the dropdown HTML structure is properly closed")
        print("5. Make sure Chart.js isn't conflicting with Bootstrap")
        print("6. Consider using separate {% block navbar %} to allow proper extension")
        
    except Exception as e:
        print(f"❌ Error checking base template: {e}")

if __name__ == "__main__":
    check_admin_dropdown()
