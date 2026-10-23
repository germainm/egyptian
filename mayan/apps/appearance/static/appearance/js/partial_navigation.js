'use strict';

$.fn.hasAnyClass = function() {
     
    for (const cssClass of arguments[0]) {
        if (this.hasClass(cssClass)) {
            return true;
        }
    }
    return false;
}

class PartialNavigation {
    constructor (parameters) {
        parameters = parameters || {};

        
        this.lastLocation = null;
         
        this.responseRedirectPending = false;

        
        
        
        this.locationURLPrevious = null;

        
        this.initialURL = parameters.initialURL || null;

        
        
        this.disabledAnchorClasses = parameters.disabledAnchorClasses || [];

        
        
        this.excludeAnchorClasses = parameters.excludeAnchorClasses || [];

        
        
        
        
        this.headerNames = parameters.headerNames;

        
        
        
        
        
        
        
        
        
        
        
        
        this.modalFragmentTransport = 'header';

        
        
        
        
        
        this.modalFragmentLinkClass = parameters.modalFragmentLinkClass || 'mayan-link-modal';

        if (!this.initialURL) {
            alert('Need to setup initialURL');
        }

        if (!this.headerNames) {
            alert('Need to setup headerNames');
        }

        
        
        this.maximumAjaxRequests = parameters.maximumAjaxRequests || 10;
        this.ajaxRequestTimeout = parameters.ajaxRequestTimeout || 5000;
        this.ajaxThrottlingMessage = parameters.ajaxThrottlingMessage || 'Too many requests.';

        
        
        
        
        this.navigationController = null;
        this.AjaxRequestTimeOutList = [];

        
        
        
        
        
        this.eventNavigationStart = 'mayan:navigation-start';

        
        this.ajaxRefreshButtonAnimationSpeed = 1000;
        this.ajaxRefreshButtonEnabled = true;
        this.ajaxRefreshButtonTimer = null;

        
        
        
        
        
        this.errorHandlers = [];

        this.$ajaxContent = $('#ajax-content');
    }

    initialize () {
        
        
        
        
        if (!this.$ajaxContent.length) {
            return;
        }

        this.setupAjaxAnchors();
        this.setupAjaxNavigation();
        this.setupAjaxForm();
        this.setupAjaxRefreshButton();
        this.setupCommunicationErrorRetry();
    }

    getResponseHeader (response, headerName) {
         
        if (!response) {
            return null;
        }

        if (response.headers && response.headers.get) {
            return response.headers.get(headerName);
        }

        if (response.getResponseHeader) {
            return response.getResponseHeader(headerName);
        }

        return null;
    }

    getResponseRedirectURL (response) {
         
        return this.getResponseHeader(
            response, this.headerNames.redirectLocation
        );
    }

    doResponseRedirect (response) {
         
        const newLocation = this.getResponseRedirectURL(response);

        if (!newLocation) {
            return null;
        }

        if (this.responseRedirectPending) {
             
            return newLocation;
        }

        if (this.getResponseHeader(response, this.headerNames.pageReload)) {
            this.responseRedirectPending = true;
            window.location = newLocation;

            return newLocation;
        }

        this.setLocation(newLocation);

        return newLocation;
    }

    registerErrorHandler (handler) {
         
        this.errorHandlers.push(handler);
    }

    ajaxContentSet (content) {
        const app = this;
        const htmlContent = app.$ajaxContent.html();

        app.$ajaxContent.trigger('preupdate');
        app.$ajaxContent.html(content).ready(function () {
            app.$ajaxContent.trigger('updated');
        });

        return htmlContent;
    }

    modalTransportURL (url) {
         
        if (
            this.modalFragmentTransport === 'query' ||
            this.modalFragmentTransport === 'both'
        ) {
            if (!/[?&]modal=/.test(url)) {
                const separator = url.indexOf('?') === -1 ? '?' : '&';
                return `${url}${separator}modal=1`;
            }
        }

        return url;
    }

    modalFragmentShow (content) {
         
        const existingModal = document.getElementById('modal-confirm');
        if (existingModal) {
            existingModal.remove();
        }

        const $modal = $($.parseHTML(content)).filter('div.modal');
        $modal.appendTo('body');

        const modalElement = $modal.get(0);
        if (!modalElement) {
            return;
        }

        modalElement.addEventListener('hidden.bs.modal', function () {
            modalElement.remove();
        });

        bootstrap.Modal.getOrCreateInstance(modalElement).show();
    }

    isExternalURL (locationString) {
         
        let url;

        try {
            url = new URL(locationString, window.location.origin);
        } catch (error) {
            if (error instanceof TypeError) {
                return false;
            } else {
                throw error;
            }
        }

        const isHttp = (url.protocol === 'http:' || url.protocol === 'https:');
        const isSameOrigin = (url.origin === window.location.origin);

        return isHttp && !isSameOrigin;
    }

    filterLocation (newLocation) {
         
        let url;

        try {
            url = new URL(newLocation, window.location.origin);
        } catch (error) {
            if (error instanceof TypeError) {
                return this.initialURL;
            } else {
                throw error;
            }
        }

        
        
        const isHttp = (url.protocol === 'http:' || url.protocol === 'https:');
        const isSameOrigin = (url.origin === window.location.origin);
        if (!isHttp || !isSameOrigin) {
            return this.initialURL;
        }

        if (url.pathname === '/') {
            if (!url.search) {
                
                
                
                
                
                return this.initialURL;
            }

            
            
            const currentHash = window.location.hash.substring(1);
            const basePath = (currentHash.startsWith('/') && !currentHash.startsWith('//')) ? currentHash : this.initialURL;
            const urlNew = new URL(basePath, window.location.origin);

            urlNew.search = url.search;

            if (urlNew.pathname === '/') {
                return this.initialURL;
            } else {
                return `${urlNew.pathname}${urlNew.search}`;
            }
        }

        return `${url.pathname}${url.search}`;
    }

    cancelCurrentNavigation () {
         
        if (!this.navigationController) {
            return;
        }

        this.navigationController.abort();
        this.navigationController = null;

        $('body').css('cursor', 'progress');
    }

    loadAjaxContent (url, requestOptions) {
         
        const app = this;

        url = this.filterLocation(url);

        
        
        const modalFragment = Boolean(
            requestOptions && requestOptions.modalFragment
        ) && app.modalFragmentTransport !== 'off';

        const ajaxRequestHeaders = {};
        let ajaxRequestURL = url;

        if (modalFragment) {
            if (
                app.modalFragmentTransport === 'header' ||
                app.modalFragmentTransport === 'both'
            ) {
                ajaxRequestHeaders[app.headerNames.modal] = 'true';
            }
            ajaxRequestURL = app.modalTransportURL(url);
        }

        
        
        
        
        
        const throttleTimeout = setTimeout(function () {
            const index = app.AjaxRequestTimeOutList.indexOf(throttleTimeout);
            if (index !== -1) {
                app.AjaxRequestTimeOutList.splice(index, 1);
            }
        }, app.ajaxRequestTimeout);
        this.AjaxRequestTimeOutList.push(throttleTimeout);

        
        if (this.AjaxRequestTimeOutList.length > app.maximumAjaxRequests) {
            let options = {};

            options['timeOut'] = 10000;

            MayanApp.doAddToast(app.ajaxThrottlingMessage, 'warning', options);
            $('body').css('cursor', 'default');
            return;
        }

        
        
        
        this.$ajaxContent.trigger(this.eventNavigationStart);

        
        
        this.cancelCurrentNavigation();

        const controller = new AbortController();
        this.navigationController = controller;

        const jqXHR = $.ajax({
            async: true,
            complete: function (jqXHR, textStatus) {
                
                
                if (app.navigationController === controller) {
                    app.navigationController = null;
                }

                if (textStatus === 'abort') {
                    
                    
                    
                    clearTimeout(throttleTimeout);
                    const index = app.AjaxRequestTimeOutList.indexOf(
                        throttleTimeout
                    );
                    if (index !== -1) {
                        app.AjaxRequestTimeOutList.splice(index, 1);
                    }
                }
            },
            dataType: 'html',
            error: function (jqXHR, textStatus, errorThrown) {
                if (textStatus === 'abort') {
                    
                    
                    return;
                }

                $('body').css('cursor', 'default');
                app.processAjaxRequestError(jqXHR);
            },
            headers: ajaxRequestHeaders,
            
            mimeType: 'text/html; charset=utf-8',
            success: function (data, textStatus, response) {
                const newLocation = app.doResponseRedirect(response);

                if (newLocation) {
                    app.lastLocation = newLocation;
                } else {
                    if (response.getResponseHeader('Content-Disposition')) {
                        app.lastLocation = url;
                        window.location = url;
                    } else if (response.getResponseHeader(app.headerNames.modal)) {
                        
                        
                        
                        
                        
                        if (app.locationURLPrevious) {
                            history.replaceState(
                                {}, '', app.locationURLPrevious
                            );
                        }
                        app.modalFragmentShow(data);
                        $('body').css('cursor', 'default');
                    } else {
                        app.lastLocation = url;
                        app.ajaxContentSet(data);
                        $('body').css('cursor', 'default');
                    }
                }

                
                for (let item of app.AjaxRequestTimeOutList) {
                    clearTimeout(item);
                }
                app.AjaxRequestTimeOutList = [];
            },
            type: 'GET',
            url: ajaxRequestURL
        });

        
        
        
        controller.signal.addEventListener('abort', function () {
            jqXHR.abort();
        }, {once: true});
    }

    onAnchorClick ($this, event) {
         
        const app = this;

        if ($this.hasAnyClass(this.excludeAnchorClasses)) {
            return true;
        }

        if ($this.hasAnyClass(this.disabledAnchorClasses)) {
            event.preventDefault();
            return;
        }

        if ($this.parents().hasAnyClass(this.disabledAnchorClasses)) {
            return false;
        }

        const url = $this.attr('href');
        if (url === undefined) {
            return true;
        }

        if (url.indexOf('javascript:;') > -1) {
            
            return true;
        }

        if (url === '#') {
            
            return true;
        }

        if (app.isExternalURL(url)) {
            
            
            
            
            
            
            
            event.preventDefault();

            window.open(url, '_blank', 'noopener,noreferrer');

            return false;
        }

        event.preventDefault();

        if (event.ctrlKey) {
            window.open(url);
            return false;
        }

        if (!($this.hasClass('disabled') || $this.parent().hasClass('disabled'))) {
            
            
            const requestOptions = {
                modalFragment: $this.hasClass(app.modalFragmentLinkClass)
            };
            this.setLocation(url, undefined, requestOptions);
        }
    }

    getErrorContent (statusCode) {
         
        const title = gettext('Service temporarily unavailable');
        const message = gettext(
            'The server is busy, restarting, or unreachable and could not ' +
            'respond. This is usually temporary.'
        );
        const retryLabel = gettext('Retry');

        let statusLine = '';
        if (statusCode) {
            statusLine = `<p class="mt-3 mb-0 small text-muted">${gettext('Status code')}: ${statusCode}</p>`;
        }

        return ` \
            <div class="row justify-content-center"> \
                <div class="col-12 col-sm-10 col-md-8 col-lg-6"> \
                    <div aria-live="polite" class="card border-primary mt-4" role="alert"> \
                        <div class="card-body p-4 p-md-5 text-center"> \
                            <p class="mb-3 text-primary"> \
                                <i aria-hidden="true" class="fa-solid fa-triangle-exclamation fa-3x"></i> \
                            </p> \
                            <h2 class="h4 mb-3">${title}</h2> \
                            <p class="mb-0 text-muted">${message}</p> \
                            <a class="btn btn-primary mt-4 appearance-communication-error-retry" href="#"> \
                                <i aria-hidden="true" class="fa-solid fa-sync me-2"></i>${retryLabel} \
                            </a> \
                            ${statusLine} \
                        </div> \
                    </div> \
                </div> \
            </div> \
        `;
    }

    processAjaxRequestError (jqXHR) {
         
        const app = this;

        
        if (jqXHR.status === 0 && jqXHR.statusText === 'abort') {
            return;
        }

        
        
        
        
        for (const errorHandler of app.errorHandlers) {
            if (errorHandler(jqXHR, app)) {
                return;
            }
        }

        
        
        
        
        
        const communicationStatusCodeList = [0, 502, 503, 504];
        if (communicationStatusCodeList.indexOf(jqXHR.status) !== -1) {
            app.ajaxContentSet(app.getErrorContent(jqXHR.status));
            return;
        }

        if (djangoDEBUG) {
            const errorMessage = jqXHR.responseText || jqXHR.statusText;

            app.ajaxContentSet(
                ` \
                    <div class="row"> \
                        <div class="col-12"> \
                            <div id="banner-server-error"> \
                                <div class="alert alert-danger d-flex align-items-center" role="alert"> \
                                    <i aria-hidden="true" class="fa-solid fa-triangle-exclamation me-2"></i> \
                                    <span>Server error, status code: ${jqXHR.status}</span> \
                                </div> \
                                <pre id="django-server-error"><code>${errorMessage}</code></pre> \
                            </div> \
                        </div> \
                    </div> \
                `
            );

            
            if (jqXHR.status === 500) {
                  hideAll(document.querySelectorAll('table.vars'));
                  hideAll(document.querySelectorAll('ol.pre-context'));
                  hideAll(document.querySelectorAll('ol.post-context'));
                  hideAll(document.querySelectorAll('div.pastebin'));
            }
        } else {
            if ([403, 404, 500].indexOf(jqXHR.status) !== -1) {
                app.ajaxContentSet(jqXHR.responseText);
            } else {
                app.ajaxContentSet(app.getErrorContent(jqXHR.status));
            }
        }
    }

    getLocationURL (newLocation) {
         
        const urlNew = new URL(window.location);

        urlNew.hash = newLocation;

        return urlNew;
    }

    setLocation (newLocation, pushState, requestOptions) {
         

        
        newLocation = this.filterLocation(newLocation);

        if (typeof pushState === 'undefined') {
            
            
            pushState = true;
        }

        const urlNew = this.getLocationURL(newLocation);

        if (pushState) {
            this.locationURLPrevious = window.location.href;
            history.pushState({}, '', urlNew);
        }
        this.loadAjaxContent(newLocation, requestOptions);
    }

    async setupAjaxAnchors () {
         
        const app = this;
        $('body').on('click', 'a', function (event) {
            app.onAnchorClick($(this), event);
        });
    }

    async setupAjaxForm () {
         
        const app = this;
        let lastAjaxFormData = {};

        $('form').ajaxForm({
            async: true,
            beforeSubmit: function(arr, $form, options) {
                const urlDefault = new URL(
                    window.location.hash.substring(1), window.location
                );
                const stringFormAction = $form.attr('action') || urlDefault.toString();

                options.url = stringFormAction;

                const urlSearchParamForm = new URLSearchParams(
                    $form.serialize()
                );
                const urlFormAction = new URL(stringFormAction, window.location);

                if (options.type.toUpperCase() === 'GET') {
                     
                    urlFormAction.search = '';
                    options.url = urlFormAction.toString();
                }

                urlFormAction.search = urlSearchParamForm.toString();
                lastAjaxFormData.url = urlFormAction;

                if ($form.attr('target') == '_blank') {
                    
                    
                    
                    window.open(urlFormAction.toString());

                    return false;
                }
            },
            dataType: 'html',
            delegation: true,
            error: function(jqXHR, textStatus, errorThrown){
                app.processAjaxRequestError(jqXHR);
            },
            
            mimeType: 'text/html; charset=utf-8',
            success: function(data, textStatus, request) {
                const newLocation = app.doResponseRedirect(request);

                if (!newLocation) {
                    const stringLocation = `${lastAjaxFormData.url.pathname}${lastAjaxFormData.url.search}`;
                    const urlCurrent = app.getLocationURL(stringLocation);

                    history.pushState({}, '', urlCurrent);
                    app.ajaxContentSet(data);
                }
            }
        });
    }

    async setupAjaxRefreshButton () {
        const app = this;

        $('body').on('click', 'a.appearance-link-ajax-refresh', function (event) {
            const $this = $(this);

            $this.blur();

            event.preventDefault();

            if (app.ajaxRefreshButtonEnabled) {
                app.ajaxRefreshButtonEnabled = false;

                clearTimeout(app.ajaxRefreshButtonTimer);
                app.setLocation(window.location.hash.substring(1));

                
                
                
                
                
                
                
                
                
                
                
                
                const $icon = $this.find('.mayan-icon');

                $icon.addClass('fa-spin');
                $icon.css(
                    'animation-duration',
                    `${app.ajaxRefreshButtonAnimationSpeed}ms`
                );

                app.ajaxRefreshButtonTimer = setTimeout(function () {
                    $icon.removeClass('fa-spin');
                    app.ajaxRefreshButtonEnabled = true;
                }, app.ajaxRefreshButtonAnimationSpeed);
            }
        });
    }

    async setupCommunicationErrorRetry () {
        const app = this;

        $('body').on('click', 'a.appearance-communication-error-retry', function (event) {
            const $this = $(this);

            $this.blur();

            event.preventDefault();

            
            
            
            $this.find('i').addClass('fa-spin');

            
            
            
            const target = window.location.hash.substring(1);
            if (target) {
                app.setLocation(target, false);
            } else {
                window.location.reload();
            }
        });
    }

    async setupAjaxNavigation () {
         
        const app = this;

        
        if (window.history && window.history.pushState) {
            $(window).on('popstate', function() {
                app.setLocation(window.location.hash.substring(1), false);
            });
        }

        
        if (window.location.hash) {
            this.setLocation(window.location.hash.substring(1));
        } else {
            this.setLocation('/');
        }

        $.ajaxSetup({
            beforeSend: function (jqXHR, settings) {
                 
                if (app.lastLocation) {
                    jqXHR.setRequestHeader(
                        app.headerNames.alternateReferer, app.lastLocation
                    );
                }
            },
        });
    }
}
