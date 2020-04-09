#!/usr/bin/env python3
"""env.py - sets environment for amdgpu-utils and establishes global variables


    Copyright (C) 2019  RueiKe

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
__copyright__ = 'Copyright (C) 2019 RueiKe'
__credits__ = ['Craig Echt - Testing, Debug, and Verification']
__license__ = 'GNU General Public License'
__program_name__ = 'amdgpu-utils'
__version__ = 'v3.0.1'
__maintainer__ = 'RueiKe'
__status__ = 'Stable Release'
__docformat__ = 'reStructuredText'
# pylint: disable=multiple-statements
# pylint: disable=line-too-long

import re
import subprocess
import platform
import sys
import os
from pathlib import Path
import shlex
import shutil
import time
from datetime import datetime


class GutConst:
    """
    GPU Utils constants used throughout the project.
    """
    def __init__(self):
        self.repository_module_path = os.path.dirname(str(Path(__file__).resolve()))
        self.repository_path = os.path.join(self.repository_module_path, '..')
        self.config_dir = os.path.join(os.getenv('HOME'), '.amdgpu-utils/')
        self.dist_share = '/usr/share/ricks-amdgpu-utils/'
        self.sys_pciid = '/usr/share/misc/pci.ids'
        self.dist_icons = os.path.join(self.dist_share, 'icons')
        if os.path.isdir(self.dist_icons):
            self.icon_path = self.dist_icons
        else:
            self.icon_path = os.path.join(self.repository_path, 'icons')
        self.featuremask = '/sys/module/amdgpu/parameters/ppfeaturemask'
        self.card_root = '/sys/class/drm/'
        self.hwmon_sub = 'hwmon/hwmon'
        self.execute_pac = False
        self.DEBUG = False
        self.PDEBUG = False
        self.SIMLOG = False
        self.LOG = False
        self.PLOT = False
        self.log_file_ptr = ''
        self.show_fans = True
        self.write_delta_only = False
        self.SLEEP = 2
        self.amdfeaturemask = ''
        self.USELTZ = False
        self.LTZ = datetime.utcnow().astimezone().tzinfo
        if self.DEBUG: print('Local TZ: {}'.format(self.LTZ))
        # GPU platform capability
        self.amd_read = None
        self.amd_write = None
        self.nv_read = None
        self.nv_write = None
        # Command access
        self.cmd_lspci = None
        self.cmd_clinfo = None
        self.cmd_dpkg = None
        self.cmd_nvidia_smi = None

    @staticmethod
    def now(ltz=False):
        """
        Get the current datetime object.
        :param ltz: Flag to get local time instead of UTC
        :type ltz: bool
        :return:
        :rtype: datetime
        """
        if ltz:
            return datetime.now()
        return datetime.utcnow()

    @staticmethod
    def utc2local(utc):
        """
        Return local time for given UTC time.
        :param utc:
        :type utc: datetime
        :return:
        :rtype: datetime
        .. note:: from https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime
        """
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
        return utc + offset

    def read_amdfeaturemask(self):
        """
        Read and return the amdfeaturemask as an int.
        :return:
        :rtype: int
        """
        with open(self.featuremask) as fm_file:
            self.amdfeaturemask = int(fm_file.readline())
            return self.amdfeaturemask

    def check_env(self):
        """
        Check the compatibility of the user environment.
        :return: Return status: ok=0, python issue= -1, kernel issue= -2, command issue= -3
        :rtype: int
        """
        # Check python version
        required_pversion = [3, 6]
        (python_major, python_minor, python_patch) = platform.python_version_tuple()
        if self.DEBUG: print('Using python: {}.{}.{}'.format(python_major, python_minor, python_patch))
        if int(python_major) < required_pversion[0]:
            print('Using python {}, but {} requires python {}.{} or higher.'.format(python_major, __program_name__,
                                                                                    required_pversion[0],
                                                                                    required_pversion[1]),
                  file=sys.stderr)
            return -1
        elif int(python_major) == required_pversion[0] and int(python_minor) < required_pversion[1]:
            print('Using python {}.{}.{}, but {} requires python {}.{} or higher.'.format(python_major, python_minor,
                                                                                          python_patch,
                                                                                          __program_name__,
                                                                                          required_pversion[0],
                                                                                          required_pversion[1]),
                  file=sys.stderr)
            return -1

        # Check Linux Kernel version
        required_kversion = [4, 8]
        linux_version = platform.release()
        if self.DEBUG: print('Using Linux Kernel: {}'.format(linux_version))
        if int(linux_version.split('.')[0]) < required_kversion[0]:
            print('Using Linux Kernel {}, but {} requires > {}.{}.'.format(linux_version, __program_name__,
                  required_kversion[0], required_kversion[1]), file=sys.stderr)
            return -2
        elif int(linux_version.split('.')[0]) == required_kversion[0] and \
                int(linux_version.split('.')[1]) < required_kversion[1]:
            print('Using Linux Kernel {}, but {} requires > {}.{}.'.format(linux_version, __program_name__,
                  required_kversion[0], required_kversion[1]), file=sys.stderr)
            return -2

        # Check access/paths to system commands
        command_access_fail = False
        self.cmd_lspci = shutil.which('lspci')
        if not self.cmd_lspci:
            print('OS command [lspci] executable not found.')
            command_access_fail = True
        self.cmd_clinfo = shutil.which('clinfo')
        if not self.cmd_clinfo:
            print('Package addon [clinfo] executable not found.  Use sudo apt-get install clinfo to install')
            #command_access_fail = True
        self.cmd_dpkg = shutil.which('dpkg')
        if not self.cmd_dpkg:
            print('OS command [dpkg] executable not found.')
            #command_access_fail = True
        self.cmd_nvidia_smi = shutil.which('nvidia_smi')
        if not self.cmd_nvidia_smi:
            pass
            #print('OS command [nvidia_smi] executable not found.')
            #command_access_fail = True
        if command_access_fail:
            return -3
        return 0

    def read_amd_driver_version(self):
        """
        Read the AMD driver version and store in GutConst object.
        :return: True if successful
        :rtype: bool
        """
        if not self.cmd_dpkg:
            print('Command {} not found. Can not determine amdgpu version.'.format(self.cmd_dpkg))
            return False
        version_ok = False
        for pkgname in ['amdgpu', 'amdgpu-core', 'amdgpu-pro', 'rocm-utils']:
            try:
                dpkg_out = subprocess.check_output(shlex.split('{} -l {}'.format(self.cmd_dpkg, pkgname)),
                                                   shell=False, stderr=subprocess.DEVNULL).decode().split('\n')
                for dpkg_line in dpkg_out:
                    for driverpkg in ['amdgpu', 'rocm']:
                        search_obj = re.search(driverpkg, dpkg_line)
                        if search_obj:
                            if self.DEBUG: print('Debug: {}'.format(dpkg_line))
                            dpkg_items = dpkg_line.split()
                            if len(dpkg_items) > 2:
                                if re.fullmatch(r'.*none.*', dpkg_items[2]):
                                    continue
                                else:
                                    print('AMD: {} version: {}'.format(driverpkg, dpkg_items[2]))
                                    version_ok = True
                                    break
                if version_ok:
                    break
            except (subprocess.CalledProcessError, OSError):
                continue
        if not version_ok:
            print('amdgpu/rocm version: UNKNOWN')
            return False
        return True


GUT_CONST = GutConst()


def about():
    """
    Display details of this module.
    :return: None
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('Credits: ', __credits__)
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
