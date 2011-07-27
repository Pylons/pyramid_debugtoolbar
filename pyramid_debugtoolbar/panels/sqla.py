import time

from pyramid.threadlocal import get_current_registry
from pyramid_debugtoolbar.panels import DebugPanel
from pyramid_debugtoolbar.utils import format_fname
from pyramid_debugtoolbar.utils import format_sql

from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.engine.base import Engine

_ = lambda x: x

@event.listens_for(Engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, stmt, params, context, execmany):
    registry = get_current_registry()
    registry['sqla_start_timer'] = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, stmt, params, context, execmany):
    stop_timer = time.time()
    registry = get_current_registry()
    queries = registry.get('sqla_queries', [])
    queries.append({
        'duration': stop_timer - registry['sqla_start_timer'],
        'statement': stmt,
        'parameters': params,
        'context': context
    })
    registry['sqla_queries'] = queries
    del registry['sqla_start_timer']


class SQLADebugPanel(DebugPanel):
    """
    Panel that displays the time a response took in milliseconds.
    """
    name = 'SQLAlchemy'

    @property
    def queries(self):
        registry = get_current_registry()
        return registry.get('sqla_queries', [])

    @property
    def has_content(self):
        return True if self.queries else False

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        pass

    def nav_title(self):
        return _('SQLAlchemy')

    def nav_subtitle(self):
        if self.queries:
            count = len(self.queries)
            return "%d %s" % (count, "query" if count == 1 else "queries")

    def title(self):
        return _('SQLAlchemy queries')

    def url(self):
        return ''

    def content(self):
        data = []
        for query in self.queries:
            data.append({
                'duration': query['duration'],
                'sql': format_sql(query['statement'], query['parameters']),
                'raw_sql': query['statement'],
                'params': query['parameters'],
                'context': query['context']
            })
        vars = {'queries': data}
        registry = get_current_registry()
        del registry['sqla_queries']
        return self.render(
            'pyramid_debugtoolbar.panels:templates/sqlalchemy.jinja2',
            vars, self.request)
