// Handle inventory monitor link
$(document).ready(function() {
    $('#inventory-monitor-tab').on('click', function(e) {
        e.preventDefault();
        const url = $(this).attr('href');
        
        // Update browser history without redirecting
        window.history.pushState({}, '', url);
        
        // Load content into main content area
        $('.col-md-9').load(url + ' #content');
        
        // Update active state
        $('.list-group-item').removeClass('active');
        $(this).addClass('active');
    });
});
