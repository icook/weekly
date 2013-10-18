#!/usr/bin/env python

from setuptools import setup, find_packages

requires = ['pymongo',
            'flask',
            'flask_mongoengine',
            'mongoengine',
            'flask-login',
            'yota>=0.3',
            'cryptacular',
            'markdown2',
            'Babel']

setup(name='weekly',
      version='0.1',
      author='Isaac Cook',
      author_email='isaac@simpload.com',
      install_requires=requires,
      dependency_links=["https://github.com/icook/yota/tarball/0.3#egg=yota-0.3"],
      url='http://www.python.org/sigs/distutils-sig/',
      packages=find_packages()
     )
