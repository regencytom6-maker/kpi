#!/usr/bin/env python
"""
Test script to verify machine data in exports
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import BatchPhaseExecution, Machine
from bmr.models import BatchManufacturingRecord
from products.models import Product
from accounts.models import CustomUser
from django.contrib.auth.models import User

def test_machine_export_data():
    """Test that machine data is included in exports"""
    print("Testing machine data in exports...")
    
    # Get a BMR with phases that have machine data
    bmr = BatchManufacturingRecord.objects.filter(status='in_progress').first()
    if not bmr:
        print("No in-progress BMR found, creating test data...")
        # Create test BMR if needed
        product = Product.objects.first()
        if not product:
            print("No products found - please ensure test data exists")
            return False
        
        qa_user = CustomUser.objects.filter(role='qa').first()
        if not qa_user:
            print("No QA user found")
            return False
            
        bmr = BatchManufacturingRecord.objects.create(
            bmr_number="TEST-001",
            product=product,
            batch_size=100,
            batch_number="0012025",
            manufacturing_date=datetime.now().date(),
            expiry_date=(datetime.now() + timedelta(days=730)).date(),
            created_by=qa_user,
            status='approved'
        )
        print(f"Created test BMR: {bmr.bmr_number}")
    
    # Check for phases with machine data
    phases_with_machines = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        machine_used__isnull=False
    )
    
    print(f"Found {phases_with_machines.count()} phases with machine data")
    
    for phase in phases_with_machines:
        print(f"Phase: {phase.phase.phase_name}")
        print(f"  Machine: {phase.machine_used}")
        print(f"  Breakdown occurred: {phase.breakdown_occurred}")
        print(f"  Breakdown start: {phase.breakdown_start_time}")
        print(f"  Breakdown end: {phase.breakdown_end_time}")
        print(f"  Changeover occurred: {phase.changeover_occurred}")
        print(f"  Changeover start: {phase.changeover_start_time}")
        print(f"  Changeover end: {phase.changeover_end_time}")
        print()
    
    # Test CSV export format
    print("Testing CSV export data format...")
    from dashboards.views import export_timeline_data
    from django.http import HttpRequest
    from django.contrib.auth import get_user_model
    
    # Create a mock request
    request = HttpRequest()
    request.user = CustomUser.objects.filter(is_superuser=True).first()
    request.GET = {'format': 'csv'}
    
    try:
        response = export_timeline_data(request)
        print(f"CSV export status: {response.status_code}")
        if response.status_code == 200:
            print("CSV export successful")
            # Check if response contains machine data headers
            content = response.content.decode('utf-8')
            if 'Machine Used' in content:
                print("✓ Machine Used column found in CSV")
            else:
                print("✗ Machine Used column NOT found in CSV")
                
            if 'Breakdown Occurred' in content:
                print("✓ Breakdown Occurred column found in CSV")
            else:
                print("✗ Breakdown Occurred column NOT found in CSV")
                
            if 'Changeover Occurred' in content:
                print("✓ Changeover Occurred column found in CSV")
            else:
                print("✗ Changeover Occurred column NOT found in CSV")
        else:
            print(f"CSV export failed with status: {response.status_code}")
    except Exception as e:
        print(f"CSV export error: {e}")
    
    # Test Excel export format
    print("\nTesting Excel export data format...")
    request.GET = {'format': 'excel'}
    
    try:
        response = export_timeline_data(request)
        print(f"Excel export status: {response.status_code}")
        if response.status_code == 200:
            print("Excel export successful")
            print("✓ Excel file generated (binary content)")
        else:
            print(f"Excel export failed with status: {response.status_code}")
    except Exception as e:
        print(f"Excel export error: {e}")
    
    return True

def check_machines_exist():
    """Check if machines exist in the system"""
    print("Checking machines in system...")
    machines = Machine.objects.all()
    print(f"Total machines: {machines.count()}")
    
    for machine in machines:
        print(f"  - {machine.name} ({machine.machine_type}) - Active: {machine.is_active}")
    
    if machines.count() == 0:
        print("No machines found - creating sample machines...")
        Machine.objects.create(name="Mixer-001", machine_type="mixing", is_active=True)
        Machine.objects.create(name="Compressor-001", machine_type="compression", is_active=True)
        Machine.objects.create(name="Filler-001", machine_type="tube_filling", is_active=True)
        print("Created 3 sample machines")

if __name__ == "__main__":
    print("=== Machine Export Test ===")
    check_machines_exist()
    print()
    test_machine_export_data()
    print("\n=== Test Complete ===")
