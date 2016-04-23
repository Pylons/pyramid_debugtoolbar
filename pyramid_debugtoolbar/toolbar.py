import sys
import os

from pyramid.exceptions import URLDecodeError
from pyramid.httpexceptions import WSGIHTTPException
from pyramid.interfaces import Interface
from pyramid.threadlocal import get_current_request
from pyramid_debugtoolbar.compat import bytes_
from pyramid_debugtoolbar.compat import url_unquote
from pyramid_debugtoolbar.tbtools import get_traceback
from pyramid_debugtoolbar.utils import addr_in
from pyramid_debugtoolbar.utils import debug_toolbar_url
from pyramid_debugtoolbar.utils import get_setting
from pyramid_debugtoolbar.utils import hexlify
from pyramid_debugtoolbar.utils import last_proxy
from pyramid_debugtoolbar.utils import logger
from pyramid_debugtoolbar.utils import make_subrequest
from pyramid_debugtoolbar.utils import replace_insensitive
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ToolbarStorage

html_types = ('text/html', 'application/xhtml+xml')

class IToolbarWSGIApp(Interface):
    """ Marker interface for the toolbar WSGI application."""
    def __call__(environ, start_response):
        pass


class IRequestAuthorization(Interface):
    def __call__(request):
        """
        Toolbar per-request authorization.

        Should return bool values whether toolbar is permitted to monitor
        the provided request.

        """


class DebugToolbar(object):

    def __init__(self, request, panel_classes, global_panel_classes,
                 default_active_panels):
        self.panels = []
        self.global_panels = []
        self.request = request
        self.status_int = 200
        self.default_active_panels = default_active_panels

        # Panels can be be activated (more features) (e.g. Performace panel)
        pdtb_active = url_unquote(request.cookies.get('pdtb_active', ''))

        activated = pdtb_active.split(',')
        # If the panel is activated in the settings, we want to enable it
        activated.extend(default_active_panels)

        def configure_panel(panel):
            panel_inst.is_active = False
            if panel_inst.name in activated and panel_inst.has_content:
                panel_inst.is_active = True
            elif not panel_inst.user_activate:
                panel_inst.is_active = True

        for panel_class in panel_classes:
            panel_inst = panel_class(request)
            configure_panel(panel_inst)
            self.panels.append(panel_inst)
        for panel_class in global_panel_classes:
            panel_inst = panel_class(request)
            configure_panel(panel_inst)
            self.global_panels.append(panel_inst)

    @property
    def json(self):
        return {'method': self.request.method,
                'path': self.request.path,
                'scheme': self.request.scheme,
                'status_code': self.status_int}

    def process_response(self, request, response):
        if isinstance(response, WSGIHTTPException):
            # the body of a WSGIHTTPException needs to be "prepared"
            response.prepare(request.environ)

        for panel in self.panels:
            panel.process_response(response)
        for panel in self.global_panels:
            panel.process_response(response)

    def inject(self, request, response):
        """
        Inject the debug toolbar iframe into an HTML response.
        """
        # called in host app
        response_html = response.body
        toolbar_url = debug_toolbar_url(request, request.pdtb_id)
        button_style = get_setting(request.registry.settings,
                                   'button_style', '')
        css_path = request.static_url(
            STATIC_PATH + 'toolbar/toolbar_button.css')
        toolbar_html = toolbar_html_template % {
            'button_style': (
                'style="{0}"'.format(button_style) if button_style else ""),
            'css_path': css_path,
            'toolbar_url': toolbar_url}
        toolbar_html = toolbar_html.encode(response.charset or 'utf-8')
        response.body = replace_insensitive(
            response_html, bytes_('</body>'),
            toolbar_html + bytes_('</body>')
            )


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


def toolbar_tween_factory(handler, registry, _logger=None, _dispatch=None):
    """ Pyramid tween factory for the debug toolbar """
    # _logger and _dispatch are passed for testing purposes only
    if _logger is None:
        _logger = logger
    if _dispatch is None:
        _dispatch = lambda app, request: request.get_response(app)
    settings = registry.settings

    def sget(opt, default=None):
        return get_setting(settings, opt, default)

    if not sget('enabled'):
        return handler

    max_request_history = sget('max_request_history')
    request_history = ToolbarStorage(max_request_history)
    registry.request_history = request_history

    redirect_codes = (301, 302, 303, 304)
    panel_classes = sget('panels', [])
    panel_classes.extend(sget('extra_panels', []))
    global_panel_classes = sget('global_panels', [])
    global_panel_classes.extend(sget('extra_global_panels', []))
    intercept_exc = sget('intercept_exc')
    intercept_redirects = sget('intercept_redirects')
    show_on_exc_only = sget('show_on_exc_only')
    hosts = sget('hosts')
    auth_check = registry.queryUtility(IRequestAuthorization)
    exclude_prefixes = sget('exclude_prefixes', [])
    registry.exc_history = exc_history = None
    registry.pdtb_token = hexlify(os.urandom(10))

    default_active_panels = sget('active_panels', [])

    if intercept_exc:
        registry.exc_history = exc_history = ExceptionHistory()
        exc_history.eval_exc = intercept_exc == 'debug'

    toolbar_app = registry.getUtility(IToolbarWSGIApp)
    dispatch = lambda request: _dispatch(toolbar_app, request)

    def toolbar_tween(request):
        try:
            p = request.path_info
        except UnicodeDecodeError as e:
            raise URLDecodeError(e.encoding, e.object, e.start, e.end, e.reason)

        last_proxy_addr = None
        if request.remote_addr:
            last_proxy_addr = last_proxy(request.remote_addr)

        if (
            last_proxy_addr is None
            or any(p.startswith(e) for e in exclude_prefixes)
            or not addr_in(last_proxy_addr, hosts)
            or auth_check and not auth_check(request)
        ):
            return handler(request)

        root_path = debug_toolbar_url(request, '', _app_url='')
        if p.startswith(root_path):
            # we know root_path will always have a trailing slash
            # but script_name doesn't want it
            request.script_name += root_path[:-1]
            request.path_info = request.path_info[len(root_path) - 1:]
            return dispatch(request)

        request.exc_history = exc_history
        request.history = request_history
        request.pdtb_id = hexlify(id(request))
        toolbar = DebugToolbar(request, panel_classes, global_panel_classes,
                               default_active_panels)
        request.debug_toolbar = toolbar

        _handler = handler
        for panel in toolbar.panels:
            _handler = panel.wrap_handler(_handler)

        try:
            response = _handler(request)
            toolbar.status_int = response.status_int
        except Exception:
            if exc_history is not None:
                tb = get_traceback(info=sys.exc_info(),
                                   skip=1,
                                   show_hidden_frames=False,
                                   ignore_system_exceptions=True)
                for frame in tb.frames:
                    exc_history.frames[frame.id] = frame
                exc_history.tracebacks[tb.id] = tb
                request.pdbt_tb = tb

                msg = 'Exception at %s\ntraceback url: %s'
                qs = {'token': registry.pdtb_token, 'tb': str(tb.id)}
                subrequest = make_subrequest(
                    request, root_path, 'exception', qs)
                exc_msg = msg % (request.url, subrequest.url)
                _logger.exception(exc_msg)

                response = dispatch(subrequest)

                # The original request must be processed so that the panel data exists
                # if the request is later examined in the full toolbar view.
                toolbar.process_response(request, response)

                toolbar.response = response
                toolbar.status_int = response.status_int

                request_history.put(request.pdtb_id, toolbar)
                # Inject the button to activate the full toolbar view.
                toolbar.inject(request, response)
                return response
            else:
                _logger.exception('Exception at %s' % request.url)
            raise

        else:
            if intercept_redirects:
                # Intercept http redirect codes and display an html page with a
                # link to the target.
                if response.status_int in redirect_codes:
                    redirect_to = response.location
                    redirect_code = response.status_int
                    if redirect_to:
                        qs = {
                            'token': registry.pdtb_token,
                            'redirect_to': redirect_to,
                            'redirect_code': str(redirect_code),
                        }
                        subrequest = make_subrequest(
                            request, root_path, 'redirect', qs)
                        content = dispatch(subrequest).text
                        response.location = None
                        response.text = content
                        response.status_int = 200

            toolbar.process_response(request, response)
            # Don't store the favicon.ico request
            # it's requested by the browser automatically
            if not "/favicon.ico" == request.path:
                toolbar.response = response
                request_history.put(request.pdtb_id, toolbar)

            if not show_on_exc_only and response.content_type in html_types:
                toolbar.inject(request, response)
            return response

        finally:
            # break circref
            del request.debug_toolbar

    return toolbar_tween

toolbar_html_template = """\
<link rel="stylesheet" type="text/css" href="%(css_path)s">

<div id="pDebug">
    <div %(button_style)s id="pDebugToolbarHandle">
        <a title="Show Toolbar" id="pShowToolBarButton"
           href="%(toolbar_url)s" target="pDebugToolbar">&#171; FIXME: Debug Toolbar</a>
    </div>
</div>
"""
