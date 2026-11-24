from pyramid import testing
import sys
import unittest


def _raise_with_info(info):
    __traceback_info__ = info  # noqa: F841
    raise ValueError('boom')


class Test_traceback_info(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mako')
        self.config.add_mako_renderer('.dbtmako', settings_prefix='dbtmako.')

    def tearDown(self):
        testing.tearDown()

    def _get_traceback(self, info):
        from pyramid_debugtoolbar.tbtools import get_traceback

        try:
            _raise_with_info(info)
        except ValueError:
            return get_traceback(sys.exc_info())

    def _get_frame(self, tb):
        return [f for f in tb.frames if f.function_name == '_raise_with_info'][
            0
        ]

    def test_no_info(self):
        tb = self._get_traceback(None)
        self.assertIsNone(self._get_frame(tb).info)
        self.assertNotIn('title=', tb.render_summary())

    def test_str_info(self):
        tb = self._get_traceback('some info')
        self.assertEqual(self._get_frame(tb).info, 'some info')
        self.assertIn('<li title="some info">', tb.render_summary())

    def test_bytes_info(self):
        tb = self._get_traceback(b'caf\xc3\xa9 \xff')
        self.assertEqual(self._get_frame(tb).info, 'caf\xe9 �')
        self.assertIn('<li title="caf\xe9 �">', tb.render_summary())

    def test_non_string_info(self):
        tb = self._get_traceback({'key': 1})
        self.assertEqual(self._get_frame(tb).info, {'key': 1})
        self.assertIn("<li title=\"{'key': 1}\">", tb.render_summary())

    def test_falsy_info(self):
        tb = self._get_traceback(0)
        self.assertIn('<li title="0">', tb.render_summary())

    def test_info_is_escaped_in_title(self):
        tb = self._get_traceback('a" onmouseover="alert(1)" <b>')
        html = tb.render_summary()
        self.assertIn(
            '<li title="a&quot; onmouseover=&quot;alert(1)&quot; &lt;b&gt;">',
            html,
        )
        self.assertNotIn('onmouseover="', html)
