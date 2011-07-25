from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_debugtoolbar.console import _ConsoleFrame
from pyramid_debugtoolbar.tbtools import render_console_html

class ExcDebugView(object):
    def __init__(self, request):
        self.request = request
        frm = self.request.params.get('frm')
        if frm is not None:
            frm = int(frm)
        self.frame = frm
        cmd = self.request.params.get('cmd')
        self.cmd = cmd

    @view_config(route_name='debugtb.source')
    def source(self):
        exc_history = self.request.exc_history
        frame = exc_history.frames.get(self.frame)
        return Response(frame.render_source(), content_type='text/html')

    @view_config(route_name='debugtb.execute')
    def execute(self):
        exc_history = self.request.exc_history
        if self.frame is not None and exc_history:
            frame = exc_history.frames.get(self.frame)
            if self.cmd is not None and frame is not None:
                return Response(frame.console.eval(self.cmd),
                                content_type='text/html')
        return HTTPNotFound()
        
    @view_config(route_name='debugtb.console')
    def console(self):
        exc_history = self.request.exc_history
        if exc_history:
            if 0 not in self.frames:
                exc_history.frames[0] = _ConsoleFrame({})
            return Response(render_console_html(), content_type='text/html')

        return HTTPNotFound()

