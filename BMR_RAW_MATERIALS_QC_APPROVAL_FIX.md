# BMR Raw Materials QC Approval Fix

## Issue
The regulatory dashboard showed raw materials as "No Tests" and "Unknown" status even though they should be QC approved. The required quantity and approved quantity were both showing as 0 kg.

## Root Causes Found

1. **Missing Product-Material Association**:
   - Raw materials were correctly associated with products but ProductMaterial quantities were not set

2. **Status Logic Improvements Needed**:
   - The system wasn't properly determining material status in QC reports
   - It didn't differentiate between missing batches, pending QC, and insufficient quantity

3. **Lack of Material Batch Data**:
   - Some materials didn't have approved batches with quantities in the system
   - QC test records were missing for some batches

## Changes Made

### 1. Improved Material QC Report Generation

- Updated `get_material_qc_report` function to properly determine material status
- Added more specific status types: 'approved', 'missing', 'pending_qc', 'insufficient'
- Better calculation of required quantities from ProductMaterial records
- Fixed unit of measure handling

### 2. Created Data Repair Utilities

- Management command `fix_raw_material_quantities` to fix:
  - Missing ProductMaterial entries
  - Zero quantities in ProductMaterial records
  - Missing RawMaterialBatch entries
  - Missing QC test records

### 3. Enhanced Error Reporting

- More detailed error messages in the regulatory dashboard
- Specific material-by-material breakdown of QC issues

### 4. Diagnostic Tools

- Created `check_bmr_0022025.py` to inspect BMR material status
- Added detailed logging for material status determination

## Expected Results

- Regulatory dashboard now correctly shows material status
- Required quantities are properly displayed
- Materials with approved QC tests show as approved
- BMR approval workflow can proceed when all materials are properly QC approved

## Future Improvements

1. **Data Validation**: Add validation to ensure ProductMaterial entries have non-zero required quantities
2. **UI Improvements**: 
   - Add ability to edit required quantities from the regulatory dashboard
   - Show more detailed error messages about specific missing tests or batches
3. **Process Improvements**:
   - Consider automatic creation of material batches when inventory is below required levels
   - Add notifications when materials are running low

## How to Verify

1. Visit the regulatory dashboard
2. View the material QC report for BMR 0022025
3. Materials should now show proper quantities and status
4. If issues persist, run the fix script: `python manage.py fix_raw_material_quantities --bmr=0022025`
