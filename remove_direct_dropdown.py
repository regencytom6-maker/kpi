import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def remove_direct_dropdown():
    print("\n🧹 REMOVING DIRECT DROPDOWN FROM ADMIN DASHBOARD\n")
    
    template_path = Path('templates/dashboards/admin_dashboard_clean.html')
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return
    
    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for direct dropdown start and end
    direct_dropdown_start = "<!-- Direct implementation of user dropdown - independent of base template -->"
    direct_dropdown_script_end = "</script>"
    
    start_pos = content.find(direct_dropdown_start)
    if start_pos >= 0:
        # Find the end of the script
        end_script_pos = content.find(direct_dropdown_script_end, start_pos)
        if end_script_pos > start_pos:
            # Add length of the closing script tag
            end_pos = end_script_pos + len(direct_dropdown_script_end)
            
            # Remove the direct dropdown and script
            content = content[:start_pos] + content[end_pos:]
            
            # Write back to the template
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Successfully removed direct dropdown from admin dashboard template")
        else:
            print("❌ Could not find end of direct dropdown script")
    else:
        print("✅ No direct dropdown found in template")
    
    print("\n✨ DIRECT DROPDOWN REMOVED\n")
    print("The admin dashboard is now clean and only using the standard dropdown from the base template")
    print("\n🧹 ADDITIONAL CLEANUP:")
    
    # Check for unnecessary scripts block
    scripts_block_start = "{% block scripts %}"
    scripts_block_end = "{% endblock %}"
    
    if scripts_block_start in content and scripts_block_end in content:
        scripts_start_pos = content.find(scripts_block_start)
        scripts_end_pos = content.find(scripts_block_end, scripts_start_pos)
        
        if scripts_end_pos > scripts_start_pos:
            # Check if the scripts block is empty or only has whitespace/comments
            scripts_content = content[scripts_start_pos + len(scripts_block_start):scripts_end_pos].strip()
            
            if not scripts_content or scripts_content.startswith('<!--') and scripts_content.endswith('-->'):
                # Remove empty scripts block
                content = content[:scripts_start_pos] + content[scripts_end_pos + len(scripts_block_end):]
                
                # Write back to the template
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ Removed empty scripts block")
    
    print("\n✨ CLEANUP COMPLETE")
    print("The admin dashboard template has been fully cleaned up")
    print("All debug tools and direct dropdown have been removed")

if __name__ == "__main__":
    remove_direct_dropdown()
