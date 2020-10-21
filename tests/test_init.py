from pyramid import testing
import unittest


class Test_parse_settings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_debugtoolbar import parse_settings

        return parse_settings(settings)

    def test_it(self):
        settings = {
            'debugtoolbar.enabled': 'false',
            'debugtoolbar.intercept_exc': 'false',
            'debugtoolbar.intercept_redirects': 'false',
            'debugtoolbar.panels': 'foo bar',
            'debugtoolbar.extra_panels': (
                'tests.test_init.DummyCustomPanel foo'
            ),
            'debugtoolbar.global_panels': 'foo\nbar baz',
            'debugtoolbar.extra_global_panels': (
                'tests.test_init.DummyGlobalPanel'
            ),
            'debugtoolbar.active_panels': 'dummy_panel',
            'debugtoolbar.hosts': '127.0.0.1',
            'debugtoolbar.exclude_prefixes': '/excluded\n/e2',
            'debugtoolbar.debug_notfound': 'false',
            'debugtoolbar.debug_routematch': 'false',
            'debugtoolbar.reload_templates': 'false',
            'debugtoolbar.reload_resources': 'false',
            'debugtoolbar.reload_assets': 'false',
            'debugtoolbar.show_on_exc_only': 'false',
            'debugtoolbar.prevent_http_cache': 'false',
            'debugtoolbar.button_style': '',
            'debugtoolbar.max_request_history': 100,
            'debugtoolbar.max_visible_requests': 10,
        }
        result = self._callFUT(settings)
        self.assertEqual(
            result,
            {
                'debugtoolbar.enabled': False,
                'debugtoolbar.intercept_exc': False,
                'debugtoolbar.intercept_redirects': False,
                'debugtoolbar.panels': ['foo', 'bar'],
                'debugtoolbar.extra_panels': [
                    'tests.test_init.DummyCustomPanel',
                    'foo',
                ],
                'debugtoolbar.global_panels': ['foo', 'bar', 'baz'],
                'debugtoolbar.extra_global_panels': [
                    'tests.test_init.DummyGlobalPanel'
                ],
                'debugtoolbar.exclude_prefixes': ['/excluded', '/e2'],
                'debugtoolbar.hosts': ['127.0.0.1'],
                'debugtoolbar.debug_notfound': False,
                'debugtoolbar.debug_routematch': False,
                'debugtoolbar.reload_templates': False,
                'debugtoolbar.reload_resources': False,
                'debugtoolbar.reload_assets': False,
                'debugtoolbar.show_on_exc_only': False,
                'debugtoolbar.prevent_http_cache': False,
                'debugtoolbar.active_panels': ['dummy_panel'],
                'debugtoolbar.includes': [],
                'debugtoolbar.button_style': '',
                'debugtoolbar.max_request_history': 100,
                'debugtoolbar.max_visible_requests': 10,
            },
        )


class Test_includeme(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def _callFUT(self, config):
        from pyramid_debugtoolbar import includeme

        return includeme(config)

    def test_it(self):
        self._callFUT(self.config)
        self.assertEqual(
            self.config.registry.settings['debugtoolbar.hosts'],
            ['127.0.0.1', '::1'],
        )

    def test_it_with_complex_hosts(self):
        s = self.config.registry.settings
        s['debugtoolbar.hosts'] = '127.0.0.1 192.168.1.1 \n 192.168.1.2'
        self._callFUT(self.config)
        self.assertEqual(
            self.config.registry.settings['debugtoolbar.hosts'],
            ['127.0.0.1', '192.168.1.1', '192.168.1.2'],
        )
