#!/usr/bin/python3

import sys
import os
import pathlib
from setuptools import setup, find_packages
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
      keywords='gpu system monitoring overclocking underclocking linux amdgpu nvidia-smi rocm amd nvidia opencl boinc',
      platforms='posix',
      author_email='rueikes.homelab@gmail.com',
      url='https://github.com/Ricks-Lab/gpu-utils',
      packages=find_packages(include=['GPUmodules']),
      include_package_data=True,
      scripts=['gpu-chk', 'gpu-ls', 'gpu-mon', 'gpu-pac', 'gpu-plot'],
      license='GPL-3',
      python_requires='>=3.6',
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
                                      'man/gpu-plot.1'])
                  ]
      )
