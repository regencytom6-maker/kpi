import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def update_template():
    """Update the template to use the inline chart.js file"""
    template_path = 'templates/dashboards/admin_dashboard_clean.html'
    backup_path = 'templates/dashboards/admin_dashboard_clean_backup_inline.html'
    
    # Create backup
    if os.path.exists(template_path):
        with open(template_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Backup created at {backup_path}")
    
    # Read template content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Find where chart.js is included
    chart_js_tag = '<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>'
    
    if chart_js_tag in content:
        # Replace with inline chart.js reference
        new_tag = '<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>\n<script src="/static/js/inline-chart.js"></script>'
        
        # Remove any existing chart script tags
        content = content.replace('<script src="/static/js/chart_data.js"></script>', '')
        content = content.replace('<script src="{% static \'js/chart_data.js\' %}"></script>', '')
        content = content.replace('<script src="/static/js/chart_init.js"></script>', '')
        content = content.replace('<script src="{% static \'js/chart_init.js\' %}"></script>', '')
        
        # Add our new tag
        content = content.replace(chart_js_tag, new_tag)
        
        # Write the updated content
        with open(template_path, 'w') as f:
            f.write(content)
        
        print(f"Template updated to use inline-chart.js")
    else:
        print(f"Warning: Could not find Chart.js script tag in template")

if __name__ == "__main__":
    update_template()
