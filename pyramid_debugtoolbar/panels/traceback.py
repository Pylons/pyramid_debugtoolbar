import re

from pyramid_debugtoolbar.tbtools import Traceback
from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import escape
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
from pyramid_debugtoolbar.utils import EXC_ROUTE_NAME

_ = lambda x: x

class TracebackPanel(DebugPanel):
    name = 'Traceback'
    template = 'pyramid_debugtoolbar.panels:templates/traceback.dbtmako'
    title = _('Traceback')
    nav_title = title

    def __init__(self, request):
        self.request = request
        self.exc_history = request.exc_history

    @property
    def has_content(self):
        if hasattr(self.request, 'pdbt_tb'):
            return True
        else:
            return False

    def process_response(self, response):
        if self.has_content:
            traceback = self.request.pdbt_tb

            exc = escape(traceback.exception)
            summary = Traceback.render_summary(traceback, include_title=False, request=self.request)
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
                'summary':          summary,
                'plaintext':        traceback.plaintext,
                'plaintext_cs':     re.sub('-{2,}', '-', traceback.plaintext),
                'traceback_id':     traceback.id,
                'token':            token,
                'url':              url,
            }

    def render_content(self, request):
        return super(TracebackPanel, self).render_content(request)

    def render_vars(self, request):
        return {
            'static_path': request.static_url(STATIC_PATH),
            'root_path': request.route_url(ROOT_ROUTE_NAME)
        }
