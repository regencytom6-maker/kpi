# Dashboard Analytics Guide

This guide explains how the analytics panels on the admin dashboard work and how to populate them with data.

## Overview

The admin dashboard features four key analytics panels:

1. **Production Status by Product Type** - Shows distribution of completed batches by product type (tablet, capsule, ointment)
2. **Phase Completion Rates** - Shows completion percentage for each workflow phase
3. **Weekly Production Trend** - Shows completed batches over the last 4 weeks
4. **QC Statistics** - Shows pass/fail ratio for quality control checks

## How Data is Generated

The dashboard analytics panels get their data from the following sources:

- **BMR Records** - Batch Manufacturing Records stored in the database
- **Batch Phase Executions** - Workflow phase data associated with each BMR
- **Product Data** - Product types and their associations with BMRs

## Data Population

### Using the Data Update Script

We've created a script to update chart data for testing and demonstration purposes:

```bash
# Navigate to the project folder
cd "path\to\project"

# Run the update script
.\pharma_env\Scripts\python.exe update_chart_data.py
```

This script:
- Updates phase completion data
- Ensures QC statistics have both passed and failed entries
- Distributes FGS (Finished Goods Store) completion dates across 4 weeks

### Adding Real Production Data

To add real production data:

1. Create BMRs for different product types
2. Process them through workflow phases
3. Complete some phases and fail others (especially QC phases)
4. Ensure some batches reach the Finished Goods Store phase

## Key Components

### 1. Views Logic

The data for analytics is prepared in `dashboards/views.py` in the `admin_fgs_monitor` view:

- `product_type_data` - Groups FGS-completed BMRs by product type
- `phase_completion` - Calculates completion percentage for each workflow phase
- `weekly_completions` - Groups FGS completions by week over the last 4 weeks
- `qc_stats` - Counts passed and failed QC phases

### 2. Chart Rendering

Charts are rendered in `templates/dashboards/admin_fgs_monitor.html` using Chart.js:

- Each chart has a canvas element (e.g., `<canvas id="productTypeChart"></canvas>`)
- JavaScript code initializes charts with data from the Django context
- Charts adapt to show placeholders when no data is available

## Troubleshooting

### Empty Charts

If charts appear empty:

1. Verify data exists in the database
   ```python
   # Check if completed FGS phases exist
   python manage.py shell -c "from workflow.models import BatchPhaseExecution; print(BatchPhaseExecution.objects.filter(phase__phase_name='finished_goods_store', status='completed').count())"
   ```

2. Run the data update script
   ```bash
   .\pharma_env\Scripts\python.exe update_chart_data.py
   ```

3. Check browser console for JavaScript errors

### Browser Compatibility

The dashboard uses modern Chart.js features. For best results:
- Use Chrome, Firefox, or Edge
- Enable JavaScript
- Clear browser cache if charts don't appear after updates

## Data Verification

To verify chart data is being generated correctly:

```bash
# Run the verification script
.\pharma_env\Scripts\python.exe verify_chart_data.py
```

This script will show:
- Product type distribution
- Phase completion percentages
- Weekly production trends
- QC statistics

## Extending the Dashboard

To add new analytics panels:

1. Add context data in `dashboards/views.py`
2. Add chart HTML in the template
3. Configure Chart.js visualization in the template's JavaScript section
