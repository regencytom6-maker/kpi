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
            'raw_material_release',      # NEW: Store manager releases materials
            'material_dispensing',       # Dispensing manager dispenses materials
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
            'raw_material_release',      # NEW: Store manager releases materials
            'material_dispensing',       # Dispensing manager dispenses materials
            'granulation',
            'blending',
            'compression',
            'post_compression_qc',  # QC test after compression - rolls back to blending if failed
            'sorting',
            'coating',  # Will be skipped if tablet is not coated
            'packaging_material_release',  # Packaging materials released IMMEDIATELY AFTER coating
            'blister_packing',  # Default packing for normal tablets (or bulk_packing for tablet_2)
            'secondary_packaging',
            'final_qa',
            'finished_goods_store'
        ],
        'capsule': [
            'bmr_creation',
            'regulatory_approval',
            'raw_material_release',      # NEW: Store manager releases materials
            'material_dispensing',       # Dispensing manager dispenses materials
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
        """Initialize all workflow phases for a new BMR using the correct system workflow"""
        product_type = bmr.product.product_type
        
        # Use the PRODUCT_WORKFLOWS dictionary which includes raw_material_release
        base_workflow = cls.PRODUCT_WORKFLOWS.get(product_type, [])
        if not base_workflow:
            raise ValueError(f"No workflow defined for product type: {product_type}")
        
        # Make a copy to avoid modifying the original
        workflow_phases = base_workflow.copy()
        
        # Handle tablet-specific logic for coating and packing types
        if product_type == 'tablet':
            # Handle coating - skip if not coated
            if not getattr(bmr.product, 'is_coated', False):
                if 'coating' in workflow_phases:
                    workflow_phases.remove('coating')
            
            # Handle packing type for tablets
            if getattr(bmr.product, 'tablet_type', None) == 'tablet_2':
                # TABLET_2 uses bulk_packing instead of blister_packing
                if 'blister_packing' in workflow_phases:
                    index = workflow_phases.index('blister_packing')
                    workflow_phases[index] = 'bulk_packing'
                    
        # Handle capsule-specific logic for packing types
        if product_type == 'capsule':
            # Handle bulk capsules
            if getattr(bmr.product, 'capsule_type', None) == 'bulk':
                # Bulk capsules use bulk_packing instead of blister_packing
                if 'blister_packing' in workflow_phases:
                    index = workflow_phases.index('blister_packing')
                    workflow_phases[index] = 'bulk_packing'
        
        # Remove any duplicate phases that might exist
        seen = set()
        workflow_phases = [x for x in workflow_phases if not (x in seen or seen.add(x))]

        # Remove any accidental duplicates
        seen = set()
        workflow_phases = [x for x in workflow_phases if not (x in seen or seen.add(x))]
        
        # Create phase executions for all phases in the workflow
        for order, phase_name in enumerate(workflow_phases, 1):
            try:
                # Get or create the production phase definition with ENFORCED correct order
                phase, created = ProductionPhase.objects.get_or_create(
                    product_type=product_type,
                    phase_name=phase_name,
                    defaults={
                        'phase_order': order,
                        'is_mandatory': True,
                        'requires_approval': phase_name in ['regulatory_approval', 'final_qa']
                    }
                )
                
                # CRITICAL: Always update phase order to ensure consistency
                if phase.phase_order != order:
                    phase.phase_order = order
                    phase.save()
                    print(f"Updated phase order for {phase_name} to {order}")
                
                # Create the batch phase execution with proper initial status
                if phase_name == 'bmr_creation':
                    initial_status = 'completed'
                elif phase_name == 'regulatory_approval':
                    initial_status = 'pending'
                elif phase_name == 'raw_material_release':
                    initial_status = 'not_ready'  # Will be activated when regulatory approval completes
                elif phase_name == 'material_dispensing':
                    initial_status = 'not_ready'  # Will be activated when raw material release completes
                else:
                    initial_status = 'not_ready'
                
                BatchPhaseExecution.objects.get_or_create(
                    bmr=bmr,
                    phase=phase,
                    defaults={
                        'status': initial_status
                    }
                )
                
            except Exception as e:
                print(f"Error creating phase {phase_name} for BMR {bmr.bmr_number}: {e}")
        
        print(f"Initialized workflow for {bmr.batch_number} ({product_type}) with {len(workflow_phases)} phases")
    
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
                
                # Store notification data in session if available
                from django.contrib import messages
                if hasattr(completed_by, 'request') and hasattr(completed_by.request, 'session'):
                    completed_by.request.session['completed_phase'] = phase_name
                    completed_by.request.session['completed_bmr'] = bmr.id
                    if next_phase:
                        next_phase_name = next_phase.phase.get_phase_name_display()
                        if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2' and phase_name == 'packaging_material_release':
                            next_phase_name = 'Bulk Packing'  # Force correct next phase name
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
            
            print(f"\n*** HANDLING QC FAILURE ROLLBACK FOR BMR {bmr.bmr_number} ***")
            print(f"Failed phase: {failed_phase_name}")
            print(f"Rolling back to: {rollback_to_phase}")
            
            # Reset phases after the rollback point to pending
            # Find the rollback phase order
            try:
                rollback_phase = BatchPhaseExecution.objects.get(
                    bmr=bmr,
                    phase__phase_name=rollback_to_phase
                )
            except BatchPhaseExecution.DoesNotExist:
                print(f"Error: Rollback phase '{rollback_to_phase}' doesn't exist for BMR {bmr.bmr_number}")
                print("Creating the required phase...")
                
                # Get the phase definition without directly importing the Phase model
                try:
                    # Use filter to find the Phase object from existing BatchPhaseExecution objects
                    example_phase = BatchPhaseExecution.objects.filter(
                        phase__phase_name=rollback_to_phase
                    ).first()
                    
                    if example_phase:
                        # Create the missing phase execution
                        rollback_phase = BatchPhaseExecution.objects.create(
                            bmr=bmr,
                            phase=example_phase.phase,
                            status='pending',
                            operator_comments=f'Auto-created for reprocessing after {failed_phase_name} failure'
                        )
                        print(f"Created new {rollback_to_phase} phase for BMR {bmr.bmr_number}")
                    else:
                        print(f"Error: Cannot find a template for phase '{rollback_to_phase}'")
                        return False
                except Exception as e:
                    print(f"Error creating phase: {e}")
                    return False
            
            print(f"Found rollback phase: {rollback_phase.phase.phase_name} (ID: {rollback_phase.id})")
            
            # Get all phases in sequence between rollback and QC phase
            phases_in_sequence = []
            if failed_phase_name == 'post_compression_qc' and rollback_to_phase == 'granulation':
                # For post_compression_qc failures, ensure we maintain the proper sequence
                sequence = ['granulation', 'blending', 'compression', 'post_compression_qc']
                
                # Find all phases in the proper sequence
                for phase_name in sequence:
                    phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name=phase_name
                    ).first()
                    if phase:
                        phases_in_sequence.append(phase)
                        print(f"Added {phase_name} phase to sequence (ID: {phase.id})")
            
            # Reset all phases after the rollback phase to pending
            # If phases_in_sequence is populated, we'll handle those specially
            if phases_in_sequence:
                # Only reset phases that aren't in our sequence
                phases_to_reset = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_order__gt=rollback_phase.phase.phase_order,
                    phase__phase_name__isnull=True  # This will be replaced below
                )
                # Exclude the sequence phases from general reset
                sequence_phase_names = [p.phase.phase_name for p in phases_in_sequence]
                phases_to_reset = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_order__gt=rollback_phase.phase.phase_order
                ).exclude(phase__phase_name__in=sequence_phase_names)
            else:
                # Original logic - reset all phases after rollback
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
                print(f"Reset phase {phase_execution.phase.phase_name} to pending (ID: {phase_execution.id})")
            
            # Set the rollback phase to pending (to be redone)
            rollback_phase.status = 'pending'
            rollback_phase.started_by = None
            rollback_phase.started_date = None
            rollback_phase.completed_by = None
            rollback_phase.completed_date = None
            # Add a clear comment indicating this is a reprocessing after QC failure
            rollback_phase.operator_comments = f'Reprocessing required after {failed_phase_name} failure'
            rollback_phase.save()
            
            print(f"Reset {rollback_to_phase} phase to pending for reprocessing (ID: {rollback_phase.id})")
            
            # For post_compression_QC failures, special handling to ensure proper sequence
            if phases_in_sequence:
                print(f"Special handling for post_compression_QC failure - ensuring proper sequence")
                # Start with granulation (already handled above - set to pending)
                
                # Next is blending - set to not_ready so granulation will activate it
                blending_phase = next((p for p in phases_in_sequence if p.phase.phase_name == 'blending'), None)
                if blending_phase:
                    blending_phase.status = 'not_ready'  # Will be activated after granulation completes
                    blending_phase.started_by = None
                    blending_phase.started_date = None
                    blending_phase.completed_by = None
                    blending_phase.completed_date = None
                    blending_phase.save()
                    print(f"Reset blending phase to not_ready for BMR {bmr.batch_number}")
                
                # Then compression - set to not_ready so blending will activate it
                compression_phase = next((p for p in phases_in_sequence if p.phase.phase_name == 'compression'), None)
                if compression_phase:
                    compression_phase.status = 'not_ready'  # Will be activated after blending completes
                    compression_phase.started_by = None
                    compression_phase.started_date = None
                    compression_phase.completed_by = None
                    compression_phase.completed_date = None
                    compression_phase.save()
                    print(f"Reset compression phase to not_ready for BMR {bmr.batch_number}")
                    
                # Then post-compression QC - set to not_ready so compression will activate it
                post_comp_qc_phase = next((p for p in phases_in_sequence if p.phase.phase_name == 'post_compression_qc'), None)
                if post_comp_qc_phase and post_comp_qc_phase.id != failed_execution.id:  # Don't reset the one we just marked as failed
                    post_comp_qc_phase.status = 'not_ready'  # Will be activated after compression completes
                    post_comp_qc_phase.started_by = None
                    post_comp_qc_phase.started_date = None
                    post_comp_qc_phase.completed_by = None
                    post_comp_qc_phase.completed_date = None
                    post_comp_qc_phase.save()
                    print(f"Reset post-compression QC phase to not_ready for BMR {bmr.batch_number}")
                else:
                    print(f"The failed QC phase is maintained as 'failed' to track the failure history")
                
                # Failed QC phase already handled above
            
            return True
            
        except Exception as e:
            print(f"Error handling QC rollback for BMR {bmr.bmr_number}: {e}")
            return False
    
    @classmethod
    def trigger_next_phase(cls, bmr, current_phase):
        """Trigger the next phase in the workflow after completing current phase"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase=current_phase
            )
            
            # NEW: Handle material_dispensing completion to reduce raw material quantities
            if current_execution.phase.phase_name == 'material_dispensing' and current_execution.status == 'completed':
                print(f"Completed material dispensing for BMR {bmr.batch_number}, processing material quantities...")
                
                # Import necessary models here to avoid circular imports
                from raw_materials.models import MaterialDispensing, MaterialDispensingItem
                
                # Get or create the dispensing record
                dispensing, created = MaterialDispensing.objects.get_or_create(
                    bmr=bmr,
                    defaults={'status': 'pending'}
                )
                
                # Set the dispensing record to completed
                dispensing.status = 'completed'
                dispensing.dispensed_by = current_execution.completed_by
                dispensing.completed_date = current_execution.completed_date
                dispensing.dispensing_notes = f"Dispensing completed by {current_execution.completed_by.get_full_name() if current_execution.completed_by else 'system'}"
                
                # Make sure all materials have dispensing items
                bmr_materials = bmr.materials.all()
                print(f"Found {bmr_materials.count()} materials to dispense for BMR {bmr.batch_number}")
                
                # Flag to track if we should process the dispensing completion
                items_created = False
                
                # Make sure each material has a dispensing item
                for bmr_material in bmr_materials:
                    # Check if a dispensing item already exists
                    dispensing_item = MaterialDispensingItem.objects.filter(
                        dispensing=dispensing,
                        bmr_material=bmr_material
                    ).first()
                    
                    if not dispensing_item:
                        # Find a suitable batch for this material
                        suitable_batch = bmr_material.get_suitable_batch()
                        
                        if suitable_batch:
                            # Create a new dispensing item
                            MaterialDispensingItem.objects.create(
                                dispensing=dispensing,
                                bmr_material=bmr_material,
                                material_batch=suitable_batch,
                                required_quantity=bmr_material.required_quantity,
                                dispensed_quantity=bmr_material.required_quantity,
                                is_dispensed=False  # Will be set to True by process_dispensing_completion
                            )
                            items_created = True
                            print(f"Created dispensing item for {bmr_material.material_name}")
                        else:
                            print(f"WARNING: No suitable batch found for {bmr_material.material_name}")
                
                # Set _complete_dispensing flag to trigger process_dispensing_completion
                dispensing._complete_dispensing = True
                dispensing.save()
                
                print(f"Material dispensing processed for BMR {bmr.batch_number}")
            
            # NEW: Handle raw material release -> material dispensing transition
            if current_execution.phase.phase_name == 'raw_material_release':
                print(f"Completed raw material release for BMR {bmr.batch_number}, activating material dispensing...")
                material_dispensing_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='material_dispensing'
                ).first()
                
                if material_dispensing_phase:
                    material_dispensing_phase.status = 'pending'
                    material_dispensing_phase.save()
                    print(f"Activated material_dispensing phase for BMR {bmr.batch_number}")
                    return True
                else:
                    print(f"WARNING: No material_dispensing phase found for BMR {bmr.batch_number}")
                    return False
            
            # NEW: Handle regulatory approval -> raw material release transition
            if current_execution.phase.phase_name == 'regulatory_approval':
                print(f"Completed regulatory approval for BMR {bmr.batch_number}, activating raw material release...")
                raw_material_release_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='raw_material_release'
                ).first()
                
                if raw_material_release_phase:
                    raw_material_release_phase.status = 'pending'
                    raw_material_release_phase.save()
                    print(f"Activated raw_material_release phase for BMR {bmr.batch_number}")
                    return True
                else:
                    print(f"WARNING: No raw_material_release phase found for BMR {bmr.batch_number}")
                    return False
            
            # Special handling for sorting -> coating for tablets
            if current_execution.phase.phase_name == 'sorting' and bmr.product.product_type == 'tablet':
                print(f"Completed sorting for tablet BMR {bmr.batch_number}, handling workflow...")
                is_coated = bmr.product.is_coated
                print(f"Is product coated: {is_coated}")
                
                # Get coating and packaging phases
                coating_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr, 
                    phase__phase_name='coating'
                ).first()
                
                packaging_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='packaging_material_release'
                ).first()
                
                if coating_phase and packaging_phase:
                    print(f"Found coating phase (status: {coating_phase.status}) and packaging phase (status: {packaging_phase.status})")
                    # For coated tablets: always go to coating first
                    if is_coated:
                        coating_phase.status = 'pending'
                        coating_phase.save()
                        print(f"Activated coating phase for coated product: {bmr.batch_number}")
                        return True
                    else:
                        # For uncoated tablets: skip coating, go to packaging
                        coating_phase.status = 'skipped'
                        coating_phase.completed_date = timezone.now()
                        coating_phase.operator_comments = "Phase skipped - product does not require coating"
                        coating_phase.save()
                        packaging_phase.status = 'pending'
                        packaging_phase.save()
                        print(f"Skipped coating, activated packaging for uncoated product: {bmr.batch_number}")
                        return True
            
            # Special handling for coating -> packaging for coated tablets
            if current_execution.phase.phase_name == 'coating' and bmr.product.product_type == 'tablet':
                print(f"Completed coating for tablet BMR {bmr.batch_number}, activating packaging...")
                packaging_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='packaging_material_release'
                ).first()
                
                if packaging_phase:
                    packaging_phase.status = 'pending'
                    packaging_phase.save()
                    print(f"Activated packaging phase after coating: {bmr.batch_number}")
                    return True
            
            # Special handling for packaging_material_release -> bulk_packing for tablet_2
            if current_execution.phase.phase_name == 'packaging_material_release' and bmr.product.product_type == 'tablet':
                tablet_type = getattr(bmr.product, 'tablet_type', None)
                print(f"Completed packaging material release for tablet BMR {bmr.batch_number}, tablet_type: {tablet_type}")
                
                if tablet_type == 'tablet_2':
                    # For tablet_2, activate bulk_packing first
                    bulk_packing_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='bulk_packing'
                    ).first()
                    
                    if bulk_packing_phase:
                        # Ensure secondary packaging is NOT activated yet
                        secondary_phase = BatchPhaseExecution.objects.filter(
                            bmr=bmr,
                            phase__phase_name='secondary_packaging'
                        ).first()
                        if secondary_phase and secondary_phase.status == 'pending':
                            secondary_phase.status = 'not_ready'
                            secondary_phase.save()
                            print(f"Reset secondary_packaging to not_ready for tablet_2: {bmr.batch_number}")
                        
                        bulk_packing_phase.status = 'pending'
                        bulk_packing_phase.save()
                        print(f"Activated bulk_packing phase for tablet_2: {bmr.batch_number}")
                        return True  # CRITICAL: Exit here to prevent standard logic from running
                else:
                    # For normal tablets, activate blister_packing
                    blister_packing_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='blister_packing'
                    ).first()
                    
                    if blister_packing_phase:
                        blister_packing_phase.status = 'pending'
                        blister_packing_phase.save()
                        print(f"Activated blister_packing phase for normal tablet: {bmr.batch_number}")
                        return True  # CRITICAL: Exit here to prevent standard logic from running
                
                # If we reach here, something went wrong with tablet handling
                print(f"WARNING: Failed to handle tablet packaging transition for BMR {bmr.batch_number}")
                return False
            
            # Special handling for bulk_packing -> secondary_packaging for tablet_2
            if current_execution.phase.phase_name == 'bulk_packing' and bmr.product.product_type == 'tablet':
                tablet_type = getattr(bmr.product, 'tablet_type', None)
                if tablet_type == 'tablet_2':
                    # After bulk packing is complete, activate secondary packaging
                    secondary_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='secondary_packaging'
                    ).first()
                    
                    if secondary_phase:
                        secondary_phase.status = 'pending'
                        secondary_phase.save()
                        print(f"Activated secondary_packaging phase after bulk_packing for tablet_2: {bmr.batch_number}")
                        return True  # CRITICAL: Exit here to prevent standard logic
                    else:
                        print(f"WARNING: No secondary_packaging phase found for tablet_2 BMR {bmr.batch_number}")
                        return False
            
            # Special handling for reprocessing: when completing granulation after post_compression_QC failure
            if current_execution.phase.phase_name == 'granulation':
                # Check if this is a reprocessing case (has a failed post_compression_QC)
                failed_qc = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_compression_qc',
                    status='failed'
                ).exists()
                
                print(f"\n*** Checking for reprocessing: {bmr.bmr_number}, Failed QC: {failed_qc} ***")
                
                if failed_qc:
                    print(f"\n*** REPROCESSING DETECTED: Completing granulation for BMR {bmr.bmr_number} after QC failure ***")
                    # Special handling - explicitly activate blending
                    blending_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='blending'
                    ).first()
                    
                    if blending_phase:
                        print(f"Activating blending phase for reprocessing: {blending_phase.id}, current status: {blending_phase.status}")
                        blending_phase.status = 'pending'
                        blending_phase.save()
                        print(f"Blending phase activated for BMR {bmr.bmr_number}")
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No blending phase found for BMR {bmr.bmr_number}")
                        print(f"Activated blending phase after granulation reprocessing")
                        return True
            
            # Special handling for blending after reprocessing 
            if current_execution.phase.phase_name == 'blending':
                # Check for different types of QC failures based on product type
                if bmr.product.product_type in ['tablet', 'tablet_normal', 'tablet_2']:
                    # For tablets, check for post_compression_qc failures
                    failed_qc = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='post_compression_qc',
                        status='failed'
                    ).exists()
                elif bmr.product.product_type == 'capsule':
                    # For capsules, check for post_blending_qc failures
                    failed_qc = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='post_blending_qc',
                        status='failed'
                    ).exists()
                else:
                    failed_qc = False
                
                # For tablets, activate compression next
                if failed_qc and bmr.product.product_type in ['tablet', 'tablet_normal', 'tablet_2']:
                    print(f"\n*** REPROCESSING PATH: Completing blending for tablet BMR {bmr.bmr_number} after QC failure ***")
                    # Special handling - explicitly activate compression
                    compression_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='compression'
                    ).first()
                    
                    if compression_phase:
                        print(f"Activating compression phase for reprocessing: {compression_phase.id}, current status: {compression_phase.status}")
                        compression_phase.status = 'pending'
                        compression_phase.save()
                        print(f"Compression phase activated for BMR {bmr.bmr_number} after reprocessing")
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No compression phase found for BMR {bmr.bmr_number}")
                        return False
                
                # For capsules, activate post_blending_qc next
                elif failed_qc and bmr.product.product_type == 'capsule':
                    print(f"\n*** REPROCESSING PATH: Completing blending for capsule BMR {bmr.bmr_number} after QC failure ***")
                    # Special handling - explicitly activate post_blending_qc
                    qc_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='post_blending_qc'
                    ).first()
                    
                    if qc_phase:
                        print(f"Activating post_blending_qc phase for reprocessing: {qc_phase.id}, current status: {qc_phase.status}")
                        qc_phase.status = 'pending'
                        qc_phase.save()
                        print(f"Post-blending QC phase activated for capsule BMR {bmr.bmr_number} after reprocessing")
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No post_blending_qc phase found for BMR {bmr.bmr_number}")
                        return False
            
            # Special handling for mixing after reprocessing - ensure post_mixing_qc is activated next
            if current_execution.phase.phase_name == 'mixing':
                # Check if this is a reprocessing case (has a failed post_mixing_QC)
                failed_qc = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_mixing_qc',
                    status='failed'
                ).exists()
                
                if failed_qc and bmr.product.product_type == 'ointment':
                    print(f"\n*** REPROCESSING PATH: Completing mixing for BMR {bmr.bmr_number} after QC failure ***")
                    # Special handling - explicitly activate post_mixing_qc
                    qc_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='post_mixing_qc'
                    ).first()
                    
                    if qc_phase:
                        print(f"Activating post_mixing_qc phase for reprocessing: {qc_phase.id}, current status: {qc_phase.status}")
                        qc_phase.status = 'pending'
                        qc_phase.save()
                        print(f"Post-mixing QC phase activated for BMR {bmr.bmr_number} after reprocessing")
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No post_mixing_qc phase found for BMR {bmr.bmr_number}")
                        return False
            
            # Special handling for compression after reprocessing - ensure post_compression_qc is activated next
            if current_execution.phase.phase_name == 'compression':
                # Check if this is a reprocessing case (has a failed post_compression_QC)
                failed_qc = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_compression_qc',
                    status='failed'
                ).exists()
                
                if failed_qc and bmr.product.product_type == 'tablet':
                    print(f"\n*** REPROCESSING PATH: Completing compression for BMR {bmr.bmr_number} after QC failure ***")
                    # Special handling - explicitly activate post_compression_qc
                    qc_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='post_compression_qc'
                    ).first()
                    
                    if qc_phase:
                        print(f"Activating post_compression_qc phase for reprocessing: {qc_phase.id}, current status: {qc_phase.status}")
                        qc_phase.status = 'pending'
                        qc_phase.save()
                        print(f"Post-compression QC phase activated for BMR {bmr.bmr_number} after reprocessing")
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No post_compression_qc phase found for BMR {bmr.bmr_number}")
                        return False
            
            # Special handling for post_blending_qc for capsules - ensure filling is activated next
            if current_execution.phase.phase_name == 'post_blending_qc' and bmr.product.product_type == 'capsule':
                # Check if there was a previous failure of this QC phase
                previous_failures = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_blending_qc',
                    status='failed'
                ).exists()
                
                if previous_failures:
                    print(f"\n*** REPROCESSING SUCCESS PATH: Post-blending QC passed for capsule BMR {bmr.bmr_number} after previous failure ***")
                    # Special handling - explicitly activate filling phase
                    filling_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='filling'
                    ).first()
                    
                    if filling_phase:
                        print(f"Activating filling phase after successful reprocessing QC: {filling_phase.id}, current status: {filling_phase.status}")
                        filling_phase.status = 'pending'
                        filling_phase.save()
                        print(f"Filling phase activated for BMR {bmr.bmr_number} after successful QC reprocessing")
                        
                        # Mark the previously failed QC phase as resolved
                        failed_qc_phases = BatchPhaseExecution.objects.filter(
                            bmr=bmr,
                            phase__phase_name='post_blending_qc',
                            status='failed'
                        )
                        for failed_qc in failed_qc_phases:
                            failed_qc.status = 'resolved'
                            failed_qc.operator_comments += " | RESOLVED by successful retest"
                            failed_qc.save()
                            print(f"Marked previously failed QC phase {failed_qc.id} as resolved")
                        
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No filling phase found for BMR {bmr.bmr_number}")
                        return False
            
            # Special handling for post_mixing_qc for ointments - ensure tube_filling is activated next
            if current_execution.phase.phase_name == 'post_mixing_qc' and bmr.product.product_type == 'ointment':
                # Check if there was a previous failure of this QC phase
                previous_failures = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_mixing_qc',
                    status='failed'
                ).exists()
                
                if previous_failures:
                    print(f"\n*** REPROCESSING SUCCESS PATH: Post-mixing QC passed for ointment BMR {bmr.bmr_number} after previous failure ***")
                    # Special handling - explicitly activate tube_filling phase
                    tube_filling_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='tube_filling'
                    ).first()
                    
                    if tube_filling_phase:
                        print(f"Activating tube filling phase after successful reprocessing QC: {tube_filling_phase.id}, current status: {tube_filling_phase.status}")
                        tube_filling_phase.status = 'pending'
                        tube_filling_phase.save()
                        print(f"Tube filling phase activated for BMR {bmr.bmr_number} after successful QC reprocessing")
                        
                        # Mark the previously failed QC phase as resolved
                        failed_qc_phases = BatchPhaseExecution.objects.filter(
                            bmr=bmr,
                            phase__phase_name='post_mixing_qc',
                            status='failed'
                        )
                        for failed_qc in failed_qc_phases:
                            failed_qc.status = 'resolved'
                            failed_qc.operator_comments += " | RESOLVED by successful retest"
                            failed_qc.save()
                            print(f"Marked previously failed QC phase {failed_qc.id} as resolved")
                        
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No tube filling phase found for BMR {bmr.bmr_number}")
                        return False
            
            # Special handling for post_compression_qc after reprocessing - ensure sorting is activated next
            if current_execution.phase.phase_name == 'post_compression_qc':
                # Check if there was a previous failure of this QC phase
                previous_failures = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='post_compression_qc',
                    status='failed'
                ).exists()
                
                if previous_failures and bmr.product.product_type in ['tablet', 'tablet_normal', 'tablet_2']:
                    print(f"\n*** REPROCESSING SUCCESS PATH: Post-compression QC passed for BMR {bmr.bmr_number} after previous failure ***")
                    # Special handling - explicitly activate sorting phase
                    sorting_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='sorting'
                    ).first()
                    
                    if sorting_phase:
                        print(f"Activating sorting phase after successful reprocessing QC: {sorting_phase.id}, current status: {sorting_phase.status}")
                        sorting_phase.status = 'pending'
                        sorting_phase.save()
                        print(f"Sorting phase activated for BMR {bmr.bmr_number} after successful QC reprocessing")
                        
                        # Mark the previously failed QC phase as resolved
                        failed_qc_phases = BatchPhaseExecution.objects.filter(
                            bmr=bmr,
                            phase__phase_name='post_compression_qc',
                            status='failed'
                        )
                        for failed_qc in failed_qc_phases:
                            failed_qc.status = 'resolved'
                            failed_qc.operator_comments += " | RESOLVED by successful retest"
                            failed_qc.save()
                            print(f"Marked previously failed QC phase {failed_qc.id} as resolved")
                        
                        return True  # Important: Return here to prevent standard logic from running
                    else:
                        print(f"WARNING: No sorting phase found for BMR {bmr.bmr_number}")
                        return False
            
            # Standard next phase logic for ALL other cases
            # This will only run if none of the special cases above returned True
            all_next = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=current_execution.phase.phase_order
            ).order_by('phase__phase_order')
            
            for next_execution in all_next:
                # Only activate if not completed/skipped/failed
                if next_execution.status in ['not_ready', 'pending']:
                    # Don't handle coating here - it's handled in the special cases above
                    if next_execution.phase.phase_name != 'coating':
                        next_execution.status = 'pending'
                        next_execution.save()
                        print(f"Triggered next phase: {next_execution.phase.phase_name} for BMR {bmr.batch_number}")
                        return True
            
            print(f"No more phases to trigger for BMR {bmr.batch_number}")
            # Debug: print all phase statuses for this BMR
            all_phases = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase').order_by('phase__phase_order')
            print("Phase order and statuses:")
            for p in all_phases:
                print(f"  {p.phase.phase_order:2d}. {p.phase.phase_name:25} {p.status}")
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
                'post_compression_qc': 'granulation',  # Roll back to granulation for tablet QC failures
                'post_mixing_qc': 'mixing',
                'post_blending_qc': 'blending',
            }
            
            failed_phase_name = failed_phase.phase_name
            rollback_to_phase = qc_rollback_mapping.get(failed_phase_name)
            
            print(f"\n*** QC FAILURE: {bmr.bmr_number} ***")
            print(f"Failed phase: {failed_phase_name}")
            print(f"Rolling back to: {rollback_to_phase}")
            
            if rollback_to_phase:
                result = cls.handle_qc_failure_rollback(bmr, failed_phase_name, rollback_to_phase)
                print(f"Rollback result: {'SUCCESS' if result else 'FAILURE'}")
                return result
            
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
            'store_manager': ['raw_material_release'],  # Store Manager handles raw material release
            'dispensing_operator': ['material_dispensing'],  # Dispensing Operator handles material dispensing
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
        
        # Check if there are any failed QC phases that would roll back to this user's responsibility
        has_rollback = False
        if user_role == 'granulation_operator':
            # Check if there's a failed post_compression_qc
            has_rollback = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='post_compression_qc',
                status='failed'
            ).exists()
            
        elif user_role == 'mixing_operator':
            # Check if there's a failed post_mixing_qc
            has_rollback = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='post_mixing_qc',
                status='failed'
            ).exists()
            
        elif user_role == 'blending_operator':
            # Check if there's a failed post_blending_qc
            has_rollback = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='post_blending_qc',
                status='failed'
            ).exists()
        
        # Standard query for user's phases
        phases = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name__in=allowed_phases,
            status__in=['pending', 'in_progress']
        ).select_related('phase').order_by('phase__phase_order')
        
        # If there's a rollback situation, we need special handling
        if has_rollback:
            # For failed QC phases, we need to check if the phase is still in the list
            # If not, we need to add it back to the list manually
            
            # Handle capsules - need to reactivate blending after post_blending_qc failure
            if user_role == 'blending_operator' and bmr.product.product_type == 'capsule':
                # Check if there's a blending phase in the list
                has_blending = any(p.phase.phase_name == 'blending' for p in phases)
                
                if not has_blending:
                    # Find the blending phase for this BMR
                    blending_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='blending'
                    ).first()
                    
                    if blending_phase:
                        # Reset it to pending if it's not already
                        if blending_phase.status not in ['pending', 'in_progress']:
                            blending_phase.status = 'pending'
                            blending_phase.save()
                            print(f"Reset blending phase to pending for capsule BMR {bmr.bmr_number} after QC failure")
                        
                        # Add it to the phases list
                        phases = list(phases)
                        phases.append(blending_phase)
            
            # Handle ointments - need to reactivate mixing after post_mixing_qc failure
            elif user_role == 'mixing_operator' and bmr.product.product_type == 'ointment':
                # Check if there's a mixing phase in the list
                has_mixing = any(p.phase.phase_name == 'mixing' for p in phases)
                
                if not has_mixing:
                    # Find the mixing phase for this BMR
                    mixing_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name='mixing'
                    ).first()
                    
                    if mixing_phase:
                        # Reset it to pending if it's not already
                        if mixing_phase.status not in ['pending', 'in_progress']:
                            mixing_phase.status = 'pending'
                            mixing_phase.save()
                            print(f"Reset mixing phase to pending for ointment BMR {bmr.bmr_number} after QC failure")
                        
                        # Add it to the phases list
                        phases = list(phases)
                        phases.append(mixing_phase)
            
            # Mark all phases as reprocessing
            for phase in phases:
                phase.is_reprocessing = True
                
        return phases
