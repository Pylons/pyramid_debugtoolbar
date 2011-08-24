``pyramid_debugtoolbar``
========================

``pyramid_debugtoolbar`` provides a debug toolbar useful while you're
developing your Pyramid application.

This code requires Pyramid 1.2a1 or better.

Note that ``pyramid_debugtoolbar`` is a blatant rip-off of Michael van
Tellingen's ``flask-debugtoolbar`` (which itself was derived from Rob
Hudson's ``django-debugtoolbar``).  It also includes a lightly sanded down
version of the Werkzeug debugger code by Armin Ronacher and team.

Demonstration
-------------

For a demonstration:

- Create a virtualenv::

  $ virtualenv2.6 --no-site-packages env26

- Clone the Pyramid trunk::

  $ git clone git@github.com:Pylons/pyramid.git

- Install the Pyramid trunk into the virtualenv::

  $ cd pyramid
  $ $VENV/bin/python setup.py develop

- Clone the ``pyramid_debugtoolbar`` trunk::

  $ git clone git@github.com:Pylons/pyramid_debugtoolbar.git

- Install the ``pyramid_debugtoolbar`` trunk into the virtualenv::

  $ cd pyramid_debugtoolbar
  $ $VENV/bin/python setup.py develop

- Install the ``pyramid_debugtoolbar/demo`` package into the virtualenv::

  $ cd demo
  $ $VENV/bin/python setup.py develop

- Run the ``pyramid_debugtoolbar`` package's ``demo/demo.py`` file using the
  virtualenv's Python::

  $ $VENV/bin/python demo.py

You will see a page full of test options to try when you visit
``http://localhost:8080``.
