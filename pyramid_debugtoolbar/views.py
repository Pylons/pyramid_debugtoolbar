from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_debugtoolbar.console import _ConsoleFrame
from pyramid_debugtoolbar import STATIC_PATH

class ExceptionDebugView(object):
    def __init__(self, request):
        self.request = request
        frm = self.request.params.get('frm')
        if frm is not None:
            frm = int(frm)
        self.frame = frm
        cmd = self.request.params.get('cmd')
        self.cmd = cmd

    @view_config(route_name='debugtoolbar.source')
    def source(self):
        exc_history = self.request.exc_history
        frame = exc_history.frames.get(self.frame)
        return Response(frame.render_source(), content_type='text/html')

    @view_config(route_name='debugtoolbar.execute')
    def execute(self):
        exc_history = self.request.exc_history
        if self.frame is not None and exc_history:
            frame = exc_history.frames.get(self.frame)
            if self.cmd is not None and frame is not None:
                return Response(frame.console.eval(self.cmd),
                                content_type='text/html')
        return HTTPNotFound()
        
    @view_config(route_name='debugtoolbar.console',
                 renderer='pyramid_debugtoolbar:templates/console.jinja2')
    def console(self):
        request = self.request
        static_path = request.static_url(STATIC_PATH)
        exc_history = request.exc_history
        if exc_history:
            vars = {
                'evalex':           'true',
                'console':          'true',
                'title':            'Console',
                'traceback_id':     -1,
                'static_path':      static_path,
                }
            if 0 not in exc_history.frames:
                exc_history.frames[0] = _ConsoleFrame({})
            return vars
        return HTTPNotFound()

