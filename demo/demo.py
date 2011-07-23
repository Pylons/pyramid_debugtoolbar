import os
import logging

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from paste.httpserver import serve
import sqlite3

logging.basicConfig()
log = logging.getLogger(__file__)

here = os.path.dirname(os.path.abspath(__file__))


@view_config(route_name='test_page', renderer='index.mako')
def test_page(request):
    title = 'Pyramid Debugtoolbar'
    log.info(title)
    return {'title': title}

@view_config(route_name='test_redirect')
def test_redirect(request):
    return HTTPFound(location=request.route_url('test_page'))


if __name__ == '__main__':
    settings = {'debugtoolbar.secret_key': 'abc'}
    config = Configurator(settings=settings)
    
    # configuration settings
    settings = {}
    settings['debugtoolbar.secret_key'] = 'abc'
    settings['mako.directories'] = os.path.join(here, 'templates')
    settings['db'] = os.path.join(here, 'tasks.db')
    # session factory
    session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    # configuration setup
    config = Configurator(settings=settings, session_factory=session_factory)
    # routes setup
    config.add_route('test_page', '/')
    config.add_route('test_redirect', '/redirect')
    config.scan('__main__')
    config.include('pyramid_debugtoolbar')
    serve(config.make_wsgi_app())
