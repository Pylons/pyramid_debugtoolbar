import unittest
import os

from pyramid_debugtoolbar.compat import bytes_
from pyramid_debugtoolbar.compat import text_


class Test_escape(unittest.TestCase):
    def test_escape(self):
        from pyramid_debugtoolbar.utils import escape
        class Foo(str):
            def __html__(self):
                return text_(self)
        assert escape(None) == ''
        assert escape(42) == '42'
        assert escape('<>') == '&lt;&gt;'
        assert escape('"foo"') == '"foo"'
        assert escape('"foo"', True) == '&quot;foo&quot;'
        assert escape(Foo('<foo>')) == '<foo>'


class Test_format_fname(unittest.TestCase):
    def _callFUT(self, value, sys_path=None):
        from pyramid_debugtoolbar.utils import format_fname
        return format_fname(value, sys_path)

    def test_builtin(self):
        self.assertEqual(self._callFUT('{a}'), '{a}')

    def test_relpath(self):
        val = '.' + os.path.sep + 'foo'
        self.assertEqual(self._callFUT(val), val)

    def test_unknown(self):
        val = '..' + os.path.sep + 'foo'
        self.assertEqual(self._callFUT(val), './../foo')

    def test_module_file_path(self):
        sys_path = [
            '/foo/',
            '/foo/bar',
            '/usr/local/python/site-packages/',
        ]
        modpath = self._callFUT(
            '/foo/bar/pyramid_debugtoolbar/tests/debugfoo.py', sys_path)
        self.assertEqual(modpath, 
            '<pyramid_debugtoolbar/tests/debugfoo.py>')

    def test_no_matching_sys_path(self):
        val = '/foo/bar/pyramid_debugtoolbar/foo.py'
        sys_path = ['/bar/baz']
        self.assertEqual(self._callFUT(val, sys_path),
            '</foo/bar/pyramid_debugtoolbar/foo.py>')


class Test_format_sql(unittest.TestCase):
    def _callFUT(self, query):
        from pyramid_debugtoolbar.utils import format_sql
        return format_sql(query)

    def test_it(self):
        result = self._callFUT('SELECT * FROM TBL')
        self.assertTrue(result.startswith('<div'))
