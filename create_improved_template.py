import os
import sys
import django
from django.template import Template, Context

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kampala_pharma.settings")
django.setup()

# Create a template with cards and queue, but no JS
TEMPLATE = """{% extends 'base.html' %}

{% block title %}Finished Goods Store Dashboard - Kampala Pharmaceutical Industries{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <!-- Header -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h2 class="text-primary mb-0">
                        <i class="fas fa-archive me-2"></i>Finished Goods Store Dashboard
                    </h2>
                    <p class="text-muted mb-0">Finished Goods Storage Management</p>
                </div>
                <div class="text-end">
                    <small class="text-muted">Welcome, {{ user.get_full_name|default:user.username }}</small><br>
                    <small class="text-success">{{ user.get_role_display }}</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Statistics Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <a href="?detail=pending" class="text-decoration-none">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="card-title mb-0">{{ stats.pending_phases }}</h5>
                                <p class="card-text">Pending Storage</p>
                            </div>
                            <i class="fas fa-clock fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </a>
        </div>
        <div class="col-md-3">
            <a href="?detail=in_progress" class="text-decoration-none">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="card-title mb-0">{{ stats.in_progress_phases }}</h5>
                                <p class="card-text">In Storage</p>
                            </div>
                            <i class="fas fa-play fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </a>
        </div>
        <div class="col-md-3">
            <a href="?detail=completed_today" class="text-decoration-none">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="card-title mb-0">{{ stats.completed_today }}</h5>
                                <p class="card-text">Stored Today</p>
                            </div>
                            <i class="fas fa-check fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </a>
        </div>
        <div class="col-md-3">
            <a href="?detail=total_batches" class="text-decoration-none">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="card-title mb-0">{{ stats.total_batches }}</h5>
                                <p class="card-text">Total Batches</p>
                            </div>
                            <i class="fas fa-warehouse fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </a>
        </div>
    </div>
    
    <!-- Finished Goods Storage Queue -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-clipboard-check me-2"></i>
                        {% if detail_title %}{{ detail_title }}{% else %}Finished Goods Storage Queue{% endif %}
                    </h5>
                </div>
                <div class="card-body">
                    {% if my_phases %}
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead class="table-light">
                                    <tr>
                                        <th>Batch #</th>
                                        <th>Product</th>
                                        <th>Phase</th>
                                        <th>Status</th>
                                        <th>Started</th>
                                        <th>Priority</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for phase in my_phases %}
                                    <tr>
                                        <td><strong>{{ phase.bmr.batch_number }}</strong></td>
                                        <td>{{ phase.bmr.product.product_name }}</td>
                                        <td><span class="badge bg-primary">{{ phase.display_name|default:phase.phase.phase_name|title }}</span></td>
                                        <td>
                                            {% if phase.status == 'pending' %}
                                                <span class="badge bg-warning">Pending</span>
                                            {% elif phase.status == 'in_progress' %}
                                                <span class="badge bg-info">In Storage</span>
                                            {% elif phase.status == 'completed' %}
                                                <span class="badge bg-success">Stored</span>
                                            {% else %}
                                                <span class="badge bg-secondary">{{ phase.status|title }}</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            {% if phase.started_date %}
                                                {{ phase.started_date|date:"M d, H:i" }}
                                            {% else %}
                                                <span class="text-muted">Not started</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            <span class="badge bg-success">Normal</span>
                                        </td>
                                        <td>
                                            <div class="btn-group btn-group-sm">
                                                <a href="{% url 'bmr:detail' phase.bmr.pk %}" class="btn btn-outline-primary btn-sm">
                                                    <i class="fas fa-eye"></i> View
                                                </a>
                                            </div>
                                        </td>
                                    </tr>
                                    {% empty %}
                                    <tr>
                                        <td colspan="7" class="text-center text-muted py-5">
                                            <i class="fas fa-archive fa-3x text-muted mb-3"></i><br>
                                            No finished goods pending storage at the moment.<br>
                                            <small>Check back later for new storage requests.</small>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-center text-muted py-5">
                            <i class="fas fa-archive fa-3x text-muted mb-3"></i><br>
                            No finished goods pending storage at the moment.<br>
                            <small>Check back later for new storage requests.</small>
                        </p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

# Write to file
with open(os.path.join('templates', 'dashboards', 'finished_goods_dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(TEMPLATE)

print("Improved template created successfully!")
