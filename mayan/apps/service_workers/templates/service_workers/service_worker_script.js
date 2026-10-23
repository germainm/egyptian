'use strict';

/*
 * Mayan EDMS gateway-error service worker.
 *
 * This script is served from the site root so its scope covers the whole
 * origin. It intercepts top level browser navigations and, when the reverse
 * proxy answers with a gateway error (HTTP 502, 503, 504) or the server is
 * unreachable, it substitutes a branded, translated fallback page instead of
 * the proxy's raw error output.
 *
 * The fallback page is produced by the backend so it inherits the deployment
 * theme (color mode, text direction, project title) and the active language.
 * While the backend is reachable the worker fetches the page and the
 * stylesheets it links and stores them in the cache; those cached copies are
 * what it serves once the backend goes down, so the fallback stays styled even
 * during a full outage. A copy of the page is also embedded in the
 * configuration below and used as a cold-cache fallback, so the worker always
 * has something to show even before the first successful fetch. Only the
 * fallback page and its stylesheets are cached, never application responses,
 * so a stale application shell can never be served.
 *
 * The Mayan version is embedded in the configuration to guarantee a byte level
 * change of this script on each release, which triggers a service worker
 * update.
 */

class MayanGatewayServiceWorker {
    constructor (options) {
        this.version = options.version;
        this.enabled = options.enabled;
        this.errorPageHtml = options.errorPageHtml;
        this.pageUrl = options.pageUrl;
        this.assetUrlList = options.assetUrlList || [];

        this.gatewayStatusCodeList = [502, 503, 504];
        this.cachePrefix = 'mayan-gateway-error-';
        this.cacheName = this.cachePrefix + this.version;

        // Refresh the cached page and stylesheets at most this often while
        // browsing, so a theme or language change is eventually reflected
        // without a request per navigation. Configured in seconds, kept
        // internally in milliseconds. Reset when the browser restarts the
        // worker.
        const cacheRefreshIntervalSeconds = (typeof options.cacheRefreshInterval === 'number') ? options.cacheRefreshInterval : 600;
        this.cacheRefreshInterval = cacheRefreshIntervalSeconds * 1000;
        this.cacheLastRefresh = 0;
        this.cacheRefreshInFlight = null;

        // Absolute forms of the precached asset URLs, matched against fetched
        // request URLs, which are always absolute.
        this.assetUrlSet = new Set(
            this.assetUrlList.map(
                function (url) {
                    return new URL(url, self.location.origin).href;
                }
            )
        );
    }

    start () {
        const instance = this;

        self.addEventListener('install', function () {
            self.skipWaiting();
        });

        if (this.enabled) {
            self.addEventListener('activate', function (event) {
                instance.onActivate(event);
            });

            self.addEventListener('fetch', function (event) {
                instance.onFetch(event);
            });
        } else {
            self.addEventListener('activate', function (event) {
                instance.onActivateDisabled(event);
            });
        }
    }

    buildGatewayErrorResponse (html) {
        return new Response(
            html, {
                headers: {
                    'Cache-Control': 'no-store',
                    'Content-Type': 'text/html; charset=utf-8'
                },
                status: 503,
                statusText: 'Service Unavailable'
            }
        );
    }

    getGatewayErrorResponse () {
        // Prefer the backend-rendered copy captured while the server was
        // reachable; fall back to the copy embedded in this script.
        const instance = this;

        if (!self.caches) {
            return Promise.resolve(
                instance.buildGatewayErrorResponse(instance.errorPageHtml)
            );
        }

        return self.caches.open(instance.cacheName).then(
            function (cache) {
                return cache.match(instance.pageUrl);
            }
        ).then(
            function (response) {
                if (response) {
                    return response.text();
                }

                return instance.errorPageHtml;
            }
        ).then(
            function (html) {
                return instance.buildGatewayErrorResponse(html);
            }
        ).catch(
            function () {
                return instance.buildGatewayErrorResponse(instance.errorPageHtml);
            }
        );
    }

    getAssetResponse (request) {
        // Network first so normal browsing always gets fresh assets; fall back
        // to the precached copy only when the network is unavailable.
        const instance = this;

        return fetch(request).catch(
            function () {
                return self.caches.open(instance.cacheName).then(
                    function (cache) {
                        return cache.match(request);
                    }
                ).then(
                    function (response) {
                        return response || Response.error();
                    }
                );
            }
        );
    }

    cachePutUrl (cache, url) {
        // Fetch a URL and store the response. Failures leave any previously
        // cached copy untouched.
        return fetch(
            url, {credentials: 'same-origin'}
        ).then(
            function (response) {
                if (response && response.ok) {
                    return cache.put(url, response.clone());
                }
            }
        ).catch(
            function () {
                // Offline or errored; keep any previously cached copy.
            }
        );
    }

    refreshCache () {
        // Fetch the backend-rendered fallback page and its stylesheets and
        // store them for offline use. Concurrent calls share a single
        // in-flight run.
        const instance = this;

        if (!self.caches) {
            return Promise.resolve();
        }

        if (instance.cacheRefreshInFlight) {
            return instance.cacheRefreshInFlight;
        }

        instance.cacheLastRefresh = Date.now();

        instance.cacheRefreshInFlight = self.caches.open(instance.cacheName).then(
            function (cache) {
                var job_list = [instance.cachePutUrl(cache, instance.pageUrl)];

                instance.assetUrlList.forEach(
                    function (url) {
                        job_list.push(instance.cachePutUrl(cache, url));
                    }
                );

                return Promise.all(job_list);
            }
        ).catch(
            function () {
                // Ignore; keep any previously cached copies.
            }
        ).then(
            function () {
                instance.cacheRefreshInFlight = null;
            }
        );

        return instance.cacheRefreshInFlight;
    }

    deleteStaleCaches () {
        const instance = this;

        if (!self.caches) {
            return Promise.resolve();
        }

        return self.caches.keys().then(
            function (name_list) {
                return Promise.all(
                    name_list.filter(
                        function (name) {
                            return name.indexOf(instance.cachePrefix) === 0 && name !== instance.cacheName;
                        }
                    ).map(
                        function (name) {
                            return self.caches.delete(name);
                        }
                    )
                );
            }
        );
    }

    onActivate (event) {
        // Drop caches from previous versions, take control of open clients,
        // then capture a fresh copy of the fallback page and stylesheets for
        // offline use.
        const instance = this;

        event.waitUntil(
            instance.deleteStaleCaches().then(
                function () {
                    return self.clients.claim();
                }
            ).then(
                function () {
                    return instance.refreshCache();
                }
            )
        );
    }

    onFetch (event) {
        const instance = this;
        var request = event.request;

        // Take over full page navigations. In application XHR/fetch traffic
        // keeps its own error handling.
        if (request.mode === 'navigate') {
            event.respondWith(
                fetch(request).then(
                    function (response) {
                        if (instance.gatewayStatusCodeList.indexOf(response.status) !== -1) {
                            return instance.getGatewayErrorResponse();
                        }

                        // The backend answered; opportunistically keep the
                        // cached page and stylesheets current, throttled so it
                        // costs at most one extra set of requests per interval.
                        if (Date.now() - instance.cacheLastRefresh > instance.cacheRefreshInterval) {
                            try {
                                event.waitUntil(instance.refreshCache());
                            } catch (error) {
                                // The event is no longer extendable; refresh
                                // without keeping the worker alive.
                                instance.refreshCache();
                            }
                        }

                        return response;
                    }
                ).catch(
                    function () {
                        return instance.getGatewayErrorResponse();
                    }
                )
            );

            return;
        }

        // Serve a precached stylesheet from the cache when the network is
        // unavailable, so the fallback page stays styled during a full outage.
        if (request.method === 'GET' && instance.assetUrlSet.has(request.url)) {
            event.respondWith(instance.getAssetResponse(request));
        }
    }

    onActivateDisabled (event) {
        // The feature is disabled. Self destruct so a previously installed
        // worker stops controlling the origin and the site returns to its
        // default proxy served behavior.
        const instance = this;

        event.waitUntil(
            instance.deleteStaleCaches().then(
                function () {
                    return self.registration.unregister();
                }
            ).then(
                function () {
                    return self.clients.matchAll(
                        {
                            type: 'window'
                        }
                    );
                }
            ).then(
                function (client_list) {
                    client_list.forEach(
                        function (client) {
                            client.navigate(client.url);
                        }
                    );
                }
            )
        );
    }
}

new MayanGatewayServiceWorker(
    {
        version: '{{ version }}',
        enabled: {{ enabled|yesno:"true,false" }},
        errorPageHtml: {{ error_page_json|safe }},
        pageUrl: '{{ error_page_url|escapejs }}',
        assetUrlList: {{ asset_url_json|safe }},
        cacheRefreshInterval: {{ cache_refresh_interval }}
    }
).start();
