import logging

from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from paste.httpserver import serve

log = logging.getLogger(__name__)

@view_config(route_name='test_page')
def test_page(request):
    request.session['a'] = 1
    request.session['b'] = 2
    log.info('Hello World')
    return Response('<body>Hello World</body>', content_type='text/html')

if __name__ == '__main__':
    session_factory = UnencryptedCookieSessionFactoryConfig('see1jksj')
    settings = {'debugtoolbar.secret_key': 'abc'}
    config = Configurator(settings=settings, session_factory=session_factory)
    config.add_route('test_page', '/')
    config.scan('__main__')
    config.include('pyramid_debugtoolbar')
    serve(config.make_wsgi_app())
