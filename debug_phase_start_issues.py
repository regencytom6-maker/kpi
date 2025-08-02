#!/usr/bin/env python
"""
Comprehensive Phase Start Diagnosis Script
Checks why operators can't start phases in granulation, mixing, and other operations
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR
from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from accounts.models import CustomUser
from django.utils import timezone

def diagnose_phase_start_issues():
    """Complete diagnosis of phase start issues"""
    
    print("=" * 60)
    print("🔧 PHASE START DIAGNOSIS - COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    
    # 1. Check all BMRs and their phase statuses
    print("\n📋 1. BMR AND PHASE STATUS OVERVIEW")
    print("-" * 40)
    
    bmrs = BMR.objects.select_related('product').all()
    print(f"Total BMRs: {bmrs.count()}")
    
    for bmr in bmrs:
        print(f"\n🏭 BMR {bmr.batch_number}: {bmr.product.product_name} ({bmr.product.product_type})")
        print(f"   Status: {bmr.status}")
        
        # Get all phases for this BMR
        phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
        
        for phase in phases:
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌',
                'not_ready': '⚫',
                'skipped': '⏭️'
            }.get(phase.status, '❓')
            
            print(f"   {status_icon} {phase.phase.phase_name} (order {phase.phase.phase_order}): {phase.status}")
    
    # 2. Check operator roles and permissions
    print("\n\n👤 2. OPERATOR ROLES AND PERMISSIONS")
    print("-" * 40)
    
    operators = CustomUser.objects.filter(role__contains='operator')
    print(f"Found {operators.count()} operators:")
    
    for operator in operators:
        print(f"\n👨‍🔬 {operator.username} ({operator.role})")
        
        # Check what phases this operator can see across all BMRs
        operator_phases = []
        for bmr in bmrs:
            try:
                user_phases = WorkflowService.get_phases_for_user_role(bmr, operator.role)
                operator_phases.extend(user_phases)
            except Exception as e:
                print(f"   ❌ Error getting phases for {bmr.batch_number}: {e}")
        
        if operator_phases:
            print(f"   Can work on {len(operator_phases)} phases:")
            pending_count = len([p for p in operator_phases if p.status == 'pending'])
            in_progress_count = len([p for p in operator_phases if p.status == 'in_progress'])
            print(f"   • Pending: {pending_count}")
            print(f"   • In Progress: {in_progress_count}")
            
            # Show specific pending phases
            pending_phases = [p for p in operator_phases if p.status == 'pending']
            for phase in pending_phases[:3]:  # Show first 3
                can_start = WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)
                start_icon = "🚀" if can_start else "🚫"
                print(f"   {start_icon} {phase.phase.phase_name} (BMR {phase.bmr.batch_number}) - Can start: {can_start}")
        else:
            print("   ❌ No phases available")
    
    # 3. Deep dive into specific phase start issues
    print("\n\n🔍 3. PHASE START VALIDATION ANALYSIS")
    print("-" * 40)
    
    # Find all pending phases that should be startable
    pending_phases = BatchPhaseExecution.objects.filter(status='pending').select_related('bmr', 'phase')
    print(f"Found {pending_phases.count()} pending phases")
    
    for phase in pending_phases:
        print(f"\n🔬 Testing: {phase.phase.phase_name} for BMR {phase.bmr.batch_number}")
        
        # Test can_start_phase
        can_start = WorkflowService.can_start_phase(phase.bmr, phase.phase.phase_name)
        print(f"   Can start: {can_start}")
        
        if not can_start:
            print("   🚫 BLOCKED - Checking prerequisites...")
            
            # Check prerequisite phases
            prereq_phases = BatchPhaseExecution.objects.filter(
                bmr=phase.bmr,
                phase__phase_order__lt=phase.phase.phase_order
            ).order_by('phase__phase_order')
            
            blocking_phases = []
            for prereq in prereq_phases:
                if prereq.status not in ['completed', 'skipped']:
                    blocking_phases.append(prereq)
                    print(f"   ❌ {prereq.phase.phase_name} (order {prereq.phase.phase_order}): {prereq.status}")
                else:
                    print(f"   ✅ {prereq.phase.phase_name} (order {prereq.phase.phase_order}): {prereq.status}")
            
            if blocking_phases:
                print(f"   💡 FIX: Complete {len(blocking_phases)} blocking phase(s) first")
            else:
                print("   ⚠️ All prerequisites met but still can't start - check can_start_phase logic")
        else:
            print("   ✅ READY TO START")
    
    # 4. Check WorkflowService role mapping
    print("\n\n⚙️ 4. WORKFLOW SERVICE ROLE MAPPING")
    print("-" * 40)
    
    # Test the role mapping logic
    role_phase_map = {
        'mixing_operator': ['mixing', 'post_mixing_qc'],
        'granulation_operator': ['granulation', 'drying'],
        'blending_operator': ['blending', 'post_blending_qc'],
        'compression_operator': ['compression', 'post_compression_qc'],
        'coating_operator': ['coating'],
        'packing_operator': ['blister_packing', 'bulk_packing', 'secondary_packaging'],
        'store_manager': ['material_dispensing', 'packaging_material_release'],
        'qc': ['post_mixing_qc', 'post_blending_qc', 'post_compression_qc'],
        'qa': ['final_qa'],
        'regulatory': ['regulatory_approval']
    }
    
    print("Expected role-to-phase mappings:")
    for role, expected_phases in role_phase_map.items():
        print(f"\n🎯 {role}:")
        print(f"   Expected phases: {', '.join(expected_phases)}")
        
        # Test with a sample BMR
        if bmrs.exists():
            test_bmr = bmrs.first()
            try:
                actual_phases = WorkflowService.get_phases_for_user_role(test_bmr, role)
                actual_phase_names = [p.phase.phase_name for p in actual_phases]
                print(f"   Actual phases: {', '.join(actual_phase_names)}")
                
                # Check for mismatches
                missing = set(expected_phases) - set(actual_phase_names)
                extra = set(actual_phase_names) - set(expected_phases)
                
                if missing:
                    print(f"   ❌ Missing: {', '.join(missing)}")
                if extra:
                    print(f"   ➕ Extra: {', '.join(extra)}")
                if not missing and not extra:
                    print("   ✅ Perfect match")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # 5. Check ProductionPhase definitions
    print("\n\n📚 5. PRODUCTION PHASE DEFINITIONS")
    print("-" * 40)
    
    phase_definitions = ProductionPhase.objects.all().order_by('product_type', 'phase_order')
    current_product_type = None
    
    for phase_def in phase_definitions:
        if phase_def.product_type != current_product_type:
            current_product_type = phase_def.product_type
            print(f"\n📦 {current_product_type.upper()} WORKFLOW:")
        
        print(f"   {phase_def.phase_order:2d}. {phase_def.phase_name}")
    
    # 6. Quick fixes and recommendations
    print("\n\n🔧 6. QUICK FIXES AND RECOMMENDATIONS")
    print("-" * 40)
    
    # Find phases that need status updates
    not_ready_phases = BatchPhaseExecution.objects.filter(status='not_ready')
    print(f"Phases in 'not_ready' status: {not_ready_phases.count()}")
    
    if not_ready_phases.count() > 0:
        print("   💡 These phases might need to be changed to 'pending' to be startable")
        for phase in not_ready_phases[:5]:  # Show first 5
            print(f"   • {phase.phase.phase_name} (BMR {phase.bmr.batch_number})")
    
    # Find BMRs stuck in regulatory approval
    regulatory_pending = BatchPhaseExecution.objects.filter(
        phase__phase_name='regulatory_approval',
        status='pending'
    )
    
    if regulatory_pending.exists():
        print(f"\nBMRs waiting for regulatory approval: {regulatory_pending.count()}")
        print("   💡 These need regulatory approval before workflow can proceed")
        for phase in regulatory_pending:
            print(f"   • BMR {phase.bmr.batch_number}")
    
    # Check for completed BMRs that might need final cleanup
    completed_bmrs = BMR.objects.filter(status='approved')
    print(f"\nApproved BMRs: {completed_bmrs.count()}")
    
    for bmr in completed_bmrs:
        next_pending = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            status='pending'
        ).first()
        
        if next_pending:
            print(f"   🚀 BMR {bmr.batch_number}: Next phase '{next_pending.phase.phase_name}' ready to start")
    
    print("\n" + "=" * 60)
    print("✅ DIAGNOSIS COMPLETE")
    print("Check the output above for specific issues and recommendations")
    print("=" * 60)

if __name__ == '__main__':
    diagnose_phase_start_issues()
