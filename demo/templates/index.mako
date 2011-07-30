<html>
    <head>
        <title>${title}</title>
    </head>
    <body>
        <h1>${title}</h1>
        <p>
          <a href="${request.route_url('test_redirect')}">Redirect example</a>
        </p>
        <p>
          <a href="${request.route_url('test_exc')}">Exception example</a>
        </p>
        <p>
          <a href="${request.route_url('test_sqla')}">SQLAlchemy example</a>
        </p>
        <p>
          <a href="${request.route_url('test_chameleon_exc')}">Chameleon Exception example</a>
        </p>
        <p>
          <a href="${request.route_url('test_mako_exc')}">Mako Exception example</a>
        </p>
        <p>
          <a href="${request.route_url('test_jinja2_exc')}">Jinja2 Exception example</a>
        </p>
    </body>
</html>
