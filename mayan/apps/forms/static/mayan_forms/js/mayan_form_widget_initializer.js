'use strict';

 

class MayanFormWidgetInitializer {
    static doInitializerAdd (initializer) {
        MayanFormWidgetInitializer.initializerList.push(initializer);
    }

    static doInitializeAll () {
        MayanFormWidgetInitializer.initializerList.forEach(
            function (initializer) {
                 
                try {
                    initializer();
                } catch (exception) {
                    console.error(
                        'Error initializing a form widget:', exception
                    );
                }
            }
        );
    }

    static doBind () {
        $('#ajax-content').on('updated', function (event) {
            MayanFormWidgetInitializer.doInitializeAll();
        });

        $(document).on('shown.bs.modal', function (event) {
            MayanFormWidgetInitializer.doInitializeAll();
        });

        jQuery(document).ready(function () {
            MayanFormWidgetInitializer.doInitializeAll();
        });
    }
}

MayanFormWidgetInitializer.initializerList = [];
