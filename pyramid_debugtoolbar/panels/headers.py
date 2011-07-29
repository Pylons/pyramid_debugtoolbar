from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x


class HeaderDebugPanel(DebugPanel):
    """
    A panel to display HTTP headers.
    """
    name = 'Header'
    has_content = True

    # List of CGI headers to display along with HTTP_ custom headers
    request_header_filter = (
        'CONTENT_TYPE',
        'QUERY_STRING',
        'REMOTE_ADDR',
        'REMOTE_HOST',
        'REQUEST_METHOD',
        'SCRIPT_NAME',
        'SERVER_NAME',
        'SERVER_PORT',
        'SERVER_PROTOCOL',
        'SERVER_SOFTWARE',
        'PATH_INFO',
    )

    def __init__(self, request):
        self.request = request
        self.request_headers = dict([
            (k, request.environ[k]) for k in request.environ
            if k in self.header_filter or k.startswith('HTTP_')
        ])

    def nav_title(self):
        return _('HTTP Headers')

    def title(self):
        return _('HTTP Headers')

    def url(self):
        return ''

    def content(self):
        vars = {'headers': self.headers}
        return self.render(
            'pyramid_debugtoolbar.panels:templates/headers.jinja2',
            vars, self.request)
