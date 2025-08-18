document.addEventListener('DOMContentLoaded', function() {
    const productTypeField = document.querySelector('#id_product_type');
    const coatingTypeRow = document.querySelector('.field-coating_type')?.closest('.form-row');
    const tabletTypeRow = document.querySelector('.field-tablet_type')?.closest('.form-row');
    const coatingTypeField = document.querySelector('#id_coating_type');
    const tabletTypeField = document.querySelector('#id_tablet_type');

    // Capsule-specific
    const capsuleTypeRow = document.querySelector('.field-capsule_type')?.closest('.form-row');
    const capsuleTypeField = document.querySelector('#id_capsule_type');
    
    // Keep track of the section headers to show/hide them
    let tabletHeader = null;
    let capsuleHeader = null;
    
    function toggleTypeFields() {
        if (!productTypeField) return;
        
        const isTablet = productTypeField.value === 'tablet';
        const isCapsule = productTypeField.value === 'capsule';

        // Tablet fields
        if (coatingTypeRow) coatingTypeRow.style.display = isTablet ? 'block' : 'none';
        if (tabletTypeRow) tabletTypeRow.style.display = isTablet ? 'block' : 'none';
        if (tabletHeader) tabletHeader.style.display = isTablet ? 'block' : 'none';
        
        // If changing away from tablet, clear tablet-specific fields
        if (!isTablet) {
            if (coatingTypeField) coatingTypeField.value = '';
            if (tabletTypeField) tabletTypeField.value = '';
        }

        // Capsule fields
        if (capsuleTypeRow) capsuleTypeRow.style.display = isCapsule ? 'block' : 'none';
        if (capsuleHeader) capsuleHeader.style.display = isCapsule ? 'block' : 'none';
        
        // If changing away from capsule, clear capsule-specific fields
        if (!isCapsule && capsuleTypeField) {
            capsuleTypeField.value = '';
        }
        
        // Add visual indicators to the product type label
        const productTypeLabel = document.querySelector('label[for="id_product_type"]');
        if (productTypeLabel) {
            // Remove any existing indicators first
            const existingIndicators = productTypeLabel.querySelectorAll('.type-indicator');
            existingIndicators.forEach(indicator => indicator.remove());
            
            // Add the appropriate indicator based on product type
            if (isTablet) {
                const span = document.createElement('span');
                span.className = 'type-indicator tablet-indicator';
                span.style.color = '#28a745';
                span.style.fontWeight = 'bold';
                span.innerHTML = ' (Tablet options below)';
                productTypeLabel.appendChild(span);
            } else if (isCapsule) {
                const span = document.createElement('span');
                span.className = 'type-indicator capsule-indicator';
                span.style.color = '#007bff';
                span.style.fontWeight = 'bold';
                span.innerHTML = ' (Capsule options below)';
                productTypeLabel.appendChild(span);
            }
        }
    }
    
    // Add styling to make it clear these are conditional fields
    function addConditionalFieldStyling() {
        // Tablet section styling
        if (coatingTypeRow && tabletTypeRow) {
            [coatingTypeRow, tabletTypeRow].forEach(row => {
                row.style.border = '1px dashed #007cba';
                row.style.padding = '10px';
                row.style.margin = '5px 0';
                row.style.backgroundColor = '#f8f9fa';
            });
            
            // Add a header for tablet-specific section
            tabletHeader = document.createElement('h3');
            tabletHeader.textContent = 'Tablet-Specific Options';
            tabletHeader.style.color = '#007cba';
            tabletHeader.style.marginTop = '20px';
            tabletHeader.style.marginBottom = '10px';
            tabletHeader.style.borderBottom = '2px solid #007cba';
            tabletHeader.style.paddingBottom = '5px';
            tabletHeader.id = 'tablet-options-header';
            
            if (coatingTypeRow.parentNode) {
                coatingTypeRow.parentNode.insertBefore(tabletHeader, coatingTypeRow);
            }
        }

        // Capsule-specific styling and header
        if (capsuleTypeRow) {
            capsuleTypeRow.style.border = '1px dashed #28a745';
            capsuleTypeRow.style.padding = '10px';
            capsuleTypeRow.style.margin = '5px 0';
            capsuleTypeRow.style.backgroundColor = '#f8f9fa';

            capsuleHeader = document.createElement('h3');
            capsuleHeader.textContent = 'Capsule-Specific Options';
            capsuleHeader.style.color = '#28a745';
            capsuleHeader.style.marginTop = '20px';
            capsuleHeader.style.marginBottom = '10px';
            capsuleHeader.style.borderBottom = '2px solid #28a745';
            capsuleHeader.style.paddingBottom = '5px';
            capsuleHeader.id = 'capsule-options-header';

            if (capsuleTypeRow.parentNode) {
                capsuleTypeRow.parentNode.insertBefore(capsuleHeader, capsuleTypeRow);
            }
        }
    }
    
    // Add form submit validation
    function addFormValidation() {
        const form = document.querySelector('#product_form');
        if (form) {
            form.addEventListener('submit', function(e) {
                const isTablet = productTypeField.value === 'tablet';
                const isCapsule = productTypeField.value === 'capsule';
                
                // Make sure conflicting fields are cleared
                if (isTablet && capsuleTypeField && capsuleTypeField.value) {
                    capsuleTypeField.value = '';
                    console.log('Cleared capsule_type field for tablet product');
                }
                
                if (isCapsule && tabletTypeField && tabletTypeField.value) {
                    tabletTypeField.value = '';
                    console.log('Cleared tablet_type field for capsule product');
                }
            });
        }
    }
    
    // Initialize everything
    if (productTypeField) {
        addConditionalFieldStyling();
        toggleTypeFields();
        addFormValidation();
        
        // Listen for changes
        productTypeField.addEventListener('change', toggleTypeFields);
    }
});
