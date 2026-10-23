'use strict';

 

 
if (
    typeof MayanApp === 'undefined' ||
    typeof PartialNavigation === 'undefined' ||
    typeof appearanceAppConfig === 'undefined'
) {
    throw new Error(
        'appearance_app.js evaluated before its prerequisites. Check the ' +
        'script load order in appearance/app/foot.html (mayan_app.js, ' +
        'partial_navigation.js and the appearanceAppConfig block must come ' +
        'first).'
    );
}

 
const djangoDEBUG = appearanceAppConfig.debug;

const app = new MayanApp({
    ajaxMenusOptions: [
        {
            callback: function () {
                MayanApp.updateNavbarState();
            },
            interval: appearanceAppConfig.menuPollingInterval,
            menuSelector: '#menu-main-content',
            name: 'menu_main',
            url: appearanceAppConfig.menuMainURL
        },
        {
            interval: appearanceAppConfig.menuPollingInterval,
            menuSelector: '#menu-topbar',
            name: 'menu_topbar',
            url: appearanceAppConfig.menuTopbarURL
        }
    ],
    messagePosition: appearanceAppConfig.messagePosition,
    multiItemActionsPrimaryKey: 'id_list'
});

const partialNavigation = new PartialNavigation({
    ajaxRequestTimeout: appearanceAppConfig.throttlingTimeout,
    ajaxThrottlingMessage: appearanceAppConfig.throttlingMessage,
    initialURL: appearanceAppConfig.homeURL,
    disabledAnchorClasses: ['disabled', 'pagination-disabled'],
    excludeAnchorClasses: ['fancybox', 'new_window', 'non-ajax'],
    headerNames: appearanceAppConfig.headerNames,
    modalFragmentLinkClass: appearanceAppConfig.modalFragmentLinkClass,
    maximumAjaxRequests: appearanceAppConfig.throttlingMaximumRequests
});

app.addAfterBaseLoadCallback({func: app.setupSelect2, self: app});
app.addAfterBaseLoadCallback({func: app.setupScrollView, self: app});

jQuery(document).ready(function () {
    app.initialize();

     
    if (window.serverSideEvents) {
        window.serverSideEvents.on('toast', function (data) {
            let toastOptions = {
                newestOnTop: true
            };

            if (data.tags === 'error') {
                toastOptions.timeOut = 0;
            } else if (data.tags === 'warning') {
                toastOptions.timeOut = 10000;
            }

            MayanApp.doAddToast(data.message, data.tags, toastOptions);
        });
    }

    app.partialNavigationApp.$ajaxContent.on('updated', function () {
        const $this = $(this);
        const $inputAppearanceSearchClearable = $this.find('.appearance-input-search-clearable input[type="search"]');
        const $spanInputSearchClear = $inputAppearanceSearchClearable.next('.appearance-input-search-clear');

        if ($inputAppearanceSearchClearable.val()) {
            $spanInputSearchClear.show();
        }
    });

    $('body').on('input', '.appearance-input-search-clearable input[type="search"]', function () {
        const $this = $(this);
        const $spanInputSearchClear = $this.next('.appearance-input-search-clear');

        if ($this.val()) {
            $spanInputSearchClear.show();
        } else {
            $spanInputSearchClear.hide();
        }
    });

    $('body').on('click', '.appearance-input-search-clearable .appearance-input-search-clear', function () {
        const $this = $(this);
        const $inputSearch = $this.prev('input[type="search"]');

        $inputSearch.val('').trigger('keyup').focus();
        if ($inputSearch.data('submit-on-clear')) {
            $(this).parents('form').submit();
        }
    });

    $('#ajax-content').on('change', '.appearance-pagination-page-select', function () {
        const $this = $(this);
        const pageNumber = parseInt($this.val());

        if (!Number.isInteger(pageNumber) || pageNumber < 1) {
            MayanApp.doAddToast(appearanceAppConfig.pageNumberInvalidMessage, 'warning', {});
            return;
        }

         
        const pagingQueryString = $this.data('paging-query-string');

         
        const pageNumberMaximum = parseInt($this.data('page-number-maximum'));
        let pageNumberTarget = pageNumber;

        if (Number.isInteger(pageNumberMaximum) && pageNumber > pageNumberMaximum) {
            pageNumberTarget = pageNumberMaximum;
        }

        partialNavigation.setLocation(`${ pagingQueryString }${ pageNumberTarget }`);
    });
});

const appearanceSanitizeHTML = function (text) {
    return $('<div>').text(text).html();
};
