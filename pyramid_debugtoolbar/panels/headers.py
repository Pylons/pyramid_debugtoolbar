from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.compat import text_

_ = lambda x: x


class HeaderDebugPanel(DebugPanel):
    """
    A panel to display HTTP request and response headers.
    """
    name = 'Header'
    has_content = True
    response_headers = ()

    def __init__(self, request):
        self.request = request
        self.request_headers = [
            (text_(k), text_(v)) for k, v in sorted(request.headers.items())
        ]

    def process_response(self, response):
        self.response_headers = [
            (text_(k), text_(v)) for k, v in sorted(response.headerlist)
        ]

    def nav_title(self):
        return _('HTTP Headers')

    def title(self):
        return _('HTTP Headers')

    def url(self):
        return ''

    def content(self):
        vars = {'request_headers': self.request_headers,
                'response_headers': self.response_headers}
        return self.render(
            'pyramid_debugtoolbar.panels:templates/headers.dbtmako',
            vars, self.request)
