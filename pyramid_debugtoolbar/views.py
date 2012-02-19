import hashlib

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_debugtoolbar.compat import json
from pyramid_debugtoolbar.compat import bytes_
from pyramid_debugtoolbar.compat import url_quote
from pyramid_debugtoolbar.console import _ConsoleFrame
from pyramid_debugtoolbar.utils import STATIC_PATH
from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
from pyramid_debugtoolbar.utils import format_sql
from pyramid_debugtoolbar.utils import get_setting

def valid_host(info, request):
    hosts = get_setting(request.registry.settings, 'hosts')
    if request.remote_addr in hosts:
        return True
    return False

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
        if not token == self.exc_history.token:
            raise HTTPBadRequest('Bad token in request')
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
        custom_predicates=(valid_host,)
        )
    def exception(self):
        tb = self.exc_history.tracebacks[self.tb]
        body = tb.render_full(self.request).encode('utf-8', 'replace')
        response = Response(body, status=500)
        return response

    @view_config(
        route_name='debugtoolbar.source',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host,)
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
        custom_predicates=(valid_host,)
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
        custom_predicates=(valid_host,)
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
            'token':            exc_history.token,
            }
        if 0 not in exc_history.frames:
            exc_history.frames[0] = _ConsoleFrame({})
        return vars


class SQLAlchemyViews(object):
    def __init__(self, request):
        self.request = request

    def validate(self):
        stmt = self.request.params['sql']
        params = self.request.params['params']

        # Validate hash
        need = self.request.exc_history.token + stmt + url_quote(params)

        hash = hashlib.sha1(bytes_(need)).hexdigest()
        if hash != self.request.params['hash']:
            raise HTTPBadRequest('Bad token in request')
        return stmt, params

    @view_config(
        route_name='debugtoolbar.sql_select',
        renderer='pyramid_debugtoolbar.panels:templates/sqlalchemy_select.dbtmako',
        permission=NO_PERMISSION_REQUIRED,
        custom_predicates=(valid_host,)
        )
    def sql_select(self):
        stmt, params = self.validate()
        engine_id = self.request.params['engine_id']
        # Make sure it is a select statement
        if not stmt.lower().strip().startswith('select'):
            raise HTTPBadRequest('Not a SELECT SQL statement')

        if not engine_id:
            raise HTTPBadRequest('No valid database engine')

        engine = getattr(self.request.registry, 'pdtb_sqla_engines')\
                      [int(engine_id)]()
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
        custom_predicates=(valid_host,)
        )
    def sql_explain(self):
        stmt, params = self.validate()
        engine_id = self.request.params['engine_id']

        if not engine_id:
            raise HTTPBadRequest('No valid database engine')

        engine = getattr(self.request.registry, 'pdtb_sqla_engines')\
                      [int(engine_id)]()
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

