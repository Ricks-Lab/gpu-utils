#!/usr/bin/env python3
"""env.py - Sets environment for rickslab-gpu-utils and establishes global
            variables.

    Copyright (C) 2019  RicksLab

    This program is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the Free
    Software Foundation, either version 3 of the License, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
    more details.

    You should have received a copy of the GNU General Public License along with
    this program.  If not, see <https://www.gnu.org/licenses/>.
"""
__author__ = 'RicksLab'
__copyright__ = 'Copyright (C) 2019 RicksLab'
__license__ = 'GNU General Public License'
__program_name__ = 'gpu-utils'
__maintainer__ = 'RicksLab'
__docformat__ = 'reStructuredText'
# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string

import argparse
import os
import re
import subprocess
from platform import release
import sys
import logging
from pathlib import Path
import inspect
from shlex import split as shlex_split
import shutil
from time import mktime as time_mktime
from datetime import datetime
from typing import Dict, Union, TextIO, Set, Optional
from GPUmodules import __required_pversion__, __required_kversion__

LOGGER = logging.getLogger('gpu-utils')


class GutConst:
    """
    GPU Utils constants used throughout the project.
    """
    # Private class variables
    _verified_distros: Set[str] = {'Debian', 'Ubuntu', 'Neon', 'Gentoo', 'Arch', 'Devuan'}
    _dpkg_tool: Dict[str, str] = {'Debian': 'dpkg', 'Ubuntu': 'dpkg', 'Neon': 'dpkg', 'Devuan': 'dpkg',
                                  'Arch': 'pacman',
                                  'Gentoo': 'equery'}
    _all_args: Set[str] = {'execute_pac', 'debug', 'pdebug', 'sleep', 'no_fan', 'ltz', 'simlog', 'log',
                           'force_all', 'force_write', 'verbose', 'no_markup'}
    _sys_pciid_list: Set[str] = {'/usr/share/misc/pci.ids', '/usr/share/hwdata/pci.ids', '/usr/share/doc/pci.ids'}
    _module_path: str = os.path.dirname(str(Path(__file__).resolve()))
    _repository_path: str = os.path.join(_module_path, '..')
    _local_config_list: Dict[str, str] = {
        'repository': _repository_path,
        'debian':     '/usr/share/rickslab-gpu-utils/config',
        'pypi-linux': os.path.join(str(Path.home()), '.local', 'share', 'rickslab-gpu-utils', 'config')}
    _local_icon_list: Dict[str, str] = {
        'repository': os.path.join(_repository_path, 'icons'),
        'debian':     '/usr/share/rickslab-gpu-utils/icons',
        'pypi-linux': '{}/.local/share/rickslab-gpu-utils/icons'.format(str(Path.home()))}
    _icons: Dict[str, str] = {'gpu-mon': 'gpu-mon.icon.png',
                              'gpu-plot': 'gpu-plot.icon.png',
                              'gpu-pac': 'gpu-pac.icon.png'}

    # Public class variables
    mark_up_codes: Dict[str, str] = {'none':      '',
                                     'bold':      '\033[1m',
                                     # Foreground colors
                                     'white':     '\033[37m',
                                     'data':      '\033[36m',
                                     'cyan':      '\033[36m',
                                     'purple':    '\033[35m',
                                     'blue':      '\033[34m',
                                     'yellow':    '\033[33m',
                                     'green':     '\033[32m',
                                     'red':       '\033[31m',
                                     # Named formats
                                     'amd':       '\033[1;37;41m',
                                     'error':     '\033[1;37;41m',
                                     'ok':        '\033[1;37;42m',
                                     'nvidia':    '\033[1;30;42m',
                                     'warn':      '\033[1;30;43m',
                                     'intel':     '\033[1;37;44m',
                                     'other':     '\033[1;37;45m',
                                     'label':     '\033[1;37;46m',
                                     'reset':     '\033[0;0;0m'}

    PATTERNS = {'HEXRGB':       re.compile(r'^#[\da-fA-F]{6}'),
                'PCIIID_L0':    re.compile(r'^[\da-fA-F]{4}.*'),
                'PCIIID_L1':    re.compile(r'^\t[\da-fA-F]{4}.*'),
                'PCIIID_L2':    re.compile(r'^\t\t[\da-fA-F]{4}.*'),
                'NUM_END_IN_ALPHA': re.compile(r'\d+[a-zA-Z]+$'),
                'END_IN_ALPHA': re.compile(r'[a-zA-Z]+$'),
                'ALPHA':        re.compile(r'[a-zA-Z]+'),
                'AMD_FEATURES': re.compile(r'^(Current pp)*\s*:*\s*features:*\s+', re.IGNORECASE),
                'AMD_GPU':      re.compile(r'(AMD|ATI)'),
                'NV_GPU':       re.compile(r'NVIDIA', re.IGNORECASE),
                'INTC_GPU':     re.compile(r'INTEL'),
                'ASPD_GPU':     re.compile(r'ASPEED', re.IGNORECASE),
                'MTRX_GPU':     re.compile(r'MATROX', re.IGNORECASE),
                'InputLabelX':  re.compile(r'[a-zA-Z]*(\d|\*)_(input|label)'),  # 'freq*_input'
                'MHz':          re.compile(r'M[Hh]z'),
                'PPM_CHK':      re.compile(r'[*].*'),
                'PCI_GPU':      re.compile(r'(VGA|3D|Display)', re.IGNORECASE),
                'NOT_PCI_GPU':  re.compile(r'Non-?VGA', re.IGNORECASE),
                'PCI_ADD':      re.compile(r'^(([\da-fA-F]{4}:)?[\da-fA-F]{2}:[\da-fA-F]{2}.[\da-fA-F])'),
                'PCI_ADD_LONG': re.compile(r'^([\da-fA-F]{4}:[\da-fA-F]{2}:[\da-fA-F]{2}.[\da-fA-F])'),
                'PCI_ADD_SHRT': re.compile(r'^([\da-fA-F]{2}:[\da-fA-F]{2}.[\da-fA-F])'),
                'PPM_NOTCHK':   re.compile(r'\s+'),
                'VALID_PS_STR': re.compile(r'\d+(\s\d)*'),
                'IS_FLOAT':     re.compile(r'[-+]?\d*\.?\d+|[-+]?\d+'),
                'DIGITS':       re.compile(r'^\d+\d*$'),
                'VAL_ITEM':     re.compile(r'.*_val$'),
                'GPU_GENERIC':  re.compile(r'(^\s|intel|amd|nvidia|amd/ati|ati|radeon|\[|])', re.IGNORECASE),
                'GPUMEMTYPE':   re.compile(r'^mem_(gtt|vram)_.*')}

    featuremask: str = '/sys/module/amdgpu/parameters/ppfeaturemask'
    card_root: str = '/sys/class/drm/'
    hwmon_sub: str = 'hwmon/hwmon'
    gui_window_title: str = 'Ricks-Lab GPU Utilities'
    mon_field_width: int = 20
    TIME_FORMAT: str = '%d-%b-%Y %H:%M:%S'

    def __init__(self):
        self.calling_program: str = ''
        self.args: Optional[argparse.Namespace] = None
        self.repository_path: str = self._repository_path
        self.install_type: Union[str, None] = None
        self.package_path: str = inspect.getfile(inspect.currentframe())

        if 'dist-packages' in self.package_path: self.install_type = 'debian'
        elif '.local' in self.package_path: self.install_type = 'pypi-linux'
        else: self.install_type = 'repository'
        self._icon_path = self._local_icon_list[self.install_type]
        self.icon_file = ''

        # Set pciid Path
        for try_pciid_path in GutConst._sys_pciid_list:
            if os.path.isfile(try_pciid_path):
                self.sys_pciid = try_pciid_path
                break
        else:
            print('Error: Invalid pciid path')
            self.sys_pciid = None

        self.distro: Dict[str, Union[str, None]] = {'Distributor': None, 'Description': None}
        self.amdfeaturemask: Union[int, None] = None
        self.log_file_ptr: Union[TextIO, None] = None

        # From args
        self.no_markup: bool = False
        self.force_all: bool = False
        self.execute_pac: bool = False
        self.verbose: bool = False
        self.debug: bool = False
        self.pdebug: bool = False
        self.simlog: bool = False
        self.log: bool = False
        self.plot: bool = False
        self.show_fans: bool = True
        self.write_delta_only: bool = False
        self.sleep: int = 2
        self.useltz: bool = False
        # Time
        self.ltz: datetime.tzinfo = datetime.utcnow().astimezone().tzinfo
        # Command access
        self.cmd_lsb_release: Union[str, None] = None
        self.cmd_lspci: Union[str, None] = None
        self.cmd_clinfo: Union[str, None] = None
        self.cmd_dpkg: Union[str, None] = None
        self.cmd_nvidia_smi: Union[str, None] = None

        # base_prefix = getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix
        # print('base_prefix: {}, sys_prefix: {}'.format(base_prefix, sys.prefix))
        # if base_prefix != sys.prefix:
        #     sys.path.append('/usr/lib/python3/dist-packages')

    def set_args(self, args: argparse.Namespace, program_name: str = '') -> None:
        """
        Set arguments for the give args object.

        :param args: The object return by args parser.
        :param program_name: The name of the calling program.
        """
        self.calling_program = program_name
        self.args = args
        for target_arg in self._all_args:
            if target_arg in self.args:
                if target_arg == 'debug': self.debug = self.args.debug
                elif target_arg == 'execute_pac': self.execute_pac = self.args.execute_pac
                elif target_arg == 'pdebug': self.pdebug = self.args.pdebug
                elif target_arg == 'sleep': self.sleep = self.args.sleep
                elif target_arg == 'no_fan': self.show_fans = not self.args.no_fan
                elif target_arg == 'ltz': self.useltz = self.args.ltz
                elif target_arg == 'simlog': self.simlog = self.args.simlog
                elif target_arg == 'log': self.log = self.args.log
                elif target_arg == 'no_markup': self.no_markup = self.args.no_markup
                elif target_arg == 'force_all': self.force_all = self.args.force_all
                elif target_arg == 'verbose': self.verbose = self.args.verbose
                elif target_arg == 'force_write': self.write_delta_only = not self.args.force_write
                else: print('Invalid arg: {}'.format(target_arg))
        LOGGER.propagate = False
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(module)s.%(funcName)s:%(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.WARNING)
        LOGGER.addHandler(stream_handler)
        LOGGER.setLevel(logging.WARNING)
        if self.debug:
            LOGGER.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                'debug_gpu-utils_{}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S")), 'w')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            LOGGER.addHandler(file_handler)
        LOGGER.debug('Install type: %s', self.install_type)
        LOGGER.debug('Calling program: %s', program_name)
        LOGGER.debug('Command line arguments:\n  %s', args)
        LOGGER.debug('Local TZ: %s', self.ltz)
        LOGGER.debug('pciid path set to: %s', self.sys_pciid)
        LOGGER.debug('Icon path set to: %s', self._icon_path)
        try:
            self.icon_file = os.path.join(self._icon_path, self._icons[program_name])
        except KeyError:
            self.icon_file = None
        else:
            if not os.path.isfile(self.icon_file):
                self.process_message('Error: Icon file not found: [{}]'.format(self.icon_file), log_flag=True)

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

    def process_message(self, message: str, log_flag: bool = False) -> None:
        """
        For given message, print to stderr and/or LOGGER depending on command line options and
        the value of log_flag.

        :param message: A string containing the message to be processed.
        :param log_flag:  If True, write to LOGGER.
        """
        if not message: return
        if self.verbose: print(message, file=sys.stderr)
        if log_flag: LOGGER.debug(message)

    def read_amdfeaturemask(self) -> int:
        """
        Read and return the amdfeaturemask as an int.

        :return: AMD Feature Mask
        """
        try:
            with open(self.featuremask, 'r', encoding='utf-8') as fm_file:
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
        current_pversion = sys.version_info
        LOGGER.debug('Using python: %s', current_pversion)
        if current_pversion[:2] < __required_pversion__:
            print('Using python {}.{}.{}, but {} requires python {}.{} or higher.'.format(
                current_pversion[0], current_pversion[1], current_pversion[2],
                __program_name__, __required_pversion__[0], __required_pversion__[1]),
                  file=sys.stderr)
            return -1

        # Check Linux Kernel version
        current_kversion_str = release()
        current_kversion = tuple([int(x) for x in re.sub('-.*', '', current_kversion_str).split('.')])
        LOGGER.debug('Using Linux Kernel: %s', current_kversion_str)
        if current_kversion < __required_kversion__:
            print('Using Linux Kernel {}, but {} requires > {}.{}.'.format(
                current_kversion_str, __program_name__, __required_kversion__[0],
                __required_kversion__[1]), file=sys.stderr)
            return -2

        # Check Linux Init Type
        init_type = 'Unknown'
        cmd_init = '/sbin/init' if os.path.isfile('/sbin/init') else shutil.which('init')
        if cmd_init:
            if os.path.islink(cmd_init):
                sys_path = os.readlink(cmd_init)
                init_type = 'systemd' if 'systemd' in sys_path else sys_path
        self.process_message('System Type: {}'.format(init_type), log_flag=True)

        # Check Linux Distro
        self.cmd_lsb_release = shutil.which('lsb_release')
        if self.cmd_lsb_release:
            lsbr_out = subprocess.check_output(shlex_split('{} -a'.format(self.cmd_lsb_release)),
                                               shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            for lsbr_line in lsbr_out:
                if 'Distributor ID' in lsbr_line:
                    lsbr_item = re.sub(r'Distributor ID:\s*', '', lsbr_line)
                    LOGGER.debug('Using Linux Distro: %s', lsbr_item)
                    self.distro['Distributor'] = lsbr_item.strip()
                if 'Description' in lsbr_line:
                    lsbr_item = re.sub(r'Description:\s*', '', lsbr_line)
                    LOGGER.debug('Linux Distro Description: %s', lsbr_item)
                    self.distro['Description'] = lsbr_item.strip()

            if self.distro['Distributor'] and self.debug:
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
            if 'clinfo' in self.args:
                print('Addon Package [clinfo] executable not found.  Use \'sudo apt install clinfo\' to install')
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
        LOGGER.debug('nvidia-smi executable full path: [%s]', self.cmd_nvidia_smi)
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
        for pkgname in ('dev-libs/amdgpu', 'dev-libs/amdgpu-pro-opencl', 'dev-libs/rocm', 'dev-libs/rocm-utils'):
            try:
                dpkg_out = subprocess.check_output(shlex_split('{} list {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            except (subprocess.CalledProcessError, OSError):
                continue
            for dpkg_line in dpkg_out:
                if '!!!' in dpkg_line:
                    continue
                for driverpkg in ('amdgpu', 'rocm'):
                    if re.search('Searching', dpkg_line):
                        continue
                    if re.search(driverpkg, dpkg_line):
                        LOGGER.debug(dpkg_line)
                        dpkg_line = re.sub(r'.*]\s*', '', dpkg_line)
                        print('AMD: {} version: {}'.format(driverpkg, dpkg_line))
                        return True
        print('AMD: amdgpu/rocm version: UNKNOWN')
        return False

    def read_amd_driver_version_arch(self) -> bool:
        """
        Read the AMD driver version and store in GutConst object.

        :return: True if successful
        """
        for pkgname in ('amdgpu', 'rocm', 'rocm-utils'):
            try:
                dpkg_out = subprocess.check_output(shlex_split('{} -Qs {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            except (subprocess.CalledProcessError, OSError):
                continue
            for dpkg_line in dpkg_out:
                for driverpkg in ('amdgpu', 'rocm'):
                    if re.search(driverpkg, dpkg_line):
                        LOGGER.debug(dpkg_line)
                        dpkg_items = dpkg_line.split()
                        if len(dpkg_items) >= 2:
                            print('AMD: {} version: {}'.format(driverpkg, dpkg_items[1]))
                            return True
        print('AMD: amdgpu/rocm version: UNKNOWN')
        return False

    def read_amd_driver_version_debian(self) -> bool:
        """
        Read the AMD driver version and store in GutConst object.

        :return: True if successful
        """
        for pkgname in ('amdgpu', 'amdgpu-core', 'amdgpu-pro', 'rocm-utils'):
            try:
                dpkg_out = subprocess.check_output(shlex_split('{} -l {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
            except (subprocess.CalledProcessError, OSError):
                continue
            for dpkg_line in dpkg_out:
                for driverpkg in ('amdgpu', 'rocm'):
                    if re.search(driverpkg, dpkg_line):
                        LOGGER.debug(dpkg_line)
                        dpkg_items = dpkg_line.split()
                        if len(dpkg_items) > 2:
                            if re.fullmatch(r'.*none.*', dpkg_items[2]): continue
                            print('AMD: {} version: {}'.format(driverpkg, dpkg_items[2]))
                            return True
        print('AMD: amdgpu/rocm version: UNKNOWN')
        return False


GUT_CONST = GutConst()
