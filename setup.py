##############################################################################
#
# Copyright (c) 2008-2013 Agendaless Consulting and Contributors.
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

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'pyramid>=1.2dev',
    'pyramid_mako>=0.3.1', # lazy configuration loading works
    'Pygments',
    'repoze.lru',
    ]

testing_extras = [
    'nose',
    'coverage',
    ]

docs_extras = [
    'Sphinx',
    ]

setup(name='pyramid_debugtoolbar',
      version='2.2',
      description=('A package which provides an interactive HTML debugger '
                   'for Pyramid application development'),
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
        ],
      keywords='wsgi pylons pyramid transaction',
      author=("Chris McDonough, Michael Merickel, Casey Duncan, "
              "Blaise Laflamme"),
      author_email="pylons-devel@googlegroups.com",
      url="http://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/",
      license="BSD",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require = {
          'testing':testing_extras,
          'docs':docs_extras,
          },
      package_data={'pyramid_debugtoolbar': ['static/css/*', 'static/font/*',
          'static/img/*', 'static/js/*', 'templates/*', 'panels/templates/*']
          },
      test_suite="pyramid_debugtoolbar",
      entry_points='',
      )
