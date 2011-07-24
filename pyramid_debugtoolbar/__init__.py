import sys

import pyramid.events
from pyramid.util import DottedNameResolver
from pyramid.settings import asbool
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid.encode import url_quote
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound

from pyramid_debugtoolbar.tbtools import get_traceback, render_console_html
from pyramid_debugtoolbar.console import Console

resolver = DottedNameResolver(None)

def replace_insensitive(string, target, replacement):
    """Similar to string.replace() but is case insensitive
    Code borrowed from: http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else: # no results so return the original string
        return string

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
    attrs = request.__dict__
    if attrs.get('debug_toolbar', None) is not None:
        for panel in request.debug_toolbar.panels:
            panel.process_beforerender(event)

def get_setting(settings, name, default=None, prefix='debugtoolbar.'):
    return settings.get('%s%s' % (prefix, name), default)

def toolbar_handler_factory(handler, registry):
    settings = registry.settings

    if not get_setting(settings, 'enabled'):
        return handler

    _redirect_codes = (301, 302, 303, 304)
    _htmltypes = ('text/html', 'application/xml+html')
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

        debug_toolbar = request.debug_toolbar = DebugToolbar(request,
                                                             panel_classes)

        _handler = handler

        for panel in debug_toolbar.panels:
            _handler = panel.wrap_handler(_handler)

        try:
            response = _handler(request)
            # Intercept http redirect codes and display an html page with a
            # link to the target.
            if intercept_redirects:
                if response.status_int in _redirect_codes:
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
            if response.content_type in _htmltypes:
                response_html = response.body
                toolbar_html = debug_toolbar.render_toolbar(response)
                response.app_iter = [
                    replace_insensitive(
                        response_html,
                        '</body>',
                        toolbar_html + '</body>')]

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
                response = Response(body)
                response.status_int = 500
                return response
            raise

    return toolbar_handler

class _ConsoleFrame(object):
    """Helper class so that we can reuse the frame console code for the
    standalone console.
    """

    def __init__(self, namespace):
        self.console = Console(namespace)
        self.id = 0

class ExcDebugView(object):
    def __init__(self, request):
        self.request = request
        frm = self.request.params.get('frm')
        if frm is not None:
            frm = int(frm)
        self.frame = frm
        cmd = self.request.params.get('cmd')
        self.cmd = cmd

    def source(self):
        exc_history = self.request.exc_history
        frame = exc_history.frames.get(self.frame)
        return Response(frame.render_source(), content_type='text/html')

    def execute(self):
        exc_history = self.request.exc_history
        if self.frame is not None and exc_history:
            frame = exc_history.frames.get(self.frame)
            if self.cmd is not None and frame is not None:
                return Response(frame.console.eval(self.cmd),
                                content_type='text/html')
        return HTTPNotFound()
        
    def console(self):
        exc_history = self.request.exc_history
        if exc_history:
            if 0 not in self.frames:
                exc_history.frames[0] = _ConsoleFrame({})
            return Response(render_console_html(), content_type='text/html')
        return HTTPNotFound()

def as_globals_list(value):
    L = []
    if isinstance(value, basestring):
        value = filter(None, [x.strip() for x in value.splitlines()])
    for dottedname in value:
        obj = resolver.resolve(dottedname)
        L.append(obj)
    return L

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
    if hasattr(config, 'get_jinja2_environment'):
        # pyramid_jinja2 after 1.0
        j2_env = config.get_jinja2_environment()
    else:
        # pyramid_jinja2 1.0 and before
        from pyramid_jinja2 import IJinja2Environment
        j2_env = config.registry.getUtility(IJinja2Environment)
    j2_env.filters['urlencode'] = url_quote
    config.add_static_view('_debug_toolbar/static',
                           'pyramid_debugtoolbar:static')
    config.add_request_handler(toolbar_handler_factory, 'debug_toolbar')
    config.add_subscriber(beforerender_subscriber,pyramid.events.BeforeRender)
    config.add_route('debugtb.source', '/_debug_toolbar/source')
    config.add_route('debugtb.execute', '/_debug_toolbar/execute')
    config.add_route('debugtb.console', '/_debug_toolbar/console')
    config.add_view(ExcDebugView, route_name='debugtb.source', attr='source')
    config.add_view(ExcDebugView, route_name='debugtb.execute',attr='execute')
    config.add_view(ExcDebugView, route_name='debugtb.console',attr='console')
        
