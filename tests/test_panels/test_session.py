from pyramid import testing
from pyramid.request import Request

try:
    from pyramid.session import SignedCookieSessionFactory as Sessn
except ImportError:
    # pyramid_debugtoolbar supports Pyramid==1.4
    from pyramid.session import UnencryptedCookieSessionFactoryConfig as Sessn

import random
import webob.cookies

from ._utils import _TestDebugtoolbarPanel, ok_response_factory

my_session_factory = Sessn('itsaseekreet')


class _TestSessionPanel(_TestDebugtoolbarPanel):
    """
    Base class for testing "Session" panel
    """

    config = None
    app = None
    enable_sessions = True

    def _session_view(self, context, request):
        """
        This function should define a Pyramid view
        * (potentially) invoke ``ISession``
        * return a ``Response``
        """
        raise NotImplementedError()

    def _session_view_two(self, context, request):
        """
        This function should define a Pyramid view
        * (potentially) invoke ``ISession``
        * return a ``Response``
        """
        raise NotImplementedError()

    def setUp(self):
        self.config = config = testing.setUp()
        config.include("pyramid_debugtoolbar")
        if self.enable_sessions:
            config.set_session_factory(my_session_factory)
        config.add_route("session_view", "/session-view")
        config.add_route("session_view_two", "/session-view-two")
        config.add_view(self._session_view, route_name="session_view")
        config.add_view(self._session_view_two, route_name="session_view_two")
        # make the app
        self.app = config.make_wsgi_app()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, is_active=None):
        """
        Makes a request to the main application
        * which invokes `self._session_view`
        * make a request to the toolbar
        * return the toolbar ``Response``

        :param is_active:
            Default ``None``
            If ``True``, a ``pdbt_active`` cookie will be sent to activate
            additional features in the "Session" panel.
        """
        # make a request
        req1 = Request.blank("/session-view")
        req1.remote_addr = "127.0.0.1"
        _cookies = []
        if is_active:
            _cookies.append("pdtb_active=session")
        if _cookies:
            _cookies = "; ".join(_cookies)
            req1.headers["Cookie"] = _cookies
        resp_app = req1.get_response(self.app)
        self.assertEqual(resp_app.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp_app.text)

        # check the toolbar
        links = self.re_toolbar_link.findall(resp_app.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp_toolbar = req2.get_response(self.app)

        return (resp_app, resp_toolbar)

    def _makeAnother(self, resp_app, is_active=None):
        """
        Makes a second request to the main application
        * which invokes ``self._session_view_two``
        * Make a request to the toolbar
        * return the toolbar ``Response``

        :param resp_app:
            The ``Response`` object of the Pyramid application view
            returned from ``_makeOne``.
        :param is_active:
            Default ``None``
            If ``True``, a ``pdbt_active`` cookie will be sent to activate
            additional features in the "Session" panel.
        """
        # make a secondary request
        req1 = Request.blank("/session-view-two")
        req1.remote_addr = "127.0.0.1"
        _cookies = []
        if is_active:
            _cookies.append("pdtb_active=session")
        if "Set-Cookie" in resp_app.headers:
            for _set_cookie_header in resp_app.headers.getall("Set-Cookie"):
                _cks = webob.cookies.parse_cookie(_set_cookie_header)
                for _ck in _cks:
                    _cookies.append(f"{_ck[0].decode()}={_ck[1].decode()}")
        if _cookies:
            _cookies = "; ".join(_cookies)
            req1.headers["Cookie"] = _cookies
        resp_app2 = req1.get_response(self.app)
        self.assertEqual(resp_app2.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp_app2.text)

        # check the toolbar
        links = self.re_toolbar_link.findall(resp_app2.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp_toolbar = req2.get_response(self.app)

        return (resp_app2, resp_toolbar)

    def _check_rendered__panel(
        self, resp, is_configured=None, is_accessed=None
    ):
        """
        Ensure the rendered panel exists with statements.

        :param resp: a ``Response`` object with a ``.text`` attribute for html
        :param is_configured: is an ``ISessionFactory`` configured for the app?
        :param is_accessed: was ``request.session`` accessed during this view?
        """
        self.assertIn('<li class="" id="pDebugPanel-session">', resp.text)
        self.assertIn(
            '<div id="pDebugPanel-session-content" class="panelContent" '
            'style="display: none;">',
            resp.text,
        )
        if is_configured:
            self.assertIn(
                "<p>Using <code>ISessionFactory</code>: <code>", resp.text
            )
        else:
            self.assertIn(
                "<p>No <code>ISessionFactory</code> Configured</p>", resp.text
            )
        if is_accessed:
            self.assertIn(
                "<code>request.session</code> was accessed during the main "
                "<code>Request</code> handler.",
                resp.text,
            )
        else:
            self.assertIn(
                "<code>request.session</code> was not accessed during the main "
                "<code>Request</code> handler.",
                resp.text,
            )


class TestNoSessionConfigured(_TestSessionPanel):
    """
    Ensure the panel works when:
    * no "Session" panel is configured
    * no "Session" data is accessed
    """

    enable_sessions = False

    def _session_view(self, context, request):
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=False, is_accessed=False
        )


class TestSessionConfiguredNoAccess(_TestSessionPanel):
    """
    Ensure the panel works when:
    * the "Session" panel is configured
    * no "Session" data is accessed
    """

    enable_sessions = True

    def _session_view(self, context, request):
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=False
        )

    def test_panel_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=False
        )


class TestSimpleSession(_TestSessionPanel):
    """
    Ensure the panel works when:
    * the "Session" panel is configured
    * "Session" data is accessed
    """

    enable_sessions = True

    def _session_view(self, context, request):
        request.session["foo"] = "bar"
        return ok_response_factory()

    def _session_view_two(self, context, request):
        request.session["foo"] = "barbar"
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )

    def test_panel_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )

    def test_panel_twice(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(resp_app)
        self._check_rendered__panel(
            resp_toolbar2, is_configured=True, is_accessed=True
        )
        # we should see the INGRESS and EGRESS value for session["foo"]
        self.assertIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertIn("<code>'barbar'</code>", resp_toolbar2.text)

    def test_panel_twice_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(
            resp_app, is_active=True
        )
        self._check_rendered__panel(
            resp_toolbar2, is_configured=True, is_accessed=True
        )
        # we should see the INGRESS and EGRESS value for session["foo"]
        self.assertIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertIn("<code>'barbar'</code>", resp_toolbar2.text)


class TestSessionAlt(_TestSessionPanel):
    """
    Ensure the panel works when:
    * the "Session" panel is configured
    * "Session" data is accessed
    """

    enable_sessions = True

    def _session_view(self, context, request):
        # touches the session
        request.session["foo"] = "bar"
        return ok_response_factory()

    def _session_view_two(self, context, request):
        # no session interaction
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )

    def test_panel_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )

    def test_panel_twice(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(resp_app)
        self._check_rendered__panel(
            resp_toolbar2, is_configured=True, is_accessed=False
        )
        # we should NOT see the INGRESS and EGRESS value for session["foo"]
        self.assertNotIn("<code>'bar'</code>", resp_toolbar2.text)

    def test_panel_twice_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(
            resp_app, is_active=True
        )
        self._check_rendered__panel(
            resp_toolbar2, is_configured=True, is_accessed=False
        )
        # we should see the INGRESS and EGRESS value for session["foo"]
        self.assertIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertEqual(2, resp_toolbar2.text.count("<code>'bar'</code>"))


class TestSortingErrorsSession(_TestSessionPanel):
    """
    Previous toolbars could encounter a fatal exception from ``TypeError`` when
    trying to sort session variables. One way to raise a ``TypeError`` is trying
    to sort a float and a string under Python3.
    """

    enable_sessions = True

    def _session_view(self, context, request):
        rand = random.random()
        request.session[rand] = True
        request.session["foo"] = "bar"
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, is_accessed=True
        )

    def test_sorting_fatal(self):
        """
        If Python3's behavior changes, the workaround to catch ``sorted()``'s
        ``TypeError`` and re-sort with string conversion is no longer necessary.
        """
        with self.assertRaises(TypeError):
            session = {
                'bar': '19',
                0.11890052815887397: 'True',
                '0.8760161306863006': 'True',
            }
            session = sorted(session)
