#!/usr/bin/python3

import sys
import os
import pathlib
from setuptools import setup
from GPUmodules import __version__, __status__

if sys.version_info < (3, 6):
    print('rickslab-gpu-utils requires at least Python 3.6.')
    sys.exit(1)

with open(os.path.join(pathlib.Path(__file__).parent, 'README.md'), 'r') as file_ptr:
    long_description = file_ptr.read()

setup(name='rickslab-gpu-utils',
      version=__version__,
      description='Ricks-Lab GPU Utilities',
      long_description_content_type='text/markdown',
      long_description=long_description,
      author='RueiKe',
      platforms='posix',
      author_email='rueikes.homelab@gmail.com',
      url='https://github.com/Ricks-Lab/amdgpu-utils',
      packages=['GPUmodules'],
      include_package_data=True,
      scripts=['gpu-chk', 'gpu-ls', 'gpu-mon', 'gpu-pac', 'gpu-plot'],
      license='GPL-3',
      python_requires='>=3.6',
      classifiers=[__status__,
                   'Operating System :: POSIX',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3',
                   'Topic :: System :: Monitoring',
                   'Environment :: GPU',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
      install_requires=['cycler>=0.10.0',
                        'kiwisolver>=1.1.0',
                        'matplotlib>=3.1.3',
                        'numpy>=1.18.1',
                        'pandas>=1.0.1',
                        'pyparsing>=2.4.6',
                        'python-dateutil>=2.8.1',
                        'pytz>=2019.3',
                        'ruamel.yaml==0.16.10',
                        'ruamel.yaml.clib==0.2.0',
                        'six>=1.11.0'],
      data_files=[('share/rickslab-gpu-utils/icons', ['icons/gpu-mon.icon.png',
                                                      'icons/gpu-pac.icon.png',
                                                      'icons/gpu-plot.icon.png']),
                  ('share/rickslab-gpu-utils/doc', ['README.md', 'LICENSE']),
                  ('share/man/man1', ['man/gpu-chk.1',
                                      'man/gpu-ls.1',
                                      'man/gpu-mon.1',
                                      'man/gpu-pac.1',
                                      'man/gpu-plot.1'])
                  ]
      )
