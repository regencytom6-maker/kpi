// Machine overview function
window.showMachineOverview = function() {
    console.log('Showing machine overview...');
    try {
        // Get machine stats data from hidden element
        const machineStatsElement = document.querySelector('[data-machine-stats]');
        let machineStats = {};
        let content = '';
        
        if (machineStatsElement) {
            try {
                // Parse the JSON content - should already be valid JSON
                const rawData = machineStatsElement.textContent.trim();
                console.log('Raw machine data:', rawData.substring(0, 100) + '...');
                console.log('Data type:', typeof rawData);
                console.log('Data length:', rawData.length);
                
                machineStats = JSON.parse(rawData);
                console.log('Machine stats parsed successfully:', Object.keys(machineStats));
                
                // Create the table with real data from the system
                content = `
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Machine Name</th>
                                    <th>Type</th>
                                    <th>Status</th>
                                    <th>Usage Count</th>
                                    <th>Breakdowns</th>
                                    <th>Changeovers</th>
                                    <th>Breakdown Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                // Add rows for actual machines in the system
                if (Object.keys(machineStats).length > 0) {
                    for (const machineId in machineStats) {
                        const stats = machineStats[machineId];
                        if (!stats || !stats.machine) continue;
                        
                        // Format machine type to match screenshot (underscore to space)
                        let machineType = stats.machine.machine_type || 'Unknown';
                        machineType = machineType.replace('_', ' ');
                        // Capitalize first letter of each word
                        machineType = machineType.split('_').map(word => 
                            word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                        
                        content += `
                            <tr>
                                <td>${stats.machine.name || 'Unknown'}</td>
                                <td>${machineType}</td>
                                <td><span class="badge ${stats.machine.is_active ? 'bg-success' : 'bg-danger'}">${stats.machine.is_active ? 'Active' : 'Inactive'}</span></td>
                                <td>${stats.usage_count || 0}</td>
                                <td>${stats.breakdown_count || 0}</td>
                                <td>${stats.changeover_count || 0}</td>
                                <td>${stats.breakdown_rate || 0}%</td>
                            </tr>
                        `;
                    }
                } else {
                    content += `<tr><td colspan="7" class="text-center">No machine data available</td></tr>`;
                }
                
                content += `
                            </tbody>
                        </table>
                    </div>
                `;
            } catch (error) {
                console.error('Error parsing machine stats:', error);
                // Fallback to a static table based on the screenshot you provided
                content = `
                    <div class="alert alert-warning mb-3">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        There was an error parsing machine data. Showing sample data.
                    </div>
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Machine Name</th>
                                    <th>Type</th>
                                    <th>Status</th>
                                    <th>Usage Count</th>
                                    <th>Breakdowns</th>
                                    <th>Changeovers</th>
                                    <th>Breakdown Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>250 Litre Penicillin</td>
                                    <td>Blending</td>
                                    <td><span class="badge bg-success">Active</span></td>
                                    <td>3</td>
                                    <td>1</td>
                                    <td>0</td>
                                    <td>33.3%</td>
                                </tr>
                                <tr>
                                    <td>300 Litre Blender Non Penicillin</td>
                                    <td>Blending</td>
                                    <td><span class="badge bg-success">Active</span></td>
                                    <td>3</td>
                                    <td>0</td>
                                    <td>0</td>
                                    <td>0.0%</td>
                                </tr>
                                <tr>
                                    <td>500 Litre Blender - Non Penicillin</td>
                                    <td>Blending</td>
                                    <td><span class="badge bg-success">Active</span></td>
                                    <td>1</td>
                                    <td>0</td>
                                    <td>0</td>
                                    <td>0.0%</td>
                                </tr>
                                <tr>
                                    <td>BGS</td>
                                    <td>Blister Packing</td>
                                    <td><span class="badge bg-success">Active</span></td>
                                    <td>1</td>
                                    <td>0</td>
                                    <td>0</td>
                                    <td>0.0%</td>
                                </tr>
                                <tr>
                                    <td>PO3</td>
                                    <td>Blister Packing</td>
                                    <td><span class="badge bg-success">Active</span></td>
                                    <td>1</td>
                                    <td>0</td>
                                    <td>0</td>
                                    <td>0.0%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `;
            }
            
            // Show the modal with the final content
            showMachineModal('Machine Overview', content);
        } else {
            console.error('Machine stats element not found');
            // Show a fallback message
            const content = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No machine statistics are available. Please try refreshing the page.
                </div>
            `;
            showMachineModal('Machine Overview', content);
        }
    } catch (error) {
        console.error('Error showing machine overview:', error);
        // Show error message
        const content = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                An error occurred while loading machine data: ${error.message}
            </div>
        `;
        showMachineModal('Machine Overview', content);
    }
};
