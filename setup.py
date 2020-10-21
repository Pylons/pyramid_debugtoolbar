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

from setuptools import find_packages, setup


def readfile(name):
    with open(name) as f:
        return f.read()


README = readfile("README.rst")
CHANGES = readfile("CHANGES.txt")

install_requires = [
    "pyramid>=1.4",
    "pyramid_mako>=0.3.1",  # lazy configuration loading works
    "repoze.lru",
    "Pygments",
]

extra_requires = [
    "ipaddress",
]

testing_extras = [
    "WebTest",
    "nose",
    "coverage",
]

docs_extras = [
    "Sphinx >= 1.7.5",
    "pylons-sphinx-themes >= 0.3",
]

setup(
    name="pyramid_debugtoolbar",
    version="4.6.1",
    description=(
        "A package which provides an interactive HTML debugger "
        "for Pyramid application development"
    ),
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
    ],
    keywords="wsgi pylons pyramid transaction",
    author=(
        "Chris McDonough, Michael Merickel, Casey Duncan, " "Blaise Laflamme"
    ),
    author_email="pylons-discuss@googlegroups.com",
    url="https://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/",  # noqa E501
    license="BSD",
    packages=find_packages("src", exclude=["tests"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    extras_require={
        ':python_version<"3.3"': extra_requires,
        "testing": testing_extras,
        "docs": docs_extras,
    },
    test_suite="tests",
)
