import unittest
from pyramid import testing

class TestExceptionDebugView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, request):
        from pyramid_debugtoolbar.views import ExceptionDebugView
        return ExceptionDebugView(request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.secret = 'abc';
        request.params['token'] = 'token'
        return request

    def _makeExceptionHistory(self, frames=None):
        if frames is None:
            frm = DummyFrame()
            frames = {0:frm}
        exc_history = DummyExceptionHistory(frames)
        return exc_history
        
    def test_source(self):
        request = self._makeRequest()
        request.params['frm'] = '0'
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.body, 'source')
        self.assertEqual(response.content_type, 'text/html')

    def test_source_no_frame(self):
        request = self._makeRequest()
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.status_int, 400)

    def test_source_frame_not_found(self):
        request = self._makeRequest()
        request.params['frm'] = '1'
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.status_int, 400)

    def test_execute(self):
        request = self._makeRequest()
        request.params['frm'] = '0'
        request.params['cmd'] = 'doit'
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.body, 'evaled')
        self.assertEqual(response.content_type, 'text/html')

    def test_execute_frame_is_None(self):
        request = self._makeRequest()
        request.params['cmd'] = 'doit'
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.status_int, 400)

    def test_execute_cmd_is_None(self):
        request = self._makeRequest()
        request.params['frm'] = '0'
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.status_int, 400)

    def test_execute_nosuchframe(self):
        request = self._makeRequest()
        request.params['frm'] = '1'
        request.params['cmd'] = 'doit'
        request.exc_history = self._makeExceptionHistory()
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.status_int, 400)

class DummyExceptionHistory(object):
    def __init__(self, frames):
        self.token = 'token'
        self.frames = frames

class DummyConsole(object):
    def eval(self, cmd):
        return 'evaled'

class DummyFrame(object):
    def __init__(self):
        self.console = DummyConsole()
        
    def render_source(self):
        return 'source'
