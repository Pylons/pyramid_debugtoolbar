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

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'pyramid>=1.1.1dev',
    'pyramid_jinja2>=1.1', # get_jinja2_environment
    'Pygments',
    ]

setup(name='pyramid_debugtoolbar',
      version='0.2',
      description=('A package which provides an interactive HTML debugger '
                   'for Pyramid application development'),
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
        ],
      keywords='wsgi pylons pyramid transaction',
      author="Chris McDonough, Michael Merickel, Casey Duncan, Blaise Laflamme",
      author_email="pylons-devel@googlegroups.com",
      url="http://docs.pylonsproject.org",
      license="BSD",
      packages=find_packages(),
      include_package_data=True,
      package_data={
          'pyramid_debugtoolbar.panels': [
              '*.jinja2',
              'templates/*'
          ],
      },
      zip_safe=False,
      install_requires=install_requires,
      tests_require=install_requires,
      test_suite="pyramid_debugtoolbar",
      entry_points='',
      )
