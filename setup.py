#!/usr/bin/env python3
from distutils.core import setup

setup(name='amdgpu-utils',
      version='2.7.0',
      description='Ricks-Lab AMD GPU Utilities',
      author='RueiKe',
      author_email='rueikes.homelab@gmail.com',
      url='https://github.com/Ricks-Lab/amdgpu-utils',
      packages=['GPUmodules'],
      scripts=['amdgpu-chk', 'amdgpu-ls', 'amdgpu-monitor', 'amdgpu-pac', 'amdgpu-pciid', 'amdgpu-plot'],
      license="GPL-3",
      package_data={'GPUmodules': ['amd_pci_id.txt']},
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
      data_files=[('icons', ['amdgpu-monitor.icon.png',  'amdgpu-pac.icon.png',  'amdgpu-plot.icon.png'])]
      )
