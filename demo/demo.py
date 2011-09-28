import os
import logging

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from wsgiref.simple_server import make_server

try:
    import sqlalchemy
except ImportError: # pragma: no cover
    sqlalchemy = None

logging.basicConfig()
log = logging.getLogger(__file__)

here = os.path.dirname(os.path.abspath(__file__))

@view_config(route_name='test_exc')
def exc(request):
    raise NotImplementedError

@view_config(route_name='test_notfound')
def notfound(request):
    raise HTTPNotFound()

@view_config(context=HTTPNotFound, renderer='notfound.mako')
def notfound_view(request):
    return {}

@view_config(route_name='test_page', renderer='index.mako')
def test_page(request):
    title = 'Pyramid Debugtoolbar'
    log.info(title)
    return {'title': title, 'show_sqla_link': bool(sqlalchemy)}

@view_config(route_name='test_redirect')
def test_redirect(request):
    return HTTPFound(location=request.route_url('test_page'))

@view_config(route_name='test_predicates', renderer='index.mako')
def test_predicates(request):
    return {'title':'Test route predicates'}

@view_config(route_name='test_chameleon_exc',
             renderer='__main__:templates/error.pt')
@view_config(route_name='test_mako_exc', renderer='error.mako')
@view_config(route_name='test_jinja2_exc',
             renderer='__main__:templates/error.jinja2')
def test_template_exc(request):
    return {'title':'Test template exceptions'}

if __name__ == '__main__':
    # configuration settings
    settings = {}
    settings['debug_templates'] = True
    settings['reload_templates'] = True
    settings['mako.directories'] = os.path.join(here, 'templates')
    settings['mako.module_directory'] = os.path.join(here, 'mako_modules')
    settings['debugtoolbar.hosts'] = ['127.0.0.1', '192.168.1.147']
    #settings['mako.strict_undefined'] = True
    # session factory
    session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    # configuration setup
    config = Configurator(settings=settings, session_factory=session_factory)
    # routes setup
    config.add_route('test_page', '/')
    config.add_route('test_redirect', '/redirect')
    config.add_route('test_predicates', '/predicates', request_method='GET')
    config.add_route('test_exc', '/exc')
    config.add_route('test_notfound', '/notfound')
    config.add_route('test_chameleon_exc', '/chameleon_exc')
    config.add_route('test_mako_exc', '/mako_exc')
    config.add_route('test_jinja2_exc', '/jinja2_exc')
    config.scan('__main__')
    if sqlalchemy:
        config.include('sqla')
    config.include('pyramid_debugtoolbar')
    httpd = make_server('', 8080, config.make_wsgi_app())
    httpd.serve_forever()
