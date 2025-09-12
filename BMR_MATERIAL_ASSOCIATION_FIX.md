# BMR Material Association Fix

## Issue
The regulatory dashboard was showing "No raw materials found for this BMR" even though materials were approved by QC. This happened because the system was incorrectly looking for materials directly associated with the BMR instead of the product.

## Context
In the pharmaceutical workflow:
- Raw materials are associated with **Products**, not directly with BMRs
- When creating a BMR, it uses a specific Product which has associated raw materials
- The regulatory approval process should check if those product raw materials have passed QC

## Changes Made

### 1. Modified Dashboard Utilities

Updated `dashboards/utils.py` to:
- Look for raw materials through `bmr.product.raw_materials.all()` instead of `bmr.materials.all()`
- Use `ProductMaterial` model to get required quantities
- Fixed error handling for better diagnostics

### 2. Created Diagnostic & Fix Scripts

- `test_bmr_material_workflow.py`: Tests the complete material approval workflow
- `fix_bmr_materials_check.py`: Fixes existing BMRs stuck in the approval process

### 3. Fixed Field References

- Updated references to use `required_quantity` from `ProductMaterial` model

## Technical Details

1. **Material Lookup Path**: 
   - Old: BMR → BMRMaterial → material_code lookup → RawMaterial
   - New: BMR → Product → raw_materials → RawMaterial

2. **Quantity Determination**:
   - Now correctly uses `ProductMaterial.required_quantity` for calculating required amounts

3. **QC Approval Process**:
   - The `all_materials_qc_approved()` function now checks product materials
   - Ensures all materials associated with a product have QC-approved batches

## Expected Results

- Regulatory dashboard now shows raw materials correctly
- BMR approval process can proceed when product raw materials have passed QC
- Data integrity maintained between BMR and Product models

## Future Considerations

1. We may want to update the BMR creation process to generate BMR-specific material records in `BMRMaterial` based on the product's raw materials
2. Consider adding clear documentation about the relationship between Products, Raw Materials, and BMRs
3. Add validation in the UI to ensure products have raw materials before creating BMRs

## Related Files

- `dashboards/utils.py`: Main fix location 
- `products/models.py`: Contains Product model with raw_materials field
- `products/models_material.py`: Contains ProductMaterial intermediate model
- `workflow/services.py`: Handles BMR workflow initialization
