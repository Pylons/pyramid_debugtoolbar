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
        request.exc_history = self._makeExceptionHistory()
        return request

    def _makeExceptionHistory(self, frames=None):
        if frames is None:
            frm = DummyFrame()
            frames = {0:frm}
        exc_history = DummyExceptionHistory(frames)
        return exc_history

    def test_no_exc_history(self):
        from pyramid.httpexceptions import HTTPBadRequest
        request = self._makeRequest()
        request.static_url = lambda *arg, **kw: 'http://static'
        request.params['frm'] = '0'
        request.exc_history = None
        self.assertRaises(HTTPBadRequest, self._makeOne, request)

    def test_without_token_in_request(self):
        from pyramid.httpexceptions import HTTPBadRequest
        request = self._makeRequest()
        del request.params['token']
        self.assertRaises(HTTPBadRequest, self._makeOne, request)

    def test_with_bad_token_in_request(self):
        from pyramid.httpexceptions import HTTPBadRequest
        request = self._makeRequest()
        request.params['token'] = 'wrong'
        self.assertRaises(HTTPBadRequest, self._makeOne, request)
        
    def test_source(self):
        request = self._makeRequest()
        request.params['frm'] = '0'
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.body, 'source')
        self.assertEqual(response.content_type, 'text/html')

    def test_source_no_frame(self):
        request = self._makeRequest()
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.status_int, 400)

    def test_source_frame_not_found(self):
        request = self._makeRequest()
        request.params['frm'] = '1'
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.status_int, 400)

    def test_execute(self):
        request = self._makeRequest()
        request.params['frm'] = '0'
        request.params['cmd'] = 'doit'
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.body, 'evaled')
        self.assertEqual(response.content_type, 'text/html')

    def test_execute_frame_is_None(self):
        request = self._makeRequest()
        request.params['cmd'] = 'doit'
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.status_int, 400)

    def test_execute_cmd_is_None(self):
        request = self._makeRequest()
        request.params['frm'] = '0'
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.status_int, 400)

    def test_execute_nosuchframe(self):
        request = self._makeRequest()
        request.params['frm'] = '1'
        request.params['cmd'] = 'doit'
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.status_int, 400)

    def test_console(self):
        request = self._makeRequest()
        request.static_url = lambda *arg, **kw: 'http://static'
        request.route_url = lambda *arg, **kw: 'http://root'
        request.params['frm'] = '0'
        view = self._makeOne(request)
        result = view.console()
        self.assertEqual(result,
                         {'console': 'true',
                          'title': 'Console',
                          'evalex': 'true',
                          'traceback_id': -1,
                          'token': 'token',
                          'static_path': 'http://static',
                          'root_path':'http://root'}
                         )

    def test_console_no_initial_history_frame(self):
        request = self._makeRequest()
        request.static_url = lambda *arg, **kw: 'http://static'
        request.route_url = lambda *arg, **kw: 'http://root'
        request.params['frm'] = '0'
        request.exc_history.frames = {}
        view = self._makeOne(request)
        view.console()
        self.assertEqual(len(request.exc_history.frames), 1)

    def test_exception_summary(self):
        from pyramid.renderers import render
        self.config.include('pyramid_jinja2')
        request = self._makeRequest()
        request.static_url = lambda *arg, **kw: 'http://static'
        vars = {
            'classes':      u'classfoo class&bar',
            'title':        u'<h3>TEH TITLE</h3>',
            'frames':       u'<pre>Frame1</pre><pre>Frame2</pre>',
        }
        html = render(
            'pyramid_debugtoolbar:templates/exception_summary.jinja2',
            vars, request=request)
        self.assert_(u'<div class="classfoo class&amp;bar">' in html, html)
        self.assert_(u'<h3>TEH TITLE</h3>' in html, html)
        self.assert_(u'<pre>Frame1</pre><pre>Frame2</pre>' in html, html)


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
