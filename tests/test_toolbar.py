import unittest
from pyramid.request import Request
from pyramid.response import Response
from pyramid import testing

from pyramid_debugtoolbar.compat import bytes_


class DebugToolbarTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.registry.settings['mako.directories'] = []
        self.config.include('pyramid_mako')
        self.config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')

    def tearDown(self):
        del self.config

    def _makeOne(self, request, panel_classes, global_panel_classes):
        from pyramid_debugtoolbar.toolbar import DebugToolbar
        return DebugToolbar(request, panel_classes, global_panel_classes)

    def test_ctor_panel_is_up(self):
        request = Request.blank('/')
        request.environ['HTTP_COOKIE'] = 'pdtb_active="id"'
        toolbar = self._makeOne(request, [DummyPanelWithContent], [DummyPanelWithContent])
        self.assertEqual(len(toolbar.panels), 1)
        panel = toolbar.panels[0]
        self.assertEqual(panel.request, request)
        self.assertEqual(panel.is_active, True)

    def test_ctor_panel_has_content(self):
        request = Request.blank('/')
        request.environ['HTTP_COOKIE'] = 'pdtb_active="id"'
        toolbar = self._makeOne(request, [DummyPanelWithContent], [DummyPanelWithContent])
        self.assertEqual(len(toolbar.panels), 1)
        panel = toolbar.panels[0]
        self.assertEqual(panel.request, request)
        self.assertEqual(panel.is_active, True)

    def test_process_response_nonhtml(self):
        response = Response()
        response.content_type = 'text/plain'
        request = Request.blank('/')
        toolbar = self._makeOne(request, [DummyPanel], [DummyPanel])
        toolbar.process_response(request, response)
        self.assertTrue(response.processed)

    def test_inject_html(self):
        from pyramid_debugtoolbar.utils import STATIC_PATH
        self.config.add_static_view('_debugtoolbar/static', STATIC_PATH)
        self.config.add_route('debugtoolbar', '/_debugtoolbar/*subpath')
        response = Response('<body></body>')
        response.content_type = 'text/html'
        request = Request.blank('/')
        request.id = 'abc'
        request.registry = self.config.registry
        toolbar = self._makeOne(request, [DummyPanel], [DummyPanel])
        toolbar.inject(request, response)
        self.assertTrue(bytes_('div id="pDebug"') in response.app_iter[0])
        self.assertEqual(response.content_length, len(response.app_iter[0]))

    def test_passing_of_button_style(self):
        from pyramid_debugtoolbar.utils import STATIC_PATH
        self.config.add_static_view('_debugtoolbar/static', STATIC_PATH)
        self.config.add_route('debugtoolbar', '/_debugtoolbar/*subpath')
        self.config.registry.settings['debugtoolbar.button_style'] = \
            'top:120px;zoom:50%'
        response = Response('<body></body>')
        response.content_type = 'text/html'
        request = Request.blank('/')
        request.id = 'abc'
        request.registry = self.config.registry
        toolbar = self._makeOne(request, [DummyPanel], [DummyPanel])
        toolbar.inject(request, response)
        self.assertTrue(bytes_('top:120px;zoom:50%') in response.app_iter[0])


class Test_beforerender_subscriber(unittest.TestCase):
    def setUp(self):
        self.request = Request.blank('/')
        self.config = testing.setUp(request=self.request)
        panel = DummyPanel(self.request)
        self.request.debug_toolbar = DummyToolbar([panel])

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, event):
        from pyramid_debugtoolbar.toolbar import beforerender_subscriber
        return beforerender_subscriber(event)

    def test_with_request_None(self):
        event = {}
        event['request'] = None
        self._callFUT(event)
        self.assertTrue(event['processed'])

    def test_with_request(self):
        event = {}
        event['request'] = self.request
        self._callFUT(event)
        self.assertTrue(event['processed'])


class Test_toolbar_tween_factory(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, handler, registry):
        from pyramid_debugtoolbar.toolbar import toolbar_tween_factory
        return toolbar_tween_factory(handler, registry)

    def test_it_disabled(self):
        def handler(): pass
        result = self._callFUT(handler, self.config.registry)
        self.assertTrue(result is handler)

    def test_it_enabled(self):
        self.config.registry.settings['debugtoolbar.enabled'] = True
        def handler(): pass
        result = self._callFUT(handler, self.config.registry)
        self.assertFalse(result is handler)


class Test_toolbar_handler(unittest.TestCase):
    def setUp(self):
        from pyramid_debugtoolbar.utils import ROOT_ROUTE_NAME
        from pyramid_debugtoolbar.utils import STATIC_PATH
        self.config = testing.setUp()
        settings = self.config.registry.settings
        settings['debugtoolbar.enabled'] = True
        settings['debugtoolbar.hosts'] = ['127.0.0.1']
        settings['mako.directories'] = []
        settings['debugtoolbar.exclude_prefixes'] = ['/excluded']
        self.config.add_route(ROOT_ROUTE_NAME, '/_debug_toolbar')
        self.config.add_route('debugtoolbar', '/_debug_toolbar/*subpath')
        self.config.add_static_view('_debugtoolbar/static', STATIC_PATH)
        self.config.include('pyramid_mako')
        self.config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')

    def tearDown(self):
        testing.tearDown()

    def _makeHandler(self):
        self.response = Response('OK')
        def handler(request):
            return self.response
        return handler

    def _callFUT(self, request, handler=None, _logger=None):
        from pyramid_debugtoolbar.toolbar import toolbar_tween_factory
        from pyramid_debugtoolbar.views import ExceptionDebugView
        registry = self.config.registry
        if handler is None:
            handler = self._makeHandler()
        def invoke_subrequest(request):
            request.registry = registry.parent_registry = registry
            request.exc_history = registry.exc_history
            return ExceptionDebugView(request).exception()
        handler = toolbar_tween_factory(handler, registry, _logger=_logger)
        request.invoke_subrequest = invoke_subrequest
        return handler(request)

    def test_it_path_cannot_be_decoded(self):
        from pyramid.exceptions import URLDecodeError
        request = Request.blank('/%c5')
        request.remote_addr = '127.0.0.1'
        self.assertRaises(URLDecodeError, self._callFUT, request)

    def test_it_startswith_root_path(self):
        request = Request.blank('/_debug_toolbar')
        request.remote_addr = '127.0.0.1'
        request.registry = self.config.registry
        result = self._callFUT(request)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(result is self.response)

    def test_it_startswith_excluded_prefix(self):
        request = Request.blank('/excluded')
        request.remote_addr = '127.0.0.1'
        result = self._callFUT(request)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(result is self.response)

    def test_it_bad_remote_addr(self):
        request = Request.blank('/')
        request.remote_addr = '123.123.123.123'
        result = self._callFUT(request)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(result is self.response)

    def test_it_remote_addr_is_None(self):
        request = Request.blank('/')
        request.remote_addr = None
        result = self._callFUT(request)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(result is self.response)

    def test_it_remote_addr_mask(self):
        self.config.registry.settings['debugtoolbar.hosts'] = ['127.0.0.0/24']
        request = Request.blank('/')
        self.config.registry.settings['debugtoolbar.panels'] = [ DummyPanel ]
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.254'
        result = self._callFUT(request)
        self.assertTrue(getattr(result, 'processed', False))
        request.remote_addr = '127.0.0.1'
        result = self._callFUT(request)
        self.assertTrue(getattr(result, 'processed', False))
        request.remote_addr = '127.0.1.1'
        result = self._callFUT(request)
        self.assertFalse(getattr(result, 'processed', False))

    def test_it_calls_wrap_handler(self):
        handler = self._makeHandler()
        request = Request.blank('/')
        self.config.registry.settings['debugtoolbar.panels'] = [ DummyPanel ]
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.1'
        result = self._callFUT(request, handler)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(result is self.response)
        self.assertTrue(handler.wrapped)
        self.assertTrue(result.processed)

    def test_it_raises_exception_no_intercept_exc(self):
        request = Request.blank('/')
        request.remote_addr = '127.0.0.1'
        def handler(request):
            raise NotImplementedError
        request.registry = self.config.registry
        logger = DummyLogger()
        self.assertRaises(NotImplementedError, self._callFUT, request, handler,
                          _logger=logger)

    def test_it_raises_exception_intercept_exc(self):
        request = Request.blank('/')
        def handler(request):
            raise NotImplementedError
        self.config.registry.settings['debugtoolbar.intercept_exc'] = True
        self.config.registry.settings['debugtoolbar.secret'] = 'abc'
        self.config.add_route('debugtoolbar.exception', '/exception')
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.1'
        logger = DummyLogger()
        response = self._callFUT(request, handler, _logger=logger)
        self.assertEqual(len(request.exc_history.tracebacks), 1)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(response.status_int, 500)

    def test_it_intercept_redirect_nonredirect_code(self):
        request = Request.blank('/')
        request.remote_addr = '127.0.0.1'
        self.config.registry.settings['debugtoolbar.intercept_redirects'] = True
        request.registry = self.config.registry
        result = self._callFUT(request)
        self.assertTrue(result is self.response)

    def test_it_intercept_redirect(self):
        from pyramid.httpexceptions import HTTPFound
        response = HTTPFound(location='http://other.com')
        def handler(request):
            return response
        request = Request.blank('/')
        request.remote_addr = '127.0.0.1'
        request.registry = self.config.registry
        self.config.registry.settings['debugtoolbar.intercept_redirects'] = True
        result = self._callFUT(request, handler)
        self.assertTrue(result is response)
        self.assertEqual(result.status_int, 200)
        self.assertEqual(result.location, None)

    def test_it_intercept_exc_with_utf8_message(self):
        request = Request.blank('/')
        def handler(request):
            raise NotImplementedError(b'K\xc3\xa4se!\xe2\x98\xa0')
        self.config.registry.settings['debugtoolbar.intercept_exc'] = True
        self.config.registry.settings['debugtoolbar.secret'] = 'abc'
        self.config.add_route('debugtoolbar.exception', '/exception')
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.1'
        logger = DummyLogger()
        response = self._callFUT(request, handler, _logger=logger)
        self.assertTrue(response.status_int, 500)
        self.assertTrue(
            b'NotImplementedError: K\xc3\xa4se!\xe2\x98\xa0' in response.body or
            # Python 3: the byte exception is escaped
            b'K\\xc3\\xa4se!\\xe2\\x98\\xa0' in response.body
        )

    def test_show_on_exc_with_exc_raised(self):
        request = Request.blank('/')
        def handler(request):
            raise NotImplementedError
        self.config.registry.settings['debugtoolbar.show_on_exc_only'] = True
        self.config.registry.settings['debugtoolbar.intercept_exc'] = True
        self.config.registry.settings['debugtoolbar.secret'] = 'abc'
        self.config.add_route('debugtoolbar.exception', '/exception')
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.1'
        logger = DummyLogger()
        response = self._callFUT(request, handler, _logger=logger)
        self.assertFalse(hasattr(request, 'debug_toolbar'))
        self.assertTrue(response.status_int, 500)

    def test_show_on_exc_without_exc_raised(self):
        request = Request.blank('/')
        def handler(request):
            response = request.response
            response.body = b"<html><body>OK!</body></html>"
            return response
        self.config.registry.settings['debugtoolbar.show_on_exc_only'] = True
        self.config.registry.settings['debugtoolbar.intercept_exc'] = True
        self.config.registry.settings['debugtoolbar.secret'] = 'abc'
        self.config.add_route('debugtoolbar.exception', '/exception')
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.1'
        response = self._callFUT(request, handler)
        self.assertTrue(response.status_int, 200)
        self.assertEqual(response.body, b"<html><body>OK!</body></html>")
        self.assertFalse(hasattr(request, 'debug_toolbar'))

    def test_show_on_exc_disabled_without_exc_raised(self):
        request = Request.blank('/')
        def handler(request):
            response = request.response
            response.body = b"<html><body>OK!</body></html>"
            return response
        self.config.registry.settings['debugtoolbar.show_on_exc_only'] = False
        self.config.registry.settings['debugtoolbar.intercept_exc'] = True
        self.config.registry.settings['debugtoolbar.secret'] = 'abc'
        self.config.add_route('debugtoolbar.exception', '/exception')
        request.registry = self.config.registry
        request.remote_addr = '127.0.0.1'
        response = self._callFUT(request, handler)
        self.assertTrue(response.status_int, 200)
        self.assertNotEqual(response.body, b"<html><body>OK!</body></html>")
        self.assertFalse(hasattr(request, 'debug_toolbar'))

    def test_request_authorization(self):
        from pyramid_debugtoolbar import set_request_authorization_callback

        def auth_check_disable_toolbar(request):
            return False

        def auth_check_enable_toolbar(request):
            return True

        request = Request.blank('/')
        request.remote_addr = '127.0.0.1'
        self.config.registry.settings['debugtoolbar.panels'] = [DummyPanel]
        request.registry = self.config.registry

        set_request_authorization_callback(request, auth_check_disable_toolbar)
        result = self._callFUT(request)
        self.assertFalse(getattr(result, 'processed', False))

        set_request_authorization_callback(request, auth_check_enable_toolbar)
        result = self._callFUT(request)
        self.assertTrue(result.processed)

    def test_it_remote_addr_proxies_list(self):
        request = Request.blank('/')
        request.remote_addr = '172.16.63.156, 64.119.211.105'
        result = self._callFUT(request)


class DummyPanel(object):
    is_active = False
    has_content = False
    user_activate = False
    dom_id = 'id'
    nav_title = 'title'
    nav_subtitle = 'subtitle'

    def __init__(self, request):
        self.request = request

    def process_response(self, response):
        response.processed = True

    def wrap_handler(self, handler):
        handler.wrapped = True
        return handler

    def process_beforerender(self, event):
        event['processed'] = True

class DummyPanelWithContent(DummyPanel):
    has_content = True

class DummyToolbar(object):
    def __init__(self, panels):
        self.panels = panels

class DummyLogger(object):
    def exception(self, msg):
        self.msg = msg

