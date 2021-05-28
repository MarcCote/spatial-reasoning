#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os

from setuptools import setup, find_packages

setup(
    name='spatial-reasoning',
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    license=open('LICENSE').read(),
    zip_safe=False,
    description="Environment for the paper Representation Learning for Grounded Spatial Reasoning.",
    install_requires=[line for line in open('requirements.txt').readlines() if "@" not in line],
)
