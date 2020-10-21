from collections import OrderedDict
from pyramid.config import Configurator
from pyramid.interfaces import Interface
from pyramid.view import view_config

from pyramid_debugtoolbar.compat import json, text_
from pyramid_debugtoolbar.toolbar import IPanelMap
from pyramid_debugtoolbar.utils import (
    ROOT_ROUTE_NAME,
    SETTINGS_PREFIX,
    STATIC_PATH,
    get_setting,
)

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


class IParentActions(Interface):
    """ Marker interface for registered parent actions in the toolbar app."""


def make_toolbar_app(settings, parent_registry):
    """ WSGI application for rendering the debug toolbar."""
    config = Configurator(settings=settings)
    config.registry.parent_registry = parent_registry
    config.registry.registerUtility(OrderedDict(), IPanelMap)
    config.add_directive('add_debugtoolbar_panel', add_debugtoolbar_panel)
    config.add_directive('inject_parent_action', inject_parent_action)

    config.include('pyramid_mako')
    config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')

    config.add_request_method(
        lambda r: r.matchdict.get('request_id'),
        'pdtb_id',
        reify=True,
    )
    config.add_request_method(
        lambda r: r.registry.parent_registry.pdtb_history,
        'pdtb_history',
        reify=True,
    )

    config.add_static_view('static', STATIC_PATH)
    config.add_route(ROOT_ROUTE_NAME, '/', static=True)
    config.add_route('debugtoolbar.sse', '/sse')
    config.add_route('debugtoolbar.redirect', '/redirect')
    config.add_route('debugtoolbar.request', '/{request_id}')
    config.add_route('debugtoolbar.main', '/')
    config.scan(__name__)

    for include in bundled_includes:
        config.include(include)

    # commit the toolbar config and include any user-defined includes
    config.commit()

    includes = settings.get(SETTINGS_PREFIX + 'includes', ())
    for include in includes:
        config.include(include)

    return config.make_wsgi_app()


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


@view_config(
    route_name='debugtoolbar.redirect',
    renderer='pyramid_debugtoolbar:templates/redirect.dbtmako',
)
def redirect_view(request):
    return {
        'redirect_to': request.params.get('redirect_to'),
        'redirect_code': request.params.get('redirect_code'),
    }


@view_config(
    route_name='debugtoolbar.main',
    renderer='pyramid_debugtoolbar:templates/toolbar.dbtmako',
)
@view_config(
    route_name='debugtoolbar.request',
    renderer='pyramid_debugtoolbar:templates/toolbar.dbtmako',
)
def request_view(request):
    history = request.pdtb_history

    try:
        last_request_pair = history.last(1)[0]
    except IndexError:
        last_request_pair = None
        last_request_id = None
    else:
        last_request_id = last_request_pair[0]

    request_id = request.matchdict.get('request_id', last_request_id)
    toolbar = history.get(request_id, None)

    # set a dictionary of panels that can be accessed inside
    # DebugPanel.render_content()
    if toolbar:
        request.toolbar_panels = {
            panel.name: panel for panel in toolbar.panels
        }

    static_path = request.static_url(STATIC_PATH)
    root_path = request.route_url(ROOT_ROUTE_NAME)

    button_style = get_setting(request.registry.settings, 'button_style')
    max_visible_requests = get_setting(
        request.registry.settings, 'max_visible_requests'
    )
    hist_toolbars = history.last(max_visible_requests)
    return {
        'panels': toolbar.panels if toolbar else [],
        'static_path': static_path,
        'root_path': root_path,
        'button_style': button_style,
        'history': hist_toolbars,
        'default_active_panels': (
            toolbar.default_active_panels if toolbar else []
        ),
        'global_panels': toolbar.global_panels if toolbar else [],
        'request_id': request_id,
    }


U_BLANK = text_("")
U_SSE_PAYLOAD = text_("id:{0}\nevent: new_request\ndata:{1}\n\n")


@view_config(route_name='debugtoolbar.sse')
def sse(request):
    response = request.response
    response.content_type = 'text/event-stream'
    history = request.pdtb_history
    response.text = U_BLANK

    active_request_id = text_(request.GET.get('request_id'))
    client_last_request_id = text_(request.headers.get('Last-Event-Id', 0))

    max_visible_requests = get_setting(
        request.registry.settings, 'max_visible_requests'
    )
    if history:
        last_request_pair = history.last(1)[0]
        last_request_id = last_request_pair[0]
        if not last_request_id == client_last_request_id:
            data = [
                [
                    _id,
                    toolbar.json,
                    'active' if active_request_id == _id else '',
                ]
                for _id, toolbar in history.last(max_visible_requests)
                if toolbar.visible
            ]
            if data:
                response.text = U_SSE_PAYLOAD.format(
                    last_request_id, json.dumps(data)
                )
    return response
