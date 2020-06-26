#!/usr/bin/env python3

import sys
from setuptools import setup

if sys.version_info < (3, 6):
    print('ricks-amdgpu-utils requires at least Python 3.6.')
    sys.exit(1)

VERSION = '3.3.11'

setup(name='ricks-amdgpu-utils',
      version=VERSION,
      description='Ricks AMD GPU Utilities (Deprecated)',
      long_description=('This release of GPU Utilities is replaced by rickslab-gpu-utils, which now supports.'
                        'additional vendors GPUs.  The amdgpu-util version will no longer be updated, as'
                        'development efforts will be focused on rickslab-gpu-utils'),
      author='RueiKe',
      platforms='posix',
      author_email='rueikes.homelab@gmail.com',
      url='https://github.com/Ricks-Lab/amdgpu-utils',
      packages=['GPUmodules'],
      include_package_data=True,
      scripts=['amdgpu-chk', 'amdgpu-ls', 'amdgpu-monitor', 'amdgpu-pac', 'amdgpu-plot'],
      license='GPL-3',
      python_requires='>=3.6',
      classifiers=['Development Status :: 6 - Mature',
                   'Operating System :: POSIX',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 3',
                   'Topic :: System :: Monitoring'],
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
      data_files=[('share/ricks-amdgpu-utils/icons', ['icons/amdgpu-monitor.icon.png',
                                                      'icons/amdgpu-pac.icon.png',
                                                      'icons/amdgpu-plot.icon.png']),
                  ('share/ricks-amdgpu-utils/doc', ['README.md', 'LICENSE']),
                  ('share/man/man1', ['man/amdgpu-chk.1',
                                      'man/amdgpu-ls.1',
                                      'man/amdgpu-monitor.1',
                                      'man/amdgpu-pac.1',
                                      'man/amdgpu-plot.1'])
                  ]
      )
