import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def add_debug_code():
    print("\n🔍 ADDING DEBUG CODE TO ADMIN DASHBOARD\n")
    
    template_path = Path('templates/dashboards/admin_dashboard_clean.html')
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return
    
    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a debug version of the dropdown
    debug_dropdown = """
<!-- Debug dropdown structure - identical but with different ID -->
<div class="position-fixed" style="top: 60px; right: 20px; z-index: 9999;">
    <div class="card">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">Debug Controls</h5>
        </div>
        <div class="card-body">
            <p class="mb-2">Click the buttons below to debug user dropdown</p>
            
            <button id="debugInitDropdown" class="btn btn-sm btn-info mb-2">
                Initialize Dropdown
            </button>
            
            <button id="debugToggleDropdown" class="btn btn-sm btn-warning mb-2">
                Toggle Dropdown
            </button>
            
            <button id="debugCheckDOM" class="btn btn-sm btn-secondary mb-2">
                Check DOM Structure
            </button>
            
            <div id="debug-output" class="mt-3 p-2 bg-light">
                <small>Debug output will appear here</small>
            </div>
        </div>
    </div>
</div>

<!-- Debug Script -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const debugOutput = document.getElementById('debug-output');
    
    // Log to both console and our debug output element
    function debugLog(message) {
        console.log(message);
        if (debugOutput) {
            const timestamp = new Date().toLocaleTimeString();
            debugOutput.innerHTML += `<div><small>${timestamp}: ${message}</small></div>`;
        }
    }
    
    debugLog('Debug script loaded');
    
    // Check for userDropdown element
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        debugLog(`Found userDropdown: ${userDropdown.tagName} with classes ${userDropdown.className}`);
    } else {
        debugLog('❌ userDropdown element not found!');
    }
    
    // Check for dropdown menu
    const dropdownMenu = document.querySelector('[aria-labelledby="userDropdown"]');
    if (dropdownMenu) {
        debugLog(`Found dropdown menu: ${dropdownMenu.tagName} with classes ${dropdownMenu.className}`);
    } else {
        debugLog('❌ Dropdown menu not found!');
    }
    
    // Check Bootstrap
    if (typeof bootstrap !== 'undefined') {
        debugLog(`Bootstrap detected: version ${bootstrap.Dropdown.VERSION || 'unknown'}`);
    } else {
        debugLog('❌ Bootstrap not loaded!');
    }
    
    // Initialize button
    const initBtn = document.getElementById('debugInitDropdown');
    if (initBtn && userDropdown) {
        initBtn.addEventListener('click', function() {
            debugLog('Initializing dropdown manually...');
            try {
                if (typeof bootstrap !== 'undefined') {
                    new bootstrap.Dropdown(userDropdown);
                    debugLog('✅ Dropdown initialized');
                } else {
                    debugLog('❌ Bootstrap not available for initialization');
                }
            } catch (e) {
                debugLog(`❌ Error initializing dropdown: ${e.message}`);
            }
        });
    }
    
    // Toggle button
    const toggleBtn = document.getElementById('debugToggleDropdown');
    if (toggleBtn && userDropdown && dropdownMenu) {
        toggleBtn.addEventListener('click', function() {
            debugLog('Toggling dropdown manually...');
            try {
                // Toggle show class
                dropdownMenu.classList.toggle('show');
                const isExpanded = dropdownMenu.classList.contains('show');
                userDropdown.setAttribute('aria-expanded', isExpanded);
                
                // Position the dropdown correctly
                if (isExpanded) {
                    dropdownMenu.style.position = 'absolute';
                    dropdownMenu.style.inset = '0px auto auto 0px';
                    dropdownMenu.style.transform = 'translate3d(0px, 40px, 0px)';
                }
                
                debugLog(`✅ Dropdown ${isExpanded ? 'opened' : 'closed'}`);
            } catch (e) {
                debugLog(`❌ Error toggling dropdown: ${e.message}`);
            }
        });
    }
    
    // DOM check button
    const checkBtn = document.getElementById('debugCheckDOM');
    if (checkBtn) {
        checkBtn.addEventListener('click', function() {
            debugLog('Checking DOM structure...');
            
            // Verify userDropdown
            const userDropdown = document.getElementById('userDropdown');
            if (userDropdown) {
                debugLog(`✅ userDropdown found: ${userDropdown.outerHTML.substring(0, 100)}...`);
                
                // Check event listeners
                debugLog('Checking for click event handler...');
                const clickHandler = function() {
                    debugLog('Click event handler works!');
                };
                userDropdown.addEventListener('click', clickHandler);
                
                // Check dropdown menu
                const dropdownMenu = document.querySelector('[aria-labelledby="userDropdown"]');
                if (dropdownMenu) {
                    debugLog(`✅ Dropdown menu found: ${dropdownMenu.outerHTML.substring(0, 100)}...`);
                    
                    // Look at parent-child relationship
                    const parent = dropdownMenu.parentElement;
                    debugLog(`Menu parent: ${parent.tagName} with classes ${parent.className}`);
                    
                    // Check positioning
                    const styles = window.getComputedStyle(dropdownMenu);
                    debugLog(`Menu position: ${styles.position}, display: ${styles.display}`);
                } else {
                    debugLog('❌ Dropdown menu not found!');
                }
            } else {
                debugLog('❌ userDropdown not found!');
            }
            
            // Check for conflicting elements
            const allDropdowns = document.querySelectorAll('.dropdown-toggle');
            debugLog(`Found ${allDropdowns.length} dropdown toggles on page`);
            
            // Check for z-index issues
            const navbarZIndex = window.getComputedStyle(document.querySelector('nav')).zIndex;
            debugLog(`Navbar z-index: ${navbarZIndex}`);
        });
    }
});
</script>
"""

    # Find a good place to insert the debug dropdown - at the beginning of content block
    content_block_start = "{% block content %}"
    if content_block_start in content:
        insert_pos = content.find(content_block_start) + len(content_block_start)
        content = content[:insert_pos] + debug_dropdown + content[insert_pos:]
        
        # Write back to the template
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added debug tools to admin dashboard template")
    else:
        print("❌ Could not find content block")
    
    print("\n🔍 DEBUG TOOLS ADDED:")
    print("1. Debug panel with interactive controls")
    print("2. Initialize Dropdown button: Manually initializes the Bootstrap dropdown")
    print("3. Toggle Dropdown button: Manually toggles the dropdown visibility")
    print("4. Check DOM Structure button: Reports on the DOM structure")
    print("5. Debug output panel to show results")
    
    print("\n✨ INSTRUCTIONS:")
    print("1. Visit the admin dashboard")
    print("2. Use the debug panel to diagnose dropdown issues")
    print("3. Check browser console for additional debug output")
    print("4. After fixing the issue, run remove_debug_tools.py to remove these tools")

def create_removal_script():
    removal_script = """import os
import django
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def remove_debug_tools():
    print("\\n🧹 REMOVING DEBUG TOOLS FROM ADMIN DASHBOARD\\n")
    
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
    
    print("\\n✨ DEBUG TOOLS REMOVED\\n")
    print("The admin dashboard should now be clean of any debug controls")

if __name__ == "__main__":
    remove_debug_tools()
"""
    
    # Write removal script
    with open("remove_debug_tools.py", 'w', encoding='utf-8') as f:
        f.write(removal_script)
    
    print("\n✅ Created removal script: remove_debug_tools.py")

if __name__ == "__main__":
    add_debug_code()
    create_removal_script()
