'use strict';

jQuery(document).ready(function() {
    /* Inject filters and tags */

    $('[data-autocopy="true"]').change(function(event) {
        const $this = $(this);
        const $idTemplate = $this.siblings('[data-template-fields="template"]');
        const templateCursorPosition = $idTemplate.prop('selectionStart');
        let templateValue = $idTemplate.val();
        const modelVariable = $idTemplate.data('model-variable') || '';
        const fieldText = $this.data('field-template')
            .split('{model_variable}').join(modelVariable)
            .split('{value}').join($this.val());

        templateValue = templateValue.slice(
            0, templateCursorPosition
        ) + fieldText + templateValue.slice(
            templateCursorPosition
        );
        $idTemplate.val(templateValue);
        $idTemplate.focus();
        $idTemplate.prop(
            'selectionStart', templateCursorPosition + fieldText.length
        );
        $idTemplate.prop(
            'selectionEnd', templateCursorPosition + fieldText.length
        );

        $idTemplate.trigger('change');

        $this.val('');
    });

    /* Update the code preview */

    const templatingPreviewRefresh = function (event) {
        const $this = $(this);
        const $preview = $this.parent().find('code.templating-widget-code');

        let content = $this.val();

        $preview.text(content);
        $preview.removeAttr('data-highlighted');
        hljs.highlightElement($preview[0]);
    }

    $('textarea.templating-widget-code').on(
        'input change keyup', templatingPreviewRefresh
    );

    $('textarea.templating-widget-code').each(templatingPreviewRefresh);

    /* Synchronize the scrolling */

    const syncScroll = function(event) {
        const $other = $syncScrollSelector.not(this)
        const other = $other.get(0);

        $other.off('scroll', syncScroll);

        let percentage = this.scrollTop / (this.scrollHeight - this.offsetHeight);

        other.scrollTop = (other.scrollHeight - other.offsetHeight) * percentage;

        setTimeout(
            function(){
                $other.on('scroll', syncScroll);
            }, 25
        );

    }

    const $syncScrollSelector = $('textarea.templating-widget-code, code.templating-widget-code');

    $syncScrollSelector.on('scroll', syncScroll);

    const selectTemplatingEntryTemplate = function (object) {
        if (!object.id) {
            return object.text;
        }

        const entryParts = object.text.split('-');
        const name = entryParts[0];
        const description = entryParts.slice(1).join('-');

        let output = '<strong> ' + appearanceSanitizeHTML(name) + '</strong>';

        if (description) {
            output += ' - <span>' + appearanceSanitizeHTML(description) + '</span>';
        }

        return $(output);
    }

    const cssClassSelect2Templating = 'select2-templating';
    const cssClassSelect2TemplatingAttached = `${cssClassSelect2Templating}-attached`;
    const $selector = $(`.${cssClassSelect2Templating}`).not(`.${cssClassSelect2TemplatingAttached}`);

    $selector.select2({
        templateResult: selectTemplatingEntryTemplate,
        templateSelection: selectTemplatingEntryTemplate,
        width: '100%'
    }).addClass(cssClassSelect2TemplatingAttached);
});
