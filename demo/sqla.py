from pyramid.view import view_config

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.pool import StaticPool

meta = MetaData()

users_table = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)

def initialize_sql(settings):
    engine = create_engine('sqlite://',
            connect_args={'check_same_thread':False},
            poolclass=StaticPool,
            echo=True)
    settings['engine'] = engine

    try:
        populate_db(engine)
    except:
        pass

def populate_db(engine):
    meta.create_all(bind=engine)

    users = ('blaflamme', 'mcdonc', 'mmerickel')
    try:
        for i, user in enumerate(users):
            engine.execute('insert into users (id, name) values (:id, :name)',
                    id=i, name=user)
    except:
        pass

@view_config(route_name='test_sqla', renderer='__main__:templates/sqla.mako')
def test_sqla(request):
    engine = request.registry.settings['engine']
    users = engine.execute('select * from users')
    return {
        'title':'Test SQLAlchemy logging',
        'users':users,
    }

def includeme(config):
    settings = config.registry.settings
    initialize_sql(settings)

    config.add_route('test_sqla', '/test_sqla')
    config.scan(__name__)
