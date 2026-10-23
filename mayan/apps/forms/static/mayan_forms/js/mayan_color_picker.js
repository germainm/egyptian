'use strict';

 

class MayanColorPicker {
    constructor (options) {
        this.element = options.element;

        this.$element = $(this.element);
        this.$buttonAuto = this.$element.find(
            '.' + MayanColorPicker.cssClassButtonAuto
        );
        this.$buttonRandom = this.$element.find(
            '.' + MayanColorPicker.cssClassButtonRandom
        );
        this.$input = this.$element.find('input[type="color"]');
        this.$inputAutoState = this.$element.find(
            '.' + MayanColorPicker.cssClassInputAutoState
        );

        this.sourceName = this.$input.attr(
            MayanColorPicker.attributeAutoSource
        );
        this.$source = this.getSourceField();
    }

    static doInitializeAll () {
        $('.' + MayanColorPicker.cssClassWidget).each(function () {
            const $element = $(this);

            if ($element.data(MayanColorPicker.dataKey)) {
                 
                return;
            }

            const widget = new MayanColorPicker({element: this});

            $element.data(MayanColorPicker.dataKey, widget);

            widget.initialize();
        });
    }

    getSourceField () {
         
        if (!this.sourceName) {
            return $();
        }

        const $form = this.$element.closest('form');

        let $scope = $form;

        if ($form.length === 0) {
            $scope = $(document);
        }

        return $scope.find('[name="' + this.sourceName + '"]');
    }

    getAutoEnabled () {
        const value = this.$input.attr(
            MayanColorPicker.attributeAutoEnabled
        );

        return value === 'true';
    }

    setAutoEnabled (enabled) {
        let value = 'false';

        if (enabled) {
            value = 'true';
        }

        this.$input.attr(MayanColorPicker.attributeAutoEnabled, value);

         
        this.$inputAutoState.val(value);

        this.$buttonAuto.attr('aria-pressed', value);
        this.$buttonAuto.toggleClass('active', enabled);
    }

    doColorAutoApply () {
        const text = this.$source.val() || '';
        const color = MayanColor.getColorFromText(text);

        if (color === null) {
             
            return;
        }

        this.$input.val(color);
    }

    initialize () {
        const widget = this;

        this.$buttonRandom.on('click', function (event) {
            widget.$input.val(
                MayanColor.getColorRandom()
            );

             
            widget.setAutoEnabled(false);
        });

        if (this.$source.length === 0) {
             
            return;
        }

        this.$source.on('input change', function (event) {
            if (widget.getAutoEnabled()) {
                widget.doColorAutoApply();
            }
        });

         
        this.$input.on('input change', function (event) {
            widget.setAutoEnabled(false);
        });

        this.$buttonAuto.on('click', function (event) {
            const enabled = !widget.getAutoEnabled();

            widget.setAutoEnabled(enabled);

            if (enabled) {
                widget.doColorAutoApply();
            }
        });
    }
}

MayanColorPicker.attributeAutoEnabled = 'data-auto-color-enabled';
MayanColorPicker.attributeAutoSource = 'data-auto-color-source';

MayanColorPicker.cssClassButtonAuto = 'forms-widget-color-picker-auto';
MayanColorPicker.cssClassButtonRandom = 'forms-widget-color-picker-random';
MayanColorPicker.cssClassInputAutoState = 'forms-widget-color-picker-state';
MayanColorPicker.cssClassWidget = 'forms-widget-color-picker';

MayanColorPicker.dataKey = 'mayanColorPicker';
