from pyramid_debugtoolbar.compat import text_
from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x


class HeaderDebugPanel(DebugPanel):
    """
    A panel to display HTTP request and response headers.
    """

    name = 'headers'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/headers.dbtmako'
    title = _('HTTP Headers')
    nav_title = title

    def __init__(self, request):
        def finished_callback(request):
            self.process_response_deferred()

        request.add_finished_callback(finished_callback)
        self.request_headers = [
            (text_(k), text_(v)) for k, v in sorted(request.headers.items())
        ]

    def process_response(self, response):
        self.response = response
        self.data = {
            'request_headers': self.request_headers,
            'response_headers': [],
        }

    def process_response_deferred(self):
        response = self.response
        response_headers = [
            (text_(k), text_(v)) for k, v in sorted(response.headerlist)
        ]
        self.data['response_headers'] = response_headers


def includeme(config):
    config.add_debugtoolbar_panel(HeaderDebugPanel)
