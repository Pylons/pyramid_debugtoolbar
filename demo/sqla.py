from pyramid.view import view_config

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.pool import StaticPool

meta = MetaData()

users_table = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)

def initialize_sql(settings):
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread':False},
        poolclass=StaticPool,
        echo=True,
    )
    settings['engine'] = engine
    populate_db(engine)

def populate_db(engine):
    meta.create_all(bind=engine)

    with engine.connect() as conn:
        users = ('blaflamme', 'mcdonc', 'mmerickel')
        for i, user in enumerate(users):
            conn.execute(
                text('insert into users (id, name) values (:id, :name)'),
                {'id': i, 'name': user},
            )
        conn.commit()

@view_config(route_name='test_sqla', renderer='__main__:templates/sqla.mako')
def test_sqla(request):
    engine = request.registry.settings['engine']
    with engine.connect() as conn:
        users = conn.execute(text('select * from users')).all()
    return {
        'title':'Test SQLAlchemy logging',
        'users':users,
    }

def includeme(config):
    settings = config.registry.settings
    initialize_sql(settings)

    config.add_route('test_sqla', '/test_sqla')
    config.scan(__name__)
