from collections import OrderedDict
from pyramid.config import Configurator
from pyramid.interfaces import Interface
from pyramid.settings import asbool
import pyramid.tweens
from pyramid_debugtoolbar.utils import (
    as_cr_separated_list,
    as_display_debug_or_false,
    as_int,
    as_list,
    find_request_history,
    ROOT_ROUTE_NAME,
    SETTINGS_PREFIX,
    STATIC_PATH,
)
from pyramid_debugtoolbar.toolbar import (
    IPanelMap,
    IRequestAuthorization,
    IToolbarWSGIApp,
    toolbar_tween_factory,
)

toolbar_tween_factory = toolbar_tween_factory  # API

bundled_includes = (
    'pyramid_debugtoolbar.panels.headers',
    'pyramid_debugtoolbar.panels.introspection',
    'pyramid_debugtoolbar.panels.logger',
    'pyramid_debugtoolbar.panels.performance',
    'pyramid_debugtoolbar.panels.renderings',
    'pyramid_debugtoolbar.panels.request_vars',
    'pyramid_debugtoolbar.panels.routes',
    'pyramid_debugtoolbar.panels.settings',
    'pyramid_debugtoolbar.panels.sqla',
    'pyramid_debugtoolbar.panels.traceback',
    'pyramid_debugtoolbar.panels.tweens',
    'pyramid_debugtoolbar.panels.versions',
)

default_hosts = ('127.0.0.1', '::1')

default_settings = [
    # name, convert, default
    ('enabled', asbool, 'true'),
    ('intercept_exc', as_display_debug_or_false, 'debug'),
    ('intercept_redirects', asbool, 'false'),
    ('panels', as_list, ()),
    ('extra_panels', as_list, ()),
    ('global_panels', as_list, ()),
    ('extra_global_panels', as_list, ()),
    ('hosts', as_list, default_hosts),
    ('exclude_prefixes', as_cr_separated_list, ()),
    ('active_panels', as_list, ()),
    ('includes', as_list, ()),
    ('button_style', None, ''),
    ('max_request_history', as_int, 100),
    ('max_visible_requests', as_int, 10),
]

# We need to transform these from debugtoolbar. to pyramid. in our
# make_application, but we want to allow people to set them in their
# configurations as debugtoolbar.
default_transform = [
    # name, convert, default
    ('debug_notfound', asbool, 'false'),
    ('debug_routematch', asbool, 'false'),
    ('prevent_http_cache', asbool, 'false'),
    ('reload_assets', asbool, 'false'),
    ('reload_resources', asbool, 'false'),
    ('reload_templates', asbool, 'false'),
]

class IParentActions(Interface):
    """ Marker interface for registered parent actions in the toolbar app."""

def parse_settings(settings):
    parsed = {}

    def populate(name, convert, default):
        name = '%s%s' % (SETTINGS_PREFIX, name)
        value = settings.get(name, default)
        if convert is not None:
            value = convert(value)
        parsed[name] = value

    # Extend the ones we are going to transform later ...
    cfg = list(default_settings)
    cfg.extend(default_transform)

    # Convert to the proper format ...
    for name, convert, default in cfg:
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

def set_request_authorization_callback(config, callback):
    """
    Register IRequestAuthorization utility to authorize toolbar per request.

    """
    config.registry.registerUtility(callback, IRequestAuthorization)

def update_parent_app(event):
    parent_registry = event.app.registry

    # inject the BeforeRender subscriber after the application is created
    # and all other subscribers are registered in hopes that this will be
    # the last subscriber in the chain and will be able to see the effects
    # of all previous subscribers on the event
    parent_config = Configurator(registry=parent_registry, introspection=False)

    parent_config.add_subscriber(
        'pyramid_debugtoolbar.toolbar.beforerender_subscriber',
        'pyramid.events.BeforeRender',
    )

    toolbar_registry = parent_registry.getUtility(IToolbarWSGIApp).registry
    actions = toolbar_registry.queryUtility(IParentActions, default=[])
    for action in actions:
        action(parent_config)

    parent_config.commit()

def includeme(config):
    """
    Activate the debug toolbar.

    Usually called via ``config.include('pyramid_debugtoolbar')`` instead
    of being invoked directly.

    """
    introspection = getattr(config, 'introspection', True)
    # dont register any introspectables for Pyramid 1.3a9+
    config.introspection = False

    # Parse the settings
    settings = parse_settings(config.registry.settings)

    # Update the current registry with the new settings
    config.registry.settings.update(settings)

    # Do the transform and update the settings dictionary
    settings.update(transform_settings(settings))

    # Create the toolbar application using the updated settings
    # Do this before adding the tween, etc to give debugtoolbar.includes
    # a chance to affect the settings beforehand incase autocommit is
    # enabled
    application = make_application(settings, config.registry)
    config.registry.registerUtility(application, IToolbarWSGIApp)

    config.add_tween(
        'pyramid_debugtoolbar.toolbar_tween_factory',
        over=[
            pyramid.tweens.EXCVIEW,
            'pyramid_tm.tm_tween_factory',
        ],
    )
    config.add_subscriber(update_parent_app,
                          'pyramid.events.ApplicationCreated')
    config.add_directive('set_debugtoolbar_request_authorization',
                         set_request_authorization_callback)

    # register routes and views that can be used within the tween
    config.add_route('debugtoolbar', '/_debug_toolbar/*subpath', static=True)
    config.add_static_view('/_debug_toolbar/static', STATIC_PATH, static=True)

    config.introspection = introspection

def make_application(settings, parent_registry):
    """ WSGI application for rendering the debug toolbar."""
    config = Configurator(settings=settings)
    config.registry.parent_registry = parent_registry
    config.registry.registerUtility(OrderedDict(), IPanelMap)
    config.add_directive('add_debugtoolbar_panel', add_debugtoolbar_panel)
    config.add_directive('inject_parent_action', inject_parent_action)

    config.include('pyramid_mako')
    config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')

    config.add_route_predicate('history_request', HistoryRequestRoutePredicate)

    config.add_static_view('static', STATIC_PATH)
    config.add_route(ROOT_ROUTE_NAME, '/', static=True)
    config.add_route('debugtoolbar.sse', '/sse')
    config.add_route('debugtoolbar.redirect', '/redirect')
    config.add_route('debugtoolbar.request', '/{request_id}',
                     history_request=True)
    config.add_route('debugtoolbar.main', '/')
    config.scan('.views')

    for include in bundled_includes:
        config.include(include)

    # commit the toolbar config and include any user-defined includes
    config.commit()

    includes = settings.get(SETTINGS_PREFIX + 'includes', ())
    for include in includes:
        config.include(include)

    return config.make_wsgi_app()

class HistoryRequestRoutePredicate(object):
    def __init__(self, val, config):
        assert isinstance(val, bool), 'must be a bool'
        self.val = val

    def text(self):
        return 'tbhistory = %s' % self.val

    phash = text

    def __call__(self, info, request):
        match = info['match']
        history = find_request_history(request)
        is_historical = bool(history.get(match.get('request_id')))
        return not (is_historical ^ self.val)

def add_debugtoolbar_panel(config, panel_class, is_global=False):
    """
    Register a new panel into the debugtoolbar.

    This is a Pyramid config directive that is accessible as
    ``config.add_debugtoolbar_panel`` within the debugtoolbar application.
    It should be used from ``includeme`` functions via the
    ``debugtoolbar.includes`` setting.

    The ``panel_class`` should be a subclass of
    :class:`pyramid_debugtoolbar.panels.DebugPanel`.

    If ``is_global`` is ``True`` then the panel will be added to the global
    panel list which includes application-wide panels that do not depend
    on per-request data to operate.

    """
    panel_class = config.maybe_dotted(panel_class)
    name = panel_class.name

    panel_map = config.registry.getUtility(IPanelMap)
    panel_map[(name, is_global)] = panel_class

def inject_parent_action(config, action):
    """
    Inject an action into the parent application.

    This is a Pyramid config directive that is accessible as
    ``config.inject_parent_action`` within the debugtoolbar application.
    It should be used from ``includeme`` functions via the
    ``debugtoolbar.includes`` setting.

    The ``action`` should be a callable that accepts the parent app's
    ``config`` object. It will be executed after the parent app is created
    to ensure that configuration is set prior to the actions being executed.

    """
    actions = config.registry.queryUtility(IParentActions)
    if actions is None:
        actions = []
        config.registry.registerUtility(actions, IParentActions)
    actions.append(action)
