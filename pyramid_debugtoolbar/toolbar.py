import binascii
import sys
import os

from pyramid.interfaces import Interface
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid_debugtoolbar.tbtools import get_traceback
from pyramid_debugtoolbar.compat import url_unquote
from pyramid_debugtoolbar.compat import bytes_
from pyramid_debugtoolbar.compat import text_
from pyramid_debugtoolbar.utils import get_setting
from pyramid_debugtoolbar.utils import replace_insensitive
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import logger
from pyramid_debugtoolbar.utils import addr_in
from pyramid_debugtoolbar.utils import last_proxy
from pyramid_debugtoolbar.utils import debug_toolbar_url
from pyramid.httpexceptions import WSGIHTTPException
from repoze.lru import LRUCache

html_types = ('text/html', 'application/xml+html')


class IRequestAuthorization(Interface):

    def __call__(request):
        """
        Toolbar per-request authorization.
        Should return bool values whether toolbar is permitted to be shown
        within provided request.
        """


class DebugToolbar(object):

    def __init__(self, request, panel_classes):
        # constructed in host app
        self.panels = []
        pdtb_active = url_unquote(request.cookies.get('pdtb_active', ''))
        activated = pdtb_active.split(';')
        for panel_class in panel_classes:
            panel_inst = panel_class(request)
            if panel_inst.dom_id() in activated and panel_inst.has_content:
                panel_inst.is_active = True
            self.panels.append(panel_inst)

    def process_response(self, request, response):
        # called in host app
        if isinstance(response, WSGIHTTPException):
            # the body of a WSGIHTTPException needs to be "prepared"
            response.prepare(request.environ)

        for panel in self.panels:
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
        css_path = request.static_url(STATIC_PATH + 'css/toolbar.css')
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

    request_history = LRUCache(100)
    registry.request_history = request_history

    redirect_codes = (301, 302, 303, 304)
    panel_classes = get_setting(settings, 'panels', [])
    intercept_exc = get_setting(settings, 'intercept_exc')
    intercept_redirects = get_setting(settings, 'intercept_redirects')
    hosts = get_setting(settings, 'hosts')
    auth_check = registry.queryUtility(IRequestAuthorization)
    exclude_prefixes = get_setting(settings, 'exclude_prefixes', [])
    registry.exc_history = exc_history = None

    if intercept_exc:
        registry.exc_history = exc_history = ExceptionHistory()
        exc_history.eval_exc = intercept_exc == 'debug'

    def toolbar_tween(request):
        request.exc_history = exc_history
        request.history = request_history
        root_url = request.route_path('debugtoolbar', subpath='')
        exclude = [root_url] + exclude_prefixes
        last_proxy_addr = None
        starts_with_excluded = list(filter(None, map(request.path.startswith,
                                                     exclude)))

        if request.remote_addr:
            last_proxy_addr = last_proxy(request.remote_addr)

        if last_proxy_addr is None \
            or starts_with_excluded \
            or not addr_in(last_proxy_addr, hosts) \
            or auth_check and not auth_check(request):
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

                qs = {'token': exc_history.token, 'tb': str(tb.id)}
                msg = 'Exception at %s\ntraceback url: %s'
                exc_url = debug_toolbar_url(request, 'exception', _query=qs)
                exc_msg = msg % (request.url, exc_url)
                logger.exception(exc_msg)

                subenviron = request.environ.copy()
                del subenviron['PATH_INFO']
                del subenviron['QUERY_STRING']
                subrequest = type(request).blank(exc_url, subenviron)
                response = request.invoke_subrequest(subrequest)

                toolbar.process_response(request, response)
                request.id = text_(binascii.hexlify(str(id(request))))
                request_history.put(request.id, toolbar)
                toolbar.inject(request, response)
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

            toolbar.process_response(request, response)
            request.id = text_(binascii.hexlify(str(id(request))))
            request_history.put(request.id, toolbar)

            if response.content_type in html_types:
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
           href="%(toolbar_url)s" target="pDebugToolbar">&laquo; FIXME: Debug Toolbar</a>
    </div>
</div>
"""
