# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'nsplus', 'version.py')
exec(compile(open(version_file, 'rb').read(), version_file, 'exec'))

APP_NAME = 'NSplus'
OPTIONS = {
    'iconfile': os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'nsplus', 'res', 'icon.icns'),
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleVersion': __version__,
        'CFBundleShortVersionString': __version__,
        'NSHumanReadableCopyright': u'© 2018 Meng Du. All Rights Reserved.'
    }
}

setup(
    name=APP_NAME,
    version=__version__,
    description='A Neurosynth-based meta-analysis tool',
    url='https://github.com/MetaD/NSplus',
    author='Meng Du',
    author_email='mengdu@umich.edu',
    app=[os.path.join(os.path.dirname(os.path.realpath(__file__)),
                      'nsplus.py')],
    data_files=[('data', [os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       'nsplus', 'data', 'database_v0.7.pkl.gz')])],
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    packages=find_packages(exclude=('tests', 'docs')),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta"
    ]
)
