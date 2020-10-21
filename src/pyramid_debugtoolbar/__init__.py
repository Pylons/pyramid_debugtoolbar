from pyramid.config import Configurator
from pyramid.settings import asbool
import pyramid.tweens

from pyramid_debugtoolbar.toolbar import (
    IRequestAuthorization,
    IToolbarWSGIApp,
    toolbar_tween_factory,
)
from pyramid_debugtoolbar.toolbar_app import IParentActions, make_toolbar_app
from pyramid_debugtoolbar.utils import (
    SETTINGS_PREFIX,
    STATIC_PATH,
    as_cr_separated_list,
    as_display_debug_or_false,
    as_int,
    as_list,
)

toolbar_tween_factory = toolbar_tween_factory  # API

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
    ('exclude_prefixes', as_cr_separated_list, ('/favicon.ico',)),
    ('active_panels', as_list, ()),
    ('includes', as_list, ()),
    ('button_style', None, ''),
    ('max_request_history', as_int, 100),
    ('max_visible_requests', as_int, 10),
    ('show_on_exc_only', asbool, 'false'),
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
    application = make_toolbar_app(settings, config.registry)
    config.registry.registerUtility(application, IToolbarWSGIApp)

    config.add_tween(
        'pyramid_debugtoolbar.toolbar_tween_factory',
        over=[
            pyramid.tweens.EXCVIEW,
            'pyramid_tm.tm_tween_factory',
        ],
    )
    config.add_directive(
        'set_debugtoolbar_request_authorization',
        set_request_authorization_callback,
    )

    # register routes and views that can be used within the tween
    config.add_route('debugtoolbar', '/_debug_toolbar/*subpath', static=True)
    config.add_static_view('/_debug_toolbar/static', STATIC_PATH, static=True)

    config.introspection = introspection


def _apply_parent_actions(parent_registry):
    toolbar_app = parent_registry.queryUtility(IToolbarWSGIApp)
    if toolbar_app is None:
        # this registry does not have a debugtoolbar attached
        return

    toolbar_registry = toolbar_app.registry

    # inject the BeforeRender subscriber after the application is created
    # and all other subscribers are registered in hopes that this will be
    # the last subscriber in the chain and will be able to see the effects
    # of all previous subscribers on the event
    parent_config = Configurator(registry=parent_registry, introspection=False)

    parent_config.add_subscriber(
        'pyramid_debugtoolbar.toolbar.beforerender_subscriber',
        'pyramid.events.BeforeRender',
    )

    actions = toolbar_registry.queryUtility(IParentActions, default=[])
    for action in actions:
        action(parent_config)

    # overwrite actions after they have been applied to avoid applying them
    # twice - but leave it as a new list incase someone adds more actions later
    # and calls config.make_wsgi_app() again... this would mainly be necessary
    # for tests that call config.make_wsgi_app() multiple times.
    toolbar_registry.registerUtility([], IParentActions)

    parent_config.commit()


# AVERT YOUR EYES NOTHING TO SEE HERE
#
# Okay so, we need a way to affect the Pyramid config **after** the user is
# done applying their config. Pyramid does not have a BeforeApplicationCreated
# hook (for good reason), and even if it did I would want to wrap it so that
# the toolbar has the opportunity to wrap all other behavior.
#
# When a user invokes config.make_wsgi_app() this is intended to intercept
# the call to pyramid.config.Router(registry) with our own router factory.
# This will create a new configurator with the registry and apply our actions.
# It will then return the use the original router factory to create a router
# and return it.
#
# The only other trick here is that we only want to apply our actions the first
# time config.make_wsgi_app() is invoked to avoid applying actions multiple
# times.
class _ToolbarRouterFactory(object):
    def __init__(self, wrapped_router):
        self.wrapped_router = wrapped_router

    def __call__(self, registry):
        _apply_parent_actions(registry)
        return self.wrapped_router(registry)


def _monkeypatch_pyramid_router():
    import pyramid.config

    router_factory = pyramid.config.Router

    # do not monkeypatch twice
    if not isinstance(pyramid.config.Router, _ToolbarRouterFactory):
        pyramid.config.Router = _ToolbarRouterFactory(router_factory)


_monkeypatch_pyramid_router()
