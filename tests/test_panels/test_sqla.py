from pyramid import testing
from pyramid.request import Request
import sqlalchemy
from sqlalchemy.sql import text as sqla_text

from ._utils import _TestDebugtoolbarPanel, ok_response_factory


class _TestSQLAlchemyPanel(_TestDebugtoolbarPanel):
    """
    Base class for testing SQLAlchemy panel
    """

    config = None
    app = None

    def _sqlalchemy_view(self, context, request):
        """
        This function should define a Pyramid view
        * (potentially) invoke SQLAlchemy
        * return a Response
        """
        raise NotImplementedError()

    def setUp(self):
        self.config = config = testing.setUp()
        config.include("pyramid_debugtoolbar")
        config.add_view(self._sqlalchemy_view)
        self.app = config.make_wsgi_app()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self):
        """
        Makes a request to the main App
        * which invokes `self._sqlalchemy_view`
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
        links = self.re_toolbar_link.findall(resp1.text)
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
        self.assertIn('<li class="" id="pDebugPanel-sqlalchemy">', resp.text)
        self.assertIn(
            '<div id="pDebugPanel-sqlalchemy-content" class="panelContent" '
            'style="display: none;">',
            resp.text,
        )

    def _check_rendered__select_null(self, resp):
        """
        Ensure the rendered panel has the "SELECT NULL" statement rendered

        """
        self.assertIn(
            '<span style="color: #008800; font-weight: bold">SELECT</span>'
            '<span style="color: #bbbbbb"> </span>'
            '<span style="color: #008800; font-weight: bold">NULL</span>;',
            resp.text,
        )

    def _check_rendered__begin_rollback(self, resp):
        """
        These are rendered as comments
        """
        self.assertIn(
            '<span style="color: #888888">-- [event] begin</span>',
            resp.text,
        )
        self.assertIn(
            '<span style="color: #888888">-- [event] rollback</span>',
            resp.text,
        )

    def _check_rendered__begin_commit(self, resp):
        """
        These are rendered as comments
        """
        self.assertIn(
            '<span style="color: #888888">-- [event] begin</span>',
            resp.text,
        )
        self.assertIn(
            '<span style="color: #888888">-- [event] commit</span',
            resp.text,
        )


class TestNone(_TestSQLAlchemyPanel):
    """
    No SQLAlchemy queries
    """

    def _sqlalchemy_view(self, context, request):
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


class TestSimpleSelect(_TestSQLAlchemyPanel):
    """
    A simple SELECT
    """

    def _sqlalchemy_view(self, context, request):
        engine = sqlalchemy.create_engine("sqlite://", isolation_level=None)
        with engine.begin() as conn:
            stmt = sqla_text("SELECT NULL;")
            conn.execute(stmt)  # noqa
        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self._check_rendered__panel(resp)
        self._check_rendered__select_null(resp)


class TestTransactionCommit(_TestSQLAlchemyPanel):
    """
    A simple transaction
    """

    def _sqlalchemy_view(self, context, request):
        engine = sqlalchemy.create_engine("sqlite://", isolation_level=None)
        with engine.begin() as conn:
            stmt = sqla_text("SELECT NULL;")
            conn.execute(stmt)  # noqa
        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self._check_rendered__panel(resp)
        self._check_rendered__select_null(resp)
        self._check_rendered__begin_commit(resp)


class TestTransactionRollback(_TestSQLAlchemyPanel):
    def _sqlalchemy_view(self, context, request):
        engine = sqlalchemy.create_engine("sqlite://", isolation_level=None)
        try:
            with engine.begin() as conn:
                stmt = sqla_text("SELECT NULL;")
                conn.execute(stmt)  # noqa
                raise ValueError("EXPECTED")
        except ValueError:
            # SQLAlchemy's ContextManager will call a rollback
            pass
        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self._check_rendered__panel(resp)
        self._check_rendered__select_null(resp)
        self._check_rendered__begin_rollback(resp)


class TestTransactionComplex(_TestSQLAlchemyPanel):
    def _sqlalchemy_view(self, context, request):
        """
        Test to ensure the following listeners do not raise Exceptions:
        [+] begin
        [+] commit
        [+] rollback
        [+] savepoint
        [+] rollback_savepoint
        [+] release_savepoint
        [+] begin_twophase
        [ ] prepare_twophase
        [ ] commit_twophase
        [ ] rollback_twophase
        """

        engine = sqlalchemy.create_engine("sqlite://", isolation_level=None)
        conn = engine.connect()

        # tests: `begin`, `commit`
        t1 = conn.begin()  # `begin`
        conn.execute(sqla_text("SELECT NULL; -- a"))
        t1.commit()  # `commit`

        # tests: `begin`, `rollback`
        t1 = conn.begin()  # `begin`
        conn.execute(sqla_text("SELECT NULL; -- b"))
        t1.rollback()  # `rollback`

        # tests: `begin`, `savepoint`, `rollback_savepoint`, `release_savepoint`
        t1 = conn.begin()  # `begin`
        conn.execute(sqla_text("SELECT NULL; -- c1"))
        t2 = conn.begin_nested()  # `savepoint`
        conn.execute(sqla_text("SELECT NULL; -- c2"))
        t2.rollback()  # `rollback_savepoint`
        t2 = conn.begin_nested()  # `savepoint`
        conn.execute(sqla_text("SELECT NULL; -- c3"))
        t2.commit()  # `release_savepoint`
        conn.execute(sqla_text("SELECT NULL; -- c4"))
        t1.commit()  # commit

        # tests: `begin_twophase`
        try:
            conn.begin_twophase()  # `begin_twophase`
        except NotImplementedError:
            pass

        # untested: `prepare_twophase`, `commit_twophase`, `rollback_twophase`

        return ok_response_factory()

    def test_panel(self):
        resp = self._makeOne()
        self.assertEqual(resp.status_code, 200)
        self._check_rendered__panel(resp)
