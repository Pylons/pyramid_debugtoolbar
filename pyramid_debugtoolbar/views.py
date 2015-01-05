import hashlib

from pyramid.events import subscriber
from pyramid.events import NewRequest
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_debugtoolbar.compat import json
from pyramid_debugtoolbar.compat import bytes_
from pyramid_debugtoolbar.compat import text_
from pyramid_debugtoolbar.compat import url_quote
from pyramid_debugtoolbar.console import _ConsoleFrame
from pyramid_debugtoolbar.utils import addr_in
from pyramid_debugtoolbar.utils import find_request_history
from pyramid_debugtoolbar.utils import format_sql
from pyramid_debugtoolbar.utils import get_setting
from pyramid_debugtoolbar.utils import last_proxy
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.toolbar import IRequestAuthorization

U_BLANK = text_("")

def valid_host(info, request):
    hosts = get_setting(request.registry.settings, 'hosts')
    if request.remote_addr is None:
        return False

    last_proxy_addr = last_proxy(request.remote_addr)

    return addr_in(last_proxy_addr, hosts)


def valid_request(info, request):
    auth_check = request.registry.queryUtility(IRequestAuthorization)
    return auth_check(request) if auth_check else True


class ExceptionDebugView(object):
    def __init__(self, request):
        self.request = request
        exc_history = request.exc_history
        if exc_history is None:
            raise HTTPBadRequest('No exception history')
        self.exc_history = exc_history
        token = self.request.params.get('token')
        if not token:
            raise HTTPBadRequest('No token in request')
        if not token == request.registry.parent_registry.pdtb_token:
            raise HTTPBadRequest('Bad token in request')
        self.token = token
        frm = self.request.params.get('frm')
        if frm is not None:
            frm = int(frm)
        self.frame = frm
        cmd = self.request.params.get('cmd')
        self.cmd = cmd
        tb = self.request.params.get('tb')
        if tb is not None:
            tb = int(tb)
        self.tb = tb

    @view_config(
        route_name='debugtoolbar.exception',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host, valid_request)
        )
    def exception(self):
        tb = self.exc_history.tracebacks[self.tb]
        body = tb.render_full(self.request).encode('utf-8', 'replace')
        response = Response(body, status=500)
        return response

    @view_config(
        route_name='debugtoolbar.source',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host, valid_request)
        )
    def source(self):
        exc_history = self.exc_history
        if self.frame is not None:
            frame = exc_history.frames.get(self.frame)
            if frame is not None:
                return Response(frame.render_source(), content_type='text/html')
        return HTTPBadRequest()

    @view_config(
        route_name='debugtoolbar.execute',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host, valid_request)
        )
    def execute(self):
        if self.request.exc_history.eval_exc:
            exc_history = self.exc_history
            if self.frame is not None and self.cmd is not None:
                frame = exc_history.frames.get(self.frame)
                if frame is not None:
                    result = frame.console.eval(self.cmd)
                    return Response(result, content_type='text/html')
        return HTTPBadRequest()

    @view_config(
        route_name='debugtoolbar.console',
        renderer='pyramid_debugtoolbar:templates/console.dbtmako',
        custom_predicates=(valid_host, valid_request)
        )
    def console(self):
        static_path = self.request.static_url(STATIC_PATH)
        toolbar_root_path = self.request.route_url(ROOT_ROUTE_NAME)
        exc_history = self.exc_history
        vars = {
            'evalex':           exc_history.eval_exc and 'true' or 'false',
            'console':          'true',
            'title':            'Console',
            'traceback_id':     self.tb or -1,
            'root_path':        toolbar_root_path,
            'static_path':      static_path,
            'token':            self.token,
            }
        if 0 not in exc_history.frames:
            exc_history.frames[0] = _ConsoleFrame({})
        return vars


class SQLAlchemyViews(object):
    def __init__(self, request):
        self.request = request
        self.token = request.registry.parent_registry.pdtb_token

    def validate(self):
        stmt = self.request.params['sql']
        params = self.request.params['params']

        # Validate hash
        need = self.token + stmt + url_quote(params)

        hash = hashlib.sha1(bytes_(need)).hexdigest()
        if hash != self.request.params['hash']:
            raise HTTPBadRequest('Bad token in request')
        return stmt, params

    @view_config(
        route_name='debugtoolbar.sql_select',
        renderer='pyramid_debugtoolbar.panels:templates/sqlalchemy_select.dbtmako',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host, valid_request)
        )
    def sql_select(self):
        stmt, params = self.validate()
        engine_id = self.request.params['engine_id']
        # Make sure it is a select statement
        if not stmt.lower().strip().startswith('select'):
            raise HTTPBadRequest('Not a SELECT SQL statement')

        if not engine_id:
            raise HTTPBadRequest('No valid database engine')

        engines = self.request.registry.parent_registry.pdtb_sqla_engines
        engine = engines[int(engine_id)]()
        params = [json.loads(params)]
        result = engine.execute(stmt, params)

        return {
            'result': result.fetchall(),
            'headers': result.keys(),
            'sql': format_sql(stmt),
            'duration': float(self.request.params['duration']),
        }

    @view_config(
        route_name='debugtoolbar.sql_explain',
        renderer='pyramid_debugtoolbar.panels:templates/sqlalchemy_explain.dbtmako',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host, valid_request)
        )
    def sql_explain(self):
        stmt, params = self.validate()
        engine_id = self.request.params['engine_id']

        if not engine_id:
            raise HTTPBadRequest('No valid database engine')

        engines = self.request.registry.parent_registry.pdtb_sqla_engines
        engine = engines[int(engine_id)]()
        params = json.loads(params)

        if engine.name.startswith('sqlite'):
            query = 'EXPLAIN QUERY PLAN %s' % stmt
        else:
            query = 'EXPLAIN %s' % stmt

        result = engine.execute(query, params)

        return {
            'result': result.fetchall(),
            'headers': result.keys(),
            'sql': format_sql(stmt),
            'str': str,
            'duration': float(self.request.params['duration']),
        }


@view_config(
    route_name='debugtoolbar.main',
    permission=NO_PERMISSION_REQUIRED,
    custom_predicates=(valid_host, valid_request),
    renderer='pyramid_debugtoolbar:templates/toolbar.dbtmako'
)
@view_config(
    route_name='debugtoolbar.request',
    permission=NO_PERMISSION_REQUIRED,
    custom_predicates=(valid_host, valid_request),
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
            'global_panels': toolbar.global_panels if toolbar else [],
            'request_id': request_id
            }

U_SSE_PAYLOAD = text_("id:{0}\nevent: new_request\ndata:{1}\n\n")
@view_config(route_name='debugtoolbar.sse',
             permission=NO_PERMISSION_REQUIRED)
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
