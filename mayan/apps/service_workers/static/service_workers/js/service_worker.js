'use strict';

const SERVICE_WORKER_GATEWAY_STATUS_CODE_LIST = [0, 502, 503, 504];

class MayanServiceWorker {
     
    constructor (options) {
        options = options || {};

        this.partialNavigation = options.partialNavigation || null;
        this.scriptUrl = options.scriptUrl || null;

        
        
        
        this.enabled = options.enabled !== false;

        
        
        this.autoRetrySeconds = (typeof options.autoRetrySeconds === 'number') ? options.autoRetrySeconds : 30;
        this.templateSelector = options.templateSelector || '#template-service-worker-unavailable';
        this.retrySelector = options.retrySelector || '#service-worker-unavailable-retry';
        this.countdownSelector = options.countdownSelector || '#service-worker-unavailable-countdown';
        this.headerSelector = options.headerSelector || '#ajax-header';
        this.timer = null;

        
        
        
        
        this.updateThrottleInterval = options.updateThrottleInterval || 60000;
        this.updateLastCheck = 0;
        this.registration = null;

        
        
        this.reloadPending = false;
        this.formDirty = false;
    }

    static setup (options) {
        const instance = new MayanServiceWorker(options);
        instance.initialize();
        return instance;
    }

    initialize () {
        if (this.scriptUrl) {
            this.registerServiceWorker();
        }

        
        
        if (this.enabled && this.partialNavigation) {
            this.setupErrorPanel();
        }
    }

    registerServiceWorker () {
        const self = this;

        if (!('serviceWorker' in navigator)) {
            return;
        }

        
        $('body').on('input change', 'input, textarea, select', function () {
            self.formDirty = true;
        });

        
        
        
        navigator.serviceWorker.addEventListener('controllerchange', function () {
            if (self.reloadPending || self.formDirty || self.isEditingField()) {
                return;
            }

            self.reloadPending = true;
            window.location.reload();
        });

        
        
        const register = function () {
            navigator.serviceWorker.register(
                self.scriptUrl, {updateViaCache: 'none'}
            ).then(function (registration) {
                self.registration = registration;
                self.scheduleUpdateChecks();
            }).catch(function () {
                
                
            });
        };

        if (document.readyState === 'complete') {
            register();
        } else {
            window.addEventListener('load', register, {once: true});
        }
    }

    scheduleUpdateChecks () {
        const self = this;

        
        
        document.addEventListener('visibilitychange', function () {
            if (document.visibilityState === 'visible') {
                self.checkForUpdate();
            }
        });

        
        
        
        if (this.partialNavigation) {
            this.partialNavigation.$ajaxContent.on(
                this.partialNavigation.eventNavigationStart, function () {
                    self.formDirty = false;
                    self.checkForUpdate();
                }
            );
        }
    }

    checkForUpdate () {
        if (!this.registration) {
            return;
        }

        const now = Date.now();
        if (now - this.updateLastCheck < this.updateThrottleInterval) {
            return;
        }
        this.updateLastCheck = now;

        this.registration.update().catch(function () {
            
        });
    }

    isEditingField () {
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

    setupErrorPanel () {
        const self = this;
        const partialNavigation = this.partialNavigation;

        
        
        $('body').on('click', this.retrySelector, function (event) {
            event.preventDefault();
            self.retry();
        });

        
        
        partialNavigation.$ajaxContent.on(
            partialNavigation.eventNavigationStart, function () {
                self.timerClear();
            }
        );

        partialNavigation.registerErrorHandler(function (jqXHR) {
            return self.handleError(jqXHR);
        });
    }

    handleError (jqXHR) {
        if (SERVICE_WORKER_GATEWAY_STATUS_CODE_LIST.indexOf(jqXHR.status) === -1) {
            return false;
        }

        this.panelShow();
        return true;
    }

    timerClear () {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    retry () {
         
        this.timerClear();

        const target = window.location.hash.substring(1);
        if (target) {
            this.partialNavigation.setLocation(target, false);
        } else {
            window.location.reload();
        }
    }

    panelShow () {
        const self = this;

        
        
        this.timerClear();
        $(this.headerSelector).empty();
        this.partialNavigation.ajaxContentSet($(this.templateSelector).html());

        const $countdown = $(this.countdownSelector);
        const messageTemplate = $countdown.attr('data-message-template');
        let secondsRemaining = this.autoRetrySeconds;

        if (!messageTemplate || !(secondsRemaining > 0)) {
            
            
            return;
        }

        const render = function () {
            $countdown.text(
                messageTemplate.replace('%(seconds)s', secondsRemaining)
            );
        };

        render();
        this.timer = setInterval(function () {
            secondsRemaining -= 1;

            if (secondsRemaining <= 0) {
                self.retry();
            } else {
                render();
            }
        }, 1000);
    }
}
