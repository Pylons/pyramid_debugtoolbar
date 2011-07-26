import unittest
import os

class Test_escape(unittest.TestCase):
    def test_escape(self):
        from pyramid_debugtoolbar.utils import escape
        class Foo(str):
            def __html__(self):
                return unicode(self)
        assert escape(None) == ''
        assert escape(42) == '42'
        assert escape('<>') == '&lt;&gt;'
        assert escape('"foo"') == '"foo"'
        assert escape('"foo"', True) == '&quot;foo&quot;'
        assert escape(Foo('<foo>')) == '<foo>'


class Test_format_fname(unittest.TestCase):
    def _callFUT(self, value):
        from pyramid_debugtoolbar.utils import format_fname
        return format_fname(value)

    def test_builtin(self):
        self.assertEqual(self._callFUT('{a}'), '{a}')

    def test_relpath(self):
        val = '.' + os.path.sep + 'foo'
        self.assertEqual(self._callFUT(val), val)

    def test_unknown(self):
        val = '..' + os.path.sep + 'foo'
        self.assertEqual(self._callFUT(val), './../foo')

    def test_here(self):
        val = __file__
        self.assertTrue(self._callFUT(val).startswith(
            '<pyramid_debugtoolbar/tests/test_utils.py'))

