from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response
from paste.httpserver import serve

@view_config(route_name='test_page')
def test_page(request):
    return Response('<body>Hello World</body>', content_type='text/html')

if __name__ == '__main__':
    settings = {'debugtoolbar.secret_key': 'abc'}
    config = Configurator(settings=settings)
    config.add_route('test_page', '/')
    config.scan('__main__')
    config.include('pyramid_debugtoolbar')
    serve(config.make_wsgi_app())
