import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def final_dashboard_cleanup():
    """Final dashboard cleanup to remove debug controls and fix logout"""
    template_path = 'templates/dashboards/admin_dashboard_clean.html'
    backup_path = 'templates/dashboards/admin_dashboard_clean_backup_final_cleanup.html'
    
    # Create backup
    if os.path.exists(template_path):
        with open(template_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Backup created at {backup_path}")
    
    # Read template content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Remove the debug script completely
    debug_script_start = content.find('<script>\n    // Debug script for dashboard charts')
    if debug_script_start > 0:
        # Find the corresponding end script tag
        debug_script_end = content.find('</script>', debug_script_start)
        if debug_script_end > debug_script_start:
            debug_script_end += len('</script>')
            content = content[:debug_script_start] + content[debug_script_end:]
            print("Removed debug script")
    else:
        print("Debug script not found")
    
    # Also make sure there are no other debug controls
    debug_controls_code = """
        // Add debug controls
        const controls = document.createElement('div');"""
    
    if debug_controls_code in content:
        # Find the start of debug controls code
        controls_start = content.find(debug_controls_code)
        if controls_start > 0:
            # Find where the function createFallbackCharts ends
            fallback_fn_start = content.find("function createFallbackCharts()", controls_start)
            if fallback_fn_start > controls_start:
                # Find the end of this function by counting braces
                brace_count = 0
                in_function = False
                fallback_fn_end = fallback_fn_start
                
                for i in range(fallback_fn_start, len(content)):
                    if content[i] == '{':
                        in_function = True
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if in_function and brace_count == 0:
                            fallback_fn_end = i + 1
                            break
                
                if fallback_fn_end > fallback_fn_start:
                    # Remove all debug controls code
                    content = content[:controls_start] + content[fallback_fn_end:]
                    print("Removed debug controls and fallback function")
                else:
                    print("Could not find end of fallback function")
            else:
                print("Could not find fallback function")
        else:
            print("Could not find debug controls code start")
    
    # Remove any other instances of debug panel controls
    panel_code = """
    // Add a control panel for debugging
    const debugPanel = document.createElement('div');"""
    
    if panel_code in content:
        panel_start = content.find(panel_code)
        if panel_start > 0:
            # Find the end of this panel creation and event listeners
            panel_end = content.find("});", panel_start)
            if panel_end > panel_start:
                # Look for end of event listener block
                panel_end += 3
                content = content[:panel_start] + content[panel_end:]
                print("Removed debug panel code")
            else:
                print("Could not find end of debug panel code")
        else:
            print("Could not find debug panel start")
    
    # Fix title block which might have script in it
    if '{% block title %}Admin Dashboard - Kampala Pharmaceutical Industries' in content:
        if '<script>' in content[:500]:  # Check beginning of file
            # Find the block title and fix it
            title_start = content.find('{% block title %}')
            title_end = content.find('{% endblock %}', title_start)
            if title_end > title_start:
                # Replace with clean title
                new_title = '{% block title %}Admin Dashboard - Kampala Pharmaceutical Industries{% endblock %}'
                content = content[:title_start] + new_title + content[title_end + len('{% endblock %}'):]
                print("Fixed title block")
            else:
                print("Could not find end of title block")
    
    # Write the updated content
    with open(template_path, 'w') as f:
        f.write(content)
    
    print("Template cleaned up successfully")
    
    # Now check and fix logout functionality in dashboard_base.html if needed
    base_template_path = 'templates/dashboards/dashboard_base.html'
    if os.path.exists(base_template_path):
        with open(base_template_path, 'r') as f:
            base_content = f.read()
        
        # Check for logout URL and fix if needed
        if "href=\"{% url 'accounts:logout' %}\"" in base_content:
            print("Logout URL seems correct")
        else:
            # Look for any logout link that might be broken
            logout_patterns = ["href=\"logout\"", "href=\"/logout\"", "href=\"#\""]
            
            for pattern in logout_patterns:
                if pattern in base_content:
                    base_content = base_content.replace(pattern, "href=\"{% url 'accounts:logout' %}\"")
                    print(f"Fixed logout link from {pattern}")
                    break
            
            with open(base_template_path, 'w') as f:
                f.write(base_content)

if __name__ == "__main__":
    final_dashboard_cleanup()
