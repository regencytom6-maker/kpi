import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.conf import settings
import shutil

def fix_static_files_issue():
    """Fix issue with static files not loading properly"""
    
    # 1. Make sure static files directory exists
    if not os.path.exists(settings.STATIC_ROOT):
        os.makedirs(settings.STATIC_ROOT, exist_ok=True)
        print(f"Created static root directory: {settings.STATIC_ROOT}")
    
    # 2. Copy chart_data.js and chart_init.js to make sure they're accessible
    js_dir = os.path.join('static', 'js')
    if not os.path.exists(js_dir):
        os.makedirs(js_dir, exist_ok=True)
        print(f"Created JS directory: {js_dir}")
    
    chart_data_src = os.path.join('static', 'js', 'chart_data.js')
    chart_init_src = os.path.join('static', 'js', 'chart_init.js')
    
    chart_data_dest = os.path.join(settings.STATIC_ROOT, 'js', 'chart_data.js')
    chart_init_dest = os.path.join(settings.STATIC_ROOT, 'js', 'chart_init.js')
    
    os.makedirs(os.path.dirname(chart_data_dest), exist_ok=True)
    
    # Copy files
    if os.path.exists(chart_data_src):
        shutil.copy2(chart_data_src, chart_data_dest)
        print(f"Copied chart_data.js to {chart_data_dest}")
    else:
        print(f"Warning: Source file {chart_data_src} not found")
    
    if os.path.exists(chart_init_src):
        shutil.copy2(chart_init_src, chart_init_dest)
        print(f"Copied chart_init.js to {chart_init_dest}")
    else:
        print(f"Warning: Source file {chart_init_src} not found")
    
    # 3. Create inline-chart.js that embeds both files directly
    create_inline_chart_js()
    
    print("Static files fix applied. Please restart your server and reload the page.")

def create_inline_chart_js():
    """Create an inline chart.js file that embeds all chart code directly"""
    
    chart_data_src = os.path.join('static', 'js', 'chart_data.js')
    chart_init_src = os.path.join('static', 'js', 'chart_init.js')
    
    combined_content = "// Combined chart data and initialization\n// Auto-generated - do not edit\n\n"
    
    # Add chart data
    if os.path.exists(chart_data_src):
        with open(chart_data_src, 'r') as f:
            combined_content += f.read() + "\n\n"
    else:
        combined_content += """
// Fallback chart data
const productData = {
    tablets: 7,
    capsules: 3,
    ointments: 2
};

// Phase Completion Data
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

// Weekly Production Trend Data
const weeklyData = {
    started_week4: 0,
    completed_week4: 63,
    started_week3: 0,
    completed_week3: 8,
    started_week2: 0,
    completed_week2: 12,
    started_week1: 0,
    completed_week1: 3
};

// Quality Control Data
const qcData = {
    passed: 127,
    failed: 5,
    pending: 78
};
"""
    
    # Add chart initialization code
    if os.path.exists(chart_init_src):
        with open(chart_init_src, 'r') as f:
            combined_content += f.read()
    else:
        combined_content += """
// Fallback chart initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inline chart initialization loaded');
    
    // Initialize charts with delay to ensure DOM is ready
    setTimeout(initializeAllCharts, 500);
});

function initializeAllCharts() {
    console.log('Initializing all charts');
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded! Loading it dynamically...');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
        script.onload = initializeCharts;
        document.head.appendChild(script);
    } else {
        initializeCharts();
    }
}

function initializeCharts() {
    try {
        initializeProductTypeChart();
        initializePhaseStatusChart();
        initializeWeeklyTrendChart();
        initializeQcStatusChart();
        
        console.log('All charts initialized successfully');
    } catch (error) {
        console.error('Error during chart initialization:', error);
    }
}

function initializeProductTypeChart() {
    const canvas = document.getElementById('productTypeChart');
    if (!canvas) {
        console.error('Product Type Chart canvas not found');
        return null;
    }
    
    // Make sure the canvas has dimensions
    ensureCanvasDimensions(canvas);
    
    return new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Tablets', 'Capsules', 'Ointments'],
            datasets: [{
                data: [productData.tablets || 0, productData.capsules || 0, productData.ointments || 0],
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
}

function initializePhaseStatusChart() {
    const canvas = document.getElementById('phaseStatusChart');
    if (!canvas) {
        console.error('Phase Status Chart canvas not found');
        return null;
    }
    
    // Make sure the canvas has dimensions
    ensureCanvasDimensions(canvas);
    
    return new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Mixing', 'Drying', 'Granulation', 'Compression', 'Packing'],
            datasets: [{
                label: 'Completed',
                data: [
                    phaseData.mixing_completed || 0,
                    phaseData.drying_completed || 0,
                    phaseData.granulation_completed || 0,
                    phaseData.compression_completed || 0,
                    phaseData.packing_completed || 0
                ],
                backgroundColor: 'rgba(75, 192, 192, 0.8)'
            }, {
                label: 'In Progress',
                data: [
                    phaseData.mixing_inprogress || 0,
                    phaseData.drying_inprogress || 0,
                    phaseData.granulation_inprogress || 0,
                    phaseData.compression_inprogress || 0,
                    phaseData.packing_inprogress || 0
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
            }
        }
    });
}

function initializeWeeklyTrendChart() {
    const canvas = document.getElementById('weeklyTrendChart');
    if (!canvas) {
        console.error('Weekly Trend Chart canvas not found');
        return null;
    }
    
    // Make sure the canvas has dimensions
    ensureCanvasDimensions(canvas);
    
    return new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'Batches Started',
                data: [
                    weeklyData.started_week1 || 0,
                    weeklyData.started_week2 || 0,
                    weeklyData.started_week3 || 0,
                    weeklyData.started_week4 || 0
                ],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: true
            }, {
                label: 'Batches Completed',
                data: [
                    weeklyData.completed_week1 || 0,
                    weeklyData.completed_week2 || 0,
                    weeklyData.completed_week3 || 0,
                    weeklyData.completed_week4 || 0
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
            }
        }
    });
}

function initializeQcStatusChart() {
    const canvas = document.getElementById('qcStatusChart');
    if (!canvas) {
        console.error('QC Status Chart canvas not found');
        return null;
    }
    
    // Make sure the canvas has dimensions
    ensureCanvasDimensions(canvas);
    
    return new Chart(canvas.getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Passed', 'Failed', 'Pending'],
            datasets: [{
                data: [
                    qcData.passed || 0,
                    qcData.failed || 0,
                    qcData.pending || 0
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
            maintainAspectRatio: false
        }
    });
}

function ensureCanvasDimensions(canvas) {
    if (canvas.width === 0 || canvas.height === 0) {
        const parent = canvas.parentElement;
        canvas.width = parent.clientWidth || 300;
        canvas.height = parent.clientHeight || 300;
    }
}
"""
    
    # Write combined file
    output_path = os.path.join('static', 'js', 'inline-chart.js')
    with open(output_path, 'w') as f:
        f.write(combined_content)
    
    # Copy to static root
    static_output_path = os.path.join(settings.STATIC_ROOT, 'js', 'inline-chart.js')
    os.makedirs(os.path.dirname(static_output_path), exist_ok=True)
    shutil.copy2(output_path, static_output_path)
    
    print(f"Created inline chart.js at {output_path} and {static_output_path}")

if __name__ == "__main__":
    fix_static_files_issue()
