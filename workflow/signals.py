from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import BatchPhaseExecution, ProductionPhase

@receiver(post_save, sender=BatchPhaseExecution)
def handle_post_compression_qc_failure(sender, instance, **kwargs):
    """
    When a post_compression_qc phase is marked as failed, automatically:
    1. Set the granulation phase to 'pending' for reprocessing
    2. Set blending and compression phases to 'not_ready'
    3. Update the batch number to indicate reprocessing
    This ensures failed batches appear on the granulation dashboard for reprocessing.
    """
    # Only process post_compression_qc phases that are being set to 'failed'
    if instance.phase.phase_name == 'post_compression_qc' and instance.status == 'failed':
        try:
            # Check if this is a tablet product
            bmr = instance.bmr
            if bmr.product.product_type != 'tablet':
                print(f"Skipping non-tablet product for QC failure rollback: {bmr.batch_number}")
                return
            
            print(f"\n*** POST-COMPRESSION QC FAILURE DETECTED FOR BMR {bmr.bmr_number} ***")
            
            # Check if batch already has a reprocessing indicator
            if "REPROCESS" in bmr.batch_number:
                print(f"Batch {bmr.batch_number} is already marked for reprocessing")
            else:
                # Update batch number to indicate reprocessing
                current_date = timezone.now().strftime('%Y-%m-%d')
                original_batch_number = bmr.batch_number
                new_batch_number = f"{original_batch_number}-REPROCESS-{current_date}"
                
                bmr.batch_number = new_batch_number
                bmr.notes = (bmr.notes or '') + f" | This batch is being reprocessed after post-compression QC failure on {current_date}."
                bmr.last_modified_date = timezone.now()
                bmr.save()
                
                print(f"Updated batch number: {original_batch_number} → {new_batch_number}")
            
            # Reset granulation phase to pending for reprocessing
            # CRITICAL: Check if a blending phase is already in progress or pending
            blending_active = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='blending',
                status__in=['pending', 'in_progress']
            ).exists()
            
            # Only reset granulation if blending is not already active
            if not blending_active:
                granulation_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='granulation'
                ).first()
                
                if granulation_phase:
                    # Only update if not already pending
                    if granulation_phase.status != 'pending':
                        old_status = granulation_phase.status
                        granulation_phase.status = 'pending'
                        granulation_phase.started_by = None
                        granulation_phase.started_date = None
                        granulation_phase.completed_by = None
                        granulation_phase.completed_date = None
                        granulation_phase.operator_comments = (granulation_phase.operator_comments or "") + f" | Reprocessing after QC failure on {timezone.now().strftime('%Y-%m-%d')}. New batch number: {bmr.batch_number}"
                        granulation_phase.save()
                        print(f"Reset granulation phase from '{old_status}' to 'pending' for BMR {bmr.bmr_number}")
                    else:
                        print(f"Granulation phase already pending for BMR {bmr.bmr_number}")
            else:
                print(f"Skipping granulation phase reset for BMR {bmr.bmr_number} as blending is already active")
                
                # Reset all subsequent phases to not_ready
                subsequent_phases = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name__in=['blending', 'compression', 'post_compression_qc', 'sorting', 'coating', 
                                          'packaging_material_release', 'blister_packing', 'secondary_packaging', 
                                          'final_qa', 'finished_goods_store']
                )
                
                for phase in subsequent_phases:
                    if phase.status != 'not_ready':
                        old_status = phase.status
                        phase.status = 'not_ready'
                        phase.started_by = None
                        phase.started_date = None
                        phase.completed_by = None
                        phase.completed_date = None
                        phase.save()
                        print(f"Reset {phase.phase.phase_name} phase from '{old_status}' to 'not_ready' for BMR {bmr.bmr_number}")
                    
                print(f"Successfully set up tablet batch {bmr.bmr_number} for reprocessing after QC failure")
            else:
                print(f"ERROR: No granulation phase found for BMR {bmr.bmr_number}")
                
        except Exception as e:
            print(f"Error in handle_post_compression_qc_failure: {str(e)}")
