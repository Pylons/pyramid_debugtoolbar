import markupsafe
from pprint import saferepr
from pyramid.request import Request
from urllib.parse import urlencode

from ._utils import _TestDebugtoolbarPanel

PARTY_HAT_UNICODE = "\U0001f389"
PARTY_HAT_UTF8 = PARTY_HAT_UNICODE.encode("utf-8")


def templated_escaped(input, expect_saferepr=None):
    """
    `expect_saferepr`: the panel applies additional escaping to POST items

    Took a while to backtrack the mako/pyramid_mako escaping...

    saferepr(str(markupsafe.escape(PARTY_HAT_UNICODE)))
    > "u'\\U0001f389'"

    str(saferepr(PARTY_HAT_UNICODE))
    > u"u'\\U0001f389'"

    markupsafe.escape(saferepr(PARTY_HAT_UNICODE))
    > Markup(u'u&#39;\\U0001f389&#39;')

    str(markupsafe.escape(saferepr(PARTY_HAT_UNICODE)))
    u'u&#39;\\U0001f389&#39;'
    """
    input = str(input)
    if expect_saferepr:
        input = saferepr(input)
    return str(markupsafe.escape(input))


class _TestPanel_RequestVars(_TestDebugtoolbarPanel):
    def _makeOne(self, query_args=None, post_body=None, content_type=None):
        # make a request
        query_args = ("?=%s" % urlencode(query_args)) if query_args else ""
        kwargs = {}
        if content_type:
            kwargs["content_type"] = content_type
        req1 = Request.blank("/%s" % query_args, POST=post_body, **kwargs)
        req1.remote_addr = "127.0.0.1"
        resp1 = req1.get_response(self.app)
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
        resp2 = req2.get_response(self.app)
        self.assertEqual(resp2.status_code, 200)

        self.assertIn(
            '<li class="" id="pDebugPanel-request_vars">', resp2.text
        )
        self.assertIn(
            '<div id="pDebugPanel-request_vars-content" class="panelContent"'
            ' style="display: none;">',
            resp2.text,
        )

        return resp2


class TestPanel_RequestVars_Simple(_TestPanel_RequestVars):
    def test_panel_injected(self):
        # no need to do anything else!
        resp = self._makeOne()  # noqa

    def test_query_args(self):
        query_args = {
            "foo": "bar",
        }
        resp = self._makeOne(query_args=query_args)
        self.assertIn("<td>foo=bar</td>", resp.text)

    def test_post_body(self):
        post_body = "bar=foo"
        resp = self._makeOne(post_body=post_body)
        self.assertIn("<td>&#39;bar&#39;</td>", resp.text)
        self.assertIn("<td>&#39;foo&#39;</td>", resp.text)

    def test_post_body_json(self):
        post_body = '{"foo": "bar"}'
        resp = self._makeOne(
            post_body=post_body, content_type="application/jose+json"
        )
        # we should see 'preview bytes'
        self.assertIn("<p>No POST variables</p>", resp.text)
        self.assertIn(
            templated_escaped(post_body, expect_saferepr=False), resp.text
        )

    def test_post_body_json__wrong_form(self):
        # send this in without a content-header
        # which webob(outgoing) will submit as a form
        # then webob(incoming) will interpret as a kv pair, without a v
        post_body = '{"foo": "bar"}'
        resp = self._makeOne(post_body=post_body)
        self.assertIn(
            "<td>%s</td>" % templated_escaped(post_body, expect_saferepr=True),
            resp.text,
        )
        self.assertIn("<td>&#39;&#39;</td>", resp.text)

    def test_query_args_post_body(self):
        query_args = {
            "foo": "bar",
        }
        post_body = "bar=foo"
        resp = self._makeOne(query_args=query_args, post_body=post_body)
        self.assertIn("<td>foo=bar</td>", resp.text)
        self.assertIn("<td>&#39;bar&#39;</td>", resp.text)
        self.assertIn("<td>&#39;foo&#39;</td>", resp.text)


class TestPanel_RequestVars_Unicode(_TestPanel_RequestVars):
    def test_query_args(self):
        query_args = {
            "party_hat": PARTY_HAT_UTF8,
        }
        resp = self._makeOne(query_args=query_args)
        self.assertIn("<td>party_hat=%s</td>" % PARTY_HAT_UNICODE, resp.text)

    def test_query_args_inverse(self):
        query_args = {PARTY_HAT_UTF8: "party_hat"}
        resp = self._makeOne(query_args=query_args)
        self.assertIn("<td>%s=party_hat</td>" % PARTY_HAT_UNICODE, resp.text)

    def test_post_body(self):
        post_body = "party_hat=%s" % PARTY_HAT_UTF8
        resp = self._makeOne(post_body=post_body)
        self.assertIn("<td>&#39;party_hat&#39;</td>", resp.text)
        self.assertIn(
            "<td>%s</td>"
            % templated_escaped(PARTY_HAT_UTF8, expect_saferepr=True),
            resp.text,
        )

    def test_post_body_json(self):
        post_body = '{"foo": "%s"}' % PARTY_HAT_UTF8
        resp = self._makeOne(
            post_body=post_body, content_type="application/jose+json"
        )
        # we should see 'preview bytes'
        self.assertIn("<p>No POST variables</p>", resp.text)
        self.assertIn(
            templated_escaped(post_body, expect_saferepr=False), resp.text
        )

    def test_post_body_json__wrong_form(self):
        # send this in without a content-header
        # which webob(outgoing) will submit as a form
        # then webob(incoming) will interpret as a kv pair, without a v
        post_body = '{"foo": %s}' % PARTY_HAT_UTF8
        resp = self._makeOne(post_body=post_body)
        self.assertIn(
            "<td>%s</td>" % templated_escaped(post_body, expect_saferepr=True),
            resp.text,
        )
        self.assertIn("<td>&#39;&#39;</td>", resp.text)
