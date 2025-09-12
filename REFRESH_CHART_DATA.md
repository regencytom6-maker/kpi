# How to Refresh Dashboard Chart Data

This quick guide explains how to refresh the dashboard chart data when needed.

## Option 1: Use the fix_charts_final.py script (Recommended)

This script updates all chart data files and ensures proper integration:

1. Open PowerShell or Command Prompt
2. Navigate to the project folder:
   ```
   cd "c:\path\to\project"
   ```
3. Run the script:
   ```
   pharma_env\Scripts\python.exe fix_charts_final.py
   ```
4. Reload the admin dashboard in your browser

## Option 2: Manually add test data

You can run the create_test_dashboard_data.py script to add test data to the database:

```
pharma_env\Scripts\python.exe create_test_dashboard_data.py
```

After adding test data, run the fix_charts_final.py script to update the chart data files:

```
pharma_env\Scripts\python.exe fix_charts_final.py
```

## Troubleshooting

### Charts still not showing after refresh?

1. Check if the Django server is running
2. Clear your browser cache
3. Check the browser console for errors (F12 > Console)
4. Verify that data files exist:
   - Check that `/static/js/chart_data.js` exists
   - Check that `/static/js/chart_init.js` exists

### Static files not loading?

1. Make sure Django's debug mode is enabled in settings.py
2. Run `python manage.py collectstatic` if needed
3. Restart the Django server:
   ```
   pharma_env\Scripts\python.exe manage.py runserver
   ```

### Chart data is outdated?

The chart data is generated from your database. If you've added new products or completed phases, simply run:

```
pharma_env\Scripts\python.exe fix_charts_final.py
```

Then refresh your browser to see the updated data.
