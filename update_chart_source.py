import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def update_admin_template_with_external_data():
    """Update the admin dashboard template to use external chart data file"""
    
    # First, create a backup if one doesn't exist
    if not os.path.exists('templates/dashboards/admin_dashboard_clean_backup.html'):
        with open('templates/dashboards/admin_dashboard_clean.html', 'r') as original:
            with open('templates/dashboards/admin_dashboard_clean_backup.html', 'w') as backup:
                backup.write(original.read())
        print("Backup created at templates/dashboards/admin_dashboard_clean_backup.html")
    
    # Read the current template
    with open('templates/dashboards/admin_dashboard_clean.html', 'r') as f:
        content = f.read()
    
    # Find where Chart.js is included and add our data file right after
    chart_js_tag = '<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>'
    data_js_tag = '<script src="/static/js/chart_data.js"></script>'
    
    if data_js_tag in content:
        print("External data file already included in template")
        return
    
    if chart_js_tag in content:
        content = content.replace(chart_js_tag, chart_js_tag + '\n' + data_js_tag)
    else:
        # Add at the top of the head section
        head_tag = '{% block extra_css %}'
        content = content.replace(head_tag, head_tag + '\n' + chart_js_tag + '\n' + data_js_tag)
    
    # Remove any old chart data variable declarations
    js_data_vars = [
        "const productData = {",
        "const phaseData = {",
        "const weeklyData = {", 
        "const qcData = {"
    ]
    
    for var_start in js_data_vars:
        if var_start in content:
            # Find the start and end of the variable declaration
            start_idx = content.find(var_start)
            if start_idx != -1:
                end_idx = content.find("};", start_idx) + 2
                if end_idx > start_idx:
                    # Replace with a comment
                    content = content.replace(content[start_idx:end_idx], 
                                             "// Using external data file: " + var_start.strip())
    
    # Write the updated content back
    with open('templates/dashboards/admin_dashboard_clean.html', 'w') as f:
        f.write(content)
    
    print("Admin dashboard template updated to use external chart data file")

def restore_original_template():
    """Restore the original admin dashboard template"""
    if os.path.exists('templates/dashboards/admin_dashboard_clean_backup.html'):
        with open('templates/dashboards/admin_dashboard_clean_backup.html', 'r') as backup:
            with open('templates/dashboards/admin_dashboard_clean.html', 'w') as original:
                original.write(backup.read())
        print("Original template restored from backup")
    else:
        print("No backup found - cannot restore")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_original_template()
    else:
        update_admin_template_with_external_data()
