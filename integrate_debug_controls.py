import os

def integrate_debug_controls():
    """Integrate debug controls into the dashboard while keeping the charts"""
    template_path = 'templates/dashboards/admin_dashboard_clean.html'
    backup_path = 'templates/dashboards/admin_dashboard_clean_backup_integrated.html'
    
    # Create backup
    if os.path.exists(template_path):
        with open(template_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Backup created at {backup_path}")
    
    # Read template content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Find the chart section in the HTML
    chart_section = '<h3 class="mb-4">Production Status</h3>'
    if chart_section in content:
        # Add the debug controls directly in the HTML rather than via JavaScript
        debug_controls_html = """
        <div class="row mb-3">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        Chart Debug Controls
                    </div>
                    <div class="card-body">
                        <button id="reloadPage" class="btn btn-primary me-2">Reload Page</button>
                        <button id="reinitCharts" class="btn btn-success me-2">Reinitialize Charts</button>
                        <button id="createFallbacks" class="btn btn-warning">Create Fallback Charts</button>
                        
                        <script>
                        document.getElementById('reloadPage').addEventListener('click', function() {
                            location.reload();
                        });
                        
                        document.getElementById('reinitCharts').addEventListener('click', function() {
                            try {
                                initProductTypeChart();
                                initPhaseStatusChart();
                                initWeeklyTrendChart();
                                initQcStatusChart();
                                alert('Charts reinitialized');
                            } catch(e) {
                                console.error('Error reinitializing charts:', e);
                                alert('Error: ' + e.message);
                            }
                        });
                        
                        document.getElementById('createFallbacks').addEventListener('click', function() {
                            try {
                                // Create fallback charts with placeholder data
                                createFallbackCharts();
                                alert('Fallback charts created');
                            } catch(e) {
                                console.error('Error creating fallback charts:', e);
                                alert('Error: ' + e.message);
                            }
                        });
                        
                        function createFallbackCharts() {
                            const chartContainers = document.querySelectorAll('.chart-container');
                            console.log(`Found ${chartContainers.length} chart containers`);
                            
                            chartContainers.forEach((container, index) => {
                                // Clear existing content
                                container.innerHTML = '';
                                
                                // Create new canvas
                                const canvas = document.createElement('canvas');
                                canvas.id = 'fallbackChart' + index;
                                container.appendChild(canvas);
                                
                                // Set canvas dimensions
                                canvas.width = container.clientWidth;
                                canvas.height = container.clientHeight;
                                
                                const chartTypes = ['doughnut', 'bar', 'line', 'pie'];
                                const ctx = canvas.getContext('2d');
                                
                                new Chart(ctx, {
                                    type: chartTypes[index % chartTypes.length],
                                    data: {
                                        labels: ['Category 1', 'Category 2', 'Category 3'],
                                        datasets: [{
                                            label: 'Fallback Data',
                                            data: [Math.random() * 10 + 5, Math.random() * 10 + 5, Math.random() * 10 + 5],
                                            backgroundColor: [
                                                'rgba(54, 162, 235, 0.8)',
                                                'rgba(255, 99, 132, 0.8)',
                                                'rgba(75, 192, 192, 0.8)'
                                            ]
                                        }]
                                    },
                                    options: {
                                        responsive: true,
                                        maintainAspectRatio: false
                                    }
                                });
                            });
                        }
                        </script>
                    </div>
                </div>
            </div>
        </div>"""
        
        # Insert the debug controls after the chart section header
        content = content.replace(chart_section, chart_section + debug_controls_html)
        
        # Remove any JavaScript code that creates floating debug panels
        floating_panel_code = """
    // Add a control panel for debugging
    const debugPanel = document.createElement('div');"""
        
        if floating_panel_code in content:
            # Find where this code starts and remove the panel creation and event listeners
            panel_start = content.find(floating_panel_code)
            if panel_start > 0:
                # Find the next }); to locate the end of the event listeners
                event_end = content.find("});", panel_start)
                if event_end > panel_start:
                    # Remove the code
                    content = content[:panel_start] + "// Floating debug panel replaced with integrated controls\n" + content[event_end+3:]
                    print("Removed floating debug panel")
        
        # Remove the other style of debug panel too
        alt_panel_code = """
        // Add debug controls
        const controls = document.createElement('div');"""
        
        if alt_panel_code in content:
            panel_start = content.find(alt_panel_code)
            if panel_start > 0:
                # Find the next }); after all the event listeners
                event_end = content.find("});", panel_start)
                if event_end > panel_start:
                    # Find the next }); after that to get past all event listeners
                    next_end = content.find("});", event_end+3)
                    if next_end > event_end:
                        # And one more to get past createFallbackCharts
                        final_end = content.find("});", next_end+3)
                        if final_end > next_end:
                            # Remove the code
                            content = content[:panel_start] + "// Floating debug controls replaced with integrated version\n" + content[final_end+3:]
                            print("Removed alternate floating debug panel")
    
        # Write the updated content
        with open(template_path, 'w') as f:
            f.write(content)
        
        print("Debug controls integrated into dashboard")
    else:
        print("Chart section not found in template")
        
if __name__ == "__main__":
    integrate_debug_controls()
