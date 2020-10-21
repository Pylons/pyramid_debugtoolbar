import os
import unittest

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
        self.assertEqual(
            self._callFUT(val), './../foo'.replace('/', os.path.sep)
        )

    def test_module_file_path(self):
        sys_path = [
            '/foo/',
            '/foo/bar',
            '/usr/local/python/site-packages/',
        ]

        sys_path = map(lambda path: path.replace('/', os.path.sep), sys_path)
        modpath = self._callFUT(
            '/foo/bar/pyramid_debugtoolbar/tests/debugfoo.py'.replace(
                '/', os.path.sep
            ),
            sys_path,
        )
        self.assertEqual(
            modpath,
            '<pyramid_debugtoolbar/tests/debugfoo.py>'.replace(
                '/', os.path.sep
            ),
        )

    def test_no_matching_sys_path(self):
        val = '/foo/bar/pyramid_debugtoolbar/foo.py'
        sys_path = ['/bar/baz']
        self.assertEqual(
            self._callFUT(val, sys_path),
            '</foo/bar/pyramid_debugtoolbar/foo.py>',
        )


class Test_format_sql(unittest.TestCase):
    def _callFUT(self, query):
        from pyramid_debugtoolbar.utils import format_sql

        return format_sql(query)

    def test_it(self):
        result = self._callFUT('SELECT * FROM TBL')
        self.assertTrue(result.startswith('<div'))


class Test_addr_in(unittest.TestCase):
    def _callFUT(self, addr, hosts):
        from pyramid_debugtoolbar.utils import addr_in

        return addr_in(addr, hosts)

    def test_empty_hosts(self):
        self.assertFalse(self._callFUT('127.0.0.1', []))

    def test_not_in(self):
        self.assertFalse(self._callFUT('127.0.0.1', ['192.168.1.1']))

    def test_in(self):
        self.assertTrue(self._callFUT('127.0.0.1', ['127.0.0.1']))

    def test_in_multi(self):
        self.assertTrue(self._callFUT('127.0.0.1', ['10.1.1.1', '127.0.0.1']))

    def test_in_network(self):
        self.assertTrue(self._callFUT('127.0.0.1', ['127.0.0.0/24']))

    def test_empty_hosts_ipv6(self):
        self.assertFalse(self._callFUT('::1', []))

    def test_in_ipv6(self):
        self.assertTrue(self._callFUT('::1', ['::1']))

    def test_in_multi_ipv6(self):
        self.assertTrue(self._callFUT('::1', ['fc00::', '::1']))

    def test_in_network_ipv6(self):
        self.assertTrue(self._callFUT('::1', ['::1/128']))

    def test_in_network_ipv6_interface(self):
        self.assertTrue(
            self._callFUT('fe80::e556:2a1a:91e2:7023%15', ['::/0'])
        )
