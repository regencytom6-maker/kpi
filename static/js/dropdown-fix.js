// Comprehensive dropdown fix script for admin dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing dropdown fixes...');

    // Delay initialization slightly to ensure all DOM elements are fully loaded and processed
    setTimeout(function() {
        // Directly target the admin dropdown (used for user profile/logout)
        const adminDropdown = document.getElementById('navbarDropdown');
        if (adminDropdown) {
            console.log('Found admin dropdown element', adminDropdown);
            
            try {
                // Make sure it's set up as a bootstrap dropdown
                const dropdown = new bootstrap.Dropdown(adminDropdown);
                
                // Force dropdown menu to be proper child of navbarDropdown parent
                const parent = adminDropdown.parentElement;
                const dropdownMenu = parent.querySelector('.dropdown-menu');
                
                if (dropdownMenu) {
                    console.log('Found dropdown menu', dropdownMenu);
                    
                    // Ensure the dropdown menu has proper classes
                    dropdownMenu.classList.add('dropdown-menu');
                    dropdownMenu.setAttribute('aria-labelledby', 'navbarDropdown');
                    
                    // Add explicit click handler with direct menu manipulation
                    adminDropdown.addEventListener('click', function(e) {
                        console.log('Admin dropdown clicked');
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Toggle the dropdown using Bootstrap API
                        dropdown.toggle();
                    });
                    
                    // Add fallback direct manipulation
                    document.addEventListener('click', function(e) {
                        if (e.target === adminDropdown || adminDropdown.contains(e.target)) {
                            if (!dropdownMenu.classList.contains('show')) {
                                dropdownMenu.classList.add('show');
                            }
                        } else if (!dropdownMenu.contains(e.target)) {
                            dropdownMenu.classList.remove('show');
                        }
                    });
                } else {
                    console.error('Dropdown menu not found for admin dropdown!');
                }
            } catch (error) {
                console.error('Error initializing admin dropdown:', error);
            }
        } else {
            console.warn('Admin dropdown element (navbarDropdown) not found!');
        }
        
        // Initialize all dropdowns for good measure
        const allDropdowns = document.querySelectorAll('.dropdown-toggle');
        console.log('Found', allDropdowns.length, 'dropdown toggles');
        
        allDropdowns.forEach(function(element) {
            try {
                // Skip if already initialized
                if (element.getAttribute('data-dropdown-initialized') === 'true') {
                    return;
                }
                
                const dropdown = new bootstrap.Dropdown(element);
                element.setAttribute('data-dropdown-initialized', 'true');
                
                console.log('Initialized dropdown:', element);
            } catch (error) {
                console.warn('Error initializing dropdown:', element, error);
            }
        });
    }, 100); // Small delay to ensure everything is loaded
});
