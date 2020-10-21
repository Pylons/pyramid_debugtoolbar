from pyramid import testing
from pyramid.config import Configurator
from pyramid.response import Response
import unittest
import webtest

HTML = """
<html>
<head><title>Hello from Pyramid</title></head>
<body>Hello %(name)s!</body>
</html>
"""


def app_view(request):
    return Response(
        HTML % request.matchdict,
        content_type='text/html',
    )


def auth_check(request):
    return request.remote_user == 'admin'


def make_app():
    config = Configurator()
    config.include('pyramid_debugtoolbar')
    config.set_debugtoolbar_request_authorization(auth_check)
    config.add_route('hello', '/hello/{name}')
    config.add_view(app_view, route_name='hello')
    app = config.make_wsgi_app()
    return app


class Test_auth(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.testapp = webtest.TestApp(make_app())

    def _req(self, url, remote_user=None, **kw):
        environ = {'REMOTE_ADDR': '127.0.0.1'}
        if remote_user:
            environ['REMOTE_USER'] = remote_user
        resp = self.testapp.get(url, extra_environ=environ, **kw)
        return resp

    def test_unauthenticated(self):
        resp = self._req('/hello/pyramid')
        self.assertEqual(resp.content_type, 'text/html')
        self.assertEqual(resp.html.body.string, 'Hello pyramid!')
        # Python 2.6 doesn't include assertIsNone or other useful asserts. Sigh.
        self.assertTrue(resp.html.body.script is None)
        self.assertTrue(resp.html.body.div is None)

    def test_authenticated_toolbar_injection(self):
        resp = self._req('/hello/secrets', remote_user='admin')
        self.assertTrue(resp.html.body.link is not None, 'unexpectedly None')
        # dive into the request history stored by the toolbar tween
        request_id = self.testapp.app.registry.pdtb_history[0][0]
        # check it against the link in the injected html
        self.assertTrue(request_id in resp.html.body.div.div.a['href'])

    def test_authenticated_toolbar_views(self):
        resp = self._req('/hello/rumors', remote_user='admin')
        new_url = resp.html.body.div.div.a['href']
        resp = self._req(new_url, remote_user='admin')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.html.head.title.string, 'Pyramid Debug Toolbar')

    def test_unauthenticated_toolbar_views(self):
        resp = self._req('/hello/protected', remote_user='admin')
        new_url = resp.html.body.div.div.a['href']
        resp = self._req(new_url, remote_user=None, status=404)
        self.assertTrue(b'404 Not Found' in resp.body)
