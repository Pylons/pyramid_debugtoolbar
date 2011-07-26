import unittest
from pyramid.request import Request
from pyramid.response import Response
from pyramid import testing

class DebugToolbarTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        del self.config
        
    def _makeOne(self, request, panel_classes):
        from pyramid_debugtoolbar.toolbar import DebugToolbar
        return DebugToolbar(request, panel_classes)

    def test_ctor_panel_is_up(self):
        request = Request.blank('/')
        request.cookies['fldt_active'] = 'id'
        toolbar = self._makeOne(request, [DummyPanel])
        self.assertEqual(len(toolbar.panels), 1)
        panel = toolbar.panels[0]
        self.assertEqual(panel.request, request)
        self.assertEqual(panel.is_active, True)

    def test_ctor_panel_is_down(self):
        request = Request.blank('/')
        request.cookies['fldt_active'] = 'id'
        class DummyDownPanel(DummyPanel):
            down = True
        toolbar = self._makeOne(request, [DummyDownPanel])
        self.assertEqual(len(toolbar.panels), 1)
        panel = toolbar.panels[0]
        self.assertEqual(panel.request, request)
        self.assertEqual(panel.is_active, False)

    def test_process_response_nonhtml(self):
        response = Response()
        response.content_type = 'text/plain'
        request = Request.blank('/')
        toolbar = self._makeOne(request, [DummyPanel])
        toolbar.process_response(response)
        self.assertTrue(response.processed)

    def test_process_response_html(self):
        self.config.include('pyramid_jinja2')
        self.config.add_static_view('_debugtoolbar/static',
                                    'pyramid_debugtoolbar:static')
        response = Response('<body></body>')
        response.content_type = 'text/html'
        request = Request.blank('/')
        request.registry = self.config.registry
        toolbar = self._makeOne(request, [DummyPanel])
        toolbar.process_response(response)
        self.assertTrue(response.processed)
        self.failUnless('div id="flDebug"' in response.app_iter[0])

class Test_beforerender_subscriber(unittest.TestCase):
    def setUp(self):
        self.request = Request.blank('/')
        panel = DummyPanel(self.request)
        self.request.debug_toolbar = DummyToolbar([panel])
        self.config = testing.setUp(request=self.request)

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

class DummyPanel(object):
    is_active = False
    down = False

    def __init__(self, request):
        self.request = request

    def process_response(self, request, response):
        response.processed = True
        
    def dom_id(self):
        return 'id'

    def nav_title(self):
        return 'title'

    def nav_subtitle(self):
        return 'subtitle'

    def process_beforerender(self, event):
        event['processed'] = True

class DummyToolbar(object):
    def __init__(self, panels):
        self.panels = panels
