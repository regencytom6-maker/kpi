import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import path
from django.core.management import call_command
from django.shortcuts import redirect

# Create a temporary route for the dashboard wrapper
def create_dashboard_debug_wrapper():
    with open('templates/dashboards/admin_dashboard_clean_original.html', 'w') as f:
        with open('templates/dashboards/admin_dashboard_clean.html', 'r') as original:
            f.write(original.read())
    
    with open('templates/dashboards/admin_dashboard_clean.html', 'r') as original:
        content = original.read()
    
    debug_script = """
    <script>
    // Debug script for dashboard charts
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Debug script loaded');
        
        // Log all chart data variables
        console.log('Product data:', window.productData);
        console.log('Phase data:', window.phaseData);
        console.log('Weekly data:', window.weeklyData);
        console.log('QC data:', window.qcData);
        
        // Check Canvas elements
        const canvasIds = ['productTypeChart', 'phaseStatusChart', 'weeklyTrendChart', 'qcStatusChart'];
        canvasIds.forEach(id => {
            const canvas = document.getElementById(id);
            console.log(`Canvas #${id}:`, canvas);
            if (canvas) {
                console.log(`  Dimensions: ${canvas.width}x${canvas.height}`);
            }
        });
        
        // Check if Chart.js is loaded
        console.log('Chart.js loaded:', typeof Chart !== 'undefined');
        
        // Check for existing charts
        if (typeof Chart !== 'undefined' && Chart.instances) {
            console.log('Existing charts:', Object.keys(Chart.instances).length);
        }
        
        // Add debug controls
        const controls = document.createElement('div');
        controls.style = 'position:fixed; bottom:10px; right:10px; background:#f8f9fa; border:1px solid #ddd; padding:10px; z-index:9999; border-radius:5px;';
        controls.innerHTML = `
            <div style="margin-bottom:10px; font-weight:bold;">Chart Debug Controls</div>
            <button id="debugReload" style="margin-right:5px;">Reload Page</button>
            <button id="debugChart" style="margin-right:5px;">Reinitialize Charts</button>
            <button id="debugFallback">Create Fallback Charts</button>
        `;
        document.body.appendChild(controls);
        
        document.getElementById('debugReload').addEventListener('click', function() {
            location.reload();
        });
        
        document.getElementById('debugChart').addEventListener('click', function() {
            if (typeof initCharts === 'function') {
                try {
                    initCharts();
                    alert('Charts reinitialized');
                } catch(e) {
                    console.error('Error reinitializing charts:', e);
                    alert('Error: ' + e.message);
                }
            } else {
                alert('initCharts function not found');
            }
        });
        
        document.getElementById('debugFallback').addEventListener('click', function() {
            try {
                createFallbackCharts();
                alert('Fallback charts created');
            } catch(e) {
                console.error('Error creating fallback charts:', e);
                alert('Error: ' + e.message);
            }
        });
        
        function createFallbackCharts() {
            if (typeof Chart === 'undefined') {
                alert('Chart.js not loaded!');
                return;
            }
            
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
                        labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple'],
                        datasets: [{
                            label: 'Fallback Data',
                            data: [12, 19, 3, 5, 2],
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.2)',
                                'rgba(54, 162, 235, 0.2)',
                                'rgba(255, 206, 86, 0.2)',
                                'rgba(75, 192, 192, 0.2)',
                                'rgba(153, 102, 255, 0.2)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Fallback Chart ' + (index + 1)
                            }
                        }
                    }
                });
            });
        }
    });
    </script>
    {% endblock %}
    """
    
    # Replace the endblock with our debug script
    content = content.replace('{% endblock %}', debug_script)
    
    with open('templates/dashboards/admin_dashboard_clean.html', 'w') as modified:
        modified.write(content)
    
    print("Dashboard debug wrapper created!")
    print("Debug controls added to the admin dashboard.")
    print("Original template backed up to admin_dashboard_clean_original.html")

def restore_original_dashboard():
    try:
        with open('templates/dashboards/admin_dashboard_clean_original.html', 'r') as backup:
            with open('templates/dashboards/admin_dashboard_clean.html', 'w') as original:
                original.write(backup.read())
        print("Original dashboard template restored!")
    except FileNotFoundError:
        print("Original backup not found. Nothing to restore.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_original_dashboard()
    else:
        create_dashboard_debug_wrapper()
        print("Debug wrapper added to the admin dashboard.")
        print("To restore the original template, run: python debug_dashboard.py restore")
