pyramid_debugtoolbar
====================

``pyramid_debugtoolbar`` provides a debug toolbar useful while you're
developing your Pyramid application.

Note that ``pyramid_debugtoolbar`` is a blatant rip-off of Michael van
Tellingen's ``flask-debugtoolbar`` (which itself was derived from Rob Hudson's
``django-debugtoolbar``). It also includes a lightly sanded down version of the
Werkzeug debugger code by Armin Ronacher and team.


Documentation
-------------

The documentation of the current stable release of ``pyramid_debugtoolbar`` is
available at
http://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/.


Demonstration
-------------

For a demonstration:

- Create a workspace.

  .. code-block:: bash

      $ mkdir ~/projects/pyramid_debugtoolbar_demo
      $ cd ~/projects/pyramid_debugtoolbar_demo

- Create a virtual environment in the workspace.

  .. code-block:: bash

      # Set the path to our virtual environment
      $ export VENV=${PWD}/env
      $ $VENV/bin/python -m venv $VENV

- Ugrade ``pip`` and ``setuptools``.

  .. code-block:: bash

      $ $VENV/bin/pip install --upgrade pip setuptools

- Clone the Pyramid trunk.

  .. code-block:: bash

      $ git clone https://github.com/Pylons/pyramid.git

- Install the Pyramid trunk into the virtual environment.

  .. code-block:: bash

      $ cd pyramid
      $ $VENV/bin/pip install -e .

- Clone the ``pyramid_debugtoolbar`` trunk.

  .. code-block:: bash

      # go back up into the workspace directory
      $ cd ..
      $ git clone https://github.com/Pylons/pyramid_debugtoolbar.git

- Install the ``pyramid_debugtoolbar`` trunk into the virtualenv.

  .. code-block:: bash

      $ cd pyramid_debugtoolbar
      $ $VENV/bin/pip install -e .

- Install the ``pyramid_debugtoolbar/demo`` package into the virtualenv.

  .. code-block:: bash

      $ cd demo
      $ $VENV/bin/pip install -e .

- Run the ``pyramid_debugtoolbar`` package's ``demo/demo.py`` file using the
  virtual environment's Python.

  .. code-block:: bash

      $ $VENV/bin/python demo.py

Visit http://localhost:8080 in a web browser to see a page full of test
options.


Testing
-------

For this section, first navigate to
``pyramid_debugtoolbar_demo/pyramid_debugtoolbar``.

If you have ``tox`` installed, run all tests with:

.. code-block:: bash

    $ tox

To run only a specific Python environment:

.. code-block:: bash

    $ tox -e py35

If you don't have ``tox`` installed, you can install the testing requirements,
then run the tests.

.. code-block:: bash

    $ $VENV/bin/pip install -e ".[testing]"
    $ $VENV/bin/nosetests


Building documentation
----------------------

For this section, first navigate to
``pyramid_debugtoolbar_demo/pyramid_debugtoolbar``.

If you have ``tox`` installed, build the docs with:

.. code-block:: bash

    $ tox -e docs

If you don't have ``tox`` installed, you can install the requirements to build
the docs, then build them.

.. code-block:: bash

    $ $VENV/bin/pip install -e ".[docs]"
    $ cd docs
    $ make clean html SPHINXBUILD=$VENV/bin/sphinx-build
