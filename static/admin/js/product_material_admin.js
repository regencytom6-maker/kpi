// This script automatically updates the unit of measure field when a raw material is selected
(function($) {
    $(document).ready(function() {
        // Function to update unit of measure from selected raw material
        function updateUnitOfMeasure(rawMaterialField) {
            var rawMaterialId = $(rawMaterialField).val();
            if (!rawMaterialId) return;
            
            // Make an AJAX request to get the unit of measure for this raw material
            $.ajax({
                url: '/admin/raw_material_unit/',
                data: { 'raw_material_id': rawMaterialId },
                dataType: 'json',
                success: function(data) {
                    if (data.unit_of_measure) {
                        // Find the unit of measure field in the same row
                        var row = $(rawMaterialField).closest('tr');
                        var unitField = row.find('input[name*=unit_of_measure]');
                        unitField.val(data.unit_of_measure);
                        
                        // Optionally make it read-only
                        unitField.attr('readonly', 'readonly');
                    }
                },
                error: function() {
                    console.error('Failed to fetch unit of measure');
                }
            });
        }
        
        // Setup event handlers for existing raw material fields
        $('.field-raw_material select').change(function() {
            updateUnitOfMeasure(this);
        });
        
        // Setup event handlers for new rows added dynamically
        $(document).on('formset:added', function(event, $row, formsetName) {
            $row.find('.field-raw_material select').change(function() {
                updateUnitOfMeasure(this);
            });
        });
        
        // Initial call for pre-selected raw materials
        $('.field-raw_material select').each(function() {
            if ($(this).val()) {
                updateUnitOfMeasure(this);
            }
        });
    });
})(django.jQuery);
