from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.compat import text_
import re


_ = lambda x: x


REGEX_traceback_message = re.compile("""URL to recover this traceback page: <a href="(?P<url_encoded>[^"]*)">(?P<url_raw>[^"]*)</a>""", re.I)


class ExceptionDebugPanel(DebugPanel):
    """
    A panel to display exception data
    """
    name = 'exception'
    template = 'pyramid_debugtoolbar.panels:templates/exception.dbtmako'
    title = _('Exception')
    nav_title = title
    
    traceback_url = None

    def __init__(self, request):
        pass

    def process_response(self, response):
        t = response.text
        if t:
            exceptions = REGEX_traceback_message.findall(t)
            if exceptions:
                self.traceback_url = exceptions[0][1]  # use the url_raw of the first match
        self.data = {'traceback_url': self.traceback_url}

    @property
    def has_content(self):
        return bool(self.traceback_url)
