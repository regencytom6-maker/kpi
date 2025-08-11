import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def comprehensive_admin_fix():
    print("\n🔧 COMPREHENSIVE ADMIN DASHBOARD FIX\n")
    
    template_path = Path('templates/dashboards/admin_dashboard_clean.html')
    backup_path = Path('templates/dashboards/admin_dashboard_clean_backup_comprehensive.html')
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return
    
    # Create backup
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created backup at {backup_path}")
    
    # 1. Check the template extends
    if "{% extends 'dashboards/dashboard_base.html' %}" not in content:
        print("❌ Template does not extend dashboard_base.html correctly")
        # Fix it
        if "{% extends" in content:
            content = content.replace("{% extends", "{% extends 'dashboards/dashboard_base.html' %}")
            print("✅ Fixed template extends")
        else:
            content = "{% extends 'dashboards/dashboard_base.html' %}\n" + content
            print("✅ Added template extends")
    else:
        print("✅ Template extends dashboard_base.html correctly")
    
    # 2. Fix Chart.js version conflicts
    if "chart.js" in content.lower() and "chart.min.js" in content.lower():
        # Remove any Chart.js scripts in the head
        start_tag = '<script src="https://cdn.jsdelivr.net/npm/chart.js'
        if start_tag in content:
            start_pos = content.find(start_tag)
            end_pos = content.find('</script>', start_pos) + 9
            if start_pos >= 0 and end_pos > start_pos:
                content = content[:start_pos] + content[end_pos:]
                print("✅ Removed duplicate Chart.js script from the template")
    
    # 3. Fix jQuery version conflicts
    if "jquery" in content.lower():
        # Remove any jQuery scripts
        jquery_tags = ['<script src="https://code.jquery.com/jquery', 
                      '<script src="https://ajax.googleapis.com/ajax/libs/jquery']
        
        for tag in jquery_tags:
            if tag in content:
                start_pos = content.find(tag)
                end_pos = content.find('</script>', start_pos) + 9
                if start_pos >= 0 and end_pos > start_pos:
                    content = content[:start_pos] + content[end_pos:]
                    print("✅ Removed duplicate jQuery script from the template")
    
    # 4. Check and fix content block
    content_block_start = "{% block content %}"
    content_block_end = "{% endblock %}"
    
    # Make sure we have a content block
    if content_block_start not in content:
        print("❌ Content block not found in template")
        # Try to find the main content and wrap it
        main_content_start = content.find('<div class="container')
        if main_content_start >= 0:
            # Insert content block before main content
            content = content[:main_content_start] + "\n" + content_block_start + "\n" + content[main_content_start:]
            # Add endblock at the end
            if content_block_end not in content:
                content = content + "\n" + content_block_end + "\n"
                print("✅ Added content block to template")
    else:
        print("✅ Content block exists in template")
    
    # 5. Add custom dropdown fix
    script_block_start = "{% block scripts %}"
    script_block_end = "{% endblock %}"
    
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
            e.stopPropagation();
            
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
        
        // Also initialize using Bootstrap's API directly
        try {
            if (typeof bootstrap !== 'undefined') {
                new bootstrap.Dropdown(userDropdown);
                console.log('Initialized dropdown with Bootstrap API');
            }
        } catch (e) {
            console.error('Error initializing dropdown with Bootstrap API:', e);
        }
    } else {
        console.error('userDropdown element not found in DOM');
    }
    
    // Check Bootstrap version and availability
    if (typeof bootstrap !== 'undefined') {
        console.log('Bootstrap version:', bootstrap.Dropdown.VERSION || 'Unknown');
    } else {
        console.error('Bootstrap not loaded!');
        // Try to add Bootstrap manually if it's missing
        const bootstrapScript = document.createElement('script');
        bootstrapScript.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js';
        document.body.appendChild(bootstrapScript);
        console.log('Added Bootstrap script dynamically');
    }
});
</script>
"""
    
    # Check for scripts block
    if script_block_start in content:
        script_start_pos = content.find(script_block_start)
        script_end_pos = content.find(script_block_end, script_start_pos)
        
        if script_end_pos > script_start_pos:
            # Insert after the scripts block start
            insert_pos = script_start_pos + len(script_block_start)
            content = content[:insert_pos] + dropdown_fix + content[insert_pos:]
            print("✅ Added dropdown fix to existing scripts block")
        else:
            print("❌ Scripts block is malformed")
    else:
        # Add scripts block at the end before the last endblock
        last_endblock_pos = content.rfind("{% endblock %}")
        
        if last_endblock_pos > 0:
            scripts_block = f"\n\n{script_block_start}{dropdown_fix}{script_block_end}\n\n"
            content = content[:last_endblock_pos] + scripts_block + content[last_endblock_pos:]
            print("✅ Added new scripts block with dropdown fix")
        else:
            content = content + f"\n\n{script_block_start}{dropdown_fix}{script_block_end}\n\n"
            print("✅ Added scripts block with dropdown fix at the end")
    
    # Write the modified content back
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n🔍 SUMMARY OF FIXES:")
    print("1. Ensured template properly extends dashboard_base.html")
    print("2. Fixed potential Chart.js version conflicts")
    print("3. Fixed potential jQuery version conflicts")
    print("4. Ensured content block is properly structured")
    print("5. Added comprehensive dropdown fix with multiple fallbacks")
    print("\n✨ RECOMMENDATION: Run 'python manage.py runserver' and test the fix")

if __name__ == "__main__":
    comprehensive_admin_fix()
