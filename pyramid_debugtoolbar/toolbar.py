import sys
import os

from pyramid.exceptions import URLDecodeError
from pyramid.httpexceptions import WSGIHTTPException
from pyramid.interfaces import Interface
from pyramid.renderers import render
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
from pyramid_debugtoolbar.utils import replace_insensitive
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ToolbarStorage

html_types = ('text/html', 'application/xhtml+xml')


class IRequestAuthorization(Interface):

    def __call__(request):
        """
        Toolbar per-request authorization.
        Should return bool values whether toolbar is permitted to be shown
        within provided request.
        """


class DebugToolbar(object):

    def __init__(self, request, panel_classes, global_panel_classes):
        self.panels = []
        self.global_panels = []
        self.request = request
        self.status_int = 200

        # Panels can be be activated (more features) (e.g. Performace panel)
        pdtb_active = url_unquote(request.cookies.get('pdtb_active', ''))

        activated = pdtb_active.split(';')
        # XXX
        for panel_class in panel_classes:
            panel_inst = panel_class(request)
            if panel_inst.dom_id in activated and panel_inst.has_content:
                panel_inst.is_active = True
            self.panels.append(panel_inst)
        for panel_class in global_panel_classes:
            panel_inst = panel_class(request)
            if panel_inst.dom_id in activated and panel_inst.has_content:
                panel_inst.is_active = True
            self.global_panels.append(panel_inst)

    @property
    def json(self):
        return {'method': self.request.method,
                'path': self.request.path,
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
        toolbar_url = debug_toolbar_url(request, request.id)
        button_style = get_setting(request.registry.settings,
                'button_style', '')
        css_path = request.static_url(STATIC_PATH + 'css/toolbar_button.css')
        toolbar_html = toolbar_html_template % {
            'button_style': button_style,
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


def toolbar_tween_factory(handler, registry, _logger=None):
    """ Pyramid tween factory for the debug toolbar """
    # _logger passed for testing purposes only
    if _logger is None:
        _logger = logger
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

    if intercept_exc:
        registry.exc_history = exc_history = ExceptionHistory()
        exc_history.eval_exc = intercept_exc == 'debug'

    def toolbar_tween(request):
        request.exc_history = exc_history
        request.history = request_history
        root_url = request.route_path('debugtoolbar', subpath='')
        exclude = [root_url] + exclude_prefixes
        last_proxy_addr = None

        try:
            p = request.path
        except UnicodeDecodeError as e:
            raise URLDecodeError(e.encoding, e.object, e.start, e.end, e.reason)
        starts_with_excluded = list(filter(None, map(p.startswith, exclude)))

        if request.remote_addr:
            last_proxy_addr = last_proxy(request.remote_addr)

        if last_proxy_addr is None \
            or starts_with_excluded \
            or not addr_in(last_proxy_addr, hosts) \
            or auth_check and not auth_check(request):
                return handler(request)

        toolbar = DebugToolbar(request, panel_classes, global_panel_classes)
        request.debug_toolbar = toolbar

        _handler = handler

        # XXX
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

                qs = {'token': registry.pdtb_token, 'tb': str(tb.id)}
                msg = 'Exception at %s\ntraceback url: %s'
                exc_url = debug_toolbar_url(request, 'exception', _query=qs)
                exc_msg = msg % (request.url, exc_url)
                _logger.exception(exc_msg)

                subenviron = request.environ.copy()
                del subenviron['PATH_INFO']
                del subenviron['QUERY_STRING']
                subrequest = type(request).blank(exc_url, subenviron)
                subrequest.script_name = request.script_name
                subrequest.path_info = \
                    subrequest.path_info[len(request.script_name):]
                response = request.invoke_subrequest(subrequest)

                toolbar.process_response(request, response)

                request.id = hexlify(id(request))
                toolbar.response = response
                toolbar.status_int = response.status_int

                request_history.put(request.id, toolbar)
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
                        content = render(
                            'pyramid_debugtoolbar:templates/redirect.dbtmako',
                            {
                                'redirect_to': redirect_to,
                                'redirect_code': redirect_code,
                            },
                            request=request)
                        content = content.encode(response.charset)
                        response.content_length = len(content)
                        response.location = None
                        response.app_iter = [content]
                        response.status_int = 200

            toolbar.process_response(request, response)
            request.id = hexlify(id(request))
            # Don't store the favicon.ico request
            # it's requested by the browser automatically
            if not "/favicon.ico" == request.path:
                toolbar.response = response
                request_history.put(request.id, toolbar)

            if not show_on_exc_only and response.content_type in html_types:
                toolbar.inject(request, response)
            return response

        finally:
            # break circref
            del request.debug_toolbar

    return toolbar_tween

toolbar_html_template = """\
<script type="text/javascript">
    var fileref=document.createElement("link")
    fileref.setAttribute("rel", "stylesheet")
    fileref.setAttribute("type", "text/css")
    fileref.setAttribute("href", "%(css_path)s")
    document.getElementsByTagName("head")[0].appendChild(fileref)
</script>

<div id="pDebug">
    <div style="display: block; %(button_style)s" id="pDebugToolbarHandle">
        <a title="Show Toolbar" id="pShowToolBarButton"
           href="%(toolbar_url)s" target="pDebugToolbar">&#171; FIXME: Debug Toolbar</a>
    </div>
</div>
"""
