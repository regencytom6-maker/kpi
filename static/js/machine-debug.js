// Debug script for machine data
document.addEventListener('DOMContentLoaded', function() {
    console.log('Machine data debugging script loaded');
    
    // Find the machine data element
    const machineStatsElement = document.querySelector('[data-machine-stats]');
    
    if (machineStatsElement) {
        console.log('Found machine stats element');
        try {
            // Get the raw data and check if it's valid JSON
            const rawData = machineStatsElement.textContent.trim();
            console.log('Machine stats raw data length:', rawData.length);
            console.log('First 50 chars:', rawData.substring(0, 50));
            
            // Try to parse the JSON
            try {
                const parsedData = JSON.parse(rawData);
                console.log('Successfully parsed machine data JSON');
                console.log('Number of machines:', Object.keys(parsedData).length);
                console.log('Machine IDs:', Object.keys(parsedData));
                
                // Print information about each machine
                for (const machineId in parsedData) {
                    const machine = parsedData[machineId].machine;
                    console.log(`Machine ID ${machineId}: ${machine.name}, Type: ${machine.machine_type}, Active: ${machine.is_active}`);
                }
            } catch (parseError) {
                console.error('Error parsing machine data:', parseError);
                console.log('Raw data starting characters:', JSON.stringify(rawData.substring(0, 20)));
                console.log('Raw data ending characters:', JSON.stringify(rawData.substring(rawData.length - 20)));
                
                // Try to identify the JSON error position
                const errorMatch = parseError.message.match(/position (\d+)/);
                if (errorMatch && errorMatch[1]) {
                    const errorPos = parseInt(errorMatch[1]);
                    console.error(`Error at position ${errorPos}`);
                    console.error('Characters around error:', JSON.stringify(rawData.substring(Math.max(0, errorPos - 10), errorPos + 10)));
                }
            }
        } catch (error) {
            console.error('General error accessing machine data:', error);
        }
    } else {
        console.error('Machine stats element not found');
        
        // Check if any other data-* elements exist
        const dataElements = document.querySelectorAll('[data-*]');
        console.log('Found', dataElements.length, 'data-* elements');
    }
});
