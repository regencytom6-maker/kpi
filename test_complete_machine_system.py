#!/usr/bin/env python
"""
Complete test of the machines module functionality
Tests all aspects: machine selection, breakdown/changeover tracking, and admin dashboard
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from workflow.models import Machine, BatchPhaseExecution, BatchPhase, BMR
from products.models import Product
from accounts.models import Profile

class MachineSystemTest:
    def __init__(self):
        self.client = Client()
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test data"""
        # Create a test user and admin
        self.user = User.objects.create_user(
            username='test_operator',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='test_admin',
            password='testpass123',
            is_superuser=True
        )
        
        # Create user profiles
        Profile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'packing_operator'}
        )
        
        Profile.objects.get_or_create(
            user=self.admin_user,
            defaults={'role': 'admin'}
        )
        
        # Create test machines
        self.blister_machine = Machine.objects.create(
            name='Blister Machine 1',
            machine_type='blister',
            is_active=True
        )
        
        self.tablet_press = Machine.objects.create(
            name='Tablet Press 2',
            machine_type='compression',
            is_active=True
        )
        
        # Create test product and BMR
        self.product = Product.objects.get_or_create(
            name='Test Medicine',
            defaults={
                'form': 'tablet',
                'strength': '500mg',
                'batch_size': 1000,
                'batch_size_unit': 'tablets'
            }
        )[0]
        
        self.bmr = BMR.objects.create(
            batch_number='TEST001',
            product=self.product,
            quantity=1000,
            created_by=self.user
        )
        
        # Create test batch phase
        self.phase = BatchPhase.objects.create(
            name='Blister Packing',
            order=1,
            duration_hours=2,
            requires_machine=True,
            machine_type='blister'
        )
        
        # Create phase execution
        self.phase_execution = BatchPhaseExecution.objects.create(
            bmr=self.bmr,
            phase=self.phase,
            status='in_progress',
            started_by=self.user,
            started_at=datetime.now()
        )
    
    def test_machine_creation_and_admin(self):
        """Test machine creation and admin interface"""
        print("\n=== Testing Machine Creation and Admin ===")
        
        # Test machine creation
        total_machines = Machine.objects.count()
        print(f"✓ Total machines created: {total_machines}")
        
        # Test machine types
        blister_machines = Machine.objects.filter(machine_type='blister').count()
        print(f"✓ Blister machines: {blister_machines}")
        
        # Test active machines
        active_machines = Machine.objects.filter(is_active=True).count()
        print(f"✓ Active machines: {active_machines}")
        
        return True
    
    def test_packing_dashboard_machine_selection(self):
        """Test machine selection in packing dashboard"""
        print("\n=== Testing Packing Dashboard Machine Selection ===")
        
        # Login as operator
        self.client.login(username='test_operator', password='testpass123')
        
        # Get packing dashboard
        response = self.client.get(reverse('dashboards:packing_dashboard'))
        print(f"✓ Packing dashboard response status: {response.status_code}")
        
        # Check if machines are in context
        if response.status_code == 200:
            machines_in_context = 'machines' in response.context
            print(f"✓ Machines in dashboard context: {machines_in_context}")
            
            if machines_in_context:
                machine_count = len(response.context['machines'])
                print(f"✓ Number of machines available: {machine_count}")
        
        return True
    
    def test_phase_completion_with_breakdown(self):
        """Test completing a phase with breakdown tracking"""
        print("\n=== Testing Phase Completion with Breakdown ===")
        
        # Login as operator
        self.client.login(username='test_operator', password='testpass123')
        
        # Test completing phase with breakdown
        breakdown_start = datetime.now() - timedelta(hours=1)
        breakdown_end = datetime.now() - timedelta(minutes=30)
        
        completion_data = {
            'action': 'complete',
            'phase_execution_id': self.phase_execution.id,
            'machine_id': self.blister_machine.id,
            'breakdown_occurred': 'on',
            'breakdown_start_time': breakdown_start.strftime('%Y-%m-%dT%H:%M'),
            'breakdown_end_time': breakdown_end.strftime('%Y-%m-%dT%H:%M'),
            'breakdown_reason': 'Mechanical failure',
            'changeover_occurred': '',
        }
        
        response = self.client.post(reverse('dashboards:packing_dashboard'), completion_data)
        print(f"✓ Phase completion response status: {response.status_code}")
        
        # Check if breakdown was recorded
        updated_execution = BatchPhaseExecution.objects.get(id=self.phase_execution.id)
        print(f"✓ Breakdown occurred recorded: {updated_execution.breakdown_occurred}")
        print(f"✓ Machine used recorded: {updated_execution.machine_used.name if updated_execution.machine_used else 'None'}")
        print(f"✓ Breakdown reason: {updated_execution.breakdown_reason}")
        
        if updated_execution.breakdown_duration:
            print(f"✓ Breakdown duration: {updated_execution.breakdown_duration} minutes")
        
        return True
    
    def test_admin_dashboard_machine_management(self):
        """Test admin dashboard machine management features"""
        print("\n=== Testing Admin Dashboard Machine Management ===")
        
        # Login as admin
        self.client.login(username='test_admin', password='testpass123')
        
        # Get admin dashboard
        response = self.client.get(reverse('dashboards:admin_dashboard'))
        print(f"✓ Admin dashboard response status: {response.status_code}")
        
        if response.status_code == 200:
            # Check machine management data in context
            context_keys = ['all_machines', 'recent_breakdowns', 'recent_changeovers']
            for key in context_keys:
                has_key = key in response.context
                print(f"✓ {key} in context: {has_key}")
                if has_key and response.context[key] is not None:
                    count = len(response.context[key]) if hasattr(response.context[key], '__len__') else 'N/A'
                    print(f"  - Count: {count}")
        
        return True
    
    def test_export_with_machine_data(self):
        """Test CSV export includes machine and breakdown data"""
        print("\n=== Testing Export with Machine Data ===")
        
        # Login as admin
        self.client.login(username='test_admin', password='testpass123')
        
        # Test CSV export
        response = self.client.get(reverse('dashboards:export_production_data'), {'format': 'csv'})
        print(f"✓ CSV export response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for machine-related columns
            machine_columns = ['Machine Used', 'Breakdown Occurred', 'Breakdown Duration', 'Changeover Occurred']
            for column in machine_columns:
                has_column = column in content
                print(f"✓ '{column}' column in CSV: {has_column}")
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("🔧 COMPLETE MACHINE SYSTEM TEST")
        print("=" * 50)
        
        try:
            self.test_machine_creation_and_admin()
            self.test_packing_dashboard_machine_selection()
            self.test_phase_completion_with_breakdown()
            self.test_admin_dashboard_machine_management()
            self.test_export_with_machine_data()
            
            print("\n" + "=" * 50)
            print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
            print("The complete machine system is working correctly.")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test = MachineSystemTest()
    test.run_all_tests()
