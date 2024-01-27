from pyramid import testing
from pyramid.response import Response
import re
import unittest

# used to ensure the toolbar link is injected into requests
# copy it onto the testcase object, but keep it global if needed otherwise
re_toolbar_link = re.compile(
    r'(?:href="http://localhost)(/_debug_toolbar/[\d]+)"'
)


def ok_response_factory():
    return Response(
        "<html><head></head><body>OK</body></html>",
        content_type="text/html",
    )


class _TestDebugtoolbarPanel(unittest.TestCase):
    re_toolbar_link = re_toolbar_link

    def setUp(self):
        self.config = config = testing.setUp()
        config.include("pyramid_debugtoolbar")
        self.settings = config.registry.settings

        # create a view
        def empty_view(request):
            return ok_response_factory()

        config.add_view(empty_view)
        self.app = self.config.make_wsgi_app()

    def tearDown(self):
        testing.tearDown()
