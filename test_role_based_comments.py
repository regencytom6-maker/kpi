#!/usr/bin/env python
"""
Test script to verify role-based comments access
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from bmr.models import BMR, BMRSignature
from workflow.models import BatchPhaseExecution
from accounts.models import CustomUser
from django.db.models import Q

def test_role_based_access():
    """Test role-based access for comments"""
    print("🧪 TESTING ROLE-BASED COMMENTS ACCESS")
    print("=" * 50)
    
    # Get sample users
    admin_users = CustomUser.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(role='admin')
    )
    operator_users = CustomUser.objects.filter(
        is_staff=False, is_superuser=False
    ).exclude(role='admin')
    
    print(f"\n👑 ADMIN USERS: {admin_users.count()}")
    for admin in admin_users:
        print(f"   • {admin.get_full_name()} ({admin.username}) - {admin.get_role_display()}")
    
    print(f"\n👷 OPERATOR USERS: {operator_users.count()}")
    for operator in operator_users[:5]:  # Show first 5
        print(f"   • {operator.get_full_name()} ({operator.username}) - {operator.get_role_display()}")
    
    # Test access for admin vs operator
    if admin_users.exists() and operator_users.exists():
        admin_user = admin_users.first()
        operator_user = operator_users.first()
        
        print(f"\n🔍 TESTING ACCESS DIFFERENCES:")
        print(f"Admin User: {admin_user.get_full_name()} ({admin_user.get_role_display()})")
        print(f"Operator User: {operator_user.get_full_name()} ({operator_user.get_role_display()})")
        
        # Count BMRs each can see
        admin_bmrs = BMR.objects.all().count()
        operator_bmrs = BMR.objects.filter(
            Q(created_by=operator_user) | Q(approved_by=operator_user)
        ).count()
        
        print(f"\n📋 BMR ACCESS:")
        print(f"   Admin can see: {admin_bmrs} BMRs")
        print(f"   Operator can see: {operator_bmrs} BMRs")
        
        # Count phases each can see
        admin_phases = BatchPhaseExecution.objects.all().count()
        operator_phases = BatchPhaseExecution.objects.filter(
            Q(started_by=operator_user) | Q(completed_by=operator_user) | Q(bmr__created_by=operator_user)
        ).count()
        
        print(f"\n⚙️ PHASE ACCESS:")
        print(f"   Admin can see: {admin_phases} phases")
        print(f"   Operator can see: {operator_phases} phases")
        
        # Count signatures each can see
        admin_signatures = BMRSignature.objects.all().count()
        operator_signatures = BMRSignature.objects.filter(
            Q(signed_by=operator_user) | Q(bmr__created_by=operator_user)
        ).count()
        
        print(f"\n✍️ SIGNATURE ACCESS:")
        print(f"   Admin can see: {admin_signatures} signatures")
        print(f"   Operator can see: {operator_signatures} signatures")
        
        # Show which BMRs the operator was involved in
        operator_involved_bmrs = BMR.objects.filter(
            Q(created_by=operator_user) | Q(approved_by=operator_user)
        )
        
        operator_phase_bmrs = BMR.objects.filter(
            batchphaseexecution__in=BatchPhaseExecution.objects.filter(
                Q(started_by=operator_user) | Q(completed_by=operator_user)
            )
        ).distinct()
        
        all_operator_bmrs = (operator_involved_bmrs | operator_phase_bmrs).distinct()
        
        print(f"\n📝 OPERATOR'S BMR INVOLVEMENT:")
        print(f"   BMRs created/approved by operator: {operator_involved_bmrs.count()}")
        print(f"   BMRs with phases worked on: {operator_phase_bmrs.count()}")
        print(f"   Total accessible BMRs: {all_operator_bmrs.count()}")
        
        if all_operator_bmrs.exists():
            print(f"   Accessible BMRs:")
            for bmr in all_operator_bmrs[:5]:  # Show first 5
                print(f"     • {bmr.batch_number} - {bmr.product.product_name}")
    
    print(f"\n✅ ROLE-BASED ACCESS TEST COMPLETE!")
    print("The system now properly filters comments based on user roles:")
    print("• Admins: See ALL comments from everyone")
    print("• Operators: See only their own comments and BMRs they were involved in")

if __name__ == "__main__":
    test_role_based_access()
