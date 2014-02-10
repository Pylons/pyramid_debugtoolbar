$(document).ready(function() {
    var source;

    function new_request(e) {
        var requests = $('ul#requests');
        console.log(e);
    }

    function connectEventSource() {
        if (source) {
            source.close();
        }

        source = new EventSource('/_debug_toolbar/sse');
        source.addEventListener('new_request', new_request);
    }

    if (!!window.EventSource) {
        connectEventSource();
    }
});
