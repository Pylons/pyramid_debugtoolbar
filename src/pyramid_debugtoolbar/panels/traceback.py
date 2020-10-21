from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config
import re

from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import (
    EXC_ROUTE_NAME,
    ROOT_ROUTE_NAME,
    STATIC_PATH,
    escape,
)

_ = lambda x: x


class TracebackPanel(DebugPanel):
    name = 'traceback'
    template = 'pyramid_debugtoolbar.panels:templates/traceback.dbtmako'
    title = _('Traceback')
    nav_title = title

    def __init__(self, request):
        self.request = request
        self.traceback = None

    @property
    def has_content(self):
        return self.traceback is not None

    def process_response(self, response):
        self.traceback = traceback = getattr(
            self.request.debug_toolbar, 'traceback', None
        )
        if self.traceback is not None:
            exc = escape(traceback.exception)
            evalex = self.request.registry.pdtb_eval_exc

            self.data = {
                'evalex': evalex and 'true' or 'false',
                'console': 'false',
                'lodgeit_url': None,
                'title': exc,
                'exception': exc,
                'exception_type': escape(traceback.exception_type),
                'plaintext': traceback.plaintext,
                'plaintext_cs': re.sub('-{2,}', '-', traceback.plaintext),
                'pdtb_token': self.request.registry.pdtb_token,
                'request_id': self.request.pdtb_id,
            }

        # stop hanging onto the request after the response is processed
        del self.request

    def render_vars(self, request):
        vars = self.data.copy()
        vars.update(
            {
                'static_path': request.static_url(STATIC_PATH),
                'root_path': request.route_url(ROOT_ROUTE_NAME),
                'url': request.route_url(
                    EXC_ROUTE_NAME, request_id=request.pdtb_id
                ),
                # render the summary using the toolbar's request object, not
                # the original request that generated the traceback!
                'summary': self.traceback.render_summary(
                    include_title=False, request=request
                ),
            }
        )
        return vars


class ExceptionDebugView(object):
    def __init__(self, request):
        self.request = request

    @property
    def history(self):
        request_id = self.request.matchdict['request_id']
        history = self.request.pdtb_history.get(request_id)
        if history is None:
            raise HTTPBadRequest('No history found for request.')
        return history

    @property
    def traceback(self):
        tb = getattr(self.history, 'traceback', None)
        if tb is None:
            raise HTTPBadRequest('No traceback found for request.')
        return tb

    @property
    def frame(self):
        frame_id = self.request.matchdict['frame_id']
        for frame in self.traceback.frames:
            if frame.id == frame_id:
                return frame
        raise HTTPBadRequest('Invalid traceback frame.')

    @view_config(route_name='debugtoolbar.exception')
    def exception(self):
        tb = self.traceback
        body = tb.render_full(self.request).encode('utf-8', 'replace')
        return Response(body, content_type='text/html', status=500)

    @view_config(route_name='debugtoolbar.source')
    def source(self):
        frame = self.frame
        body = frame.render_source()
        return Response(body, content_type='text/html')

    @view_config(route_name='debugtoolbar.execute')
    def execute(self):
        if not self.request.registry.parent_registry.pdtb_eval_exc:
            raise HTTPBadRequest(
                'Evaluating code in stack frames is not allowed.'
            )
        frame = self.frame
        cmd = self.request.params.get('cmd')
        if cmd is None:
            raise HTTPBadRequest('Missing command.')
        body = frame.console.eval(cmd)
        return Response(body, content_type='text/html')


def includeme(config):
    config.add_route(EXC_ROUTE_NAME, '/{request_id}/exception')
    config.add_route(
        'debugtoolbar.source',
        '{request_id}/exception/source/{frame_id}',
    )
    config.add_route(
        'debugtoolbar.execute',
        '/{request_id}/exception/execute/{frame_id}',
    )

    config.add_debugtoolbar_panel(TracebackPanel)
    config.scan(__name__)
