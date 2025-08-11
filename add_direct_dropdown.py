import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def add_direct_dropdown():
    print("\n🔧 ADDING DIRECT DROPDOWN TO ADMIN DASHBOARD\n")
    
    template_path = Path('templates/dashboards/admin_dashboard_clean.html')
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return
    
    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a direct dropdown that doesn't rely on the base template
    direct_dropdown = """
<!-- Direct implementation of user dropdown - independent of base template -->
<div class="position-fixed" style="top: 10px; right: 20px; z-index: 9999;">
    <div class="dropdown">
        <a class="btn btn-primary dropdown-toggle" href="#" id="directUserDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
            <i class="fas fa-user me-1"></i> User Options
        </a>
        <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="directUserDropdown">
            <li><a class="dropdown-item" href="/"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a></li>
            <li><a class="dropdown-item" href="{% url 'accounts:profile' %}"><i class="fas fa-user me-2"></i>Profile</a></li>
            {% if user.is_staff %}
            <li><a class="dropdown-item" href="{% url 'admin:index' %}"><i class="fas fa-cog me-2"></i>Admin Panel</a></li>
            {% endif %}
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="{% url 'accounts:logout' %}"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
        </ul>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('Direct dropdown script loaded');
    
    // Get the direct dropdown element
    const directDropdown = document.getElementById('directUserDropdown');
    if (directDropdown) {
        console.log('Found directUserDropdown element');
        
        // Add click handler
        directDropdown.addEventListener('click', function(e) {
            console.log('Direct dropdown clicked');
            e.preventDefault();
            
            // Get dropdown menu
            const dropdownMenu = document.querySelector('[aria-labelledby="directUserDropdown"]');
            if (dropdownMenu) {
                // Toggle show class manually
                dropdownMenu.classList.toggle('show');
                
                // Update aria-expanded attribute
                const isExpanded = dropdownMenu.classList.contains('show');
                directDropdown.setAttribute('aria-expanded', isExpanded);
                
                // Position the dropdown correctly
                if (isExpanded) {
                    dropdownMenu.style.position = 'absolute';
                    dropdownMenu.style.inset = '0px auto auto 0px';
                    dropdownMenu.style.transform = 'translate3d(0px, 40px, 0px)';
                }
                
                console.log('Toggled direct dropdown visibility:', isExpanded);
                
                // Close dropdown when clicking outside
                if (isExpanded) {
                    const closeDropdownOnClick = function(event) {
                        if (!dropdownMenu.contains(event.target) && event.target !== directDropdown) {
                            dropdownMenu.classList.remove('show');
                            directDropdown.setAttribute('aria-expanded', 'false');
                            document.removeEventListener('click', closeDropdownOnClick);
                        }
                    };
                    
                    // Add listener with slight delay to avoid immediate trigger
                    setTimeout(() => {
                        document.addEventListener('click', closeDropdownOnClick);
                    }, 10);
                }
            } else {
                console.error('Direct dropdown menu not found');
            }
        });
        
        console.log('Added click handler to directUserDropdown');
        
        // Also try Bootstrap initialization
        try {
            if (typeof bootstrap !== 'undefined') {
                new bootstrap.Dropdown(directDropdown);
                console.log('Initialized direct dropdown with Bootstrap API');
            }
        } catch (e) {
            console.error('Error initializing direct dropdown:', e);
        }
    } else {
        console.error('directUserDropdown element not found');
    }
});
</script>
"""

    # Find a good place to insert the direct dropdown - at the beginning of content block
    content_block_start = "{% block content %}"
    if content_block_start in content:
        insert_pos = content.find(content_block_start) + len(content_block_start)
        content = content[:insert_pos] + direct_dropdown + content[insert_pos:]
        
        # Write back to the template
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added direct dropdown to admin dashboard template")
    else:
        print("❌ Could not find content block")
    
    print("\n✨ DIRECT DROPDOWN ADDED:")
    print("1. Independent dropdown in the top right corner")
    print("2. Does not rely on base template implementation")
    print("3. Has its own JavaScript for initialization")
    print("4. Should work regardless of template inheritance issues")
    
    print("\n🔍 INSTRUCTIONS:")
    print("1. Visit the admin dashboard")
    print("2. Look for the 'User Options' dropdown in the top right")
    print("3. This dropdown should work independently of the base template")

if __name__ == "__main__":
    add_direct_dropdown()
