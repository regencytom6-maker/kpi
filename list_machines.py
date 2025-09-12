import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from workflow.models import Machine

def display_machines():
    print("\n=== EQUIPMENT INVENTORY ===\n")
    
    for machine_type, display_name in Machine.MACHINE_TYPE_CHOICES:
        machines = Machine.objects.filter(machine_type=machine_type)
        
        print(f"\n{display_name.upper()} MACHINES ({machines.count()}):")
        
        if machines.exists():
            for machine in machines:
                status = "✓ Active" if machine.is_active else "✗ Inactive"
                print(f"  - {machine.name} [{status}]")
        else:
            print("  No machines of this type")
    
    print(f"\n\nTOTAL MACHINES: {Machine.objects.count()}")
    print(f"ACTIVE MACHINES: {Machine.objects.filter(is_active=True).count()}")
    print(f"INACTIVE MACHINES: {Machine.objects.filter(is_active=False).count()}")

if __name__ == "__main__":
    display_machines()
