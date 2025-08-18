# Guide to Fixing Product Type Conflicts

## Issue Description
Some products have both tablet and capsule types set, causing confusion in the workflow system. This leads to batches appearing incomplete, especially in the secondary packaging phase.

## Step 1: Fix the Model (Already Done)
The `Product` model has been updated to:
1. Validate that tablet products don't have capsule types and vice versa
2. Automatically clear irrelevant fields based on the product type
3. Ensure validation runs on save

## Step 2: Fix Existing Products

### Option A: Using SQL in Django Admin
1. Go to Django Admin → Home → SQL
2. Run the SQL from the `fix_product_conflicts.sql` file:

```sql
-- Fix tablets with capsule type
UPDATE products_product
SET capsule_type = ''
WHERE product_type = 'tablet' AND capsule_type != '';

-- Fix capsules with tablet type
UPDATE products_product
SET tablet_type = ''
WHERE product_type = 'capsule' AND tablet_type != '';
```

### Option B: Through Django Admin UI
1. Go to Django Admin → Products → Products
2. For each product, check if:
   - Any tablet product has a capsule type - If so, clear the capsule type
   - Any capsule product has a tablet type - If so, clear the tablet type
3. Save each product after correcting it

## Step 3: Check Problematic Batches
Use the SQL from `check_problem_batches.sql` to check if the issue is resolved:

```sql
-- Check specific batches
SELECT 
    bmr.id as bmr_id,
    bmr.batch_number,
    p.product_name,
    p.product_type,
    p.tablet_type,
    p.capsule_type,
    w.id as workflow_id,
    w.status as workflow_status
FROM 
    bmr_bmr bmr
JOIN 
    products_product p ON bmr.product_id = p.id
LEFT JOIN 
    workflow_workflowexecution w ON w.bmr_id = bmr.id
WHERE 
    bmr.batch_number IN ('0012025', '0042025', '0082025');
```

## Step 4: Reset Workflow if Needed
If the batches are still showing as incomplete, you may need to reset the workflow:

1. Go to Django Admin → Workflow → Workflow Executions
2. Find the workflow execution for the problematic batch
3. Delete it (this will also delete all phase executions)
4. Go to Django Admin → BMR → BMR
5. Find the BMR for the problematic batch
6. Click "Save" - this will automatically re-initialize the workflow with the correct phases

## Step 5: Verify Fix
1. Go to the production dashboard
2. Check if the previously incomplete batches now show correctly
3. Verify that the workflow is progressing as expected

## Preventing Future Issues
The following improvements have been made:
1. Added validation in the Product model to prevent conflicting types
2. Updated the JavaScript form in the admin to properly handle product type changes
3. Improved visual indicators in the admin to clearly show which fields apply to which product types
