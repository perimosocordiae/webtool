#!/usr/bin/env python3
from setuptools import setup

setup(
    name='webtool',
    version='0.0.1',
    author='CJ Carey',
    author_email='perimosocordiae@gmail.com',
    description='Quickly create web-based interfaces.',
    url='http://github.com/perimosocordiae/webtool',
    license='MIT',
    packages=['webtool'],
    install_requires=[
        'matplotlib >= 1.3.1',
        'tornado >= 4.1',
    ],
)
