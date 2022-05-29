#!/usr/bin/python3
""" setup.py used in producing source and binary distributions.

    Usage: python3 setup.py sdist bdist_wheel

    Copyright (C) 2020  RicksLab

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
__author__ = 'RicksLab'
__credits__ = []
__license__ = 'GNU General Public License - GPL-3'
__program_name__ = 'setup.py'
__maintainer__ = 'RicksLab'
__docformat__ = 'reStructuredText'

# pylint: disable=line-too-long

import sys
import os
import pathlib
from setuptools import setup, find_packages
from GPUmodules import __version__, __status__, __required_pversion__

if sys.version_info[:2] < __required_pversion__:
    print('rickslab-gpu-utils requires at least Python {}.{}.'.format(__required_pversion__[0],
                                                                      __required_pversion__[1]))
    sys.exit(1)

with open(os.path.join(pathlib.Path(__file__).parent, 'README.md'), 'r') as file_ptr:
    LONG_DESCRIPTION = file_ptr.read()

setup(name='rickslab-gpu-utils',
      version=__version__,
      description='Ricks-Lab GPU Utilities',
      long_description_content_type='text/markdown',
      long_description=LONG_DESCRIPTION,
      author=__author__,
      keywords='gpu system monitoring overclocking underclocking linux amdgpu nvidia-smi rocm amd nvidia opencl boinc',
      platforms='posix',
      author_email='rueikes.homelab@gmail.com',
      url='https://github.com/Ricks-Lab/gpu-utils',
      packages=find_packages(include=['GPUmodules']),
      include_package_data=True,
      scripts=['gpu-chk', 'gpu-ls', 'gpu-mon', 'gpu-pac', 'gpu-plot'],
      license='GPL-3',
      python_requires='>={}.{}'.format(__required_pversion__[0], __required_pversion__[1]),
      project_urls={'Bug Tracker':   'https://github.com/Ricks-Lab/gpu-utils/issues',
                    'Documentation': 'https://github.com/Ricks-Lab/gpu-utils/blob/master/docs/USER_GUIDE.md',
                    'Source Code':   'https://github.com/Ricks-Lab/gpu-utils'},
      classifiers=[__status__,
                   'Operating System :: POSIX',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3',
                   'Topic :: System :: Monitoring',
                   'Environment :: GPU',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
      install_requires=['matplotlib>=3.1.3',
                        'pandas>=1.0.1'],
      data_files=[('share/rickslab-gpu-utils/icons', ['icons/gpu-mon.icon.png',
                                                      'icons/gpu-pac.icon.png',
                                                      'icons/gpu-plot.icon.png']),
                  ('share/rickslab-gpu-utils/doc', ['README.md', 'LICENSE']),
                  ('share/man/man1', ['man/gpu-chk.1',
                                      'man/gpu-ls.1',
                                      'man/gpu-mon.1',
                                      'man/gpu-pac.1',
                                      'man/gpu-plot.1'])])
