Pyramid Debug Toolbar Demo App
==============================

Demonstration application for the Pyramid debug toolbar.

Running the Demo
----------------

- Create a virtualenv::

    $ virtualenv2.6 --no-site-packages /path/to/my/venv

  Hereafter ``/path/to/my/venv`` will be referred to as $VENV in steps
  below.

- Get a checkout of pyramid_debugtoolbar::

    $ git clone git://github.com/Pylons/pyramid_debugtoolbar.git

- ``cd`` to the newly checked out pyramid_debugtoolbar package::

    $ cd pyramid_debugtoolbar

- Run ``setup.py develop`` using the virtualenv's ``python`` command::

    $ $VENV/bin/python setup.py develop

- While your working directory is still ``pyramid_debugtoolbar``, cd to the
  ``demo`` directory and run *its* ``setup.py develop``::

    $ cd demo
    $ $VENV/bin/python setup.py develop


- Start the demo application::

    $ $VENV/bin/python demo.py

- Visit http://localhost:8080 in a browser to see the demo.

Running the Demo's Selenium Tests
---------------------------------

The ``pyramid_debugtoolbar`` demo application application serves as a target
for functional testing during the toolbar's development.  A suite of Selenium
tests may be run against a local instance of the demonstration application.
It is wise to run these tests before submitting a patch.  Here's how:

- Make sure you have a Java interpreter installed.

- Start the demo application as described above in "Running the Demo".  Leave
  the terminal window running this application open, and open another
  terminal window to perform the below steps.

- Download `Selenium Server <http://seleniumhq.org/download/>` standalone jar
  file.

- Run ``java -jar selenium-server-standalone-X.X.jar``.  Success is defined
  as seeing output on the console that ends like this::

   01:49:06.105 INFO - Started SocketListener on 0.0.0.0:4444
   01:49:06.105 INFO - Started org.openqa.jetty.jetty.Server@7d2a1e44

- Leave the terminal window in which the selenium server is now
  running open, and open (yet) another terminal window.

- In the newest terminal window, cd to the ``pyramid_debugtoolbar/demo``
  directory you created above in "Running the Demo"::

   $ cd /path/to/my/pyramid_debugtoolbar/demo

- Run the tests::

   $ $VENV/bin/python test.py

  ``$VENV`` is defined as it was in "Running the Demo" above.

- You will (hopefully) see Firefox pop up in a two-windowed
  arrangement, and it will begin to display in quick succession the
  loading of pages in the bottom window and some test output in the
  top window.  The tests will run for a minute or two.

- Test success means that the console window on which you ran
  ``test.py`` shows a bunch of dots, a test summary, then ``OK``.  If
  it shows a traceback, ``FAILED``, or anything other than a straight
  line of dots, it means there was an error.

- Fix any errors by modifying your code or by modifying the tests to
  expect the changes you've made.

- Note that as of this writing, Firefox 22 is broken for Selenium and can't be 
  used.  Firefox 21 seems to work fine.
