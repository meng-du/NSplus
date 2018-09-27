# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='neurosynthPlus',
    version='alpha',
    description='Meta-src package based on NeuroSynth',
    url='https://github.com/MetaD/neurosynthPlus',
    license='MIT',
    author='Meng Du',
    author_email='mengdu@umich.edu',
    packages=find_packages(exclude=('tests', 'docs'))
)
