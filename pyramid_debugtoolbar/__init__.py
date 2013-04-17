from pyramid.settings import asbool
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
    'pyramid_debugtoolbar.panels.versions.VersionDebugPanel',
    'pyramid_debugtoolbar.panels.settings.SettingsDebugPanel',
    'pyramid_debugtoolbar.panels.headers.HeaderDebugPanel',
    'pyramid_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'pyramid_debugtoolbar.panels.renderings.RenderingsDebugPanel',
    'pyramid_debugtoolbar.panels.logger.LoggingPanel',
    'pyramid_debugtoolbar.panels.performance.PerformanceDebugPanel',
    'pyramid_debugtoolbar.panels.routes.RoutesDebugPanel',
    'pyramid_debugtoolbar.panels.sqla.SQLADebugPanel',
    'pyramid_debugtoolbar.panels.tweens.TweensDebugPanel',
    'pyramid_debugtoolbar.panels.introspection.IntrospectionDebugPanel',
    )

default_hosts = ('127.0.0.1', '::1')

default_settings = (
    ('enabled', asbool, 'true'),
    ('intercept_exc', as_display_debug_or_false, 'debug'),
    ('intercept_redirects', asbool, 'false'),
    ('panels', as_globals_list, default_panel_names),
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

try:
    # Try to take advantage of MakoRendererFactoryHelper in Pyramid 1.3a8+.
    # If we can do this, the toolbar templates won't be effected by
    # normal mako settings.
    from pyramid.mako_templating import MakoRendererFactoryHelper
    renderer_factory = MakoRendererFactoryHelper('dbtmako.')
except ImportError:  # pragma: no cover
    # Buuut, if not (1.2 probably), just use the normal mako renderer factory
    from pyramid.mako_templating import renderer_factory


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
    config.add_renderer('.dbtmako', renderer_factory)
    settings = parse_settings(config.registry.settings)
    config.registry.settings.update(settings)
    if not 'mako.directories' in config.registry.settings:
        # XXX FBO 1.2.X only
        config.registry.settings['mako.directories'] = []
    config.add_static_view('_debug_toolbar/static', STATIC_PATH)
    config.add_tween('pyramid_debugtoolbar.toolbar_tween_factory')
    config.add_subscriber(
        'pyramid_debugtoolbar.toolbar.beforerender_subscriber',
        'pyramid.events.BeforeRender')
    config.add_route(ROOT_ROUTE_NAME, '/_debug_toolbar', static=True)
    config.add_route('debugtoolbar.source', '/_debug_toolbar/source')
    config.add_route('debugtoolbar.execute', '/_debug_toolbar/execute')
    config.add_route('debugtoolbar.console', '/_debug_toolbar/console')
    config.add_route(EXC_ROUTE_NAME, '/_debug_toolbar/exception')
    config.add_route('debugtoolbar.sql_select',
                     '/_debug_toolbar/sqlalchemy/sql_select')
    config.add_route('debugtoolbar.sql_explain',
                     '/_debug_toolbar/sqlalchemy/sql_explain')
    config.scan('pyramid_debugtoolbar.views')
    config.add_directive('set_debugtoolbar_request_authorization',
                         set_request_authorization_callback)

    config.introspection = introspection
