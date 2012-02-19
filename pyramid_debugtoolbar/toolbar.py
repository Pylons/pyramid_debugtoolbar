import binascii
import sys
import os

from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid.response import Response
from pyramid_debugtoolbar.tbtools import get_traceback
from pyramid_debugtoolbar.compat import url_unquote
from pyramid_debugtoolbar.compat import bytes_
from pyramid_debugtoolbar.compat import text_
from pyramid_debugtoolbar.utils import get_setting
from pyramid_debugtoolbar.utils import replace_insensitive
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
from pyramid_debugtoolbar.utils import EXC_ROUTE_NAME
from pyramid_debugtoolbar.utils import logger
from pyramid.httpexceptions import WSGIHTTPException

class DebugToolbar(object):

    html_types = ('text/html', 'application/xml+html')

    def __init__(self, request, panel_classes):
        self.request = request
        self.panels = []
        pdtb_active = url_unquote(self.request.cookies.get('pdtb_active', ''))
        activated = pdtb_active.split(';')
        for panel_class in panel_classes:
            panel_inst = panel_class(request)
            if panel_inst.dom_id() in activated and panel_inst.has_content:
                panel_inst.is_active = True
            self.panels.append(panel_inst)

    def process_response(self, response):
        # If the body is HTML, then we add the toolbar to the response.
        request = self.request

        if isinstance(response, WSGIHTTPException):
            # the body of a WSGIHTTPException needs to be "prepared"
            response.prepare(request.environ)

        for panel in self.panels:
            panel.process_response(response)

        if response.content_type in self.html_types:
            static_path = request.static_url(STATIC_PATH)
            root_path = request.route_url(ROOT_ROUTE_NAME)
            button_style = get_setting(request.registry.settings,
                    'button_style', '')
            vars = {'panels': self.panels, 'static_path': static_path,
                    'root_path': root_path, 'button_style': button_style}
            toolbar_html = render(
                    'pyramid_debugtoolbar:templates/toolbar.dbtmako',
                    vars, request=request)
            response_html = response.body
            toolbar_html = toolbar_html.encode(response.charset or 'utf-8')
            body = replace_insensitive(
                response_html, bytes_('</body>'),
                toolbar_html + bytes_('</body>')
                )
            response.app_iter = [body]
            response.content_length = len(body)

class ExceptionHistory(object):
    def __init__(self):
        self.token = text_(binascii.hexlify(os.urandom(10)))
        self.frames = {}
        self.tracebacks = {}

def beforerender_subscriber(event):
    request = event['request']
    if request is None:
        request = get_current_request()
    if getattr(request, 'debug_toolbar', None) is not None:
        for panel in request.debug_toolbar.panels:
            panel.process_beforerender(event)

def toolbar_tween_factory(handler, registry):
    """ Pyramid tween factory for the debug toolbar """
    settings = registry.settings

    if not get_setting(settings, 'enabled'):
        return handler

    redirect_codes = (301, 302, 303, 304)
    panel_classes = get_setting(settings, 'panels', [])
    intercept_exc = get_setting(settings, 'intercept_exc')
    intercept_redirects = get_setting(settings, 'intercept_redirects')
    hosts = get_setting(settings, 'hosts')

    exc_history = None

    if intercept_exc:
        exc_history = ExceptionHistory()
        exc_history.eval_exc = intercept_exc == 'debug'

    def toolbar_tween(request):
        root_path = request.route_path(ROOT_ROUTE_NAME)
        request.exc_history = exc_history
        remote_addr = request.remote_addr

        if (request.path.startswith(root_path) or (not remote_addr in hosts)):
            return handler(request)

        toolbar = DebugToolbar(request, panel_classes)
        request.debug_toolbar = toolbar
        
        _handler = handler

        for panel in toolbar.panels:
            _handler = panel.wrap_handler(_handler)

        try:
            response = _handler(request)
        except Exception:
            if exc_history is not None:
                tb = get_traceback(info=sys.exc_info(),
                                   skip=1,
                                   show_hidden_frames=False,
                                   ignore_system_exceptions=True)
                for frame in tb.frames:
                    exc_history.frames[frame.id] = frame

                exc_history.tracebacks[tb.id] = tb
                body = tb.render_full(request).encode('utf-8', 'replace')
                response = Response(body, status=500)
                toolbar.process_response(response)
                qs = {'token':exc_history.token, 'tb':str(tb.id)}
                msg = 'Exception at %s\ntraceback url: %s' 
                exc_url = request.route_url(EXC_ROUTE_NAME, _query=qs)
                exc_msg = msg % (request.url, exc_url)
                logger.exception(exc_msg)
                return response
            else:
                logger.exception('Exception at %s' % request.url)
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
                            'pyramid_debugtoolbar:templates/redirect.dbtmako',
                            {'redirect_to': redirect_to,
                            'redirect_code': redirect_code},
                            request=request)
                        content = content.encode(response.charset)
                        response.content_length = len(content)
                        response.location = None
                        response.app_iter = [content]
                        response.status_int = 200

            toolbar.process_response(response)
            return response

        finally:
            # break circref
            del request.debug_toolbar

    return toolbar_tween
