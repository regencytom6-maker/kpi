import os
import sys
import django
from django.template import Template, Context
from django.template.loader import get_template
from django.conf import settings

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kampala_pharma.settings")
django.setup()

print("Django setup complete")

# Open a log file
with open('template_debug.log', 'w') as log_file:
    log_file.write("Starting template debug\n")
    
    try:
        log_file.write("Checking if template exists...\n")
        template_path = os.path.join(settings.BASE_DIR, 'templates', 'dashboards', 'finished_goods_dashboard.html')
        if os.path.exists(template_path):
            log_file.write(f"Template file exists at path: {template_path}\n")
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                log_file.write(f"Template content length: {len(template_content)} bytes\n")
                log_file.write(f"Template first 100 characters: {template_content[:100]}\n")
        else:
            log_file.write(f"Template file DOES NOT EXIST at path: {template_path}\n")
            
        # Try to load the template
        log_file.write("Attempting to load template...\n")
        template = get_template('dashboards/finished_goods_dashboard.html')
        log_file.write("Template loaded successfully!\n")
        
        # Basic context for testing
        context = {
            'user': {'get_full_name': lambda: 'Test User', 'username': 'testuser', 'get_role_display': 'Finished Goods Store'},
            'stats': {
                'pending_phases': 5,
                'in_progress_phases': 3,
                'completed_today': 10,
                'total_batches': 50,
                'daily_history': {'Mon': 5, 'Tue': 7, 'Wed': 3, 'Thu': 8, 'Fri': 10, 'Sat': 2, 'Sun': 0},
                'product_types': {'tablet': 20, 'capsule': 15, 'liquid': 10, 'ointment': 5},
            },
            'daily_progress': 75,
            'my_phases': [],
            'detail_view': None,
            'detail_title': None,
        }
        
        # Try to render the template
        log_file.write("Attempting to render template...\n")
        rendered = template.render(context)
        log_file.write(f"Template rendered successfully! Output length: {len(rendered)} bytes\n")
        
        # Write rendered content to file for inspection
        with open('rendered_template.html', 'w', encoding='utf-8') as f:
            f.write(rendered)
        log_file.write("Rendered template saved to file 'rendered_template.html'\n")
        
        # Check for possible JS issues
        if "{% for" in template_content or "%}" in template_content:
            log_file.write("WARNING: Unprocessed template tags found in output. This suggests template processing issues.\n")
            
    except Exception as e:
        error_msg = f"Error loading or rendering template: {e}"
        log_file.write(error_msg + "\n")
        # Print more detailed traceback
        import traceback
        tb = traceback.format_exc()
        log_file.write(tb + "\n")
        print(error_msg)

print("Debug complete, check template_debug.log for details")
