##############################################################################
#
# Copyright (c) 2008-2011 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires=[
    'pyramid>=1.1.1dev',
    'pyramid_debugtoolbar',
    'pyramid_mako',
    'pyramid_jinja2',
    'pyramid_chameleon',
    'selenium',
    'SQLAlchemy',
    ]

setup(name='debugtoolbar_demo',
      version='0.0',
      description='A demo application for the debug toolbar',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
        ],
      keywords='web wsgi pylons pyramid',
      author="Agendaless Consulting and team",
      author_email="pylons-devel@googlegroups.com",
      url="http://pylonsproject.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      py_modules=['demo', 'sqla'],
      package_data = {'debugtoolbar_demo':
                      ['templates/*.mako',
                       'templates/*.jinja2]',
                       'templates/*.pt']},
      )

