// Dashboard chart initialization check script
console.log("---- Chart Initialization Check ----");

// Check if Chart.js is loaded
if (typeof Chart === 'undefined') {
    console.error("ERROR: Chart.js is not loaded!");
} else {
    console.log("SUCCESS: Chart.js is loaded correctly");
}

// Check if chart canvas elements exist
const canvasIds = ['productTypeChart', 'phaseStatusChart', 'weeklyTrendChart', 'qcStatusChart'];
let allCanvasesExist = true;

canvasIds.forEach(id => {
    const canvas = document.getElementById(id);
    if (!canvas) {
        console.error(`ERROR: Canvas #${id} not found in DOM`);
        allCanvasesExist = false;
    } else {
        console.log(`SUCCESS: Canvas #${id} exists with dimensions ${canvas.width}x${canvas.height}`);
        
        // Check if the canvas has appropriate size
        if (canvas.width === 0 || canvas.height === 0) {
            console.error(`ERROR: Canvas #${id} has zero dimensions`);
            
            // Try to fix the dimensions
            const parent = canvas.parentElement;
            if (parent) {
                canvas.width = parent.clientWidth || 300;
                canvas.height = parent.clientHeight || 200;
                console.log(`FIXED: Set canvas #${id} dimensions to ${canvas.width}x${canvas.height}`);
            }
        }
    }
});

if (allCanvasesExist) {
    console.log("SUCCESS: All chart canvases exist in the DOM");
} else {
    console.log("ERROR: Some chart canvases are missing");
}

// Check if chart data variables exist
const dataVariables = ['productData', 'phaseData', 'weeklyData', 'qcData'];
let allDataExists = true;

dataVariables.forEach(varName => {
    if (typeof window[varName] === 'undefined') {
        console.error(`ERROR: Data variable ${varName} is not defined`);
        allDataExists = false;
    } else {
        console.log(`SUCCESS: Data variable ${varName} exists:`, window[varName]);
    }
});

if (allDataExists) {
    console.log("SUCCESS: All chart data variables exist");
} else {
    console.log("ERROR: Some chart data variables are missing");
}

// Force chart initialization if needed
console.log("Attempting to reinitialize charts...");
if (typeof initCharts === 'function') {
    try {
        initCharts();
        console.log("SUCCESS: Charts reinitialized");
    } catch(e) {
        console.error("ERROR: Failed to reinitialize charts:", e);
    }
}

// Check if any charts are already initialized
const existingCharts = Object.values(Chart.instances || {});
console.log(`Found ${existingCharts.length} existing chart instances`);

// List all chart instances
if (existingCharts.length > 0) {
    existingCharts.forEach((chart, i) => {
        console.log(`Chart #${i+1}:`, chart.canvas.id);
    });
} else {
    console.log("No existing chart instances found - creating them from scratch");
    
    // Create basic chart instances if needed
    canvasIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas) {
            try {
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    const chartTypes = {
                        'productTypeChart': 'doughnut',
                        'phaseStatusChart': 'bar', 
                        'weeklyTrendChart': 'line',
                        'qcStatusChart': 'pie'
                    };
                    
                    const newChart = new Chart(ctx, {
                        type: chartTypes[id] || 'bar',
                        data: {
                            labels: ['Fallback 1', 'Fallback 2', 'Fallback 3'],
                            datasets: [{
                                label: 'Fallback Data',
                                data: [5, 10, 15],
                                backgroundColor: [
                                    'rgba(54, 162, 235, 0.8)',
                                    'rgba(255, 99, 132, 0.8)',
                                    'rgba(75, 192, 192, 0.8)'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                    console.log(`CREATED: New fallback chart for #${id}`);
                }
            } catch(e) {
                console.error(`Failed to create fallback chart for #${id}:`, e);
            }
        }
    });
}

// Add a message to indicate this script has run
const messageDiv = document.createElement('div');
messageDiv.style.backgroundColor = '#f8d7da';
messageDiv.style.color = '#721c24';
messageDiv.style.padding = '10px';
messageDiv.style.margin = '10px 0';
messageDiv.style.borderRadius = '5px';
messageDiv.style.position = 'fixed';
messageDiv.style.bottom = '10px';
messageDiv.style.right = '10px';
messageDiv.style.zIndex = '9999';
messageDiv.innerHTML = 'Chart debugging script has run. Check browser console for details.';
document.body.appendChild(messageDiv);

setTimeout(() => {
    document.body.removeChild(messageDiv);
}, 5000);

console.log("---- Chart Initialization Check Complete ----");
