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

# Open a log file
log_file = open('template_debug.log', 'w')
log_file.write("Starting template debug\n")

try:
    # Try to load and render the template
    log_file.write("Attempting to load template...\n")
    template = get_template('dashboards/finished_goods_dashboard.html')
    log_file.write("Template loaded successfully!\n")
    print("Template loaded successfully!")
    
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
    log_file.write("Template rendered successfully!\n")
    print("Template rendered successfully!")
    
    # Write rendered content to file for inspection
    with open('rendered_template.html', 'w', encoding='utf-8') as f:
        f.write(rendered)
    log_file.write("Rendered template saved to file 'rendered_template.html'\n")
    
except Exception as e:
    error_msg = f"Error loading or rendering template: {e}"
    log_file.write(error_msg + "\n")
    print(error_msg)
    # Print more detailed traceback
    import traceback
    tb = traceback.format_exc()
    log_file.write(tb + "\n")
    traceback.print_exc()

finally:
    log_file.close()
