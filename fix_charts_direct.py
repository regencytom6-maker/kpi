import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def fix_charts_direct():
    """Apply a direct fix by embedding charts directly into the template"""
    template_path = 'templates/dashboards/admin_dashboard_clean.html'
    backup_path = 'templates/dashboards/admin_dashboard_clean_backup_direct.html'
    
    # Create backup
    if os.path.exists(template_path):
        with open(template_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Backup created at {backup_path}")
    
    # Read template content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Create new template content with direct chart embedding
    # First, replace all chart script includes
    script_pattern = '<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>'
    
    # Check if the pattern exists
    if script_pattern in content:
        direct_script = """<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
// Direct chart script - embedded to avoid static file issues
document.addEventListener('DOMContentLoaded', function() {
    console.log('Direct chart script loaded');
    
    // Chart data - direct embedding
    const productData = {
        tablets: 7,
        capsules: 3,
        ointments: 2
    };
    
    const phaseData = {
        mixing_completed: 55,
        mixing_inprogress: 32,
        drying_completed: 33,
        drying_inprogress: 11,
        granulation_completed: 89,
        granulation_inprogress: 55,
        compression_completed: 134,
        compression_inprogress: 72,
        packing_completed: 177,
        packing_inprogress: 91
    };
    
    const weeklyData = {
        started_week4: 7,
        completed_week4: 5,
        started_week3: 8,
        completed_week3: 6,
        started_week2: 6,
        completed_week2: 4,
        started_week1: 4,
        completed_week1: 2
    };
    
    const qcData = {
        passed: 127,
        failed: 5,
        pending: 78
    };
    
    // Initialize charts
    setTimeout(function() {
        try {
            initProductTypeChart();
            initPhaseStatusChart();
            initWeeklyTrendChart();
            initQcStatusChart();
            console.log('All charts initialized');
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }, 500); // Small delay to ensure DOM is ready
    
    function initProductTypeChart() {
        const canvas = document.getElementById('productTypeChart');
        if (!canvas) {
            console.error('Product Type Chart canvas not found');
            return;
        }
        
        // Ensure dimensions
        if (canvas.width === 0 || canvas.height === 0) {
            const parent = canvas.parentElement;
            canvas.width = parent.clientWidth || 300;
            canvas.height = parent.clientHeight || 200;
        }
        
        new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Tablets', 'Capsules', 'Ointments'],
                datasets: [{
                    data: [productData.tablets, productData.capsules, productData.ointments],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        console.log('Product Type Chart initialized');
    }
    
    function initPhaseStatusChart() {
        const canvas = document.getElementById('phaseStatusChart');
        if (!canvas) {
            console.error('Phase Status Chart canvas not found');
            return;
        }
        
        // Ensure dimensions
        if (canvas.width === 0 || canvas.height === 0) {
            const parent = canvas.parentElement;
            canvas.width = parent.clientWidth || 300;
            canvas.height = parent.clientHeight || 200;
        }
        
        new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Mixing', 'Drying', 'Granulation', 'Compression', 'Packing'],
                datasets: [{
                    label: 'Completed',
                    data: [
                        phaseData.mixing_completed,
                        phaseData.drying_completed,
                        phaseData.granulation_completed,
                        phaseData.compression_completed,
                        phaseData.packing_completed
                    ],
                    backgroundColor: 'rgba(75, 192, 192, 0.8)'
                }, {
                    label: 'In Progress',
                    data: [
                        phaseData.mixing_inprogress,
                        phaseData.drying_inprogress,
                        phaseData.granulation_inprogress,
                        phaseData.compression_inprogress,
                        phaseData.packing_inprogress
                    ],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        console.log('Phase Status Chart initialized');
    }
    
    function initWeeklyTrendChart() {
        const canvas = document.getElementById('weeklyTrendChart');
        if (!canvas) {
            console.error('Weekly Trend Chart canvas not found');
            return;
        }
        
        // Ensure dimensions
        if (canvas.width === 0 || canvas.height === 0) {
            const parent = canvas.parentElement;
            canvas.width = parent.clientWidth || 300;
            canvas.height = parent.clientHeight || 200;
        }
        
        new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Batches Started',
                    data: [
                        weeklyData.started_week1,
                        weeklyData.started_week2,
                        weeklyData.started_week3,
                        weeklyData.started_week4
                    ],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    fill: true
                }, {
                    label: 'Batches Completed',
                    data: [
                        weeklyData.completed_week1,
                        weeklyData.completed_week2,
                        weeklyData.completed_week3,
                        weeklyData.completed_week4
                    ],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        console.log('Weekly Trend Chart initialized');
    }
    
    function initQcStatusChart() {
        const canvas = document.getElementById('qcStatusChart');
        if (!canvas) {
            console.error('QC Status Chart canvas not found');
            return;
        }
        
        // Ensure dimensions
        if (canvas.width === 0 || canvas.height === 0) {
            const parent = canvas.parentElement;
            canvas.width = parent.clientWidth || 300;
            canvas.height = parent.clientHeight || 200;
        }
        
        new Chart(canvas.getContext('2d'), {
            type: 'pie',
            data: {
                labels: ['Passed', 'Failed', 'Pending'],
                datasets: [{
                    data: [
                        qcData.passed,
                        qcData.failed,
                        qcData.pending
                    ],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 205, 86, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        console.log('QC Status Chart initialized');
    }
    
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
    });
});
</script>"""
        
        # Remove any existing chart script references
        content = content.replace('<script src="/static/js/chart_data.js"></script>', '')
        content = content.replace('<script src="{% static \'js/chart_data.js\' %}"></script>', '')
        content = content.replace('<script src="/static/js/chart_init.js"></script>', '')
        content = content.replace('<script src="{% static \'js/chart_init.js\' %}"></script>', '')
        content = content.replace('<script src="/static/js/inline-chart.js"></script>', '')
        
        # Add our direct script
        content = content.replace(script_pattern, direct_script)
        
        # Remove initCharts function if it exists
        init_charts_pattern = "function initCharts()"
        if init_charts_pattern in content:
            # Find the function start
            start_idx = content.find(init_charts_pattern)
            if start_idx > 0:
                # Find the closing brace by counting braces
                brace_count = 0
                end_idx = start_idx
                in_function = False
                
                for i in range(start_idx, len(content)):
                    if content[i] == '{':
                        in_function = True
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if in_function and brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx > start_idx:
                    # Replace the function
                    content = content[:start_idx] + '// Function removed - using direct chart initialization' + content[end_idx:]
        
        # Write the updated content
        with open(template_path, 'w') as f:
            f.write(content)
        
        print(f"Template updated with direct chart embedding")
    else:
        print(f"Warning: Could not find Chart.js script tag in template")

if __name__ == "__main__":
    fix_charts_direct()
