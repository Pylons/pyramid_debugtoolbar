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
https://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/.


Demonstration
-------------

For a demonstration:

- Clone the ``pyramid_debugtoolbar`` trunk.

  .. code-block:: bash

      $ git clone https://github.com/Pylons/pyramid_debugtoolbar.git

- Create a virtual environment in the workspace.

  .. code-block:: bash

      $ cd pyramid_debugtoolbar
      $ python3 -m venv env

- Install the ``pyramid_debugtoolbar`` trunk into the virtualenv.

  .. code-block:: bash

      $ env/bin/pip install -e .

- Install the ``pyramid_debugtoolbar/demo`` package into the virtualenv.

  .. code-block:: bash

      $ env/bin/pip install -e demo

- Run the ``pyramid_debugtoolbar`` package's ``demo/demo.py`` file using the
  virtual environment's Python.

  .. code-block:: bash

      $ env/bin/python demo/demo.py

Visit http://localhost:8080 in a web browser to see a page full of test
options.


Testing
-------

If you have ``tox`` installed, run all tests with:

.. code-block:: bash

    $ tox

To run only a specific Python environment:

.. code-block:: bash

    $ tox -e py35

If you don't have ``tox`` installed, you can install the testing requirements,
then run the tests.

.. code-block:: bash

    $ python3 -m venv env
    $ env/bin/pip install -e ".[testing]"
    $ env/bin/nosetests


Building documentation
----------------------

If you have ``tox`` installed, build the docs with:

.. code-block:: bash

    $ tox -e docs

If you don't have ``tox`` installed, you can install the requirements to build
the docs, then build them.

.. code-block:: bash

    $ env/bin/pip install -e ".[docs]"
    $ cd docs
    $ make clean html SPHINXBUILD=../env/bin/sphinx-build
