#!/usr/bin/env python

from setuptools import setup, find_packages

requires = ['pymongo',
            'flask',
            'flask_mongoengine',
            'mongoengine',
            'flask-login',
            'yota',
            'cryptacular',
            'misaka',
            'Babel']

setup(name='weekly',
      version='0.1',
      author='Isaac Cook',
      author_email='isaac@simpload.com',
      install_requires=requires,
      url='http://www.python.org/sigs/distutils-sig/',
      packages=find_packages()
     )
