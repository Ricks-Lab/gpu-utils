#!/usr/bin/env python3
"""env.py - sets environment for rickslab-gpu-utils and establishes global variables

    Copyright (C) 2019  RicksLab

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
__author__ = 'RueiKe'
__copyright__ = 'Copyright (C) 2019 RicksLab'
__credits__ = ['Craig Echt - Testing, Debug, and Verification']
__license__ = 'GNU General Public License'
__program_name__ = 'gpu-utils'
__maintainer__ = 'RueiKe'
__docformat__ = 'reStructuredText'
# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=bad-continuation

import argparse
import re
import subprocess
import platform
import sys
from os import path as os_path
import logging
from pathlib import Path
import inspect
import shlex
import shutil
from time import mktime as time_mktime
from datetime import datetime
from typing import Dict, Union, List, TextIO
from GPUmodules import __version__, __status__

LOGGER = logging.getLogger('gpu-utils')


class GutConst:
    """
    GPU Utils constants used throughout the project.
    """
    _verified_distros: List[str] = ['Debian', 'Ubuntu', 'Neon', 'Gentoo', 'Arch']
    _dpkg_tool: Dict[str, str] = {'Debian': 'dpkg', 'Ubuntu': 'dpkg', 'Neon': 'dpkg',
                                  'Arch': 'pacman',
                                  'Gentoo': 'equery'}
    _all_args: List[str] = ['execute_pac', 'debug', 'pdebug', 'sleep', 'no_fan', 'ltz', 'simlog', 'log', 'force_write']
    PATTERNS = {'HEXRGB':       re.compile(r'^#[0-9a-fA-F]{6}'),
                'PCIIID_L0':    re.compile(r'^[0-9a-fA-F]{4}.*'),
                'PCIIID_L1':    re.compile(r'^\t[0-9a-fA-F]{4}.*'),
                'PCIIID_L2':    re.compile(r'^\t\t[0-9a-fA-F]{4}.*'),
                'END_IN_ALPHA': re.compile(r'[a-zA-Z]+$'),
                'ALPHA':        re.compile(r'[a-zA-Z]+'),
                'AMD_GPU':      re.compile(r'(AMD|amd|ATI|ati)'),
                'NV_GPU':       re.compile(r'(NVIDIA|nvidia|nVidia)'),
                'INTC_GPU':     re.compile(r'(INTEL|intel|Intel)'),
                'ASPD_GPU':     re.compile(r'(ASPEED|aspeed|Aspeed)'),
                'MTRX_GPU':     re.compile(r'(MATROX|matrox|Matrox)'),
                'MHz':          re.compile(r'M[Hh]z'),
                'PPM_CHK':      re.compile(r'[*].*'),
                'PCI_GPU':      re.compile(r'(VGA|3D|Display)'),
                'PCI_ADD':      re.compile(r'^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}.[0-9a-fA-F])'),
                'PPM_NOTCHK':   re.compile(r'[ ]+'),
                'VALID_PS_STR': re.compile(r'[0-9]+(\s[0-9])*'),
                'IS_FLOAT':     re.compile(r'[-+]?\d*\.?\d+|[-+]?\d+'),
                'DIGITS':       re.compile(r'^[0-9]+[0-9]*$'),
                'VAL_ITEM':     re.compile(r'.*_val$'),
                'GPU_GENERIC':  re.compile(r'(^\s|intel|amd|nvidia|amd/ati|ati|radeon|\[|\])', re.IGNORECASE),
                'GPUMEMTYPE':   re.compile(r'^mem_(gtt|vram)_.*')}

    _sys_pciid_list: List[str] = ['/usr/share/misc/pci.ids', '/usr/share/hwdata/pci.ids']
    _module_path: str = os_path.dirname(str(Path(__file__).resolve()))
    _repository_path: str = os_path.join(_module_path, '..')
    _local_config_list: Dict[str, str] = {
        'repository': _repository_path,
        'debian':     '/usr/share/rickslab-gpu-utils/config',
        'pypi-linux': os_path.join(str(Path.home()), '.local', 'share', 'rickslab-gpu-utils', 'config')}
    _local_icon_list: Dict[str, str] = {
        'repository': os_path.join(_repository_path, 'icons'),
        'debian':     '/usr/share/rickslab-gpu-utils/icons',
        'pypi-linux': '{}/.local/share/rickslab-gpu-utils/icons'.format(str(Path.home()))}
    featuremask: str = '/sys/module/amdgpu/parameters/ppfeaturemask'
    card_root: str = '/sys/class/drm/'
    hwmon_sub: str = 'hwmon/hwmon'
    gui_window_title: str = 'Ricks-Lab GPU Utilities'
    mon_field_width = 20

    def __init__(self):
        self.args: Union[argparse.Namespace, None] = None
        self.repository_path: str = self._repository_path
        self.install_type: Union[str, None] = None
        self.package_path: str = inspect.getfile(inspect.currentframe())

        if 'dist-packages' in self.package_path:
            self.install_type = 'debian'
        elif '.local' in self.package_path:
            self.install_type = 'pypi-linux'
        else:
            self.install_type = 'repository'
        self.icon_path = self._local_icon_list[self.install_type]
        if not os_path.isfile(os_path.join(self.icon_path, 'gpu-mon.icon.png')):
            print('Error: Invalid icon path')
            self.icon_path = None

        # Set pciid Path
        for try_pciid_path in GutConst._sys_pciid_list:
            if os_path.isfile(try_pciid_path):
                self.sys_pciid = try_pciid_path
                break
        else:
            self.sys_pciid = None

        self.distro: Dict[str, Union[str, None]] = {'Distributor': None, 'Description': None}
        self.amdfeaturemask: Union[int, None] = None
        self.log_file_ptr: Union[TextIO, None] = None

        # From args
        self.execute_pac: bool = False
        self.DEBUG: bool = False
        self.PDEBUG: bool = False
        self.SIMLOG: bool = False
        self.LOG: bool = False
        self.PLOT: bool = False
        self.show_fans: bool = True
        self.write_delta_only: bool = False
        self.SLEEP: int = 2
        self.USELTZ: bool = False
        # Time
        self.TIME_FORMAT: str = '%d-%b-%Y %H:%M:%S'
        self.LTZ: datetime.tzinfo = datetime.utcnow().astimezone().tzinfo
        # Command access
        self.cmd_lsb_release: Union[str, None] = None
        self.cmd_lspci: Union[str, None] = None
        self.cmd_clinfo: Union[str, None] = None
        self.cmd_dpkg: Union[str, None] = None
        self.cmd_nvidia_smi: Union[str, None] = None

    def set_args(self, args: argparse.Namespace) -> None:
        """
        Set arguments for the give args object.

        :param args: The object return by args parser.
        """
        self.args = args
        for target_arg in self._all_args:
            if target_arg in self.args:
                if target_arg == 'debug': self.DEBUG = self.args.debug
                elif target_arg == 'execute_pac': self.execute_pac = self.args.execute_pac
                elif target_arg == 'pdebug': self.PDEBUG = self.args.pdebug
                elif target_arg == 'sleep': self.SLEEP = self.args.sleep
                elif target_arg == 'no_fan': self.show_fans = not self.args.no_fan
                elif target_arg == 'ltz': self.USELTZ = self.args.ltz
                elif target_arg == 'simlog': self.SIMLOG = self.args.simlog
                elif target_arg == 'log': self.LOG = self.args.log
                elif target_arg == 'force_write': self.write_delta_only = not self.args.force_write
                else: print('Invalid arg: {}'.format(target_arg))
        LOGGER.propagate = False
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(module)s.%(funcName)s:%(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.WARNING)
        LOGGER.addHandler(stream_handler)
        LOGGER.setLevel(logging.WARNING)
        if self.DEBUG:
            LOGGER.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                'debug_gpu-utils_{}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S")), 'w')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            LOGGER.addHandler(file_handler)
        LOGGER.debug('Install type: %s', self.install_type)
        LOGGER.debug('Command line arguments:\n  %s', args)
        LOGGER.debug('Local TZ: %s', self.LTZ)
        LOGGER.debug('pciid path set to: %s', self.sys_pciid)
        LOGGER.debug('Icon path set to: %s', self.icon_path)

    @staticmethod
    def now(ltz: bool = False) -> datetime:
        """
        Get the current datetime object.

        :param ltz: Flag to get local time instead of UTC
        :return: datetime obj of current time
        """
        return datetime.now() if ltz else datetime.utcnow()

    @staticmethod
    def utc2local(utc: datetime) -> datetime:
        """
        Return local time for given UTC time.

        :param utc: Time for UTC
        :return: Time for local time zone
        .. note:: from https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime
        """
        epoch = time_mktime(utc.timetuple())
        offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
        return utc + offset

    def read_amdfeaturemask(self) -> int:
        """
        Read and return the amdfeaturemask as an int.

        :return: AMD Feature Mask
        """
        try:
            with open(self.featuremask) as fm_file:
                fm_str = fm_file.readline().rstrip()
                LOGGER.debug('Raw Featuremask string: [%s]', fm_str)
                self.amdfeaturemask = int(fm_str, 0)
        except TypeError as err:
            LOGGER.debug('Invalid AMD Featuremask str [%s], %s', fm_str, err)
            self.amdfeaturemask = 0
        except OSError as err:
            LOGGER.debug('Could not read AMD Featuremask, %s', err)
            self.amdfeaturemask = 0
        LOGGER.debug('AMD featuremask: %s', hex(self.amdfeaturemask))
        return self.amdfeaturemask

    def check_env(self) -> int:
        """
        Check the compatibility of the user environment.

        :return: Return status: ok=0, python issue= -1, kernel issue= -2, command issue= -3
        """
        # Check python version
        required_pversion = (3, 6)
        (python_major, python_minor, python_patch) = platform.python_version_tuple()
        LOGGER.debug('Using python: %s.%s.%s', python_major, python_minor, python_patch)
        if int(python_major) < required_pversion[0]:
            print('Using python {}, but {} requires python {}.{} or higher.'.format(python_major, __program_name__,
                                                                                    required_pversion[0],
                                                                                    required_pversion[1]),
                  file=sys.stderr)
            return -1
        if int(python_major) == required_pversion[0] and int(python_minor) < required_pversion[1]:
            print('Using python {}.{}.{}, but {} requires python {}.{} or higher.'.format(python_major, python_minor,
                                                                                          python_patch,
                                                                                          __program_name__,
                                                                                          required_pversion[0],
                                                                                          required_pversion[1]),
                  file=sys.stderr)
            return -1

        # Check Linux Kernel version
        required_kversion = (4, 8)
        linux_version = platform.release()
        LOGGER.debug('Using Linux Kernel: %s', linux_version)
        if int(linux_version.split('.')[0]) < required_kversion[0]:
            print('Using Linux Kernel {}, but {} requires > {}.{}.'.format(linux_version, __program_name__,
                  required_kversion[0], required_kversion[1]), file=sys.stderr)
            return -2
        if int(linux_version.split('.')[0]) == required_kversion[0] and \
                int(linux_version.split('.')[1]) < required_kversion[1]:
            print('Using Linux Kernel {}, but {} requires > {}.{}.'.format(linux_version, __program_name__,
                  required_kversion[0], required_kversion[1]), file=sys.stderr)
            return -2

        # Check Linux Distro
        self.cmd_lsb_release = shutil.which('lsb_release')
        if self.cmd_lsb_release:
            lsbr_out = subprocess.check_output(shlex.split('{} -a'.format(self.cmd_lsb_release)),
                                               shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            for lsbr_line in lsbr_out:
                if 'Distributor ID' in lsbr_line:
                    lsbr_item = re.sub(r'Distributor ID:[\s]*', '', lsbr_line)
                    LOGGER.debug('Using Linux Distro: %s', lsbr_item)
                    self.distro['Distributor'] = lsbr_item.strip()
                if 'Description' in lsbr_line:
                    lsbr_item = re.sub(r'Description:[\s]*', '', lsbr_line)
                    LOGGER.debug('Linux Distro Description: %s', lsbr_item)
                    self.distro['Description'] = lsbr_item.strip()

            if self.distro['Distributor'] and self.DEBUG:
                print('{}: '.format(self.distro['Distributor']), end='')
                if self.distro['Distributor'] in GutConst._verified_distros: print('Validated')
                else: print('Unverified')
        else:
            print('OS command [lsb_release] executable not found.')

        LOGGER.debug('Distro: %s, %s', self.distro['Distributor'], self.distro['Description'])
        # Check access/paths to system commands
        command_access_fail = False
        self.cmd_lspci = shutil.which('lspci')
        if not self.cmd_lspci:
            print('Error: OS command [lspci] executable not found.')
            command_access_fail = True
        LOGGER.debug('lspci path: %s', self.cmd_lspci)

        self.cmd_clinfo = shutil.which('clinfo')
        if not self.cmd_clinfo:
            print('Package addon [clinfo] executable not found.  Use sudo apt-get install clinfo to install')
        LOGGER.debug('clinfo path: %s', self.cmd_clinfo)

        # Package Reader
        if self.distro['Distributor'] in GutConst._dpkg_tool:
            pkg_tool = GutConst._dpkg_tool[self.distro['Distributor']]
            self.cmd_dpkg = shutil.which(pkg_tool)
            if not self.cmd_dpkg:
                print('OS command [{}] executable not found.'.format(pkg_tool))
        else:
            for test_dpkg in GutConst._dpkg_tool.values():
                self.cmd_dpkg = shutil.which(test_dpkg)
                if self.cmd_dpkg:
                    break
            else:
                self.cmd_dpkg = None
        LOGGER.debug('%s package query tool: %s', self.distro["Distributor"], self.cmd_dpkg)

        self.cmd_nvidia_smi = shutil.which('nvidia-smi')
        if self.cmd_nvidia_smi:
            print('OS command [nvidia-smi] executable found: [{}]'.format(self.cmd_nvidia_smi))
        if command_access_fail:
            return -3
        return 0

    def read_amd_driver_version(self) -> bool:
        """
        Read the AMD driver version and store in GutConst object.

        :return: True on success.
        """
        if not self.cmd_dpkg:
            print('Can not access package read utility to verify AMD driver.')
            return False
        if re.search(r'([uU]buntu|[dD]ebian)', self.distro['Distributor']):
            return self.read_amd_driver_version_debian()
        if re.search(r'([gG]entoo)', self.distro['Distributor']):
            return self.read_amd_driver_version_gentoo()
        if re.search(r'([aA]rch)', self.distro['Distributor']):
            return self.read_amd_driver_version_arch()
        return False

    def read_amd_driver_version_gentoo(self) -> bool:
        """
        Read the AMD driver version and store in GutConst object.

        :return: True if successful
        """
        for pkgname in ['dev-libs/amdgpu', 'dev-libs/amdgpu-pro-opencl', 'dev-libs/rocm', 'dev-libs/rocm-utils']:
            try:
                dpkg_out = subprocess.check_output(shlex.split('{} list {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            except (subprocess.CalledProcessError, OSError):
                continue
            for dpkg_line in dpkg_out:
                if '!!!' in dpkg_line:
                    continue
                for driverpkg in ['amdgpu', 'rocm']:
                    if re.search('Searching', dpkg_line):
                        continue
                    if re.search(driverpkg, dpkg_line):
                        LOGGER.debug(dpkg_line)
                        dpkg_line = re.sub(r'.*\][\s]*', '', dpkg_line)
                        print('AMD: {} version: {}'.format(driverpkg, dpkg_line))
                        return True
        print('amdgpu/rocm version: UNKNOWN')
        return False

    def read_amd_driver_version_arch(self) -> bool:
        """
        Read the AMD driver version and store in GutConst object.

        :return: True if successful
        """
        for pkgname in ['amdgpu', 'rocm', 'rocm-utils']:
            try:
                dpkg_out = subprocess.check_output(shlex.split('{} -Qs {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            except (subprocess.CalledProcessError, OSError):
                continue
            for dpkg_line in dpkg_out:
                for driverpkg in ['amdgpu', 'rocm']:
                    if re.search(driverpkg, dpkg_line):
                        LOGGER.debug(dpkg_line)
                        dpkg_items = dpkg_line.split()
                        if len(dpkg_items) >= 2:
                            print('AMD: {} version: {}'.format(driverpkg, dpkg_items[1]))
                            return True
        print('amdgpu/rocm version: UNKNOWN')
        return False

    def read_amd_driver_version_debian(self) -> bool:
        """
        Read the AMD driver version and store in GutConst object.

        :return: True if successful
        """
        for pkgname in ['amdgpu', 'amdgpu-core', 'amdgpu-pro', 'rocm-utils']:
            try:
                dpkg_out = subprocess.check_output(shlex.split('{} -l {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            except (subprocess.CalledProcessError, OSError):
                continue
            for dpkg_line in dpkg_out:
                for driverpkg in ['amdgpu', 'rocm']:
                    if re.search(driverpkg, dpkg_line):
                        LOGGER.debug(dpkg_line)
                        dpkg_items = dpkg_line.split()
                        if len(dpkg_items) > 2:
                            if re.fullmatch(r'.*none.*', dpkg_items[2]): continue
                            print('AMD: {} version: {}'.format(driverpkg, dpkg_items[2]))
                            return True
        print('amdgpu/rocm version: UNKNOWN')
        return False


GUT_CONST = GutConst()


def about() -> None:
    """
    Display details of this module.
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('Credits: ', *['\n      {}'.format(item) for item in __credits__])
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Install Type: ', GUT_CONST.install_type)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
