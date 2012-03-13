import unittest

from pyramid import testing

class TestSQLAPanel(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self):
        from pyramid_debugtoolbar.panels.sqla import SQLADebugPanel
        request = testing.DummyRequest()
        return SQLADebugPanel(request)
        
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
