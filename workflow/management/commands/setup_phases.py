from django.core.management.base import BaseCommand
from workflow.models import ProductionPhase

class Command(BaseCommand):
    help = 'Initialize production phases for all product types'

    def handle(self, *args, **options):
        """Create production phases for different product types"""
        
        # Ointment workflow phases
        ointment_phases = [
            ('bmr_creation', 1, True, False),
            ('regulatory_approval', 2, True, True),
            ('material_dispensing', 3, True, False),
            ('mixing', 4, True, False),
            ('quality_control', 5, True, True),
            ('tube_filling', 6, True, False),
            ('packaging_material_release', 7, True, False),
            ('secondary_packaging', 8, True, False),
            ('final_qa', 9, True, True),
            ('finished_goods_store', 10, True, False),
        ]
        
        # Tablet Normal workflow phases
        tablet_normal_phases = [
            ('bmr_creation', 1, True, False),
            ('regulatory_approval', 2, True, True),
            ('material_dispensing', 3, True, False),
            ('granulation', 4, True, False),
            ('blending', 5, True, False),
            ('compression', 6, True, False),
            ('quality_control', 7, True, True),
            ('sorting', 8, True, False),
            ('coating', 9, False, False),  # Optional for coated tablets
            ('packaging_material_release', 10, True, False),
            ('blister_packing', 11, True, False),
            ('secondary_packaging', 12, True, False),
            ('final_qa', 13, True, True),
            ('finished_goods_store', 14, True, False),
        ]
        
        # Tablet 2 workflow phases (bulk packing instead of blister)
        tablet_2_phases = [
            ('bmr_creation', 1, True, False),
            ('regulatory_approval', 2, True, True),
            ('material_dispensing', 3, True, False),
            ('granulation', 4, True, False),
            ('blending', 5, True, False),
            ('compression', 6, True, False),
            ('quality_control', 7, True, True),
            ('sorting', 8, True, False),
            ('coating', 9, False, False),  # Optional for coated tablets
            ('packaging_material_release', 10, True, False),
            ('bulk_packing', 11, True, False),
            ('secondary_packaging', 12, True, False),
            ('final_qa', 13, True, True),
            ('finished_goods_store', 14, True, False),
        ]
        
        # Capsule workflow phases
        capsule_phases = [
            ('bmr_creation', 1, True, False),
            ('regulatory_approval', 2, True, True),
            ('material_dispensing', 3, True, False),
            ('drying', 4, True, False),
            ('blending', 5, True, False),
            ('quality_control', 6, True, True),
            ('filling', 7, True, False),
            ('sorting', 8, True, False),
            ('packaging_material_release', 9, True, False),
            ('blister_packing', 10, True, False),
            ('secondary_packaging', 11, True, False),
            ('final_qa', 12, True, True),
            ('finished_goods_store', 13, True, False),
        ]
        
        # Create phases for each product type
        workflows = [
            ('ointment', ointment_phases),
            ('tablet_normal', tablet_normal_phases),
            ('tablet_2', tablet_2_phases),
            ('capsule', capsule_phases),
        ]
        
        created_count = 0
        for product_type, phases in workflows:
            for phase_name, order, mandatory, requires_approval in phases:
                phase, created = ProductionPhase.objects.get_or_create(
                    product_type=product_type,
                    phase_name=phase_name,
                    defaults={
                        'phase_order': order,
                        'is_mandatory': mandatory,
                        'requires_approval': requires_approval,
                        'estimated_duration_hours': self.get_estimated_duration(phase_name)
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        f"Created phase: {product_type} - {phase_name}"
                    )
        
        # Set rollback phases for quality control failures
        self.set_rollback_phases()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} production phases'
            )
        )
    
    def get_estimated_duration(self, phase_name):
        """Get estimated duration for each phase type"""
        durations = {
            'bmr_creation': 2.0,
            'regulatory_approval': 4.0,
            'material_dispensing': 1.0,
            'mixing': 3.0,
            'granulation': 4.0,
            'blending': 2.0,
            'compression': 3.0,
            'drying': 8.0,
            'quality_control': 2.0,
            'tube_filling': 2.0,
            'filling': 2.0,
            'sorting': 1.0,
            'coating': 3.0,
            'packaging_material_release': 0.5,
            'blister_packing': 2.0,
            'bulk_packing': 1.5,
            'secondary_packaging': 1.0,
            'final_qa': 1.0,
            'finished_goods_store': 0.5,
        }
        return durations.get(phase_name, 1.0)
    
    def set_rollback_phases(self):
        """Set rollback phases for quality control failures"""
        rollback_mappings = [
            # For ointments: QC failure goes back to mixing
            ('ointment', 'quality_control', 'mixing'),
            # For tablets: QC failure goes back to blending
            ('tablet_normal', 'quality_control', 'blending'),
            ('tablet_2', 'quality_control', 'blending'),
            # For capsules: QC failure goes back to blending
            ('capsule', 'quality_control', 'blending'),
            # Final QA failures
            ('ointment', 'final_qa', 'secondary_packaging'),
            ('tablet_normal', 'final_qa', 'blister_packing'),
            ('tablet_2', 'final_qa', 'bulk_packing'),
            ('capsule', 'final_qa', 'blister_packing'),
        ]
        
        for product_type, phase_name, rollback_phase_name in rollback_mappings:
            try:
                phase = ProductionPhase.objects.get(
                    product_type=product_type,
                    phase_name=phase_name
                )
                rollback_phase = ProductionPhase.objects.get(
                    product_type=product_type,
                    phase_name=rollback_phase_name
                )
                phase.can_rollback_to = rollback_phase
                phase.save()
                
                self.stdout.write(
                    f"Set rollback: {product_type} {phase_name} -> {rollback_phase_name}"
                )
            except ProductionPhase.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"Could not set rollback for {product_type} {phase_name}"
                    )
                )
