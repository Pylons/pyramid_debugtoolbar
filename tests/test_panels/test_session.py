from pyramid import testing
from pyramid.request import Request

try:
    from pyramid.session import SignedCookieSessionFactory as Sessn
except ImportError:
    # pyramid_debugtoolbar supports Pyramid==1.4
    from pyramid.session import UnencryptedCookieSessionFactoryConfig as Sessn

import random
import unittest

from pyramid_debugtoolbar.compat import PY3

from ._utils import (
    _TestDebugtoolbarPanel,
    ok_response_factory,
    re_toolbar_link,
)

my_session_factory = Sessn('itsaseekreet')


class _TestSessionPanel(_TestDebugtoolbarPanel):
    """
    Base class for testing SQLAlchemy panel
    """

    config = None
    app = None

    def _session_view(self, context, request):
        """
        This function should define a Pyramid view
        * (potentially) invoke SQLAlchemy
        * return a Response
        """
        raise NotImplementedError()

    def setUp(self):
        self.config = config = testing.setUp()
        config.include("pyramid_debugtoolbar")
        config.set_session_factory(my_session_factory)
        config.add_view(self._session_view)
        self.app = config.make_wsgi_app()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self):
        """
        Makes a request to the main App
        * which invokes `self._session_view`
        * Make a request to the toolbar
        * return the toolbar Response
        """
        # make the app
        app = self.config.make_wsgi_app()
        # make a request
        req1 = Request.blank("/")
        req1.remote_addr = "127.0.0.1"
        resp1 = req1.get_response(app)
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp1.text)

        # check the toolbar
        links = re_toolbar_link.findall(resp1.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp2 = req2.get_response(app)

        return resp2

    def _check_rendered__panel(self, resp):
        """
        Ensure the rendered panel exists with statements
        """
        self.assertIn('<li class="" id="pDebugPanel-session">', resp.text)
        self.assertIn(
            '<div id="pDebugPanel-session-content" class="panelContent" '
            'style="display: none;">',
            resp.text,
        )


class TestNone(_TestSessionPanel):
    """
    No Session changes
    """

    def _session_view(self, context, request):
        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            '<li class="disabled" id="pDebugPanel-sqlalchemy">', resp.text
        )
        self.assertNotIn(
            '<div id="pDebugPanel-sqlalchemy-content" class="panelContent" '
            'style="display: none;">',
            resp.text,
        )


class TestSimpleSession(_TestSessionPanel):
    """
    A simple session
    """

    def _session_view(self, context, request):
        request.session["foo"] = "bar"
        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self._check_rendered__panel(resp)


class TestSortingErrorsSession(_TestSessionPanel):
    """
    Previous toolbars could encounter a fatal exception from TypeError when
    trying to sort session variables. One way to raise a TypeError is trying
    to sort a float and a string under Python3.
    """

    def _session_view(self, context, request):
        rand = random.random()
        request.session[rand] = True
        request.session["foo"] = "bar"
        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self._check_rendered__panel(resp)

    @unittest.skipUnless(PY3, "PY2 doesn't care")
    def test_sorting_fatal(self):
        """
        If Python3's behavior changes, the workaround to catch `sorted()`
        TypeErrors and resort with a string conversion is no longer necessary.
        """
        with self.assertRaises(TypeError):
            session = {
                'bar': '19',
                0.11890052815887397: 'True',
                '0.8760161306863006': 'True',
            }
            session = sorted(session)
