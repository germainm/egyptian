'use strict';

const CAROUSEL_MARGIN_LOAD = '300%';
const CAROUSEL_MARGIN_UNLOAD = '900%';
const IMAGE_RETENTION_MARGIN = '300%';

 
const CAROUSEL_REQUEST_CONCURRENCY_DEFAULT = 4;
const CAROUSEL_REQUEST_RATE_DEFAULT = 8;
const CAROUSEL_RETRY_ATTEMPT_MAXIMUM_DEFAULT = 6;
const CAROUSEL_RETRY_DELAY_INITIAL_DEFAULT = 500;
const CAROUSEL_RETRY_DELAY_MAXIMUM_DEFAULT = 20000;

 
const HTTP_STATUS_SERVICE_UNAVAILABLE = 503;
const HTTP_STATUS_TOO_MANY_REQUESTS = 429;

class MayanImage {
    static async setup (mayanApp, options) {
        const self = this;

        const config = Object.assign(
            {
                requestConcurrency: CAROUSEL_REQUEST_CONCURRENCY_DEFAULT,
                requestRate: CAROUSEL_REQUEST_RATE_DEFAULT,
                retryAttemptMaximum: CAROUSEL_RETRY_ATTEMPT_MAXIMUM_DEFAULT,
                retryDelayInitial: CAROUSEL_RETRY_DELAY_INITIAL_DEFAULT,
                retryDelayMaximum: CAROUSEL_RETRY_DELAY_MAXIMUM_DEFAULT
            }, options || {}
        );

        const carouselRequestInterval = 1000 / config.requestRate;

        $().fancybox({
            afterShow: function (instance, current) {
                $('a.a-caption').off('click').on('click', function(event) {
                    instance.close(true);
                });
            },
            animationEffect: 'fade',
            animationDuration : 100,
            buttons : [
                'fullScreen',
                'close'
            ],
            hash: false,
            idleTime: false,
            infobar: true,
            selector: 'a.fancybox'
        });

         
        this.requestActiveSet = new Set();
        this.requestQueue = [];
        this.requestResumeTime = 0;
        this.requestStartTime = 0;
        this.requestTimer = null;

        this.requestSchedule = function (time) {
            const delay = Math.max(0, time - Date.now());

            if (self.requestTimer) {
                clearTimeout(self.requestTimer);
            }

            self.requestTimer = setTimeout(self.requestPump, delay);
        }

        this.retryDelayCompute = function (attempt, response) {
             
            if (response) {
                const retryAfter = response.headers.get('Retry-After');

                if (retryAfter) {
                    const seconds = parseInt(retryAfter, 10);

                    if (!isNaN(seconds)) {
                        return seconds * 1000;
                    }
                }
            }

             
            const delay = Math.min(
                config.retryDelayInitial * Math.pow(2, attempt),
                config.retryDelayMaximum
            );

            return delay / 2 + Math.random() * (delay / 2);
        }

        this.requestDefer = function (job, response) {
            job.attempt++;

            if (job.attempt > config.retryAttemptMaximum) {
                self.requestErrorShow(job, response);
                return;
            }

            const delay = self.retryDelayCompute(job.attempt, response);

             
            self.requestResumeTime = Math.max(
                self.requestResumeTime, Date.now() + delay
            );

            self.requestQueue.unshift(job);
        }

        this.requestErrorMarkupGet = async function (response) {
             
            if (!response) {
                return null;
            }

            try {
                const data = await response.json();

                if (data && data.app_image_error_image_template) {
                    return data.app_image_error_image_template;
                }
            } catch (exception) {
                
            }

            return null;
        }

        this.genericErrorMarkupGet = function () {
             
            const template = document.getElementById(
                'mayan-image-error-template'
            );

            if (template) {
              return template.innerHTML;
            } else {
              return '';
            }
        }

        this.requestErrorShow = async function (job, response) {
            if (job.cancelled) {
                return;
            }

            const markup = await self.requestErrorMarkupGet(response);

            if (job.cancelled) {
                return;
            }

             
            job.handlerError(
                job, markup || self.genericErrorMarkupGet()
            );
        }

        this.requestRun = async function (job) {
            self.requestActiveSet.add(job);

            const navigation = mayanApp.partialNavigationApp;

            try {
                 
                const headers = {
                    'X-Requested-With': 'XMLHttpRequest'
                };

                if (navigation && navigation.lastLocation) {
                    headers[navigation.headerNames.alternateReferer] = (
                        navigation.lastLocation
                    );
                }

                const response = await fetch(
                    job.url, {
                        credentials: 'same-origin', headers: headers,
                        signal: job.controller.signal
                    }
                );

                 
                if (navigation && navigation.doResponseRedirect(response)) {
                    return;
                }

                const statusDeferred = (
                    response.status === HTTP_STATUS_TOO_MANY_REQUESTS ||
                    response.status === HTTP_STATUS_SERVICE_UNAVAILABLE
                );

                if (statusDeferred) {
                    self.requestDefer(job, response);
                } else if (!response.ok) {
                    await self.requestErrorShow(job, response);
                } else {
                    job.handlerSuccess(
                        job, await response.blob()
                    );
                }
            } catch (exception) {
                if (!job.cancelled) {
                     
                    self.requestDefer(job, null);
                }
            } finally {
                self.requestActiveSet.delete(job);
                self.requestPump();
            }
        }

        this.requestPump = function () {
            if (self.requestTimer) {
                clearTimeout(self.requestTimer);
                self.requestTimer = null;
            }

            
            while (
                self.requestQueue.length && self.requestQueue[0].cancelled
            ) {
                self.requestQueue.shift();
            }

            if (!self.requestQueue.length) {
                return;
            }

            if (self.requestActiveSet.size >= config.requestConcurrency) {
                
                return;
            }

            const now = Date.now();

            const time = Math.max(
                self.requestResumeTime, self.requestStartTime
            );

            if (now < time) {
                self.requestSchedule(time);
                return;
            }

            const job = self.requestQueue.shift();

            self.requestStartTime = now + carouselRequestInterval;

            self.requestRun(job);

            if (self.requestQueue.length) {
                self.requestSchedule(self.requestStartTime);
            }
        }

        this.requestCancel = function (job) {
            job.cancelled = true;
            job.controller.abort();
        }

        this.requestSubmit = function (job) {
            job.attempt = 0;
            job.cancelled = false;
            job.controller = new AbortController();

            self.requestQueue.push(job);
            self.requestPump();
        }

        this.requestQueueClear = function () {
             
            for (const job of self.requestQueue) {
                self.requestCancel(job);
            }

            for (const job of self.requestActiveSet) {
                self.requestCancel(job);
            }

            self.requestQueue = [];
            self.requestResumeTime = 0;
            self.requestStartTime = 0;
        }

        this.carouselSlotImageShow = function (job, blob) {
            if (job.cancelled) {
                return;
            }

            const $slot = job.$slot;

            $slot.removeData('carouselJob');

            const $image = $('<img/>');

            $image.on('load', function () {
                self.carouselSlotHeightStore($slot, $image);
                $slot.removeClass('carousel-item-image-slot-empty');
            });

             
            $slot.children().not('.lazyload-spinner-container').remove();

            $slot.append($image);
            $image.attr(
                'src', URL.createObjectURL(blob)
            );
        }

        this.carouselSlotErrorShow = function (job, markup) {
            if (job.cancelled) {
                return;
            }

            const $slot = job.$slot;

            $slot.removeData('carouselJob');
            $slot.html(markup);
            $slot.removeClass('carousel-item-image-slot-empty');
        }

        this.carouselSlotHeightStore = function ($slot, $image) {
             
            const height = $image.outerHeight();

            if (height > 0) {
                $slot.css('height', height + 'px');
            }
        }

        this.carouselSlotLoad = function (element) {
            const $slot = $(element);

            if ($slot.data('carouselJob') || $slot.children('img').length) {
                return;
            }

            const url = $slot.attr('data-image-url');

            if (!url) {
                return;
            }

            const job = {
                $slot: $slot, handlerError: self.carouselSlotErrorShow,
                handlerSuccess: self.carouselSlotImageShow, url: url
            };

            $slot.data('carouselJob', job);

            self.requestSubmit(job);
        }

        this.carouselSlotUnload = function (element) {
            const $slot = $(element);
            const job = $slot.data('carouselJob');

            if (job) {
                 
                self.requestCancel(job);
                $slot.removeData('carouselJob');
            }

            const $image = $slot.children('img');

            if (!$image.length) {
                return;
            }

            self.carouselSlotHeightStore($slot, $image);

             
            const source = $image.attr('src');

            $image.off();
            $image.remove();

            if (source && source.startsWith('blob:')) {
                URL.revokeObjectURL(source);
            }

            $slot.addClass('carousel-item-image-slot-empty');
        }

        this.carouselObserverList = [];

        this.carouselObserverDisconnect = function () {
            for (const observer of self.carouselObserverList) {
                observer.disconnect();
            }

            self.carouselObserverList = [];
        }

        this.carouselObserverSetup = function () {
             
            const container = document.getElementById('carousel-container');

            if (!container) {
                return;
            }

            const observerLoad = new IntersectionObserver(
                function (entryList) {
                    for (const entry of entryList) {
                        if (entry.isIntersecting) {
                            self.carouselSlotLoad(entry.target);
                        }
                    };
                }, {
                    root: container, rootMargin: CAROUSEL_MARGIN_LOAD
                }
            );

            const observerUnload = new IntersectionObserver(
                function (entryList) {
                    for (const entry of entryList) {
                        if (!entry.isIntersecting) {
                            self.carouselSlotUnload(entry.target);
                        }
                    };
                }, {
                    root: container, rootMargin: CAROUSEL_MARGIN_UNLOAD
                }
            );

            self.carouselObserverList.push(observerLoad, observerUnload);

            $('.carousel-item-image-slot').each(function (index, element) {
                observerLoad.observe(element);
                observerUnload.observe(element);
            });
        }

        this.eventHandlerImageError = function (event) {
             
            const $this = $(this);

            $this.siblings('.lazyload-spinner-container').remove();
            $this.removeClass('lazy-load pull-left');
        }

        this.imageObjectUrlRevoke = function ($image) {
             
            const source = $image.attr('src');

            if (source && source.startsWith('blob:')) {
                URL.revokeObjectURL(source);
            }
        }

        this.imageObjectUrlRevokeAll = function ($container) {
            $container.find('img[data-src]').each(function (index, element) {
                self.imageObjectUrlRevoke(
                    $(element)
                );
            });
        }

        this.imageShow = function (job, blob) {
            if (job.cancelled) {
                return;
            }

            const $image = job.$image;

            $image.removeData('imageJob');

             
            $image.attr(
                'src', URL.createObjectURL(blob)
            );
        }

        this.imageErrorShow = function (job, markup) {
            if (job.cancelled) {
                return;
            }

            const $image = job.$image;

            $image.removeData('imageJob');
            $image.siblings('.lazyload-spinner-container').remove();

             
            $image.closest('a.fancybox').removeClass(
                'fancybox'
            ).removeAttr('data-fancybox').removeAttr('href');

             
            const $container = $image.closest('.instance-image-widget');

            self.observerIntersection.unobserve($image[0]);

            if ($container.length) {
                $container.html(markup);
            } else {
                $image.replaceWith(markup);
            }
        }

        this.imageLoad = function ($image) {
            const dataSrc = $image.attr('data-src');

            if (!dataSrc) {
                return;
            }

            if ($image.data('imageJob')) {
                
                return;
            }

            const source = $image.attr('src');

            if (source && source.startsWith('blob:')) {
                
                return;
            }

             
            const job = {
                $image: $image, handlerError: self.imageErrorShow,
                handlerSuccess: self.imageShow, url: dataSrc
            };

            $image.data('imageJob', job);
            $image.off('error', self.eventHandlerImageError).on(
                'error', self.eventHandlerImageError
            );

            self.requestSubmit(job);
        }

        this.imageUnload = function ($image) {
             
            const job = $image.data('imageJob');

            if (job) {
                 
                self.requestCancel(job);
                $image.removeData('imageJob');
                return;
            }

            if (!$image.is('.lazy-load-carousel-loaded')) {
                return;
            }

            $image.css(
                {
                    height: $image.height() + 'px',
                    width: $image.width() + 'px'
                }
            );

            $image.off('error', self.eventHandlerImageError);
            self.imageObjectUrlRevoke($image);
            $image.removeAttr('src');
        }

        this.observerIntersection = new IntersectionObserver(
            function (entryList) {
                for (const entry of entryList) {
                    const $image = $(entry.target);

                    if (entry.isIntersecting) {
                        self.imageLoad($image);
                    } else {
                        self.imageUnload($image);
                    }
                };
            }, {
                rootMargin: IMAGE_RETENTION_MARGIN
            }
        );

        mayanApp.partialNavigationApp.$ajaxContent.on('preupdate', function (event) {
            self.observerIntersection.disconnect();
            self.carouselObserverDisconnect();
            self.requestQueueClear();
            self.imageObjectUrlRevokeAll(
                mayanApp.partialNavigationApp.$ajaxContent
            );
        });

        mayanApp.partialNavigationApp.$ajaxContent.on('updated', function (event) {
            $('img.lazy-load').each(async function(index, element) {
                self.observerIntersection.observe(element);
            });

            self.carouselObserverSetup();

            $('.lazy-load').on('load', async function() {
                const $this = $(this);

                $this.siblings('.lazyload-spinner-container').remove();
                $this.removeClass('lazy-load pull-left');
            });
        });
    }
}
