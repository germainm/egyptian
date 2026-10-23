'use strict';

jQuery(document).ready(function() {
    const tagsTagTemplate = function (object) {
        return $(
            '<span class="badge label-tag" style="background: ' + object.element.dataset.color + '; color: ' + object.element.dataset.colorContrast + ';"> ' + appearanceSanitizeHTML(object.text) + '</span>'
        );
    }

    const tagSelectionTemplate = function (object) {
        return tagsTagTemplate(object);
    }

    const tagResultTemplate = function (object) {
        if (!object.element) {
            return '';
        }

        return tagsTagTemplate(object);
    }

    $('.select2-tags').select2({
        templateSelection: tagSelectionTemplate,
        templateResult: tagResultTemplate,
        width: '100%'
    });
});
