'use strict';

jQuery(document).ready(function() {
     

    $('[data-autocopy="true"]').change(function(event) {
        const $this = $(this);
        const $idTemplate = $this.parent().find(
            '[data-template-fields="template"]'
        ).first();
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

     

    const templatingPreviewRefresh = function () {
        const $this = $(this);
        const editor = this;
        const $preview = $this.parent().find(
            'code.templating-widget-code-preview-code'
        );
        const previewCode = $preview.get(0);

        let content = $this.val();

         
        if (content.slice(-1) === '\n') {
            content = content + ' ';
        }

        $preview.text(content);
        $preview.removeAttr('data-highlighted');

        if (typeof hljs !== 'undefined') {
            hljs.highlightElement(previewCode);

             
            const foreground = window.getComputedStyle(previewCode).color;

            editor.style.setProperty(
                '--templating-widget-code-caret-color', foreground
            );
            editor.style.setProperty(
                '--templating-widget-code-selection-background',
                'color-mix(in srgb, ' + foreground + ' 30%, transparent)'
            );
        }
    };

     

    const templatingPreviewScroll = function () {
        const $this = $(this);
        const textarea = this;
        const preview = $this.parent().find(
            'pre.templating-widget-code-preview'
        ).get(0);

        if (preview) {
            preview.scrollLeft = textarea.scrollLeft;
            preview.scrollTop = textarea.scrollTop;
        }
    };

    const $editorSelector = $('textarea.templating-widget-code');

    $editorSelector.on('input change keyup', templatingPreviewRefresh);
    $editorSelector.on('input change keyup scroll', templatingPreviewScroll);

    $editorSelector.each(function () {
        templatingPreviewRefresh.call(this);
        templatingPreviewScroll.call(this);
    });

     

    const templatingCopyText = function ($textarea) {
        const text = $textarea.val();

        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }

         
        const textarea = $textarea.get(0);
        textarea.focus();
        textarea.select();

        let succeeded = false;

        try {
            succeeded = document.execCommand('copy');
        } catch (error) {
            succeeded = false;
        }

        return succeeded ? Promise.resolve() : Promise.reject();
    };

    $('.templating-widget-code-copy').each(function () {
        const $button = $(this);
        $button.data('label-original', $button.text());
    });

    $('.templating-widget-code-copy').on('click', function (event) {
        const $button = $(this);
        const $textarea = $button.siblings('textarea.templating-widget-code');
        const labelOriginal = $button.data('label-original');
        const labelDone = typeof gettext !== 'undefined' ? gettext('Copied!') : 'Copied!';

        templatingCopyText($textarea).then(function () {
            $button.text(labelDone);
            setTimeout(
                function () {
                    $button.text(labelOriginal);
                }, 2000
            );
        });
    });

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
