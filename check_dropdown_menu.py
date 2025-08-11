"""
Script to verify the user dropdown menu functionality.
This script checks the HTML template and ensures that:
1. The dropdown menu has correct Bootstrap 5.3+ markup
2. All required JavaScript is loaded in the correct order
3. The proper aria attributes are used for accessibility
"""
import os
import sys
import django
import re

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def check_template_file(file_path):
    """Check the template file for proper dropdown markup"""
    print(f"Checking template: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check for Bootstrap 5.3
    if 'bootstrap@5.3' not in content:
        issues.append("⚠️ Bootstrap version should be 5.3+")
    
    # Check for jQuery loading before Bootstrap
    jquery_pos = content.find('jquery')
    bootstrap_pos = content.find('bootstrap.bundle')
    if jquery_pos > bootstrap_pos and bootstrap_pos != -1:
        issues.append("⚠️ jQuery should be loaded before Bootstrap")
    
    # Check for proper dropdown markup
    dropdown_toggle = re.search(r'<a[^>]*class="[^"]*dropdown-toggle[^"]*"[^>]*>', content)
    if not dropdown_toggle:
        issues.append("⚠️ No dropdown-toggle element found")
    
    # Check for data-bs-toggle attribute
    if 'data-bs-toggle="dropdown"' not in content:
        issues.append("⚠️ Missing data-bs-toggle=\"dropdown\" attribute")
    
    # Check for aria-expanded attribute
    if 'aria-expanded=' not in content:
        issues.append("⚠️ Missing aria-expanded attribute for accessibility")
    
    # Check for proper dropdown menu
    dropdown_menu = re.search(r'<ul[^>]*class="[^"]*dropdown-menu[^"]*"[^>]*>', content)
    if not dropdown_menu:
        issues.append("⚠️ No dropdown-menu element found")
    
    # Check for right-aligned dropdown (Bootstrap 5.3+)
    if 'dropdown-menu-end' not in content:
        issues.append("⚠️ Missing dropdown-menu-end class for right alignment")
    
    # Check for aria-labelledby
    if 'aria-labelledby="userDropdown"' not in content:
        issues.append("⚠️ Missing aria-labelledby attribute for accessibility")
    
    # Check for JavaScript initialization
    if 'bootstrap.Dropdown' not in content:
        issues.append("⚠️ Missing Bootstrap Dropdown JavaScript initialization")
    
    # Print results
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ All checks passed!")
    
    # Check for logout link
    logout_link = re.search(r'href="[^"]*logout[^"]*"', content)
    if logout_link:
        print(f"✅ Logout link found: {logout_link.group(0)}")
    else:
        print("⚠️ No logout link found")
    
    return len(issues) == 0

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'dashboards', 'dashboard_base.html')
    
    if os.path.exists(template_path):
        success = check_template_file(template_path)
        if success:
            print("\n✨ DROPDOWN MENU IS PROPERLY CONFIGURED")
            print("The user dropdown menu should now work correctly when clicked.")
        else:
            print("\n⚠️ DROPDOWN MENU CONFIGURATION HAS ISSUES")
            print("Please address the issues listed above.")
    else:
        print(f"❌ Template file not found: {template_path}")
