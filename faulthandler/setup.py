#!/usr/bin/env python

# Todo list to prepare a release:
#  - run ./run_tests.py
#  - run tests on FreeBSD and Windows
#  - set VERSION in faulthandler.c
#  - set VERSION in setup.py
#  - set release date in the ChangeLog (README file)
#  - git commit -a
#  - git tag -a faulthandler-x.y -m "tag version x.y"
#  - git push
#  - git push --tags
#  - python setup.py register sdist upload
#  - python2.6 setup.py bdist_wininst upload
#  - python2.7 setup.py bdist_wininst upload
#  - python3.1 setup.py bdist_wininst upload
#  - update the website
#
# After the release:
#  - increment VERSION in faulthandler.c
#  - increment VERSION in setup.py
#  - add a new empty section in the Changelog for the new version
#  - git commit -a
#  - git push

from __future__ import with_statement
from distutils.core import setup, Extension
from os.path import join as path_join
import sys

if sys.version_info >= (3,3):
    print("ERROR: faulthandler is a builtin module since Python 3.3")
    sys.exit(1)

VERSION = "2.2"

FILES = ['faulthandler.c', 'traceback.c']

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: C',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development :: Debuggers',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

with open('README') as f:
    long_description = f.read().strip()

options = {
    'name': "faulthandler",
    'version': VERSION,
    'license': "BSD (2-clause)",
    'description': 'Display the Python traceback on a crash',
    'long_description': long_description,
    'url': "https://github.com/haypo/faulthandler/wiki/",
    'author': 'Victor Stinner',
    'author_email': 'victor.stinner@haypocalc.com',
    'ext_modules': [Extension('faulthandler', FILES)],
    'classifiers': CLASSIFIERS,
}

setup(**options)

