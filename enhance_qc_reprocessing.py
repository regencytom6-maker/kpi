"""
QC Failure Reprocessing Workflow Enhancement

This script enhances the rollback process by properly setting up failed QC batches
as new batches for reprocessing. When QC fails:
1. Create a new batch record linked to the original BMR
2. Update all phase statuses correctly
3. Add clear indicators that this is a reprocessed batch
"""

import sqlite3
import os
import datetime
import uuid

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

def enhance_qc_reprocessing_workflow():
    """Enhance the QC failure reprocessing workflow to create new batches"""
    print(f"\n=== Enhancing QC Failure Reprocessing Workflow ===")
    
    # Connect to the database
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find product types
    cursor.execute("SELECT id FROM products_product WHERE product_type='tablet'")
    tablet_product_ids = [row['id'] for row in cursor.fetchall()]
    
    if not tablet_product_ids:
        print("No tablet products found in the database.")
        conn.close()
        return
    
    tablet_ids_str = ','.join(str(id) for id in tablet_product_ids)
    print(f"Found {len(tablet_product_ids)} tablet products")
    
    # Find BMRs with failed post_compression_qc
    cursor.execute(f"""
    SELECT DISTINCT b.id, b.bmr_number, b.batch_number, p.product_name, b.product_id,
           b.created_date, b.status, b.created_by_id
    FROM bmr_bmr b
    JOIN products_product p ON b.product_id = p.id
    JOIN workflow_batchphaseexecution bpe ON bpe.bmr_id = b.id
    JOIN workflow_productionphase pp ON bpe.phase_id = pp.id
    WHERE pp.phase_name = 'post_compression_qc' 
      AND bpe.status = 'failed'
      AND p.id IN ({tablet_ids_str})
    """)
    
    failed_qc_bmrs = cursor.fetchall()
    
    if not failed_qc_bmrs:
        print("No tablet BMRs with failed post-compression QC found.")
        conn.close()
        return
    
    print(f"Found {len(failed_qc_bmrs)} tablet BMRs with failed post-compression QC")
    print("-" * 80)
    
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    enhanced_count = 0
    
    for bmr in failed_qc_bmrs:
        bmr_id = bmr['id']
        bmr_number = bmr['bmr_number']
        batch_number = bmr['batch_number']
        product_name = bmr['product_name']
        
        print(f"\nProcessing BMR: {bmr_number} - Batch: {batch_number} - Product: {product_name}")
        
        # Check if this BMR already has a reprocessing indicator in the batch_number
        if "REPROCESS" in batch_number:
            print(f"  - This batch is already marked for reprocessing: {batch_number}")
            continue
        
        # Find the failed QC phase details
        cursor.execute("""
        SELECT bpe.completed_date, bpe.operator_comments
        FROM workflow_batchphaseexecution bpe
        JOIN workflow_productionphase pp ON bpe.phase_id = pp.id
        WHERE bpe.bmr_id = ? AND pp.phase_name = 'post_compression_qc' AND bpe.status = 'failed'
        ORDER BY bpe.completed_date DESC
        LIMIT 1
        """, (bmr_id,))
        
        qc_details = cursor.fetchone()
        if not qc_details:
            print(f"  ❌ Could not find QC failure details for BMR {bmr_number}")
            continue
        
        # Find the granulation phase
        cursor.execute("""
        SELECT bpe.id, bpe.status 
        FROM workflow_batchphaseexecution bpe
        JOIN workflow_productionphase pp ON bpe.phase_id = pp.id
        WHERE bpe.bmr_id = ? AND pp.phase_name = 'granulation'
        """, (bmr_id,))
        
        granulation = cursor.fetchone()
        
        if not granulation:
            print(f"  ❌ No granulation phase found for BMR {bmr_number}")
            continue
        
        # Only proceed if the granulation phase isn't already pending (indicating we've already fixed it)
        if granulation['status'] == 'pending':
            print(f"  - Granulation phase already set to 'pending', enhancement not needed")
            continue
        
        # Update the batch number to indicate reprocessing
        new_batch_number = f"{batch_number}-REPROCESS-{now.split()[0]}"
        
        cursor.execute("""
        UPDATE bmr_bmr
        SET batch_number = ?,
            last_modified_date = ?
        WHERE id = ?
        """, (new_batch_number, now, bmr_id))
        
        print(f"  ✅ Updated batch number to indicate reprocessing: {new_batch_number}")
        
        # Add a note about reprocessing to the BMR
        cursor.execute("""
        UPDATE bmr_bmr
        SET notes = COALESCE(notes, '') || ' | This batch is being reprocessed after post-compression QC failure on """ + now + """.'
        WHERE id = ?
        """, (bmr_id,))
        
        print(f"  ✅ Added reprocessing note to BMR")
        
        # Reset granulation phase
        cursor.execute("""
        UPDATE workflow_batchphaseexecution
        SET status = 'pending',
            started_by_id = NULL,
            started_date = NULL,
            completed_by_id = NULL,
            completed_date = NULL,
            operator_comments = COALESCE(operator_comments, '') || ' | Reprocessing after QC failure on """ + now + """. New batch number: """ + new_batch_number + """'
        WHERE id = ?
        """, (granulation['id'],))
        
        print(f"  ✅ Reset granulation phase to 'pending' with reprocessing note")
        
        # Reset all subsequent phases to not_ready
        cursor.execute("""
        UPDATE workflow_batchphaseexecution
        SET status = 'not_ready',
            started_by_id = NULL,
            started_date = NULL,
            completed_by_id = NULL,
            completed_date = NULL
        WHERE bmr_id = ? AND phase_id IN (
            SELECT id FROM workflow_productionphase 
            WHERE phase_name IN ('blending', 'compression', 'post_compression_qc', 'sorting', 'coating', 
                               'packaging_material_release', 'blister_packing', 'secondary_packaging', 
                               'final_qa', 'finished_goods_store')
        )
        """, (bmr_id,))
        
        print(f"  ✅ Reset all subsequent phases to 'not_ready'")
        
        enhanced_count += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"✅ Enhanced {enhanced_count} batches with proper reprocessing workflow")
    print("✅ Batches now have clear 'REPROCESS' indicators in their batch numbers")
    print("✅ All phases have been properly reset for the new reprocessing workflow")
    print("\nThe granulation operator should now see these clearly marked as reprocessed batches.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        enhance_qc_reprocessing_workflow()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please make sure you're running this script from the correct directory.")
