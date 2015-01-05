import unittest
from pyramid import testing

class Test_parse_settings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_debugtoolbar import parse_settings
        return parse_settings(settings)

    def test_it(self):
        panels = ('pyramid_debugtoolbar.tests.test_init.DummyPanel\n'
                  'pyramid_debugtoolbar.tests.test_init.DummyPanel')
        global_panels = ('pyramid_debugtoolbar.tests.test_init.DummyPanel\n'
                  'pyramid_debugtoolbar.tests.test_init.DummyPanel')
        settings = {'debugtoolbar.enabled':'false',
                    'debugtoolbar.intercept_exc':'false',
                    'debugtoolbar.intercept_redirects': 'false',
                    'debugtoolbar.panels': panels,
                    'debugtoolbar.extra_panels': (
                        'pyramid_debugtoolbar.tests.test_init.DummyCustomPanel'),
                    'debugtoolbar.global_panels': global_panels,
                    'debugtoolbar.extra_global_panels': (
                        'pyramid_debugtoolbar.tests.test_init.DummyGlobalPanel'),
                    'debugtoolbar.hosts': '127.0.0.1',
                    'debugtoolbar.exclude_prefixes': '/excluded\n/e2',
                    'debugtoolbar.debug_notfound': 'false',
                    'debugtoolbar.debug_routematch': 'false',
                    'debugtoolbar.reload_templates': 'false',
                    'debugtoolbar.reload_resources': 'false',
                    'debugtoolbar.reload_assets': 'false',
                    'debugtoolbar.prevent_http_cache': 'false',
                    'debugtoolbar.button_style': '',
                    'debugtoolbar.max_request_history': 100,
                    'debugtoolbar.max_visible_requests': 10,
                    }
        result = self._callFUT(settings)
        self.assertEqual(result,
                         {'debugtoolbar.enabled':False,
                          'debugtoolbar.intercept_exc': False,
                          'debugtoolbar.intercept_redirects': False,
                          'debugtoolbar.panels': [DummyPanel, DummyPanel],
                          'debugtoolbar.extra_panels': [DummyCustomPanel],
                          'debugtoolbar.global_panels': [DummyPanel, DummyPanel],
                          'debugtoolbar.extra_global_panels': [DummyGlobalPanel],
                          'debugtoolbar.exclude_prefixes': ['/excluded', '/e2'],
                          'debugtoolbar.hosts': ['127.0.0.1'],
                          'debugtoolbar.debug_notfound': False,
                          'debugtoolbar.debug_routematch': False,
                          'debugtoolbar.reload_templates': False,
                          'debugtoolbar.reload_resources': False,
                          'debugtoolbar.reload_assets': False,
                          'debugtoolbar.prevent_http_cache': False,
                          'debugtoolbar.includes': (),
                          'debugtoolbar.button_style': '',
                          'debugtoolbar.max_request_history': 100,
                          'debugtoolbar.max_visible_requests': 10,
                          }
                         )

class Test_includeme(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def _callFUT(self, config):
        from pyramid_debugtoolbar import includeme
        return includeme(config)

    def test_it(self):
        self._callFUT(self.config)
        self.assertEqual(self.config.registry.settings['debugtoolbar.hosts'],
                         ['127.0.0.1', '::1'])

    def test_it_with_complex_hosts(self):
        s = self.config.registry.settings
        s['debugtoolbar.hosts'] ='127.0.0.1 192.168.1.1 \n 192.168.1.2'
        self._callFUT(self.config)
        self.assertEqual(self.config.registry.settings['debugtoolbar.hosts'],
                         ['127.0.0.1', '192.168.1.1', '192.168.1.2'])

class DummyPanel(object):
    pass

class DummyCustomPanel(object):
    pass

class DummyGlobalPanel(object):
    pass
