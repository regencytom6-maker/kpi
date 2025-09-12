// Make sure jQuery is loaded and all DOM elements are ready
document.addEventListener('DOMContentLoaded', function() {
    // Setup CSRF token for all AJAX requests with jQuery
    function setupCSRFForAjax() {
        if (typeof jQuery !== 'undefined') {
            // Function to get cookie by name
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            
            // Get CSRF token from cookie
            const csrftoken = getCookie('csrftoken');
            
            // Setup jQuery AJAX with CSRF token
            jQuery.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
            // CSRF protection setup complete
        }
    }

    // Make sure jQuery is loaded
    if (typeof jQuery === 'undefined') {
        console.error("jQuery is not loaded! Loading jQuery dynamically...");
        // Load jQuery dynamically if not available
        var jqScript = document.createElement('script');
        jqScript.src = "https://code.jquery.com/jquery-3.6.0.min.js";
        jqScript.onload = function() {
            console.log("jQuery loaded dynamically!");
            setupCSRFForAjax();
            initializeQcEvents();
        };
        document.head.appendChild(jqScript);
    } else {
        console.log("jQuery is already loaded, version:", jQuery.fn.jquery);
        setupCSRFForAjax();
        initializeQcEvents();
    }
    
    function initializeQcEvents() {
        // Add event handler for qc_test_modal.html save button
        jQuery(document).on('click', '#qcSaveButton', function(e) {
            console.log("=== QC Save Button clicked ===");
            e.preventDefault();
            
            // Get form values - standard form serialization
            var formData = jQuery('#qcTestForm').serializeArray();
            
            // Convert to regular object
            var formObject = {};
            jQuery(formData).each(function(index, obj){
                formObject[obj.name] = obj.value;
            });
            
            // Important: Map test_notes to comments field that backend expects
            if (formObject.test_notes) {
                formObject.comments = formObject.test_notes;
            }
            
            // Ensure batch_id is present (fallback)
            if (!formObject.batch_id && jQuery('#material_batch_id').val()) {
                formObject.batch_id = jQuery('#material_batch_id').val();
            }
            
            console.log("Form data ready for submission");
            
            // Disable the save button and show loading state
            jQuery('#qcSaveButton').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
            
            // Get CSRF token
            const csrfToken = jQuery('input[name=csrfmiddlewaretoken]').val();
            
            // Add CSRF token to form data
            formObject.csrfmiddlewaretoken = csrfToken;
            
            // Send AJAX request
            jQuery.ajax({
                url: '/raw-materials/api/save-qc-test/',
                method: 'POST',
                headers: {
                    'X-Content-Type-Options': 'nosniff',
                    'Cache-Control': 'no-store, max-age=0',
                    'X-CSRFToken': csrfToken
                },
                data: formObject,
                beforeSend: function(xhr) {
                    // Include CSRF token in header for extra security
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                },
                success: function(response) {
                    console.log("Save QC Test Response:", response);
                    if (response.success) {
                        // Show success message
                        jQuery('#qcTestAlert')
                            .removeClass('d-none alert-danger')
                            .addClass('alert-success')
                            .html('<i class="fas fa-check-circle me-2"></i> Test results saved successfully!');
                            
                        // Re-enable save button
                        jQuery('#qcSaveButton').prop('disabled', false).html('<i class="fas fa-save me-2"></i>Save Test Results');
                        
                        // Reload the page after a short delay to show updated data
                        setTimeout(function() {
                            location.reload();
                        }, 1500);
                    } else {
                        // Show error message
                        jQuery('#qcTestAlert')
                            .removeClass('d-none alert-success')
                            .addClass('alert-danger')
                            .html('<i class="fas fa-exclamation-triangle me-2"></i> ' + (response.error || 'Unknown error occurred'));
                            
                        // Re-enable save button
                        jQuery('#qcSaveButton').prop('disabled', false).html('<i class="fas fa-save me-2"></i>Save Test Results');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("AJAX Error:", xhr.responseText);
                    
                    // Show error message
                    jQuery('#qcTestAlert')
                        .removeClass('d-none alert-success')
                        .addClass('alert-danger')
                        .html('<i class="fas fa-exclamation-triangle me-2"></i> Error saving test results. Please try again.');
                        
                    // Re-enable save button
                    jQuery('#qcSaveButton').prop('disabled', false).html('<i class="fas fa-save me-2"></i>Save Test Results');
                }
            });
        });
    }
});
