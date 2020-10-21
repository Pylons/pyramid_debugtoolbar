import os
from pyramid.exceptions import URLDecodeError
from pyramid.httpexceptions import WSGIHTTPException
from pyramid.interfaces import Interface
from pyramid.threadlocal import get_current_request
import sys
import warnings

from pyramid_debugtoolbar.compat import bytes_, url_unquote
from pyramid_debugtoolbar.tbtools import get_traceback
from pyramid_debugtoolbar.utils import (
    STATIC_PATH,
    ToolbarStorage,
    addr_in,
    debug_toolbar_url,
    get_exc_name,
    get_setting,
    hexlify,
    logger,
    make_subrequest,
    replace_insensitive,
    resolve_panel_classes,
)

html_types = ('text/html', 'application/xhtml+xml')


class IToolbarWSGIApp(Interface):
    """ Marker interface for the toolbar WSGI application."""

    def __call__(environ, start_response):
        pass


class IPanelMap(Interface):
    """ Marker interface for the set of known panels."""


class IRequestAuthorization(Interface):
    def __call__(request):
        """
        Toolbar per-request authorization.

        Should return bool values whether toolbar is permitted to monitor
        the provided request.

        """


class DebugToolbar(object):
    def __init__(
        self,
        request,
        panel_classes,
        global_panel_classes,
        default_active_panels,
    ):
        self.panels = []
        self.global_panels = []
        self.request = request
        self.status_int = 200
        self.default_active_panels = default_active_panels
        self.visible = False

        # Panels can be be activated (more features) (e.g. Performace panel)
        pdtb_active = url_unquote(request.cookies.get('pdtb_active', ''))

        activated = pdtb_active.split(',')
        # If the panel is activated in the settings, we want to enable it
        activated.extend(default_active_panels)

        def configure_panel(panel_inst):
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
        return {
            'host': self.request.host,
            'method': self.request.method,
            'path': self.request.path,
            'scheme': self.request.scheme,
            'status_code': self.status_int,
        }

    def process_response(self, request, response):
        if isinstance(response, WSGIHTTPException):
            # the body of a WSGIHTTPException needs to be "prepared"
            response.prepare(request.environ)

        for panel in self.panels:
            panel.process_response(response)
        for panel in self.global_panels:
            panel.process_response(response)

        self.response = response
        self.visible = True

    def inject(self, request, response):
        """
        Inject the debug toolbar iframe into an HTML response.
        """
        # called in host app
        response_html = response.body
        toolbar_url = debug_toolbar_url(request, request.pdtb_id)
        button_style = get_setting(
            request.registry.settings, 'button_style', ''
        )
        css_path = request.static_url(
            STATIC_PATH + 'toolbar/toolbar_button.css'
        )
        toolbar_html = toolbar_html_template % {
            'button_style': (
                'style="{0}"'.format(button_style) if button_style else ""
            ),
            'css_path': css_path,
            'toolbar_url': toolbar_url,
        }
        toolbar_html = toolbar_html.encode(response.charset or 'utf-8')
        response.body = replace_insensitive(
            response_html, bytes_('</body>'), toolbar_html + bytes_('</body>')
        )


def process_traceback(info):
    return get_traceback(
        info=info,
        skip=1,
        show_hidden_frames=False,
        ignore_system_exceptions=True,
    )


def beforerender_subscriber(event):
    request = event.get('request')
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

    toolbar_app = registry.getUtility(IToolbarWSGIApp)
    toolbar_registry = toolbar_app.registry

    max_request_history = sget('max_request_history')
    request_history = ToolbarStorage(max_request_history)
    registry.pdtb_history = request_history

    panel_map = toolbar_registry.queryUtility(IPanelMap, default={})
    resolve_panels = lambda a, b: resolve_panel_classes(a, b, panel_map)

    panel_classes = list(sget('panels', []))
    if not panel_classes:
        # if no panels are defined then use all available panels
        panel_classes = [p for p, g in panel_map if not g]
    panel_classes.extend(sget('extra_panels', []))
    panel_classes = resolve_panels(panel_classes, False)
    global_panel_classes = list(sget('global_panels', []))
    if not global_panel_classes:
        # if no panels are defined then use all available global panels
        global_panel_classes = [p for p, g in panel_map if g]
    global_panel_classes.extend(sget('extra_global_panels', []))
    global_panel_classes = resolve_panels(global_panel_classes, True)

    redirect_codes = (301, 302, 303, 304)
    intercept_exc = sget('intercept_exc')
    intercept_redirects = sget('intercept_redirects')
    show_on_exc_only = sget('show_on_exc_only')
    hosts = sget('hosts')
    auth_check = registry.queryUtility(IRequestAuthorization)
    exclude_prefixes = sget('exclude_prefixes', [])
    registry.pdtb_token = hexlify(os.urandom(5))
    registry.pdtb_eval_exc = intercept_exc

    default_active_panels = sget('active_panels', [])

    dispatch = lambda request: _dispatch(toolbar_app, request)

    def toolbar_tween(request):
        try:
            p = request.path_info
        except UnicodeDecodeError as e:
            raise URLDecodeError(
                e.encoding, e.object, e.start, e.end, e.reason
            )

        client_addr = None
        if request.remote_addr and ',' not in request.remote_addr:
            client_addr = request.remote_addr.strip()
        elif request.remote_addr is not None:
            warnings.warn(
                'pyramid_debugtoolbar has detected a broken proxy '
                'that modified REMOTE_ADDR with an invalid value and is '
                'cowardly going to refuse to serve the toolbar. If you see '
                'this message, and you think it is incorrect, please open an '
                'issue with more details including the proxy you\'re using and '
                'the format of the REMOTE_ADDR at '
                'https://github.com/Pylons/pyramid_debugtoolbar/issues/'
            )

        if (
            client_addr is None
            or any(p.startswith(e) for e in exclude_prefixes)
            or not addr_in(client_addr, hosts)
            or auth_check
            and not auth_check(request)
        ):
            return handler(request)

        if request.environ.get('wsgi.multiprocess', False):
            warnings.warn(
                'pyramid_debugtoolbar has detected that the application is '
                'being served by a forking / multiprocess web server. The '
                'toolbar relies on global state to work and is not compatible '
                'with this environment. The toolbar will be disabled.'
            )
            return handler(request)

        root_path = debug_toolbar_url(request, '', _app_url='')
        if p.startswith(root_path):
            # we know root_path will always have a trailing slash
            # but script_name doesn't want it
            try:
                old_script_name = request.script_name
                old_path_info = request.path_info
                request.script_name += root_path[:-1]
                request.path_info = request.path_info[len(root_path) - 1 :]
                return dispatch(request)
            finally:
                request.script_name = old_script_name
                request.path_info = old_path_info

        request.pdtb_id = hexlify(id(request))
        toolbar = DebugToolbar(
            request, panel_classes, global_panel_classes, default_active_panels
        )
        request.debug_toolbar = toolbar
        request_history.put(request.pdtb_id, toolbar)

        _handler = handler
        for panel in toolbar.panels:
            _handler = panel.wrap_handler(_handler)

        try:
            response = _handler(request)
            toolbar.status_int = response.status_int

            if request.exc_info and intercept_exc:
                toolbar.traceback = process_traceback(request.exc_info)

                msg = 'Squashed %s at %s\ntraceback url: %s'
                exc_name = get_exc_name(request.exc_info[1])
                subrequest = make_subrequest(
                    request, root_path, request.pdtb_id + '/exception'
                )
                exc_msg = msg % (exc_name, request.url, subrequest.url)
                _logger.info(exc_msg)

        except Exception as exc:
            exc_name = get_exc_name(exc)
            if intercept_exc:
                toolbar.traceback = process_traceback(sys.exc_info())

                msg = 'Uncaught %s at %s\ntraceback url: %s'
                subrequest = make_subrequest(
                    request, root_path, request.pdtb_id + '/exception'
                )
                exc_msg = msg % (exc_name, request.url, subrequest.url)
                _logger.exception(exc_msg)

                response = dispatch(subrequest)
                toolbar.status_int = response.status_int

                # The original request must be processed so that the panel
                # data exists if the request is later examined in the full
                # toolbar view.
                toolbar.process_response(request, response)

                # Inject the button to activate the full toolbar view.
                toolbar.inject(request, response)

                # we want later tweens to understand that the response
                # is from handling an exception, so we must add
                # request.exc_info and request.exception as an indicator
                # see Pylons/pyramid_debugtoolbar#341
                request.exception = exc
                request.exc_info = sys.exc_info()
                return response

            else:
                msg = 'Uncaught %s at %s'
                _logger.exception(msg % (exc_name, request.url))
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
                            'redirect_to': redirect_to,
                            'redirect_code': str(redirect_code),
                        }
                        subrequest = make_subrequest(
                            request, root_path, 'redirect', qs
                        )
                        content = dispatch(subrequest).text
                        response.location = None
                        response.text = content
                        response.status_int = 200

            toolbar.process_response(request, response)

            if not show_on_exc_only and response.content_type in html_types:
                toolbar.inject(request, response)
            return response

        finally:
            # break circref
            del request.debug_toolbar

    return toolbar_tween


toolbar_html_template = """\
<link rel="stylesheet" type="text/css" href="%(css_path)s" />

<div id="pDebug">
    <div %(button_style)s id="pDebugToolbarHandle">
        <a title="Show Toolbar" id="pShowToolBarButton"
           href="%(toolbar_url)s" target="pDebugToolbar">&#171;</a>
    </div>
</div>
"""
