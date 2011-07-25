import sys

import pyramid.events
from pyramid.settings import asbool
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid.encode import url_quote
from pyramid.response import Response
from pyramid_debugtoolbar.utils import replace_insensitive, as_globals_list
from pyramid_debugtoolbar.tbtools import get_traceback

class DebugToolbar(object):
    def __init__(self, request, panel_classes):
        self.request = request
        self.panels = []
        activated = self.request.cookies.get('fldt_active', '').split(';')
        for panel_class in panel_classes:
            panel_inst = panel_class(request)
            if panel_inst.dom_id() in activated and not panel_inst.down:
                panel_inst.is_active = True
            self.panels.append(panel_inst)

    def render_toolbar(self, response):
        request = self.request
        static_path = request.static_url('pyramid_debugtoolbar:static/')
        vars = {'panels': self.panels, 'static_path':static_path}
        content = render('pyramid_debugtoolbar:templates/base.jinja2',
                         vars, request=request)
        content = content.encode(response.charset)
        return content

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
    html_types = ('text/html', 'application/xml+html')
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

        debug_toolbar = DebugToolbar(request, panel_classes)
        request.debug_toolbar = debug_toolbar
        
        _handler = handler

        for panel in debug_toolbar.panels:
            _handler = panel.wrap_handler(_handler)

        try:

            response = _handler(request)

            # Intercept http redirect codes and display an html page with a
            # link to the target.
            if intercept_redirects:
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

            for panel in debug_toolbar.panels:
                panel.process_response(request, response)

            # If the body is HTML, then we add the toolbar to the returned
            # html response.
            if response.content_type in html_types:
                response_html = response.body
                toolbar_html = debug_toolbar.render_toolbar(response)
                body = replace_insensitive(response_html, '</body>',
                                           toolbar_html + '</body>')
                response.app_iter = [body]

            return response

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
                return response

            raise

    return toolbar_handler

# default config settings
default_panel_names = (
    'pyramid_debugtoolbar.panels.versions.VersionDebugPanel',
    'pyramid_debugtoolbar.panels.settings.SettingsDebugPanel',
    'pyramid_debugtoolbar.panels.timer.TimerDebugPanel',
    'pyramid_debugtoolbar.panels.headers.HeaderDebugPanel',
    'pyramid_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'pyramid_debugtoolbar.panels.renderings.RenderingsDebugPanel',
#    'pyramid_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
    'pyramid_debugtoolbar.panels.logger.LoggingPanel',
    'pyramid_debugtoolbar.panels.profiler.ProfilerDebugPanel',
    'pyramid_debugtoolbar.panels.routes.RoutesDebugPanel',
    )

default_settings = (
    ('enabled', asbool, 'true'),
    ('intercept_exc', asbool, 'true'),
    ('intercept_redirects', asbool, 'true'),
    ('panels', as_globals_list, default_panel_names),
    )

def get_setting(settings, name, default=None, prefix='debugtoolbar.'):
    return settings.get('%s%s' % (prefix, name), default)

def parse_settings(settings, prefix='debugtoolbar.'):
    parsed = {}
    def populate(name, convert=None, default=None):
        if convert is None:
            convert = lambda x: x
        name = '%s%s' % (prefix, name)
        value = convert(settings.get(name, default))
        parsed[name] = value
    for name, convert, default in default_settings:
        populate(name, convert, default)
    return parsed

def includeme(config):
    settings = parse_settings(config.registry.settings)
    config.registry.settings.update(settings)
    config.include('pyramid_jinja2')
    j2_env = config.get_jinja2_environment()
    j2_env.filters['urlencode'] = url_quote
    config.add_static_view(
        '_debug_toolbar/static', 'pyramid_debugtoolbar:static')
    config.add_request_handler(toolbar_handler_factory, 'debug_toolbar')
    config.add_subscriber(beforerender_subscriber, pyramid.events.BeforeRender)
    config.add_route('debugtb.source', '/_debug_toolbar/source')
    config.add_route('debugtb.execute', '/_debug_toolbar/execute')
    config.add_route('debugtb.console', '/_debug_toolbar/console')
    config.scan('pyramid_debugtoolbar.views')
        
