-- SQL script to check problematic batches
-- Run this in the Django admin SQL console

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

-- Check workflow phases for these batches
SELECT 
    pe.id as phase_execution_id,
    bmr.batch_number,
    pp.phase_name,
    pe.status as phase_status,
    pe.phase_order,
    pe.is_current
FROM 
    bmr_bmr bmr
JOIN 
    workflow_workflowexecution w ON w.bmr_id = bmr.id
JOIN 
    workflow_phaseexecution pe ON pe.workflow_execution_id = w.id
JOIN 
    workflow_productionphase pp ON pe.production_phase_id = pp.id
WHERE 
    bmr.batch_number IN ('0012025', '0042025', '0082025')
ORDER BY 
    bmr.batch_number, pe.phase_order;
