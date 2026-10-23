'use strict';

class MayanApp {
    constructor (options) {
        this.options = options || {
            ajaxMenusOptions: []
        }

        this.afterBaseLoadCallbacks = [];
        this.ajaxExecuting = false;
        this.ajaxMenusOptions = options.ajaxMenusOptions;
        this.ajaxMenuHashes = {};
        this.ajaxSpinnerSeletor = '#ajax-spinner';
        
        
        
        
        this.menuRefreshRequests = new Set();
        
        
        
        this.unattendedNavigationDeferrals = 0;
        
        
        
        
        
        
        
        
        
        this.menuRefreshFailures = 0;
        this.window = $(window);

        
        
        
        
        MayanApp.unattendedNavigationDeferralLimit = 3;

        
        
        
        
        
        MayanApp.menuRefreshBackoffLimit = 4;

        
        
        
        
        
        
        
        MayanApp.defaultMessagePosition = this.options.messagePosition;
    }

    

    static async countChecked() {
        const checkCount = $('.check-all-slave:checked').length;

        if (checkCount) {
            $('#mayan-multi-item-title').removeClass('d-xxl-block').hide();
            $('#mayan-multi-item-actions').show();
        } else {
            $('#mayan-multi-item-title').addClass('d-xxl-block').show();
            $('#mayan-multi-item-actions').hide();
        }
    }

    async setupMultiItemActions () {
        const app = this;

        $('body').on('change', '.check-all-slave', function () {
            MayanApp.countChecked();
        });

        $('body').on('click', '#mayan-multi-item-actions .dropdown-item', function (event) {
            const $this = $(this);
            const href = $this.attr('href');
            let idList = [];

            $('.check-all-slave:checked').each(function (index, value) {
                
                idList.push(
                    value.name.split('_')[1]
                );
            });

            const url = new URL(href, window.location.origin);
            url.searchParams.set(
                app.options.multiItemActionsPrimaryKey, idList
            );

            $this.attr('href', `${url.pathname}${url.search}`);
        });
    }

    static async setupNavBarState () {
        $('body').on('click', '#accordion-sidebar a', function (event) {
            $('#accordion-sidebar a').removeClass('active');
            $('#accordion-sidebar li').removeClass('active');
            $(this).addClass('active');
            $(this).parents('li').addClass('active');
        });
    }

    static async updateNavbarState () {
        const uriFragment = window.location.hash.substring(1);
        const uriFragmentPath = new URL(
            uriFragment, window.location.origin
        ).pathname;
        $('#accordion-sidebar a').each(function (index, value) {
            if (value.pathname === uriFragmentPath) {
                const $this = $(this);
                const collapseElement = $this.closest('.accordion-collapse')[0];

                if (collapseElement) {
                    bootstrap.Collapse.getOrCreateInstance(
                        collapseElement, {toggle: false}
                    ).show();
                }

                $this.addClass('active');
                $this.parents('li').addClass('active');
            }
        });
    }

    

    async addAfterBaseLoadCallback ({func, self, args=null}) {
        this.afterBaseLoadCallbacks.push({func: func, self: self, args: args});
    }

    async afterBaseLoad (callContext) {
        let context = {
            ...callContext,
            self: this
        };

        const self = this;
        for (const callback of self.afterBaseLoadCallbacks) {
            let callingArguments;

            if (callback.args) {
                callingArguments = callback.args;
            } else {
                callingArguments = context;
            }

            callback.func.bind(callback.self)(callingArguments);
        };
    }

    callbackAJAXSpinnerUpdate () {
        if (this.ajaxExecuting) {
            $(this.ajaxSpinnerSeletor).fadeIn(50);
        }
    }

    getIsReaderEditing () {
         
        const element = document.activeElement;

        if (!element) {
            return false;
        }

        const tagName = element.tagName;

        return (
            tagName === 'INPUT' || tagName === 'TEXTAREA' ||
            tagName === 'SELECT' || element.isContentEditable
        );
    }

    getIsUnattendedNavigationDeferred () {
         
        if (this.unattendedNavigationDeferrals >= MayanApp.unattendedNavigationDeferralLimit) {
            return false;
        }

        if (!this.getIsReaderEditing()) {
            
            
            
            
            this.unattendedNavigationDeferrals = 0;
            return false;
        }

        this.unattendedNavigationDeferrals++;

        return true;
    }

    getMenuRefreshInterval (options) {
         
        const exponent = Math.min(
            this.menuRefreshFailures, MayanApp.menuRefreshBackoffLimit
        );

        return options.interval * Math.pow(2, exponent);
    }

    async doRefreshAJAXMenu (options) {
        const app = this;

        const menuRequest = $.ajax({
            complete: function() {
                app.menuRefreshRequests.delete(menuRequest);

                
                
                
                if (options.interval !== null) {
                    setTimeout(
                        function () {
                            app.doRefreshAJAXMenu(options);
                        }, app.getMenuRefreshInterval(options)
                    );
                }
            },
            error: function (jqXHR, textStatus) {
                 
                if (textStatus === 'abort') {
                    
                    
                    return;
                }

                app.menuRefreshFailures++;
            },
            success: function (data, textStatus, jqXHR) {
                
                app.menuRefreshFailures = 0;

                const partialNavigation = app.partialNavigationApp;

                 
                if (partialNavigation) {
                    const newLocation = partialNavigation.getResponseRedirectURL(
                        jqXHR
                    );

                    if (newLocation) {
                        if (app.getIsUnattendedNavigationDeferred()) {
                            return;
                        }

                        partialNavigation.doResponseRedirect(jqXHR);

                        return;
                    }
                }

                
                
                
                app.unattendedNavigationDeferrals = 0;

                const menuHash = options.app.ajaxMenuHashes[data.name];

                if ((menuHash === undefined) || (menuHash !== data.hex_hash)) {
                    const $menu = $(options.menuSelector);

                    
                    
                    if ($menu.find(':focus').length) {
                        return;
                    }

                    $menu.html(data.html);
                    options.app.ajaxMenuHashes[data.name] = data.hex_hash;
                    if (options.callback !== undefined) {
                        options.callback(options);
                    }
                }
            },
            url: options.url,
        });

        app.menuRefreshRequests.add(menuRequest);
    }

    static doAddToast (message, tags, options) {
        options = options || {};

        
        const colorClassMap = {
            'success': 'text-bg-success',
            'info': 'text-bg-info',
            'warning': 'text-bg-warning',
            'error': 'text-bg-danger',
            'danger': 'text-bg-danger',
        };
        const colorClass = colorClassMap[tags] || 'text-bg-info';

        
        const placementClassMap = {
            'top-right': 'top-0 end-0',
            'top-left': 'top-0 start-0',
            'top-center': 'top-0 start-50 translate-middle-x',
            'top-full-width': 'top-0 start-50 translate-middle-x',
            'bottom-right': 'bottom-0 end-0',
            'bottom-left': 'bottom-0 start-0',
            'bottom-center': 'bottom-0 start-50 translate-middle-x',
            'bottom-full-width': 'bottom-0 start-50 translate-middle-x',
        };
        
        
        
        
        
        
        let messagePosition = options.position;

        if (!messagePosition) {
            messagePosition = MayanApp.defaultMessagePosition;
        }

        const placementClass = placementClassMap[messagePosition] || 'bottom-0 end-0';

        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }
        container.className = `toast-container position-fixed p-3 ${placementClass}`;

        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center ${colorClass} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');

        const flexElement = document.createElement('div');
        flexElement.className = 'd-flex';

        const bodyElement = document.createElement('div');
        bodyElement.className = 'toast-body';
        bodyElement.textContent = message;

        const closeButton = document.createElement('button');
        closeButton.className = 'btn-close btn-close-white me-2 m-auto';
        closeButton.setAttribute('type', 'button');
        closeButton.setAttribute('data-bs-dismiss', 'toast');
        closeButton.setAttribute('aria-label', gettext('Close'));

        flexElement.appendChild(bodyElement);
        flexElement.appendChild(closeButton);
        toastElement.appendChild(flexElement);

        if (options.newestOnTop) {
            container.prepend(toastElement);
        } else {
            container.appendChild(toastElement);
        }

        
        const timeOut = options.timeOut === undefined ? 5000 : options.timeOut;
        const toast = new bootstrap.Toast(toastElement, {
            autohide: timeOut !== 0,
            delay: timeOut || 5000,
        });

        toastElement.addEventListener('hidden.bs.toast', function () {
            toastElement.remove();
        });

        toast.show();
    }

    async initialize () {
        this.partialNavigationApp = partialNavigation;

        this.setupAJAXMenus();
        this.setupAJAXSpinner();
        this.setupFormElementContentCopy();
        this.setupFormHotkeys();
        this.setupItemsSelector();
        this.setupMultiItemActions();
        this.setupNavbarCollapse();
        MayanApp.setupNavBarState();
        this.setupNewWindowAnchor();
        this.setupCardSelection();
        this.setupTableRowSelection();
        this.setupResizePersist();
        this.setupTooltips();

        partialNavigation.initialize();
    }

    async setupAJAXMenus() {
        const app = this;

        
        
        
        
        
        app.partialNavigationApp.$ajaxContent.on(
            app.partialNavigationApp.eventNavigationStart, function () {
                for (const menuRequest of Array.from(app.menuRefreshRequests)) {
                    menuRequest.abort();
                }
            }
        );

        for (const menuOptions of this.ajaxMenusOptions) {
            
            
            
            
            if (!document.querySelector(menuOptions.menuSelector)) {
                continue;
            }

            menuOptions.app = app;
            app.doRefreshAJAXMenu(menuOptions);
        }
    }

    async setupAJAXSpinner () {
        const app = this;

        $(document).ajaxStart(function() {
            app.ajaxExecuting = true;
            setTimeout(
                function () {
                    app.callbackAJAXSpinnerUpdate();
                }, 450
            );
        });

        $(document).ready(function() {
            $(document).ajaxStop(function() {
                $(app.ajaxSpinnerSeletor).fadeOut();
                app.ajaxExecuting = false;
            });
        });
    }

    async setupFormElementContentCopy () {
        const app = this;
        const cssClassSelector = 'appearance-form-control-copy';
        const cssClassSelectorAttached = `${cssClassSelector}-attached`;

        const updateTooltip = function ($this, text) {
            const element = $this[0];
            const tooltip = bootstrap.Tooltip.getOrCreateInstance(element);
            const originalTitle = element.getAttribute('data-bs-original-title') || element.getAttribute('title') || '';

            tooltip.setContent({'.tooltip-inner': text});
            tooltip.show();

            
            element.addEventListener('hidden.bs.tooltip', function restore () {
                tooltip.setContent({'.tooltip-inner': originalTitle});
                element.removeEventListener('hidden.bs.tooltip', restore);
            });
        }

        app.partialNavigationApp.$ajaxContent.on('updated', function (event) {
            const $selector = $(`.${cssClassSelector}`).not(`.${cssClassSelectorAttached}`);

            if ($selector.length) {
                const html = $('#template-appearance-form-element-content-copy').html();

                $selector.siblings('label').after(html);

                $selector.addClass(cssClassSelectorAttached);
            }
        });

        app.partialNavigationApp.$ajaxContent.on('click', '.appearance-btn-copy', function (event) {
            const $this = $(this);
            const $source = $this.parent().parent().children(`.${cssClassSelectorAttached}`)

            navigator.clipboard.writeText($source.val()).then(function () {
                updateTooltip($this, gettext('Copied!'));
            }, function () {
                updateTooltip($this, gettext('Failed. Check clipboard permissions.'));
            });
        });
    }

    async setupFormHotkeys () {
        $('body').on('keypress', '.form-hotkey-enter', function (event) {
            if ((event.which && event.which == 13) || (event.keyCode && event.keyCode == 13)) {
                $(this).find('.btn-hotkey-default').click();
                event.preventDefault();
            }
        });
        $('body').on('dblclick', '.input-hotkey-double-click', function (event) {
            $(this).parents('form').find('.btn-hotkey-default').click();
            event.preventDefault();
        });
    }

    async setupItemsSelector () {
        const app = this;
        app.lastChecked = null;

        $('body').on('click', '.check-all', function (event) {
            const $this = $(this);
            let checked = $(event.target).prop('checked');
            const $checkBoxes = $('.check-all-slave');

            if (checked === undefined) {
                checked = $this.data('checked');
                checked = !checked;
                $this.data('checked', checked);
            }

            $checkBoxes.prop('checked', checked);
            $checkBoxes.trigger('change');
        });

        $('body').on('click', '.check-all-slave', function(e) {
            if (!app.lastChecked) {
                app.lastChecked = this;
                return;
            }
            if (e.shiftKey) {
                const $checkBoxes = $('.check-all-slave');

                const start = $checkBoxes.index(this);
                const end = $checkBoxes.index(app.lastChecked);

                $checkBoxes.slice(
                    Math.min(start,end), Math.max(start,end) + 1
                ).prop('checked', app.lastChecked.checked).trigger('change');
            }
            app.lastChecked = this;
        })
    }

    navbarCollapseHide () {
        document.querySelectorAll('.navbar-collapse').forEach(function (element) {
            bootstrap.Collapse.getOrCreateInstance(
                element, {toggle: false}
            ).hide();
        });

        document.querySelectorAll('.navbar .offcanvas').forEach(function (element) {
            const offcanvas = bootstrap.Offcanvas.getInstance(element);

            if (offcanvas) {
                offcanvas.hide();
            }
        });
    }

    async setupNavbarCollapse () {
        const app = this;

        $(document).keyup(function(e) {
            if (e.keyCode === 27) {
                app.navbarCollapseHide();
            }
        });

        $('body').on('click', 'a', function (event) {
            if (!$(this).hasAnyClass(['dropdown-toggle'])) {
                app.navbarCollapseHide();
            }
        });

        
        
        
        
        $('body').on('submit', '.navbar .offcanvas form', function (event) {
            app.navbarCollapseHide();
        });

        
        
        
        
        app.doSmallScreenMenuClose = function () {
            const element = document.getElementById('menu-main');

            if (element) {
                const offcanvas = bootstrap.Offcanvas.getInstance(element);

                if (offcanvas) {
                    offcanvas.hide();
                }
            }
        }

        
        $('body').on('click', '.a-main-menu-accordion-link', function (event) {
            app.doSmallScreenMenuClose();
        });
    }

    async setupNewWindowAnchor () {
        $('body').on('click', 'a.new_window', function (event) {
            event.preventDefault();

            const href = $(this).attr('href');

            
            
            
            
            window.open(href, '_blank', 'noopener,noreferrer');
        });
    }

    pointerIsOverText (element, x, y) {
        
        
        
        
        
        
        const range = document.createRange();
        const treeWalker = document.createTreeWalker(
            element, NodeFilter.SHOW_TEXT, null
        );
        let textNode = treeWalker.nextNode();

        while (textNode !== null) {
            range.selectNodeContents(textNode);
            const rectangleList = range.getClientRects();

            for (let index = 0; index < rectangleList.length; index++) {
                const rectangle = rectangleList[index];
                const insideHorizontally = (x >= rectangle.left) && (x <= rectangle.right);
                const insideVertically = (y >= rectangle.top) && (y <= rectangle.bottom);

                if (insideHorizontally && insideVertically) {
                    return true;
                }
            }

            textNode = treeWalker.nextNode();
        }

        return false;
    }

    async setupCardSelection () {
        const app = this;

        
        $('body').on('change', '.check-all-slave', function (event) {
            const checked = $(event.target).prop('checked');
            if (checked) {
                $(this).closest('.card-item').addClass('border-success');
            } else {
                $(this).closest('.card-item').removeClass('border-success');
            }
        });

        
        $('body').on('mousedown', '.card-item', function (event) {
            app.cardPointerDownPosition = {x: event.clientX, y: event.clientY};
        });

        $('body').on('click', '.card-item', function (event) {
            const pointerDownPosition = app.cardPointerDownPosition;
            app.cardPointerDownPosition = null;

            if (pointerDownPosition && (
                Math.abs(event.clientX - pointerDownPosition.x) > 5 ||
                Math.abs(event.clientY - pointerDownPosition.y) > 5
            )) {
                return;
            }

            const $this = $(this);
            const $checkbox = $this.find('.check-all-slave');

            
            
            if ($checkbox.length === 0) {
                return;
            }

            
            
            
            
            
            
            const $interactive = $(event.target).closest(
                'a, button, img, input, label, select, textarea'
            );

            if ($interactive.length) {
                const interactiveElement = $interactive[0];
                const isTitleLink = $interactive.hasClass('mayan-card-item-label');
                const pointerOnText = app.pointerIsOverText(
                    interactiveElement, event.clientX, event.clientY
                );
                
                
                
                
                
                const clickIsOnTitleLinkEmptyArea = isTitleLink && (pointerOnText === false);

                if (clickIsOnTitleLinkEmptyArea === false) {
                    return;
                }

                
                
                
                event.preventDefault();
            }

            const checked = $checkbox.prop('checked');

            if (checked) {
                $checkbox.prop('checked', '');
                $checkbox.trigger('change');
            } else {
                $checkbox.prop('checked', 'checked');
                $checkbox.trigger('change');
            }

            if (!app.lastChecked) {
                app.lastChecked = $checkbox;
            }

            if (event.shiftKey) {
                const $checkBoxes = $('.check-all-slave');

                const start = $checkBoxes.index($checkbox);
                const end = $checkBoxes.index(app.lastChecked);

                $checkBoxes.slice(
                    Math.min(start, end), Math.max(start, end) + 1
                ).prop('checked', app.lastChecked.prop('checked')).trigger('change');
            }
            app.lastChecked = $checkbox;
            window.getSelection().removeAllRanges();
        });
    }

    async setupTableRowSelection () {
        const app = this;

        
        
        
        $('body').on('change', '.check-all-slave', function (event) {
            const checked = $(event.target).prop('checked');
            const $row = $(this).closest('.mayan-table-item');

            if (checked) {
                $row.addClass('mayan-table-item-selected');
            } else {
                $row.removeClass('mayan-table-item-selected');
            }
        });

        
        
        $('body').on('mousedown', '.mayan-table-item', function (event) {
            app.tablePointerDownPosition = {x: event.clientX, y: event.clientY};
        });

        
        
        $('body').on('click', '.mayan-table-item', function (event) {
            const pointerDownPosition = app.tablePointerDownPosition;
            app.tablePointerDownPosition = null;

            if (pointerDownPosition) {
                const movedX = Math.abs(event.clientX - pointerDownPosition.x);
                const movedY = Math.abs(event.clientY - pointerDownPosition.y);

                if ((movedX > 5) || (movedY > 5)) {
                    return;
                }
            }

            
            
            
            
            const $interactive = $(event.target).closest(
                'a, button, input, label, select, textarea'
            );

            if ($interactive.length) {
                return;
            }

            const $row = $(this);
            const $checkbox = $row.find('.check-all-slave');
            const checkboxElement = $checkbox[0];

            if (checkboxElement === undefined) {
                return;
            }

            const checked = $checkbox.prop('checked');

            if (checked) {
                $checkbox.prop('checked', '');
            } else {
                $checkbox.prop('checked', 'checked');
            }

            $checkbox.trigger('change');

            if (!app.lastChecked) {
                app.lastChecked = checkboxElement;
            }

            if (event.shiftKey) {
                const $checkBoxes = $('.check-all-slave');

                const start = $checkBoxes.index(checkboxElement);
                const end = $checkBoxes.index(app.lastChecked);

                const $range = $checkBoxes.slice(
                    Math.min(start, end), Math.max(start, end) + 1
                );
                $range.prop('checked', app.lastChecked.checked);
                $range.trigger('change');
            }

            app.lastChecked = checkboxElement;
            window.getSelection().removeAllRanges();
        });
    }

    async setupResizePersist () {
        const app = this;
        const cssClassResizePersist = 'appearance-resize-persist';
        const selectorClass = `.${cssClassResizePersist}`;
        const keySelector = `${cssClassResizePersist}-`;
        const cssClassResizePersistAttached = `${cssClassResizePersist}-attached`;

        const resizeObserver = new ResizeObserver(function (entries) {
            for (const entry of entries) {
                const element = entry.target;

                if (element.id) {
                    const height = $(element).height();

                    if (height > 0) {
                        localStorage.setItem(
                            `${keySelector}${element.id}`, height
                        );
                    }
                }
            }
        });

        
        
        
        
        const resizePersistSetup = function () {
            const $selector = $(selectorClass).not(
                `.${cssClassResizePersistAttached}`
            );

            for (const element of $selector) {
                if (element.id) {
                    const height = parseFloat(
                        localStorage.getItem(`${keySelector}${element.id}`)
                    );

                    if (height > 0) {
                        $(element).height(height);
                    }
                }

                resizeObserver.observe(element);
            }

            $selector.addClass(cssClassResizePersistAttached);
        };

        app.partialNavigationApp.$ajaxContent.on('preupdate', function (event) {
            for (const element of $(selectorClass)) {
                resizeObserver.unobserve(element);
            }
        });

        app.partialNavigationApp.$ajaxContent.on('updated', function (event) {
            resizePersistSetup();
        });

        resizePersistSetup();
    }

    async setupTooltips () {
        const app = this;

         
        app.partialNavigationApp.$ajaxContent.on('preupdate', function (event) {
            $(this).find('[data-bs-toggle="tooltip"]').each(function () {
                const tooltip = bootstrap.Tooltip.getInstance(this);

                if (tooltip) {
                    tooltip.dispose();
                }
            });
        });

        app.partialNavigationApp.$ajaxContent.on('updated', function (event) {
             
            document.querySelectorAll('body > .tooltip').forEach(
                function (element) {
                    const owner = document.querySelector(
                        `[aria-describedby="${element.id}"]`
                    );

                    if (!owner) {
                        element.remove();
                    }
                }
            );
        });
    }

    async setupScrollView () {
         
        const elementList = document.querySelectorAll('.scrollable');

        elementList.forEach(
            function (element) {
                if (element.dataset.grabScrollReady) {
                    return;
                }
                element.dataset.grabScrollReady = 'true';
                element.style.cursor = 'grab';

                let dragging = false;
                let pointerStartX = 0;
                let pointerStartY = 0;
                let scrollStartLeft = 0;
                let scrollStartTop = 0;

                 
                element.addEventListener(
                    'dragstart', function (event) {
                        event.preventDefault();
                    }
                );

                element.addEventListener(
                    'pointerdown', function (event) {
                        if (event.pointerType === 'touch') {
                            return;
                        }

                        dragging = true;
                        pointerStartX = event.clientX;
                        pointerStartY = event.clientY;
                        scrollStartLeft = element.scrollLeft;
                        scrollStartTop = element.scrollTop;
                        element.style.cursor = 'grabbing';
                        element.style.userSelect = 'none';
                        element.setPointerCapture(event.pointerId);
                    }
                );

                element.addEventListener(
                    'pointermove', function (event) {
                        if (!dragging) {
                            return;
                        }

                        const deltaX = event.clientX - pointerStartX;
                        const deltaY = event.clientY - pointerStartY;
                        element.scrollLeft = scrollStartLeft - deltaX;
                        element.scrollTop = scrollStartTop - deltaY;
                    }
                );

                const stopDragging = function (event) {
                    if (!dragging) {
                        return;
                    }

                    dragging = false;
                    element.style.cursor = 'grab';
                    element.style.userSelect = '';

                    if (element.hasPointerCapture(event.pointerId)) {
                        element.releasePointerCapture(event.pointerId);
                    }
                };

                element.addEventListener('pointerup', stopDragging);
                element.addEventListener('pointercancel', stopDragging);
            }
        );
    }

    async setupSelect2 () {
        $('.select2').select2({
            dropdownAutoWidth: true,
            width: '100%'
        });
    }
}
