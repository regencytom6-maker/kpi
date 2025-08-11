import os
import sys
import django
from django.template import Template, Context

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kampala_pharma.settings")
django.setup()

# Create a very simple template
SIMPLE_TEMPLATE = """{% extends 'base.html' %}

{% block title %}Finished Goods Store Dashboard - Kampala Pharmaceutical Industries{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <h2>Finished Goods Store Dashboard</h2>
    <p>This is a test dashboard.</p>
</div>
{% endblock %}
"""

# Write to file
with open(os.path.join('templates', 'dashboards', 'finished_goods_dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(SIMPLE_TEMPLATE)

print("Simple template created successfully!")
