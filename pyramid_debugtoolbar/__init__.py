from pyramid.config import Configurator
try:
    from pyramid.security import NO_PERMISSION_REQUIRED
except ImportError: # pragma: no cover
    from pyramid.interfaces import NO_PERMISSION_REQUIRED
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

default_settings = [
    ('enabled', asbool, 'true'),
    ('intercept_exc', as_display_debug_or_false, 'debug'),
    ('intercept_redirects', asbool, 'false'),
    ('panels', as_globals_list, default_panel_names),
    ('extra_panels', as_globals_list, ()),
    ('global_panels', as_globals_list, default_global_panel_names),
    ('extra_global_panels', as_globals_list, ()),
    ('hosts', as_list, default_hosts),
    ('exclude_prefixes', as_cr_separated_list, []),
]

# We need to transform these from debugtoolbar. to pyramid. in our
# make_application, but we want to allow people to set them in their
# configurations as debugtoolbar.
default_transform = [
    ('debug_notfound', asbool, 'false'),
    ('debug_routematch', asbool, 'false'),
    ('reload_templates', asbool, 'false'),
    ('reload_resources', asbool, 'false'),
    ('reload_assets', asbool, 'false'),
    ('prevent_http_cache', asbool, 'false'),
]


def parse_settings(settings):
    parsed = {}

    def populate(name, convert, default):
        name = '%s%s' % (SETTINGS_PREFIX, name)
        value = convert(settings.get(name, default))
        parsed[name] = value

    # Extend the ones we are going to transform later ...
    default_settings.extend(default_transform)
    for name, convert, default in default_settings:
        populate(name, convert, default)
    return parsed

def transform_settings(settings):
    parsed = {}

    def populate(name):
        oname = '%s%s' % (SETTINGS_PREFIX, name)
        nname = 'pyramid.%s' % name
        value = settings.get(oname, False)
        parsed[nname] = value

    for name, _, _ in default_transform:
        populate(name)

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

    # Parse the settings
    settings = parse_settings(config.registry.settings)

    # Update the current registry with the new settings
    config.registry.settings.update(settings)

    config.include('pyramid_mako')
    config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')
    config.add_tween('pyramid_debugtoolbar.toolbar_tween_factory')
    config.add_subscriber(
        'pyramid_debugtoolbar.toolbar.beforerender_subscriber',
        'pyramid.events.BeforeRender')
    config.add_directive('set_debugtoolbar_request_authorization',
                         set_request_authorization_callback)

    # Do the transform and update the settings dictionary
    settings.update(transform_settings(settings))

    # Create the new application using the updated settings
    application = make_application(settings, config.registry)
    config.add_route('debugtoolbar', '/_debug_toolbar/*subpath')
    config.add_view(wsgiapp2(application), route_name='debugtoolbar',
                    permission=NO_PERMISSION_REQUIRED)
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
