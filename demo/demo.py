# -*- coding: utf-8 -*-

import os
import sys
import logging
import shutil

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

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
    binary_type = bytes
else:
    binary_type = str

def text_(s, encoding='latin-1', errors='strict'):
    """ If ``s`` is an instance of ``binary_type``, return
    ``s.decode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s # pragma: no cover

logging.basicConfig(level=logging.NOTSET)
log = logging.getLogger(__file__)

here = os.path.dirname(os.path.abspath(__file__))

@view_config(route_name='test_exc')
def exc(request):
    raise NotImplementedError

@view_config(route_name='test_notfound')
def notfound(request):
    raise HTTPNotFound()

@view_config(route_name='test_ajax', renderer='__main__:templates/ajax.mako')
def test_ajax(request):
    return {}

@view_config(route_name='call_ajax', renderer='json')
def call_ajax(request):
    return {'ajax':'success'}

@view_config(context=HTTPNotFound, renderer='__main__:templates/notfound.mako')
def notfound_view(request):
    request.response.status_code = 404
    return {}

@view_config(renderer='__main__:templates/index.mako') # found via traversal
def test_page(request):
    title = 'Pyramid Debugtoolbar'
    log.info(title)
    return {
        'title': title,
        'show_jinja2_link': True,
        'show_sqla_link': bool(sqlalchemy)}

@view_config(route_name='test_redirect')
def test_redirect(request):
    return HTTPFound(location='/')

@view_config(route_name='test_highorder',
             renderer='__main__:templates/highorder.mako')
def test_highorder(request):
    return {}

@view_config(route_name='test_predicates',
             renderer='__main__:templates/index.mako')
def test_predicates(request):
    return {'title': 'Test route predicates'}

@view_config(route_name='test_chameleon_exc',
             renderer='__main__:templates/error.pt')
@view_config(route_name='test_mako_exc',
             renderer='__main__:templates/error.mako')
@view_config(route_name='test_jinja2_exc',
             renderer='__main__:templates/error.jinja2')
def test_template_exc(request):
    return {'title': 'Test template exceptions'}

class DummyRootFactory(object):
    def __init__(self, request):
        self.request = request
    def __getitem__(self, name):
        return self

if __name__ == '__main__':
    # configuration settings
    try:
        # ease testing py2 and py3 in same directory
        shutil.rmtree(os.path.join(here, 'mako_modules'))
    except:
        pass
    settings = {}
    settings['reload_templates'] = True
    settings['mako.directories'] = '__main__:templates'
    settings['mako.module_directory'] = '__main__:mako_modules'
    settings['debugtoolbar.reload_templates'] = True
    settings['debugtoolbar.hosts'] = ['127.0.0.1']
    settings['debugtoolbar.intercept_redirects'] = True
    settings['debugtoolbar.exclude_prefixes'] = ['/static']

    # session factory
    session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    # configuration setup
    config = Configurator(settings=settings, session_factory=session_factory,
                          root_factory=DummyRootFactory)
    # static view
    config.add_static_view('static', os.path.join(here, 'static'))
    # routes setup
    config.add_route('test_redirect', '/redirect')
    config.add_route('test_predicates', '/predicates', request_method='GET')
    config.add_route('test_exc', '/exc')
    config.add_route('test_notfound', '/notfound')
    config.add_route('test_chameleon_exc', '/chameleon_exc')
    config.add_route('test_mako_exc', '/mako_exc')
    config.add_route('test_jinja2_exc', '/jinja2_exc')
    config.add_route('test_highorder', text_(b'/La Pe\xc3\xb1a', 'utf-8'))
    config.add_route('test_ajax', '/ajax')
    config.add_route('call_ajax', '/call_ajax')
    config.scan('__main__')
    config.include('pyramid_chameleon')
    config.include('pyramid_jinja2')
    config.include('pyramid_mako')

    if sqlalchemy:
        config.include('sqla')
    config.include('pyramid_debugtoolbar')
    app = config.make_wsgi_app()
    httpd = make_server('', 8080, app)
    httpd.serve_forever()
