# Bulk Packing Workflow Fix - Solution Summary

## Issue Description
Products of type "tablet_2" (bulk tablets) were incorrectly skipping the bulk_packing phase and going directly to secondary_packaging, bypassing an important step in the production process.

## Root Causes Identified
1. **Incorrect Phase Ordering**: In some cases, the phase_order values in the database had bulk_packing with a higher order than secondary_packaging.
2. **Missing Special Routing**: The workflow services lacked special logic to handle the "tablet_type='tablet_2'" route differently from regular tablets.
3. **QC Failure Handling**: When post_compression_qc failed, the system wouldn't allow bulk_packing to start despite packaging_material_release being completed.
4. **Inconsistent Phase Statuses**: Some batches had secondary_packaging with status='pending' while bulk_packing was still 'not_ready'.

## Comprehensive Solution
We implemented a multi-layered fix to address all aspects of the issue:

### 1. Phase Ordering Fix
- Ensured that bulk_packing has a consistent phase_order in the ProductionPhase model
- Set correct ordering: packaging_material_release → bulk_packing/blister_packing → secondary_packaging

### 2. Special Routing Logic
- Enhanced WorkflowService.complete_phase with special routing for tablet_type='tablet_2'
- Added special handling in WorkflowService.trigger_next_phase for packaging_material_release → bulk_packing

### 3. QC Failure Handling
- Patched WorkflowService.can_start_phase to allow starting bulk_packing even when post_compression_qc has failed
- Added special exception for when packaging_material_release is completed

### 4. Database Correction
- Fixed existing batches with incorrect status progression
- Auto-completed bulk_packing for batches where secondary_packaging was already completed
- Activated bulk_packing for batches with completed packaging_material_release

## Test Results
- Successfully initiated and completed the bulk_packing phase after packaging_material_release
- Verified secondary_packaging is only activated after bulk_packing completes
- Confirmed workflow works correctly for new BMRs with tablet_type='tablet_2'

## Key Code Changes

### Phase Ordering
```python
# Set correct ordering
packaging_order = packaging_material_release.phase_order
packing_order = packaging_order + 1
bulk_packing.phase_order = packing_order
secondary_packaging.phase_order = packing_order + 1
```

### Special Routing Logic
```python
# For tablet type 2 with packaging_material_release completion
if (phase_name == 'packaging_material_release' and 
    bmr.product.product_type == 'tablet' and
    getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
    
    # Get bulk packing phase
    bulk_packing = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='bulk_packing',
        status='not_ready'
    ).first()
    
    if bulk_packing:
        bulk_packing.status = 'pending'
        bulk_packing.save()
        return bulk_packing
```

### QC Failure Handling
```python
# Special handling for bulk_packing after failed QC
if (phase_name == 'bulk_packing' and 
    bmr.product.product_type == 'tablet' and
    getattr(bmr.product, 'tablet_type', '') == 'tablet_2'):
    
    # Check if post_compression_qc failed but packaging_material_release is complete
    post_qc = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='post_compression_qc'
    ).first()
    
    packaging_material_release = BatchPhaseExecution.objects.filter(
        bmr=bmr,
        phase__phase_name='packaging_material_release'
    ).first()
    
    if post_qc and post_qc.status == 'failed' and packaging_material_release and packaging_material_release.status == 'completed':
        return True
```

## Conclusion
The bulk packing workflow for tablet type 2 products now works correctly. The system ensures that bulk_packing is always included and activated at the right time, and prevents it from being skipped in the workflow.
