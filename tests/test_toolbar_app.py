import unittest
from pyramid import testing
from pyramid.request import Request


class TestToolbarApp(unittest.TestCase):
    def setUp(self):
        from pyramid_debugtoolbar.utils import ToolbarStorage
        self.config = testing.setUp()
        self.config.registry.pdtb_history = ToolbarStorage(1)

    def tearDown(self):
        testing.tearDown()
        
    def _get_response(self, host, domains_setting=None):
        from pyramid_debugtoolbar import default_app_domains
        from pyramid_debugtoolbar.toolbar_app import make_toolbar_app
        from pyramid_debugtoolbar.utils import SETTINGS_PREFIX
        if domains_setting is None:
            domains_setting = default_app_domains
        settings = {SETTINGS_PREFIX + 'app_domains': domains_setting}
        request = Request.blank('/')
        request.host = host
        request.registry = self.config.registry
        app = make_toolbar_app(settings, self.config.registry)
        return request.get_response(app)
    
    def _check_hosts_response(self, hosts, provided=None, status_code=200):
        for host in hosts:
            for header in (host, host + ':6543'):
                response = self._get_response(header, provided)
                self.assertEqual(response.status_code, status_code)
    
    def test_localhost_works_by_default(self):
        self._check_hosts_response(('localhost',))
    
    def test_provided_app_domains_work(self):
        provided_domains = ('foo.bar123', 'bar123.f.o.o')
        self._check_hosts_response(provided_domains, provided_domains)
    
    def test_ipv4_works(self):
        self._check_hosts_response(('192.168.0.1', '127.0.0.1'))
    
    def test_ipv6_works(self):
        self._check_hosts_response(('[2001:db8:85a3::8a2e:370:7334]', '[::1]'))
    
    def test_invalid_ipv4_returns_404(self):
        self._check_hosts_response(
            ('192.168.0.01', '10.10.256.3', '10a.1.1.7'),
            status_code=404,
        )

    def test_not_included_domain_returns_404(self):
        self._check_hosts_response(('attackingdomain',), status_code=404)
