"""Unittests for DebugPanels."""

import unittest

from pyramid_debugtoolbar.compat import PY3, text_type
from pyramid import testing


class TestVersionDebugPanel(unittest.TestCase):

    def _make_one(self):
        from pyramid_debugtoolbar.panels.versions import VersionDebugPanel
        request = testing.DummyRequest()
        return VersionDebugPanel(request)

    def test_it_with_nonascii_platform_name(self):
        panel = self._make_one()
        test_string = b'Schr\xc3\xb6dinger\xe2\x80\x99s_Cat'
        if PY3:
            # it's unicode string in py3
            test_string = test_string.decode('utf8')

        panel._get_platform_name = lambda: test_string

        platform = panel.properties['platform']
        self.assertTrue(isinstance(platform, text_type))
