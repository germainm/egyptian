'use strict';

jQuery(document).ready(function() {
    $('.metadata-value').on('input', function(event) {
        
        
        $(event.target).parents('tr').find(':checkbox').prop('checked', true);
    });
});
