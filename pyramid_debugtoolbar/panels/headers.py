from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.compat import text_

_ = lambda x: x


class HeaderDebugPanel(DebugPanel):
    """
    A panel to display HTTP request and response headers.
    """
    name = 'header'
    has_content = True
    template = 'pyramid_debugtoolbar.panels:templates/headers.dbtmako'
    title = _('HTTP Headers')
    nav_title = title

    def __init__(self, request):
        self.request_headers = [
            (text_(k), text_(v)) for k, v in sorted(request.headers.items())
        ]

    def process_response(self, response):
        response_headers = [
            (text_(k), text_(v)) for k, v in sorted(response.headerlist)
        ]
        self.data = {'request_headers': self.request_headers,
                     'response_headers': response_headers}
