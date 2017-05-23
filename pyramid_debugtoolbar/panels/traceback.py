import re

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import escape
from pyramid_debugtoolbar.utils import EXC_ROUTE_NAME
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

class ExceptionDebugView(object):
    def __init__(self, request):
        self.request = request
        exc_history = request.exc_history
        if exc_history is None:
            raise HTTPBadRequest('No exception history')
        self.exc_history = exc_history
        token = self.request.matchdict.get('token')
        if not token:
            raise HTTPBadRequest('No token in request')
        if not token == request.registry.parent_registry.pdtb_token:
            raise HTTPBadRequest('Bad token in request')
        self.token = token
        frm = self.request.params.get('frm')
        if frm is not None:
            frm = int(frm)
        self.frame = frm
        cmd = self.request.params.get('cmd')
        self.cmd = cmd
        tb = self.request.params.get('tb')
        if tb is not None:
            tb = int(tb)
        self.tb = tb

    @view_config(route_name='debugtoolbar.exception')
    def exception(self):
        tb = self.exc_history.tracebacks[self.tb]
        body = tb.render_full(self.request).encode('utf-8', 'replace')
        response = Response(body, status=500)
        return response

    @view_config(route_name='debugtoolbar.source')
    def source(self):
        exc_history = self.exc_history
        if self.frame is not None:
            frame = exc_history.frames.get(self.frame)
            if frame is not None:
                return Response(frame.render_source(), content_type='text/html')
        return HTTPBadRequest()

    @view_config(route_name='debugtoolbar.execute')
    def execute(self):
        if self.request.exc_history.eval_exc:
            exc_history = self.exc_history
            if self.frame is not None and self.cmd is not None:
                frame = exc_history.frames.get(self.frame)
                if frame is not None:
                    result = frame.console.eval(self.cmd)
                    return Response(result, content_type='text/html')
        return HTTPBadRequest()

def includeme(config):
    config.add_route(EXC_ROUTE_NAME, '/exception/{token}')
    config.add_route('debugtoolbar.source', '/source/{token}')
    config.add_route('debugtoolbar.execute', '/execute/{token}')

    config.add_debugtoolbar_panel(TracebackPanel)
    config.scan(__name__)
