from pyramid.config import Configurator
from pyramid.settings import asbool
from pyramid.wsgi import wsgiapp2
from pyramid_debugtoolbar.utils import as_globals_list
from pyramid_debugtoolbar.utils import as_list
from pyramid_debugtoolbar.utils import as_cr_separated_list
from pyramid_debugtoolbar.utils import as_display_debug_or_false
from pyramid_debugtoolbar.utils import SETTINGS_PREFIX
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
from pyramid_debugtoolbar.utils import EXC_ROUTE_NAME
from pyramid_debugtoolbar.toolbar import (IRequestAuthorization,
                                          toolbar_tween_factory)  # API
toolbar_tween_factory = toolbar_tween_factory  # pyflakes

default_panel_names = (
    'pyramid_debugtoolbar.panels.headers.HeaderDebugPanel',
    'pyramid_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'pyramid_debugtoolbar.panels.renderings.RenderingsDebugPanel',
    'pyramid_debugtoolbar.panels.logger.LoggingPanel',
    'pyramid_debugtoolbar.panels.performance.PerformanceDebugPanel',
    'pyramid_debugtoolbar.panels.sqla.SQLADebugPanel',
    'pyramid_debugtoolbar.panels.traceback.TracebackPanel',
)

default_global_panel_names = (
    'pyramid_debugtoolbar.panels.versions.VersionDebugPanel',
    'pyramid_debugtoolbar.panels.settings.SettingsDebugPanel',
    'pyramid_debugtoolbar.panels.routes.RoutesDebugPanel',
    'pyramid_debugtoolbar.panels.tweens.TweensDebugPanel',
    'pyramid_debugtoolbar.panels.introspection.IntrospectionDebugPanel',
)

default_hosts = ('127.0.0.1', '::1')

default_settings = (
    ('enabled', asbool, 'true'),
    ('intercept_exc', as_display_debug_or_false, 'debug'),
    ('intercept_redirects', asbool, 'false'),
    ('panels', as_globals_list, default_panel_names),
    ('global_panels', as_globals_list, default_global_panel_names),
    ('hosts', as_list, default_hosts),
    ('exclude_prefixes', as_cr_separated_list, []),
)


def parse_settings(settings):
    parsed = {}

    def populate(name, convert, default):
        name = '%s%s' % (SETTINGS_PREFIX, name)
        value = convert(settings.get(name, default))
        parsed[name] = value
    for name, convert, default in default_settings:
        populate(name, convert, default)
    return parsed

def set_request_authorization_callback(request, callback):
    """
    Register IRequestAuthorization utility to authorize toolbar per request.
    """
    request.registry.registerUtility(callback, IRequestAuthorization)

def includeme(config):
    """ Activate the debug toolbar; usually called via
    ``config.include('pyramid_debugtoolbar')`` instead of being invoked
    directly. """
    introspection = getattr(config, 'introspection', True)
    # dont register any introspectables for Pyramid 1.3a9+
    config.introspection = False
    settings = parse_settings(config.registry.settings)
    config.registry.settings.update(settings)
    config.include('pyramid_mako')
    config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')
    config.add_tween('pyramid_debugtoolbar.toolbar_tween_factory')
    config.add_subscriber(
        'pyramid_debugtoolbar.toolbar.beforerender_subscriber',
        'pyramid.events.BeforeRender')
    config.add_directive('set_debugtoolbar_request_authorization',
                         set_request_authorization_callback)

    application = make_application(settings, config.registry)
    config.add_route('debugtoolbar', '/_debug_toolbar/*subpath')
    config.add_view(wsgiapp2(application), route_name='debugtoolbar')
    config.add_static_view('/_debug_toolbar/static', STATIC_PATH, static=True)
    config.introspection = introspection


def make_application(settings, parent_registry):
    """ WSGI application for rendering the debug toolbar."""
    config = Configurator(settings=settings)
    config.registry.parent_registry = parent_registry
    config.include('pyramid_mako')
    config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')
    config.add_static_view('static', STATIC_PATH)
    config.add_route(ROOT_ROUTE_NAME, '/', static=True)
    config.add_route('debugtoolbar.sse', '/sse')
    config.add_route('debugtoolbar.source', '/source')
    config.add_route('debugtoolbar.execute', '/execute')
    config.add_route('debugtoolbar.console', '/console')
    config.add_route(EXC_ROUTE_NAME, '/exception')
    config.add_route('debugtoolbar.sql_select', '/sqlalchemy/sql_select')
    config.add_route('debugtoolbar.sql_explain', '/sqlalchemy/sql_explain')
    config.add_route('debugtoolbar.request', '/{request_id}')
    config.add_route('debugtoolbar.main', '/')
    config.scan('pyramid_debugtoolbar.views')

    return config.make_wsgi_app()
