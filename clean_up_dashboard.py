import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def clean_up_dashboard():
    """Remove debug controls from the admin dashboard template"""
    template_path = 'templates/dashboards/admin_dashboard_clean.html'
    backup_path = 'templates/dashboards/admin_dashboard_clean_backup_final.html'
    
    # Create backup
    if os.path.exists(template_path):
        with open(template_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Backup created at {backup_path}")
    
    # Read template content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Remove the debug controls div
    debug_control_pattern = 'Chart Debug Controls'
    if debug_control_pattern in content:
        # Find the debug panel div
        debug_panel_start = content.find('// Add a control panel for debugging')
        if debug_panel_start > 0:
            # Find the end of the debug panel code
            debug_panel_end = content.find('document.body.appendChild(debugPanel);', debug_panel_start)
            # Find the end of the related event listener
            event_listener_end = content.find('});', debug_panel_end)
            if debug_panel_end > debug_panel_start and event_listener_end > debug_panel_end:
                # Find the next closing brace after the event listener
                next_brace = content.find('});', event_listener_end + 3)
                if next_brace > event_listener_end:
                    # Remove the debug panel and its event listener
                    content = content[:debug_panel_start] + '// Debug controls removed for production\n' + content[next_brace+3:]
                    print("Debug panel removed successfully")
                else:
                    print("Could not find the end of event listener code")
            else:
                print("Could not find debug panel code boundaries")
        else:
            print("Could not find debug panel start")
    else:
        print("Debug controls not found in template")
        
    # Also remove any other debug-related elements
    content = content.replace('<div id="debugInfo" style="display: none;">', '<!-- Debug info removed -->')
    content = content.replace('id="reinitCharts" class="btn btn-sm btn-primary"', 'style="display:none;"')
    
    # Write the updated content
    with open(template_path, 'w') as f:
        f.write(content)
    
    print("Template cleaned up successfully")

if __name__ == "__main__":
    clean_up_dashboard()
