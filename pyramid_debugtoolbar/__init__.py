from pyramid.util import DottedNameResolver
from pyramid.exceptions import ConfigurationError
from pyramid.settings import asbool
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
import pyramid.events
from pyramid.encode import url_quote

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
    def __init__(self, request):
        self.request = request
        self.panels = []
        panel_classes = self.request.registry.settings['debugtoolbar.classes']
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

class DebugToolbarSubscriber(object):
    _redirect_codes = (301, 302, 303, 304)
    _htmltypes = ('text/html', 'application/xml+html')

    def __init__(self, settings):
        secret_key = settings.get('debugtoolbar.secret_key')
        if secret_key is None:
            raise ConfigurationError(
                "The Pyramid debug toolbar requires the "
                "'debugtoolbar.secret_key' config setting")
            
        self.secret_key = secret_key
        self.intercept_redirects = asbool(
            settings.get('debugtoolbar.intercept_redirects'))

    def process_request(self, event):
        request = event.request
        if request.path.startswith('/_debug_toolbar/'):
            request.debug_toolbar = None
            return False

        request.debug_toolbar = DebugToolbar(request)

        for panel in request.debug_toolbar.panels:
            panel.process_request(request)

        request.add_response_callback(self._process_response)

    def process_beforerender(self, event):
        request = event['request']
        if request is None:
            request = get_current_request()
        if getattr(request, 'debug_toolbar', None) is not None:
            for panel in request.debug_toolbar.panels:
                panel.process_beforerender(event)

    def _process_response(self, request, response):
        if request.debug_toolbar is None:
            return response

        # Intercept http redirect codes and display an html page with a
        # link to the target.
        if self.intercept_redirects:
            if response.status_int in self._redirect_codes:
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

        # If the http response code is 200 then we process to add the
        # toolbar to the returned html response.
        if (response.status_int == 200 and
            response.content_type in self._htmltypes):
            for panel in request.debug_toolbar.panels:
                panel.process_response(request, response)

            response_html = response.body
            toolbar_html = request.debug_toolbar.render_toolbar(response)
            response.app_iter = [
                replace_insensitive(
                    response_html,
                    '</body>',
                    toolbar_html + '</body>')]
        del request.debug_toolbar
        return response

# default config settings
default_settings = {
    'debugtoolbar.intercept_redirects': True,
    'debugtoolbar.panels': (
        'pyramid_debugtoolbar.panels.versions.VersionDebugPanel',
        'pyramid_debugtoolbar.panels.settings.SettingsDebugPanel',
        'pyramid_debugtoolbar.panels.timer.TimerDebugPanel',
        'pyramid_debugtoolbar.panels.headers.HeaderDebugPanel',
        'pyramid_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'pyramid_debugtoolbar.panels.renderings.RenderingsDebugPanel',
#        'pyramid_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
        'pyramid_debugtoolbar.panels.logger.LoggingPanel',
        'pyramid_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        
        )
    }

def includeme(config):
    panels = config.registry.settings.get('debugtoolbar.panels')
    if isinstance(panels, basestring):
        panels = filter(None, [x.strip() for x in panels.splitlines()])
    settings = default_settings.copy()
    settings.update(config.registry.settings)
    if panels is not None:
        settings['debugtoolbar.panels'] = panels
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
    classes = settings['debugtoolbar.classes'] = []
    for dottedname in settings['debugtoolbar.panels']:
        panel_class = resolver.resolve(dottedname)
        classes.append(panel_class)
    config.registry.settings.update(settings)
    subscriber = DebugToolbarSubscriber(settings)
    config.add_subscriber(subscriber.process_request,
                          pyramid.events.NewRequest)
    config.add_subscriber(subscriber.process_beforerender,
                          pyramid.events.BeforeRender)
        
