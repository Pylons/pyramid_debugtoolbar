from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_debugtoolbar.console import _ConsoleFrame
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME

class ExceptionDebugView(object):
    def __init__(self, request):
        self.request = request
        exc_history = request.exc_history
        if exc_history is None:
            raise HTTPBadRequest('No exception history')
        self.exc_history = exc_history
        token = self.request.params.get('token')
        if not token:
            raise HTTPBadRequest('No token in request')
        if not token == self.exc_history.token:
            raise HTTPBadRequest('Bad token in request')
        frm = self.request.params.get('frm')
        if frm is not None:
            frm = int(frm)
        self.frame = frm
        cmd = self.request.params.get('cmd')
        self.cmd = cmd

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
        exc_history = self.exc_history
        if self.frame is not None and self.cmd is not None:
            frame = exc_history.frames.get(self.frame)
            if frame is not None:
                result = frame.console.eval(self.cmd)
                return Response(result, content_type='text/html')
        return HTTPBadRequest()
        
    @view_config(route_name='debugtoolbar.console',
                 renderer='pyramid_debugtoolbar:templates/console.jinja2')
    def console(self):
        static_path = self.request.static_url(STATIC_PATH)
        toolbar_root_path = self.request.route_url(ROOT_ROUTE_NAME)
        exc_history = self.exc_history
        vars = {
            'evalex':           'true',
            'console':          'true',
            'title':            'Console',
            'traceback_id':     -1,
            'root_path':        toolbar_root_path,
            'static_path':      static_path,
            'token':            exc_history.token,
            }
        if 0 not in exc_history.frames:
            exc_history.frames[0] = _ConsoleFrame({})
        return vars

