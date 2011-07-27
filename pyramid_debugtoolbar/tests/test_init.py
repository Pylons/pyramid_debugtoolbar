import unittest
from pyramid import testing

class Test_parse_settings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_debugtoolbar import parse_settings
        return parse_settings(settings)

    def test_it(self):
        panels = ('pyramid_debugtoolbar.tests.test_init.DummyPanel\n'
                  'pyramid_debugtoolbar.tests.test_init.DummyPanel')
        settings = {'debugtoolbar.enabled':'false',
                    'debugtoolbar.intercept_exc':'false',
                    'debugtoolbar.intercept_redirects': 'false',
                    'debugtoolbar.panels': panels,
                    'debugtoolbar.secret':'abc'}
        result = self._callFUT(settings)
        self.assertEqual(result,
                         {'debugtoolbar.enabled':False,
                          'debugtoolbar.intercept_exc': False,
                          'debugtoolbar.intercept_redirects': False,
                          'debugtoolbar.panels': [DummyPanel, DummyPanel],
                          'debugtoolbar.secret':'abc'}
                         )

class Test_includeme(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def _callFUT(self, config):
        from pyramid_debugtoolbar import includeme
        return includeme(config)

    def test_it(self):
        self.config.registry.settings['debugtoolbar.secret'] = 'abc'
        self._callFUT(self.config)

    

class DummyPanel(object):
    pass
