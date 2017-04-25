from pyramid.events import subscriber
from pyramid.events import NewRequest
from pyramid.view import view_config

from pyramid_debugtoolbar.compat import json
from pyramid_debugtoolbar.compat import text_
from pyramid_debugtoolbar.utils import find_request_history
from pyramid_debugtoolbar.utils import get_setting
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
from pyramid_debugtoolbar.utils import STATIC_PATH

U_BLANK = text_("")

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
    renderer='pyramid_debugtoolbar:templates/toolbar.dbtmako'
)
@view_config(
    route_name='debugtoolbar.request',
    renderer='pyramid_debugtoolbar:templates/toolbar.dbtmako'
)
def request_view(request):
    history = find_request_history(request)

    try:
        last_request_pair = history.last(1)[0]
    except IndexError:
        last_request_pair = None
        last_request_id = None
    else:
        last_request_id = last_request_pair[0]

    request_id = request.matchdict.get('request_id', last_request_id)
    toolbar = history.get(request_id, None)

    static_path = request.static_url(STATIC_PATH)
    root_path = request.route_url(ROOT_ROUTE_NAME)
    
    button_style = get_setting(request.registry.settings,
            'button_style')
    max_visible_requests = get_setting(request.registry.settings, 
            'max_visible_requests')
    hist_toolbars = history.last(max_visible_requests)
    return {'panels': toolbar.panels if toolbar else [],
            'static_path': static_path,
            'root_path': root_path,
            'button_style': button_style,
            'history': hist_toolbars,
            'default_active_panels': (
                toolbar.default_active_panels if toolbar else []),
            'global_panels': toolbar.global_panels if toolbar else [],
            'request_id': request_id
            }

U_SSE_PAYLOAD = text_("id:{0}\nevent: new_request\ndata:{1}\n\n")
@view_config(route_name='debugtoolbar.sse')
def sse(request):
    response = request.response
    response.content_type = 'text/event-stream'
    history = find_request_history(request)
    response.text = U_BLANK

    active_request_id = text_(request.GET.get('request_id'))
    client_last_request_id = text_(request.headers.get('Last-Event-Id', 0))

    max_visible_requests = get_setting(request.registry.settings,
        'max_visible_requests')
    if history:
        last_request_pair = history.last(1)[0]
        last_request_id = last_request_pair[0]
        if not last_request_id == client_last_request_id:
            data = [[_id, toolbar.json, 'active'
                        if active_request_id == _id else '']
                            for _id,toolbar in history.last(max_visible_requests)]
            if data:
                response.text = U_SSE_PAYLOAD.format(last_request_id,
                                                     json.dumps(data))
    return response

@subscriber(NewRequest)
def find_exc_history(event):
    # Move the chickens to a new hen house
    request = event.request
    exc_history = request.registry.parent_registry.exc_history
    request.exc_history = exc_history
