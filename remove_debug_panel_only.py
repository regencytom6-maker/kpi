import os

def remove_only_debug_panel():
    """Remove only the debug controls panel from the admin dashboard template"""
    template_path = 'templates/dashboards/admin_dashboard_clean.html'
    backup_path = 'templates/dashboards/admin_dashboard_clean_backup_panel_only.html'
    
    # Create backup
    if os.path.exists(template_path):
        with open(template_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Backup created at {backup_path}")
    
    # Read template content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # First restore from any previous backup to get the charts back
    backup_direct_path = 'templates/dashboards/admin_dashboard_clean_backup_direct.html'
    if os.path.exists(backup_direct_path):
        with open(backup_direct_path, 'r') as f:
            content = f.read()
        print("Restored content from backup with working charts")
    
    # Find and remove only the debug panel
    panel_code = """
    // Add a control panel for debugging
    const debugPanel = document.createElement('div');
    debugPanel.style = 'position: fixed; bottom: 20px; right: 20px; background: #f8f9fa; border: 1px solid #ddd; padding: 10px; z-index: 9999;';
    debugPanel.innerHTML = `
        <button id="reinitCharts" class="btn btn-sm btn-primary">Reinit Charts</button>
    `;
    document.body.appendChild(debugPanel);
    
    document.getElementById('reinitCharts').addEventListener('click', function() {
        initProductTypeChart();
        initPhaseStatusChart();
        initWeeklyTrendChart();
        initQcStatusChart();
        alert('Charts reinitialized');
    });"""
    
    if panel_code.strip() in content:
        content = content.replace(panel_code, "// Debug panel removed")
        print("Debug panel code removed while preserving chart functionality")
    
    # Also check for other debug panel code
    alt_panel_code = """
        // Add debug controls
        const controls = document.createElement('div');
        controls.style = 'position:fixed; bottom:10px; right:10px; background:#f8f9fa; border:1px solid #ddd; padding:10px; z-index:9999; border-radius:5px;';
        controls.innerHTML = `
            <div style="margin-bottom:10px; font-weight:bold;">Chart Debug Controls</div>
            <button id="debugReload" style="margin-right:5px;">Reload Page</button>
            <button id="debugChart" style="margin-right:5px;">Reinitialize Charts</button>
            <button id="debugFallback">Create Fallback Charts</button>
        `;
        document.body.appendChild(controls);"""
    
    if alt_panel_code.strip() in content:
        # Find where the debug controls event listeners end
        control_start = content.find(alt_panel_code)
        if control_start > 0:
            # Find the end of the event listeners - look for end of createFallbackCharts function
            event_end = content.find("function createFallbackCharts()", control_start)
            if event_end > control_start:
                function_start = event_end
                # Find the end of createFallbackCharts by counting braces
                brace_count = 0
                in_function = False
                function_end = function_start
                
                for i in range(function_start, len(content)):
                    if content[i] == '{':
                        in_function = True
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if in_function and brace_count == 0:
                            function_end = i + 1
                            break
                
                if function_end > function_start:
                    # Remove the debug panel and event listeners
                    content = content[:control_start] + "// Debug controls removed\n" + content[function_end:]
                    print("Debug controls and related event listeners removed")
            else:
                # Just remove the panel creation
                content = content.replace(alt_panel_code, "// Debug controls removed")
                print("Debug controls panel removed")
    
    # Write the updated content
    with open(template_path, 'w') as f:
        f.write(content)
    
    print("Template updated successfully - charts should be visible and debug controls removed")

if __name__ == "__main__":
    remove_only_debug_panel()
