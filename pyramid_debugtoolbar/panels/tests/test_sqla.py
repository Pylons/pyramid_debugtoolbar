import unittest

from pyramid import testing

class TestSQLAPanel(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self):
        from pyramid_debugtoolbar.panels.sqla import SQLADebugPanel
        return SQLADebugPanel(self.request)

    def test_max_queries(self):
        panel = self._makeOne()
        self.assertEqual(panel.max_queries, None)
        self.config.registry.settings['debugtoolbar.sqla_max_queries'] = '10'
        self.assertEqual(panel.max_queries, '10')

    def test_nav_subtitle(self):
        panel =  self._makeOne()
        self.assertEqual(panel.nav_subtitle(), None)
        panel.request.pdtb_sqla_queries = [1]
        self.assertEqual(panel.nav_subtitle(), '1 query ')
        self.config.registry.settings['debugtoolbar.sqla_max_queries'] = '10'
        self.assertEqual(panel.nav_subtitle(), '1 query (10 max)')


class Test_after_cursor_execute(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self):
        from pyramid_debugtoolbar.panels.sqla import _after_cursor_execute
        _after_cursor_execute(DummyConnection(), None, None, None, None, None)

    def test_no_max_queries(self):
        self._makeOne()
        self.assertEqual(self.request.registry.settings.get(
            'debugtoolbar.sqla_max_queries'), None)
        self.assertEqual(self.request.pdtb_sqla_queries.maxlen, None)

    def test_max_queries(self):
        self.request.registry.settings['debugtoolbar.sqla_max_queries'] = '10'
        self.assertEqual(self.request.registry.settings.get(
            'debugtoolbar.sqla_max_queries'), '10')
        self._makeOne()
        self.assertEqual(self.request.pdtb_sqla_queries.maxlen, 10)


class DummyConnection(object):
    """Dummy Database Connection"""

    def __init__(self):
        import time
        self.pdtb_start_timer = time.time()

    def engine(self):
        pass
