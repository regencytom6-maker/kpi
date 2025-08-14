# Cleanup Script - Remove Development/Debug Files
# Run this from the project root directory

Write-Host "Starting cleanup of development/debug files..." -ForegroundColor Green

# Debug files
$debugFiles = Get-ChildItem -Name "debug_*.py"
if ($debugFiles) {
    Write-Host "Removing debug files..." -ForegroundColor Yellow
    Remove-Item debug_*.py -Force
}

# Test files
$testFiles = Get-ChildItem -Name "test_*.py"
if ($testFiles) {
    Write-Host "Removing test files..." -ForegroundColor Yellow
    Remove-Item test_*.py -Force
}

# Fix files
$fixFiles = Get-ChildItem -Name "fix_*.py"
if ($fixFiles) {
    Write-Host "Removing fix files..." -ForegroundColor Yellow
    Remove-Item fix_*.py -Force
}

# Check files
$checkFiles = Get-ChildItem -Name "check_*.py"
if ($checkFiles) {
    Write-Host "Removing check files..." -ForegroundColor Yellow
    Remove-Item check_*.py -Force
}

# Verify files
$verifyFiles = Get-ChildItem -Name "verify_*.py"
if ($verifyFiles) {
    Write-Host "Removing verify files..." -ForegroundColor Yellow
    Remove-Item verify_*.py -Force
}

# Create test files
$createTestFiles = Get-ChildItem -Name "create_test_*.py"
if ($createTestFiles) {
    Write-Host "Removing create test files..." -ForegroundColor Yellow
    Remove-Item create_test_*.py -Force
}

# Analysis files
$analysisFiles = Get-ChildItem -Name "analyze_*.py"
if ($analysisFiles) {
    Write-Host "Removing analysis files..." -ForegroundColor Yellow
    Remove-Item analyze_*.py -Force
}

# Comprehensive files
$comprehensiveFiles = Get-ChildItem -Name "comprehensive_*.py"
if ($comprehensiveFiles) {
    Write-Host "Removing comprehensive files..." -ForegroundColor Yellow
    Remove-Item comprehensive_*.py -Force
}

# Emergency fix files
$emergencyFiles = Get-ChildItem -Name "emergency_fix_*.py"
if ($emergencyFiles) {
    Write-Host "Removing emergency fix files..." -ForegroundColor Yellow
    Remove-Item emergency_fix_*.py -Force
}

# Final fix files
$finalFiles = Get-ChildItem -Name "final_*.py"
if ($finalFiles) {
    Write-Host "Removing final fix files..." -ForegroundColor Yellow
    Remove-Item final_*.py -Force
}

# Permanent fix files
$permanentFiles = Get-ChildItem -Name "permanent_*.py"
if ($permanentFiles) {
    Write-Host "Removing permanent fix files..." -ForegroundColor Yellow
    Remove-Item permanent_*.py -Force
}

# Repair files
$repairFiles = Get-ChildItem -Name "repair_*.py"
if ($repairFiles) {
    Write-Host "Removing repair files..." -ForegroundColor Yellow
    Remove-Item repair_*.py -Force
}

# Simple files
$simpleFiles = Get-ChildItem -Name "simple_*.py"
if ($simpleFiles) {
    Write-Host "Removing simple files..." -ForegroundColor Yellow
    Remove-Item simple_*.py -Force
}

# Unblock files
$unblockFiles = Get-ChildItem -Name "unblock_*.py"
if ($unblockFiles) {
    Write-Host "Removing unblock files..." -ForegroundColor Yellow
    Remove-Item unblock_*.py -Force
}

# Update files (keep update_store_roles.py as it might be useful)
$updateFiles = Get-ChildItem -Name "update_*.py" | Where-Object { $_.Name -ne "update_store_roles.py" }
if ($updateFiles) {
    Write-Host "Removing update files (keeping update_store_roles.py)..." -ForegroundColor Yellow
    $updateFiles | Remove-Item -Force
}

# Other development files
$otherFiles = @(
    "add_debug_tools.py",
    "add_direct_dropdown.py", 
    "add_sample_comments.py",
    "clean_up_dashboard.py",
    "clear_sessions.py",
    "create_chart_debug.py",
    "create_improved_template.py",
    "create_simple_template.py",
    "create_tablet2_product.py",
    "create_test_dashboard_data.py",
    "create_test_inventory.py",
    "deployment_verification.py",
    "generate_comments_report.py",
    "integrate_debug_controls.py",
    "populate_chart_data.py",
    "populate_dashboard_analytics.py",
    "quick_workflow_check.py",
    "remove_debug_panel_only.py",
    "remove_debug_tools.py",
    "remove_direct_dropdown.py",
    "restart_server.py",
    "restore_dashboard_layout.py",
    "setup_analytics_data.py",
    "setup_dashboard_charts.py"
)

foreach ($file in $otherFiles) {
    if (Test-Path $file) {
        Write-Host "Removing $file..." -ForegroundColor Yellow
        Remove-Item $file -Force
    }
}

# Log and debug files
$logFiles = @(
    "template_debug.log",
    "batch_analysis.txt", 
    "batch_analysis_result.txt",
    "chart_debugger.html",
    "rendered_template.html"
)

foreach ($file in $logFiles) {
    if (Test-Path $file) {
        Write-Host "Removing $file..." -ForegroundColor Yellow
        Remove-Item $file -Force
    }
}

# Batch files (keep .ps1 files)
$batchFiles = Get-ChildItem -Name "*.bat"
if ($batchFiles) {
    Write-Host "Removing batch files..." -ForegroundColor Yellow
    Remove-Item *.bat -Force
}

# JavaScript fix files
$jsFiles = @(
    "fix_dashboard_charts.js"
)

foreach ($file in $jsFiles) {
    if (Test-Path $file) {
        Write-Host "Removing $file..." -ForegroundColor Yellow
        Remove-Item $file -Force
    }
}

Write-Host "Cleanup completed!" -ForegroundColor Green
Write-Host "The following important files were kept:" -ForegroundColor Cyan
Write-Host "- manage.py (Django management)" -ForegroundColor White
Write-Host "- requirements.txt (dependencies)" -ForegroundColor White
Write-Host "- show_users.py (utility script)" -ForegroundColor White
Write-Host "- start_server.ps1 (server startup)" -ForegroundColor White
Write-Host "- activate_env.ps1 (environment activation)" -ForegroundColor White
Write-Host "- update_store_roles.py (potentially useful)" -ForegroundColor White
Write-Host "- All documentation (.md files)" -ForegroundColor White
Write-Host "- All app folders and core Django files" -ForegroundColor White
