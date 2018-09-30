# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='neurosynthplus',
    version='alpha',
    description='Meta-analysis package based on NeuroSynth',
    url='https://github.com/MetaD/neurosynthplus',
    license='MIT',
    author='Meng Du',
    author_email='mengdu@umich.edu',
    packages=find_packages(exclude=('tests', 'docs'))
)
