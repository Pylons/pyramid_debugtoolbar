from pyramid_debugtoolbar.toolbar import DebugToolbar

from pyramid.util import DottedNameResolver
from pyramid.exceptions import ConfigurationError
from pyramid.settings import asbool
from pyramid.renderers import render
import pyramid.events

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

class DebugToolbarSubscriber(object):
    _redirect_codes = [301, 302, 303, 304]

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
        if request is not None and request.debug_toolbar:
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
                redirect_code = response.status_code
                if redirect_to:
                    content = render('redirect.jinja2', {
                        'redirect_to': redirect_to,
                        'redirect_code': redirect_code
                    })
                    response.content_length = len(content)
                    response.location = None
                    response.app_iter = [content]
                    response.status_code = 200

        # If the http response code is 200 then we process to add the
        # toolbar to the returned html response.
        if response.status_int == 200:
            for panel in request.debug_toolbar.panels:
                panel.process_response(request, response)

            response_html = response.ubody
            toolbar_html = request.debug_toolbar.render_toolbar()
            response.app_iter = [
                replace_insensitive(
                    response_html,
                    '</body>',
                    toolbar_html + '</body>')]
        return response

# default config settings
default_settings = {
    'debugtoolbar.intercept_redirects': True,
    'debugtoolbar.panels': (
        'pyramid_debugtoolbar.panels.versions.VersionDebugPanel',
        'pyramid_debugtoolbar.panels.timer.TimerDebugPanel',
        'pyramid_debugtoolbar.panels.headers.HeaderDebugPanel',
        'pyramid_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'pyramid_debugtoolbar.panels.template.TemplateDebugPanel',
#        'pyramid_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
        'pyramid_debugtoolbar.panels.logger.LoggingPanel',
        'pyramid_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        
        )
    }

def includeme(config):
    settings = default_settings.copy()
    settings.update(config.registry.settings)
    from pyramid_jinja2 import IJinja2Environment
    from pyramid.encode import url_quote
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('pyramid_debugtoolbar:templates/')
    # XXX should be a better way to do this, IJinja2Environment nor
    # url_quote are APIs AFAIK
    j2_env = config.registry.getUtility(IJinja2Environment)
    j2_env.filters['urlencode'] = url_quote
    config.add_static_view('_debug_toolbar/static',
                           'pyramid_debugtoolbar:static')
    config.add_route('pyramid.debugtoolbar', '_debugtoolbar/{id}')
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
        
