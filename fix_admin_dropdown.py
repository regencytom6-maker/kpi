import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def fix_admin_dropdown_js():
    print("\n🔧 FIXING ADMIN DASHBOARD DROPDOWN\n")
    
    template_path = Path('templates/dashboards/admin_dashboard_clean.html')
    backup_path = Path('templates/dashboards/admin_dashboard_clean_backup_dropdown.html')
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return
    
    # Create backup
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created backup at {backup_path}")
    
    # Check if the admin template has script block
    script_block_start = "{% block scripts %}"
    has_script_block = script_block_start in content
    
    # Find where to insert our dropdown fix
    if has_script_block:
        print("✅ Found scripts block in the template")
        script_block_pos = content.find(script_block_start)
        # Find the end of the block or the end of the file
        script_block_end = content.find("{% endblock %}", script_block_pos)
        
        if script_block_end > script_block_pos:
            insertion_point = script_block_pos + len(script_block_start)
            
            # Create the dropdown fix script
            dropdown_fix = """
<!-- Dropdown Fix Script -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Dashboard Dropdown Fix loaded');
    
    // Find the user dropdown toggle
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        console.log('Found userDropdown element:', userDropdown);
        
        // Direct event listener
        userDropdown.addEventListener('click', function(e) {
            console.log('User dropdown clicked');
            e.preventDefault();
            
            // Get dropdown menu
            const dropdownMenu = document.querySelector('[aria-labelledby="userDropdown"]');
            if (dropdownMenu) {
                // Toggle show class manually
                dropdownMenu.classList.toggle('show');
                
                // Update aria-expanded attribute
                const isExpanded = dropdownMenu.classList.contains('show');
                userDropdown.setAttribute('aria-expanded', isExpanded);
                
                // Position the dropdown correctly
                if (isExpanded) {
                    dropdownMenu.style.position = 'absolute';
                    dropdownMenu.style.inset = '0px auto auto 0px';
                    dropdownMenu.style.transform = 'translate3d(0px, 40px, 0px)';
                }
                
                console.log('Toggled dropdown visibility:', isExpanded);
                
                // Close dropdown when clicking outside
                if (isExpanded) {
                    const closeDropdownOnClick = function(event) {
                        if (!dropdownMenu.contains(event.target) && event.target !== userDropdown) {
                            dropdownMenu.classList.remove('show');
                            userDropdown.setAttribute('aria-expanded', 'false');
                            document.removeEventListener('click', closeDropdownOnClick);
                        }
                    };
                    
                    // Add listener with slight delay to avoid immediate trigger
                    setTimeout(() => {
                        document.addEventListener('click', closeDropdownOnClick);
                    }, 10);
                }
            } else {
                console.error('Dropdown menu not found');
            }
        });
        
        console.log('Added click handler to userDropdown');
    } else {
        console.error('userDropdown element not found in DOM');
    }
    
    // Check Bootstrap version and availability
    if (typeof bootstrap !== 'undefined') {
        console.log('Bootstrap version:', bootstrap.Dropdown.VERSION || 'Unknown');
    } else {
        console.error('Bootstrap not loaded!');
    }
});
</script>
"""
            # Insert the dropdown fix
            modified_content = content[:insertion_point] + dropdown_fix + content[insertion_point:]
            
            # Write the modified content
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
                
            print("✅ Added dropdown fix script to the admin dashboard template")
        else:
            print("❌ Couldn't find the end of scripts block")
    else:
        print("❌ No scripts block found in the template")
        # Add scripts block at the end of the file before the last endblock
        last_endblock_pos = content.rfind("{% endblock %}")
        
        if last_endblock_pos > 0:
            # Add scripts block before the last endblock
            script_block = """

{% block scripts %}
<!-- Dropdown Fix Script -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Dashboard Dropdown Fix loaded');
    
    // Find the user dropdown toggle
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        console.log('Found userDropdown element:', userDropdown);
        
        // Direct event listener
        userDropdown.addEventListener('click', function(e) {
            console.log('User dropdown clicked');
            e.preventDefault();
            
            // Get dropdown menu
            const dropdownMenu = document.querySelector('[aria-labelledby="userDropdown"]');
            if (dropdownMenu) {
                // Toggle show class manually
                dropdownMenu.classList.toggle('show');
                
                // Update aria-expanded attribute
                const isExpanded = dropdownMenu.classList.contains('show');
                userDropdown.setAttribute('aria-expanded', isExpanded);
                
                // Position the dropdown correctly
                if (isExpanded) {
                    dropdownMenu.style.position = 'absolute';
                    dropdownMenu.style.inset = '0px auto auto 0px';
                    dropdownMenu.style.transform = 'translate3d(0px, 40px, 0px)';
                }
                
                console.log('Toggled dropdown visibility:', isExpanded);
                
                // Close dropdown when clicking outside
                if (isExpanded) {
                    const closeDropdownOnClick = function(event) {
                        if (!dropdownMenu.contains(event.target) && event.target !== userDropdown) {
                            dropdownMenu.classList.remove('show');
                            userDropdown.setAttribute('aria-expanded', 'false');
                            document.removeEventListener('click', closeDropdownOnClick);
                        }
                    };
                    
                    // Add listener with slight delay to avoid immediate trigger
                    setTimeout(() => {
                        document.addEventListener('click', closeDropdownOnClick);
                    }, 10);
                }
            } else {
                console.error('Dropdown menu not found');
            }
        });
        
        console.log('Added click handler to userDropdown');
    } else {
        console.error('userDropdown element not found in DOM');
    }
    
    // Check Bootstrap version and availability
    if (typeof bootstrap !== 'undefined') {
        console.log('Bootstrap version:', bootstrap.Dropdown.VERSION || 'Unknown');
    } else {
        console.error('Bootstrap not loaded!');
    }
});
</script>
{% endblock %}

"""
            modified_content = content[:last_endblock_pos] + script_block + content[last_endblock_pos:]
            
            # Write the modified content
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
                
            print("✅ Added dropdown fix script block to the admin dashboard template")
        else:
            print("❌ Couldn't find a suitable place to add scripts block")
    
    print("\n🔍 SUMMARY:")
    print("1. Added manual dropdown initialization for the admin dashboard")
    print("2. This should fix the dropdown menu not working on the admin dashboard")
    print("3. Test by running the Django server and visiting the admin dashboard")
    print("\n✨ RECOMMENDATION: Run 'python manage.py runserver' and test the fix")

if __name__ == "__main__":
    fix_admin_dropdown_js()
