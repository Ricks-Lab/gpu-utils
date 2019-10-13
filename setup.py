#!/usr/bin/env python3
# from distutils.core import setup
import sys
from setuptools import setup

if sys.version_info < (3, 6):
    print('ricks-amdgpu-utils requires at least Python 3.6.')
    sys.exit(1)


setup(name='ricks-amdgpu-utils',
      version='2.7.0',
      description='Ricks-Lab AMD GPU Utilities',
      long_description='A set of utilities for monitoring AMD GPU performance and modifying control settings.',
      author='RueiKe',
      platforms='posix',
      author_email='rueikes.homelab@gmail.com',
      url='https://github.com/Ricks-Lab/amdgpu-utils',
      packages=['GPUmodules'],
      include_package_data=True,
      scripts=['amdgpu-chk', 'amdgpu-ls', 'amdgpu-monitor', 'amdgpu-pac', 'amdgpu-pciid', 'amdgpu-plot'],
      license='GPL-3',
      # package_data={'GPUmodules': ['amd_pci_id.txt']},
      python_requires='>=3.6',
      install_requires=['cycler==0.10.0',
                        'kiwisolver==1.1.0',
                        'matplotlib==3.0.3',
                        'numpy==1.16.3',
                        'pandas==0.24.2',
                        'pyparsing==2.4.0',
                        'python-dateutil==2.8.0',
                        'pytz==2019.1',
                        'ruamel.yaml==0.16.5',
                        'ruamel.yaml.clib==0.1.2',
                        'six==1.12.0'],
      data_files=[('share/ricks-amdgpu-utils/icons', ['icons/amdgpu-monitor.icon.png',
                                                      'icons/amdgpu-pac.icon.png',
                                                      'icons/amdgpu-plot.icon.png']),
                  ('share/ricks-amdgpu-utils/doc', ['README.md']),
                  ('share/man/man1', ['man/amdgpu-chk.1',
                                      'man/amdgpu-ls.1',
                                      'man/amdgpu-monitor.1',
                                      'man/amdgpu-pac.1',
                                      'man/amdgpu-pciid.1',
                                      'man/amdgpu-plot.1'])
                  ]
      )
