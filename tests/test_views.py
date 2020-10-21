from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
import unittest

from pyramid_debugtoolbar.compat import bytes_, text_


class TestExceptionDebugView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.registry.settings['mako.directories'] = []
        self.config.registry.parent_registry = self.config.registry
        self.config.registry.parent_registry.pdtb_eval_exc = True
        self.config.registry.pdtb_token = 'token'
        self.config.include('pyramid_mako')
        self.config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, request):
        from pyramid_debugtoolbar.panels.traceback import ExceptionDebugView

        return ExceptionDebugView(request)

    def _makeRequest(self):
        from pyramid_debugtoolbar.utils import ToolbarStorage

        request = testing.DummyRequest()
        request.matchdict['request_id'] = 'reqid'
        request.matchdict['frame_id'] = '0'

        toolbar = DummyToolbar()
        toolbar.traceback = self._makeTraceback('tbid')

        history = ToolbarStorage(10)
        history.put('reqid', toolbar)
        request.pdtb_history = history
        return request

    def _makeTraceback(self, tbid, frames=None):
        if frames is None:
            frm = DummyFrame('0')
            frames = [frm]
        return DummyTraceback(tbid, frames)

    def test_exception_with_no_traceback(self):
        request = self._makeRequest()
        del request.pdtb_history.last(1)[0][1].traceback
        view = self._makeOne(request)
        self.assertRaises(HTTPBadRequest, view.exception)

    def test_source(self):
        request = self._makeRequest()
        view = self._makeOne(request)
        response = view.source()
        self.assertEqual(response.body, bytes_('source'))
        self.assertEqual(response.content_type, 'text/html')

    def test_source_frame_not_found(self):
        request = self._makeRequest()
        request.matchdict['frame_id'] = 'missing'
        view = self._makeOne(request)
        self.assertRaises(HTTPBadRequest, view.source)

    def test_execute(self):
        request = self._makeRequest()
        request.params['cmd'] = 'doit'
        view = self._makeOne(request)
        response = view.execute()
        self.assertEqual(response.body, bytes_('evaled'))
        self.assertEqual(response.content_type, 'text/html')

    def test_execute_cmd_is_None(self):
        request = self._makeRequest()
        view = self._makeOne(request)
        self.assertRaises(HTTPBadRequest, view.execute)

    def test_execute_nosuchframe(self):
        request = self._makeRequest()
        request.matchdict['frame_id'] = 'missing'
        request.params['cmd'] = 'doit'
        view = self._makeOne(request)
        self.assertRaises(HTTPBadRequest, view.execute)

    def test_execute_disabled(self):
        request = self._makeRequest()
        request.registry.parent_registry.pdtb_eval_exc = False
        request.params['cmd'] = 'doit'
        view = self._makeOne(request)
        self.assertRaises(HTTPBadRequest, view.execute)

    def test_exception_summary(self):
        from pyramid.renderers import render

        request = self._makeRequest()
        request.static_url = lambda *arg, **kw: 'http://static'
        vars = {
            'classes': text_('classfoo class&bar'),
            'title': text_('<h3>TEH TITLE</h3>'),
            'frames': text_('<pre>Frame1</pre><pre>Frame2</pre>'),
        }
        html = render(
            'pyramid_debugtoolbar:templates/exception_summary.dbtmako',
            vars,
            request=request,
        )
        self.assertTrue(
            text_('<div class="classfoo class&amp;bar">') in html, html
        )
        self.assertTrue(text_('<h3>TEH TITLE</h3>') in html, html)
        self.assertTrue(
            text_('<pre>Frame1</pre><pre>Frame2</pre>') in html, html
        )


class DummyToolbar(object):
    pass


class DummyTraceback(object):
    def __init__(self, id, frames):
        self.id = id
        self.frames = frames


class DummyConsole(object):
    def eval(self, cmd):
        return 'evaled'


class DummyFrame(object):
    def __init__(self, id):
        self.console = DummyConsole()
        self.id = id

    def render_source(self):
        return 'source'
