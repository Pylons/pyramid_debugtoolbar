import re

from pyramid_debugtoolbar.tbtools import Traceback
from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import escape
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME

_ = lambda x: x

class TracebackPanel(DebugPanel):
    name = 'traceback'
    template = 'pyramid_debugtoolbar.panels:templates/traceback.dbtmako'
    title = _('Traceback')
    nav_title = title

    def __init__(self, request):
        self.request = request
        self.traceback = None
        self.exc_history = request.exc_history

    @property
    def has_content(self):
        return self.traceback is not None

    def process_response(self, response):
        self.traceback = traceback = getattr(self.request, 'pdbt_tb', None)
        if self.traceback is not None:
            exc = escape(traceback.exception)
            token = self.request.registry.pdtb_token
            url = '' # self.request.route_url(EXC_ROUTE_NAME, _query=qs)
            evalex = self.exc_history.eval_exc

            self.data = {
                'evalex':           evalex and 'true' or 'false',
                'console':          'false',
                'lodgeit_url':      None,
                'title':            exc,
                'exception':        exc,
                'exception_type':   escape(traceback.exception_type),
                'plaintext':        traceback.plaintext,
                'plaintext_cs':     re.sub('-{2,}', '-', traceback.plaintext),
                'traceback_id':     traceback.id,
                'token':            token,
                'url':              url,
            }

        # stop hanging onto the request after the response is processed
        del self.request

    def render_vars(self, request):
        return {
            'static_path': request.static_url(STATIC_PATH),
            'root_path': request.route_url(ROOT_ROUTE_NAME),

            # render the summary using the toolbar's request object, not
            # the original request that generated the traceback!
            'summary': self.traceback.render_summary(
                include_title=False, request=request),
        }
