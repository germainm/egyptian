'use strict';

 
class MayanServerSideEvents {
    constructor (options) {
        options = options || {};

        this.url = options.url;
        this.handlers = {};
        this.source = null;
    }

    on (eventType, handler) {
        if (!this.handlers[eventType]) {
            this.handlers[eventType] = [];

            
            
            if (this.source) {
                this._attachListener(eventType);
            }
        }

        this.handlers[eventType].push(handler);

        return this;
    }

    _attachListener (eventType) {
        const self = this;

        this.source.addEventListener(eventType, function (event) {
            let data;

            try {
                data = JSON.parse(event.data);
            } catch (error) {
                data = event.data;
            }

            self.handlers[eventType].forEach(function (handler) {
                handler(data, event);
            });
        });
    }

    connect () {
        if (!this.url || this.source) {
            return;
        }

        this.source = new EventSource(this.url);

        for (const eventType in this.handlers) {
            if (Object.prototype.hasOwnProperty.call(this.handlers, eventType)) {
                this._attachListener(eventType);
            }
        }
    }

    disconnect () {
        if (this.source) {
            this.source.close();
            this.source = null;
        }
    }
}
