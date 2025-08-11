import os
import django
import sys
import json

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Count
from products.models import Product
from bmr.models import BMR
from workflow.models import ProductionPhase, BatchPhaseExecution
from django.utils import timezone
from datetime import timedelta

def get_chart_data():
    """Get all data needed for chart rendering"""
    # Product Type Distribution
    product_types = Product.objects.values('product_type').annotate(count=Count('product_type'))
    tablet_count = 0
    capsule_count = 0
    ointment_count = 0
    
    for item in product_types:
        product_type = item['product_type'].lower() if item['product_type'] else ''
        if 'tablet' in product_type:
            tablet_count += item['count']
        elif 'capsule' in product_type:
            capsule_count += item['count']
        elif 'ointment' in product_type or 'cream' in product_type:
            ointment_count += item['count']
    
    # Phase completion data
    phase_data = {}
    common_phases = ['mixing', 'drying', 'granulation', 'compression', 'packing']
    
    for phase_name in common_phases:
        # Get completed phases
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name__icontains=phase_name,
            status='completed'
        ).count()
        
        # Get in-progress phases
        in_progress = BatchPhaseExecution.objects.filter(
            phase__phase_name__icontains=phase_name,
            status__in=['pending', 'in_progress']
        ).count()
        
        phase_data[f"{phase_name}_completed"] = completed
        phase_data[f"{phase_name}_inprogress"] = in_progress
    
    # Weekly production trend data
    current_date = timezone.now().date()
    week_start = current_date - timedelta(days=current_date.weekday())
    
    weekly_data = {}
    for i in range(4):
        week_end = week_start - timedelta(days=1)
        week_start_prev = week_start - timedelta(days=7)
        
        # Batches started in this week
        started = BMR.objects.filter(
            created_date__date__gte=week_start_prev,
            created_date__date__lte=week_end
        ).count()
        
        # Batches completed in this week
        completed = BatchPhaseExecution.objects.filter(
            phase__phase_name='finished_goods_store',
            completed_date__date__gte=week_start_prev,
            completed_date__date__lte=week_end,
            status='completed'
        ).count()
        
        weekly_data[f"started_week{4-i}"] = started
        weekly_data[f"completed_week{4-i}"] = completed
        
        week_start = week_start_prev
        
    # Quality Control data for chart
    qc_phases = BatchPhaseExecution.objects.filter(
        phase__phase_name__icontains='qc'
    )
    
    qc_data = {
        'passed': qc_phases.filter(status='completed').count(),
        'failed': qc_phases.filter(status='failed').count(),
        'pending': qc_phases.filter(status__in=['pending', 'in_progress']).count(),
    }
    
    return {
        'product_data': {
            'tablets': tablet_count,
            'capsules': capsule_count,
            'ointments': ointment_count
        },
        'phase_data': phase_data,
        'weekly_data': weekly_data,
        'qc_data': qc_data
    }

def create_data_js_file():
    """Create a JavaScript file with all the chart data variables"""
    data = get_chart_data()
    
    js_content = """// Chart data for admin dashboard
// Generated automatically - do not edit

// Product Type Data
const productData = {
    tablets: %s,
    capsules: %s,
    ointments: %s
};

// Phase Completion Data
const phaseData = {
    mixing_completed: %s,
    mixing_inprogress: %s,
    drying_completed: %s,
    drying_inprogress: %s,
    granulation_completed: %s,
    granulation_inprogress: %s,
    compression_completed: %s,
    compression_inprogress: %s,
    packing_completed: %s,
    packing_inprogress: %s
};

// Weekly Production Trend Data
const weeklyData = {
    started_week1: %s,
    started_week2: %s,
    started_week3: %s,
    started_week4: %s,
    completed_week1: %s,
    completed_week2: %s,
    completed_week3: %s,
    completed_week4: %s
};

// Quality Control Data
const qcData = {
    passed: %s,
    failed: %s,
    pending: %s
};

console.log('Chart data loaded from external file');
""" % (
    data['product_data']['tablets'],
    data['product_data']['capsules'],
    data['product_data']['ointments'],
    data['phase_data']['mixing_completed'],
    data['phase_data']['mixing_inprogress'],
    data['phase_data']['drying_completed'],
    data['phase_data']['drying_inprogress'],
    data['phase_data']['granulation_completed'],
    data['phase_data']['granulation_inprogress'],
    data['phase_data']['compression_completed'],
    data['phase_data']['compression_inprogress'],
    data['phase_data']['packing_completed'],
    data['phase_data']['packing_inprogress'],
    data['weekly_data']['started_week1'],
    data['weekly_data']['started_week2'],
    data['weekly_data']['started_week3'],
    data['weekly_data']['started_week4'],
    data['weekly_data']['completed_week1'],
    data['weekly_data']['completed_week2'],
    data['weekly_data']['completed_week3'],
    data['weekly_data']['completed_week4'],
    data['qc_data']['passed'],
    data['qc_data']['failed'],
    data['qc_data']['pending']
)
    
    # Save to static directory
    static_dir = 'static/js'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    filepath = os.path.join(static_dir, 'chart_data.js')
    with open(filepath, 'w') as f:
        f.write(js_content)
        
    print(f"Chart data written to {filepath}")
    
    # Create the minimal chart rendering HTML
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Charts Debug</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script src="/static/js/chart_data.js"></script>
    <style>
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
        }
    </style>
</head>
<body>
    <h1>Dashboard Charts Debug</h1>
    
    <h2>Product Type Chart</h2>
    <div class="chart-container">
        <canvas id="productTypeChart"></canvas>
    </div>
    
    <h2>Phase Status Chart</h2>
    <div class="chart-container">
        <canvas id="phaseStatusChart"></canvas>
    </div>
    
    <h2>Weekly Trend Chart</h2>
    <div class="chart-container">
        <canvas id="weeklyTrendChart"></canvas>
    </div>
    
    <h2>QC Status Chart</h2>
    <div class="chart-container">
        <canvas id="qcStatusChart"></canvas>
    </div>
    
    <script>
        // Initialize charts when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing charts');
            
            // Product Type Chart
            const productTypeChart = new Chart(
                document.getElementById('productTypeChart'),
                {
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
                        maintainAspectRatio: false
                    }
                }
            );
            
            // Phase Status Chart
            const phaseStatusChart = new Chart(
                document.getElementById('phaseStatusChart'),
                {
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
                        }
                    }
                }
            );
            
            // Weekly Trend Chart
            const weeklyTrendChart = new Chart(
                document.getElementById('weeklyTrendChart'),
                {
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
                        }
                    }
                }
            );
            
            // QC Status Chart
            const qcStatusChart = new Chart(
                document.getElementById('qcStatusChart'),
                {
                    type: 'pie',
                    data: {
                        labels: ['Passed', 'Failed', 'Pending'],
                        datasets: [{
                            data: [qcData.passed, qcData.failed, qcData.pending],
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
                }
            );
        });
    </script>
</body>
</html>
"""
    
    # Save the HTML file
    html_path = 'static/chart_debug.html'
    with open(html_path, 'w') as f:
        f.write(html_content)
        
    print(f"Debug HTML written to {html_path}")
    print(f"Access it at: http://127.0.0.1:8000/static/chart_debug.html")

if __name__ == "__main__":
    create_data_js_file()
