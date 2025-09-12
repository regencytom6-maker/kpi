-- SQL script to fix products with conflicting types
-- Run this in the Django admin SQL console

-- Fix tablets with capsule type
UPDATE products_product
SET capsule_type = ''
WHERE product_type = 'tablet' AND capsule_type != '';

-- Fix capsules with tablet type
UPDATE products_product
SET tablet_type = ''
WHERE product_type = 'capsule' AND tablet_type != '';

-- Show fixed products
SELECT id, product_name, product_type, tablet_type, capsule_type
FROM products_product
WHERE (product_type = 'tablet' AND capsule_type != '')
   OR (product_type = 'capsule' AND tablet_type != '');
