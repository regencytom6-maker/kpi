import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def remove_debug_tools():
    print("\n🧹 REMOVING DEBUG TOOLS FROM ADMIN DASHBOARD\n")
    
    template_path = Path('templates/dashboards/admin_dashboard_clean.html')
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return
    
    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for debug panel start and end
    debug_panel_start = "<!-- Debug dropdown structure - identical but with different ID -->"
    debug_script_end = "</script>"
    
    start_pos = content.find(debug_panel_start)
    if start_pos >= 0:
        # Find the end of the debug script
        end_script_pos = content.find(debug_script_end, start_pos)
        if end_script_pos > start_pos:
            # Add length of the closing script tag
            end_pos = end_script_pos + len(debug_script_end)
            
            # Remove the debug panel and script
            content = content[:start_pos] + content[end_pos:]
            
            # Write back to the template
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Successfully removed debug tools from admin dashboard template")
        else:
            print("❌ Could not find end of debug script")
    else:
        print("✅ No debug tools found in template")
    
    print("\n✨ DEBUG TOOLS REMOVED\n")
    print("The admin dashboard should now be clean of any debug controls")

if __name__ == "__main__":
    remove_debug_tools()
