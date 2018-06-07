from setuptools import setup, find_packages

setup(
    name='neurosynthPlus',
    version='alpha',
    url='https://github.com/MetaD/neurosynthPlus',
    license='MIT',
    author='Meng Du',
    author_email='mengdu@umich.edu',
    packages=find_packages(exclude=('tests', 'docs'))
)
