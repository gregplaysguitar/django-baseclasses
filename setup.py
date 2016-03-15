#!/usr/bin/env python
# coding: utf8

import os
from setuptools import setup, find_packages


# if there's a converted readme, use it, otherwise fall back to markdown
if os.path.exists('README.rst'):
    readme_path = 'README.rst'
else:
    readme_path = 'README.md'

# avoid importing the module
exec(open('baseclasses/_version.py').read())

setup(
    name='django-baseclasses',
    version=__version__,
    description='A set of reusable base classes and helpers for django',
    long_description=open(readme_path).read(),
    author='Greg Brown',
    author_email='greg@gregbrown.co.nz',
    url='https://github.com/gregplaysguitar/django-baseclasses',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['Django>=1.7'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Framework :: Django',
    ],
)
