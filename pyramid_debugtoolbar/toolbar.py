import sys

from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid.response import Response
from pyramid_debugtoolbar.utils import replace_insensitive, get_setting
from pyramid_debugtoolbar.tbtools import get_traceback

class DebugToolbar(object):

    html_types = ('text/html', 'application/xml+html')

    def __init__(self, request, panel_classes):
        self.request = request
        self.panels = []
        activated = self.request.cookies.get('fldt_active', '').split(';')
        for panel_class in panel_classes:
            panel_inst = panel_class(request)
            if panel_inst.dom_id() in activated and not panel_inst.down:
                panel_inst.is_active = True
            self.panels.append(panel_inst)

    def process_response(self, response):
        # If the body is HTML, then we add the toolbar to the response.
        request = self.request

        for panel in self.panels:
            panel.process_response(request, response)

        if response.content_type in self.html_types:
            static_path = request.static_url('pyramid_debugtoolbar:static/')
            vars = {'panels': self.panels, 'static_path':static_path}
            toolbar_html = render('pyramid_debugtoolbar:templates/base.jinja2',
                                  vars, request=request)
            toolbar_html = toolbar_html.encode(response.charset)
            response_html = response.body
            body = replace_insensitive(response_html, '</body>',
                                       toolbar_html + '</body>')
            response.app_iter = [body]

class ExceptionHistory(object):
    def __init__(self):
        self.frames = {}
        self.tracebacks = {}

def beforerender_subscriber(event):
    request = event['request']
    if request is None:
        request = get_current_request()
    if getattr(request, 'debug_toolbar', None) is not None:
        for panel in request.debug_toolbar.panels:
            panel.process_beforerender(event)

def toolbar_handler_factory(handler, registry):
    settings = registry.settings

    if not get_setting(settings, 'enabled'):
        return handler

    redirect_codes = (301, 302, 303, 304)
    panel_classes = get_setting(settings, 'panels', [])
    intercept_exc = get_setting(settings, 'intercept_exc')
    intercept_redirects = get_setting(settings, 'intercept_redirects')

    exc_history = None

    if intercept_exc:
        exc_history = ExceptionHistory()

    def toolbar_handler(request):
        request.exc_history = exc_history

        if request.path.startswith('/_debug_toolbar/'):
            return handler(request)

        toolbar = DebugToolbar(request, panel_classes)
        request.debug_toolbar = toolbar
        
        _handler = handler

        for panel in toolbar.panels:
            _handler = panel.wrap_handler(_handler)

        try:
            response = _handler(request)
        except Exception:
            info = sys.exc_info()
            if exc_history is not None:
                tb = get_traceback(info=info,
                                   skip=1,
                                   show_hidden_frames=False,
                                   ignore_system_exceptions=True)
                for frame in tb.frames:
                    exc_history.frames[frame.id] = frame

                exc_history.tracebacks[tb.id] = tb
                body = tb.render_full(evalex=True).encode('utf-8', 'replace')
                response = Response(body, status=500)
                toolbar.process_response(response)
                return response

            raise

        else:
            if intercept_redirects:
                # Intercept http redirect codes and display an html page with a
                # link to the target.
                if response.status_int in redirect_codes:
                    redirect_to = response.location
                    redirect_code = response.status_int
                    if redirect_to:
                        content = render(
                            'pyramid_debugtoolbar:templates/redirect.jinja2', {
                            'redirect_to': redirect_to,
                            'redirect_code': redirect_code
                        })
                        content = content.encode(response.charset)
                        response.content_length = len(content)
                        response.location = None
                        response.app_iter = [content]
                        response.status_int = 200

            toolbar.process_response(response)
            return response

    return toolbar_handler
