import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def final_dropdown_fix():
    print("\n🔧 APPLYING FINAL DROPDOWN FIX\n")
    
    base_template_path = Path('templates/dashboards/dashboard_base.html')
    
    if not base_template_path.exists():
        print(f"❌ Base template file not found: {base_template_path}")
        return
    
    # Read the base template
    with open(base_template_path, 'r', encoding='utf-8') as f:
        base_content = f.read()
    
    # Ensure Bootstrap JS is included correctly
    bootstrap_script = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>'
    if bootstrap_script not in base_content:
        print("❌ Bootstrap script not found in base template")
        
        # Find a good spot to add it
        scripts_pos = base_content.find('<script src="https://code.jquery.com/jquery')
        if scripts_pos > 0:
            # Add after jQuery
            jquery_script_end = base_content.find('</script>', scripts_pos) + 9
            if jquery_script_end > scripts_pos:
                base_content = base_content[:jquery_script_end] + '\n    ' + bootstrap_script + base_content[jquery_script_end:]
                print("✅ Added Bootstrap script to base template")
    else:
        print("✅ Bootstrap script already present in base template")
    
    # Ensure the dropdown initialization is working
    dropdown_init = """
    <!-- Custom JavaScript for dropdown functionality -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize all dropdowns using Bootstrap's API
            var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
            var dropdownList = dropdownElementList.map(function(element) {
                return new bootstrap.Dropdown(element);
            });
            
            // Add explicit click handler for user dropdown
            const userDropdown = document.getElementById('userDropdown');
            if (userDropdown) {
                userDropdown.addEventListener('click', function(e) {
                    e.stopPropagation();
                    
                    // Create dropdown instance if not already created
                    var dropdownInstance = bootstrap.Dropdown.getInstance(userDropdown);
                    if (!dropdownInstance) {
                        dropdownInstance = new bootstrap.Dropdown(userDropdown);
                    }
                    
                    // Toggle the dropdown
                    dropdownInstance.toggle();
                    
                    console.log('User dropdown clicked');
                });
            }
        });
    </script>
    """
    
    # Check if the dropdown initialization exists
    if "Custom JavaScript for dropdown functionality" in base_content:
        # Replace the existing initialization with our enhanced version
        start_comment = "<!-- Custom JavaScript for dropdown functionality -->"
        start_pos = base_content.find(start_comment)
        if start_pos > 0:
            end_comment = "</script>"
            end_pos = base_content.find(end_comment, start_pos) + len(end_comment)
            
            if end_pos > start_pos:
                # Replace with our enhanced version
                base_content = base_content[:start_pos] + dropdown_init + base_content[end_pos:]
                print("✅ Updated dropdown initialization in base template")
    else:
        # Add the dropdown initialization
        scripts_end = base_content.find('{% block scripts %}')
        if scripts_end > 0:
            base_content = base_content[:scripts_end] + dropdown_init + '\n    ' + base_content[scripts_end:]
            print("✅ Added dropdown initialization to base template")
    
    # Write the updated base content
    with open(base_template_path, 'w', encoding='utf-8') as f:
        f.write(base_content)
    
    print("\n✨ FINAL FIX APPLIED")
    print("The dropdown should now work reliably on all dashboards including admin")
    print("You can verify by restarting the server and checking the admin dashboard")

if __name__ == "__main__":
    final_dropdown_fix()
