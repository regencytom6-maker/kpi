from django.utils import timezone
from bmr.models import BMR
from .models import ProductionPhase, BatchPhaseExecution

class WorkflowService:
    """Service to manage workflow progression and phase automation"""
    
    # Define the workflow sequences for each product type
    PRODUCT_WORKFLOWS = {
        'ointment': [
            'bmr_creation',
            'regulatory_approval', 
            'material_dispensing',
            'mixing',
            'post_mixing_qc',  # QC test after mixing - rolls back to mixing if failed
            'tube_filling',
            'packaging_material_release',  # Packaging materials released BEFORE secondary packaging
            'secondary_packaging',
            'final_qa',
            'finished_goods_store'
        ],
        'tablet': [
            'bmr_creation',
            'regulatory_approval',
            'material_dispensing', 
            'granulation',
            'blending',
            'compression',
            'post_compression_qc',  # QC test after compression - rolls back to blending if failed
            'sorting',
            'coating',  # Will be skipped if tablet is not coated
            'packaging_material_release',  # Packaging materials released BEFORE packing
            'blister_packing',  # Default packing for normal tablets (or bulk_packing for tablet_2)
            'secondary_packaging',
            'final_qa',
            'finished_goods_store'
        ],
        'capsule': [
            'bmr_creation',
            'regulatory_approval',
            'material_dispensing',
            'drying',
            'blending',
            'post_blending_qc',  # QC test after blending - rolls back to blending if failed
            'filling',
            'sorting',  # Sorting after filling for capsules
            'packaging_material_release',  # Packaging materials released BEFORE packing
            'blister_packing',
            'secondary_packaging', 
            'final_qa',
            'finished_goods_store'
        ]
    }
    
    @classmethod
    def initialize_workflow_for_bmr(cls, bmr):
        """Initialize all workflow phases for a new BMR"""
        product_type = bmr.product.product_type
        workflow_phases = cls.PRODUCT_WORKFLOWS.get(product_type, [])
        
        if not workflow_phases:
            raise ValueError(f"No workflow defined for product type: {product_type}")
        
        # Customize workflow based on product specifics
        if product_type == 'tablet':
            # Skip coating phase if tablet is not coated
            if not bmr.product.is_coated and 'coating' in workflow_phases:
                workflow_phases = [phase for phase in workflow_phases if phase != 'coating']
            
            # Change packing based on tablet type
            if bmr.product.tablet_type == 'tablet_2':
                # Replace blister_packing with bulk_packing for tablet type 2
                workflow_phases = [
                    'bulk_packing' if phase == 'blister_packing' else phase 
                    for phase in workflow_phases
                ]
        
        # Create phase executions for all phases in the workflow
        for order, phase_name in enumerate(workflow_phases, 1):
            try:
                # Get or create the production phase definition with correct order
                phase, created = ProductionPhase.objects.get_or_create(
                    product_type=product_type,
                    phase_name=phase_name,
                    defaults={
                        'phase_order': order,
                        'is_mandatory': True,
                        'requires_approval': phase_name in ['regulatory_approval', 'final_qa']
                    }
                )
                
                # Update phase order if it exists but has wrong order
                if not created and phase.phase_order != order:
                    phase.phase_order = order
                    phase.save()
                
                # Create the batch phase execution with proper initial status
                # Only the first few phases should be pending initially
                if phase_name == 'bmr_creation':
                    initial_status = 'completed'
                elif phase_name in ['regulatory_approval']:
                    initial_status = 'pending'  # Next immediate phase after BMR creation
                else:
                    initial_status = 'not_ready'  # All other phases wait for prerequisites
                
                BatchPhaseExecution.objects.get_or_create(
                    bmr=bmr,
                    phase=phase,
                    defaults={
                        'status': initial_status
                    }
                )
                
            except Exception as e:
                print(f"Error creating phase {phase_name} for BMR {bmr.bmr_number}: {e}")
    
    @classmethod
    def get_current_phase(cls, bmr):
        """Get the current active phase for a BMR"""
        return BatchPhaseExecution.objects.filter(
            bmr=bmr,
            status__in=['pending', 'in_progress']
        ).order_by('phase__phase_order').first()
    
    @classmethod
    def get_next_phase(cls, bmr):
        """Get the next available phase for a BMR (pending or not_ready)"""
        current_executions = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).order_by('phase__phase_order')
        
        # Find the first pending phase
        for execution in current_executions:
            if execution.status == 'pending':
                return execution
        
        # If no pending phases, find the first not_ready phase
        for execution in current_executions:
            if execution.status == 'not_ready':
                return execution
        
        return None
    
    @classmethod
    def complete_phase(cls, bmr, phase_name, completed_by, comments=None):
        """Mark a phase as completed and activate the next phase"""
        try:
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Mark current phase as completed
            execution.status = 'completed'
            execution.completed_by = completed_by
            execution.completed_date = timezone.now()
            if comments:
                execution.operator_comments = comments
            execution.save()
            
            # Activate next phase by finding the next 'not_ready' phase in sequence
            next_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=execution.phase.phase_order,
                status='not_ready'
            ).order_by('phase__phase_order')
            
            if next_phases.exists():
                next_phase = next_phases.first()
                next_phase.status = 'pending'  # Make it available for operators
                next_phase.save()
                return next_phase
                
        except BatchPhaseExecution.DoesNotExist:
            print(f"Phase execution not found: {phase_name} for BMR {bmr.bmr_number}")
        
        return None
    
    @classmethod
    def start_phase(cls, bmr, phase_name, started_by):
        """Start a phase execution - with prerequisite validation"""
        try:
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name,
                status='pending'
            )
            
            # Validate that all prerequisite phases are completed
            if not cls.can_start_phase(bmr, phase_name):
                print(f"Cannot start phase {phase_name} for BMR {bmr.bmr_number} - prerequisites not met")
                return None
            
            execution.status = 'in_progress'
            execution.started_by = started_by
            execution.started_date = timezone.now()
            execution.save()
            
            return execution
            
        except BatchPhaseExecution.DoesNotExist:
            print(f"Cannot start phase {phase_name} for BMR {bmr.bmr_number} - not pending")
        
        return None
    
    @classmethod
    def can_start_phase(cls, bmr, phase_name):
        """Check if a phase can be started (all prerequisites completed)"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Cannot start phases that are not pending
            if current_execution.status != 'pending':
                return False
            
            # Get all phases with lower order (prerequisites)
            prerequisite_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__lt=current_execution.phase.phase_order
            )
            
            # Check if all prerequisite phases are completed or skipped
            for prereq in prerequisite_phases:
                if prereq.status not in ['completed', 'skipped']:
                    return False
            
            return True
            
        except BatchPhaseExecution.DoesNotExist:
            return False
    
    @classmethod
    def get_workflow_status(cls, bmr):
        """Get complete workflow status for a BMR"""
        executions = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).select_related('phase').order_by('phase__phase_order')
        
        total_phases = executions.count()
        completed_phases = executions.filter(status='completed').count()
        current_phase = cls.get_current_phase(bmr)
        next_phase = cls.get_next_phase(bmr)
        
        return {
            'total_phases': total_phases,
            'completed_phases': completed_phases,
            'progress_percentage': (completed_phases / total_phases * 100) if total_phases > 0 else 0,
            'current_phase': current_phase,
            'next_phase': next_phase,
            'all_executions': executions,
            'is_complete': completed_phases == total_phases
        }
    
    @classmethod
    def handle_qc_failure_rollback(cls, bmr, failed_phase_name, rollback_to_phase):
        """Handle QC failure and rollback to a previous phase"""
        try:
            # Mark the failed QC phase as failed
            failed_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=failed_phase_name,
                status='in_progress'
            )
            failed_execution.status = 'failed'
            failed_execution.completed_date = timezone.now()
            failed_execution.save()
            
            # Reset phases after the rollback point to pending
            # Find the rollback phase order
            rollback_phase = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=rollback_to_phase
            )
            
            # Reset all phases after the rollback phase to pending
            phases_to_reset = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=rollback_phase.phase.phase_order,
                status__in=['completed', 'failed', 'in_progress']
            )
            
            for phase_execution in phases_to_reset:
                phase_execution.status = 'pending'
                phase_execution.started_by = None
                phase_execution.started_date = None
                phase_execution.completed_by = None
                phase_execution.completed_date = None
                phase_execution.operator_comments = ''
                phase_execution.save()
            
            # Set the rollback phase to pending (to be redone)
            rollback_phase.status = 'pending'
            rollback_phase.started_by = None
            rollback_phase.started_date = None
            rollback_phase.completed_by = None
            rollback_phase.completed_date = None
            rollback_phase.operator_comments = ''
            rollback_phase.save()
            
            return True
            
        except Exception as e:
            print(f"Error handling QC rollback for BMR {bmr.bmr_number}: {e}")
            return False
    
    @classmethod
    def trigger_next_phase(cls, bmr, current_phase):
        """Trigger the next phase in the workflow after completing current phase"""
        try:
            # Instead of using workflow array, find the next phase by phase_order
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase=current_phase
            )
            
            # Find the next phase in sequence by phase_order
            next_execution = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=current_execution.phase.phase_order,
                status='not_ready'
            ).order_by('phase__phase_order').first()
            
            if next_execution:
                # Handle special skipping logic for coating
                if next_execution.phase.phase_name == 'coating' and not bmr.product.is_coated:
                    # Skip coating phase
                    next_execution.status = 'skipped'
                    next_execution.completed_date = timezone.now()
                    next_execution.operator_comments = "Phase skipped - product does not require coating"
                    next_execution.save()
                    print(f"Skipped coating phase for BMR {bmr.batch_number}")
                    # Find the next phase after coating
                    return cls.trigger_next_phase(bmr, next_execution.phase)
                else:
                    # Normal activation
                    next_execution.status = 'pending'
                    next_execution.save()
                    print(f"Triggered next phase: {next_execution.phase.phase_name} for BMR {bmr.batch_number}")
                    return True
            else:
                print(f"No more phases to trigger for BMR {bmr.batch_number}")
            
            return False
            
        except BatchPhaseExecution.DoesNotExist:
            print(f"Current phase execution not found for BMR {bmr.batch_number}")
            return False
        except Exception as e:
            print(f"Error triggering next phase for BMR {bmr.batch_number}: {e}")
            return False
        except Exception as e:
            print(f"Error triggering next phase for BMR {bmr.batch_number}: {e}")
            return False
    
    @classmethod
    def rollback_to_previous_phase(cls, bmr, failed_phase):
        """Rollback to previous phase when QC fails"""
        try:
            # Define QC rollback mapping
            qc_rollback_mapping = {
                'post_compression_qc': 'blending',  # Roll back to blending, not compression
                'post_mixing_qc': 'mixing',
                'post_blending_qc': 'blending',
            }
            
            failed_phase_name = failed_phase.phase_name
            rollback_to_phase = qc_rollback_mapping.get(failed_phase_name)
            
            if rollback_to_phase:
                return cls.handle_qc_failure_rollback(bmr, failed_phase_name, rollback_to_phase)
            
            return False
        except Exception as e:
            print(f"Error rolling back for BMR {bmr.batch_number}: {e}")
            return False
    
    @classmethod
    def get_phases_for_user_role(cls, bmr, user_role):
        """Get phases that a specific user role can work on"""
        # Map user roles to phases they can handle
        role_phase_mapping = {
            'qa': ['bmr_creation', 'final_qa'],
            'regulatory': ['regulatory_approval'],
            'store_manager': ['material_dispensing'],  # Store Manager only handles material dispensing
            'packaging_store': ['packaging_material_release'],  # Packaging store handles packaging material release
            'finished_goods_store': ['finished_goods_store'],  # Finished Goods Store only handles finished goods storage
            'qc': ['post_compression_qc', 'post_mixing_qc', 'post_blending_qc'],
            'mixing_operator': ['mixing'],
            'granulation_operator': ['granulation'],
            'blending_operator': ['blending'],
            'compression_operator': ['compression'],
            'coating_operator': ['coating'],
            'drying_operator': ['drying'],
            'filling_operator': ['filling'],
            'tube_filling_operator': ['tube_filling'],
            'packing_operator': ['blister_packing', 'bulk_packing', 'secondary_packaging'],
            'sorting_operator': ['sorting'],
        }
        
        allowed_phases = role_phase_mapping.get(user_role, [])
        
        return BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name__in=allowed_phases,
            status__in=['pending', 'in_progress']
        ).select_related('phase').order_by('phase__phase_order')
