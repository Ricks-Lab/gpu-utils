#!/usr/bin/env python3
"""PCImodules  -  classes to parse PCI ID Repository file https://pci-ids.ucw.cz/

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
__credits__ = ['']
__license__ = 'GNU General Public License'
__program_name__ = 'amdgpu-utils'
__version__ = 'v2.7.0'
__maintainer__ = 'RueiKe'
__status__ = 'Stable Release'

import re
import os
import sys
from datetime import datetime
from pathlib import Path
import shutil
import urllib.request

try:
    from GPUmodules import env
except:
    import env


class PCI_ID:
    def __init__(self, file_name='amd_pci_id.txt'):
        self.pciid_url = 'https://pci-ids.ucw.cz/v2.2/pci.ids'
        self.pciid_file = 'pci.ids'    # base of name for downloaded file

        # Possible locations of PCI ID files
        self.pciid_file_local = os.path.join(env.gut_const.config_dir, file_name)
        self.pciid_file_distribution = os.path.join(env.gut_const.dist_share, file_name)
        self.pciid_file_repository = os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name)

        # Details on PCI-ID file in use
        self.file_open_status = False
        self.amdgpu_utils_file = None
        self.pci_id_file_ptr = None

        for try_filename in [self.pciid_file_local, self.pciid_file_distribution, self.pciid_file_repository]:
            if env.gut_const.DEBUG: print('Trying pci-id file [{}].'.format(try_filename))
            self.amdgpu_utils_file = try_filename
            if not os.path.isfile(self.amdgpu_utils_file):
                continue
            try:
                self.pci_id_file_ptr = open(self.amdgpu_utils_file, 'r')
            except FileNotFoundError:
                print('File [%s] not found.' %
                      os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name))
                continue
            except OSError:
                print('Can not open [%s] to read.' %
                      os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name))
                continue
            finally:
                self.file_open_status = True
                return
        if not self.file_open_status:
            print('Can not find a valid PCI-ID file: [%s]. Exiting...' % file_name)
            sys.exit(-1)

    def get_pciid_version(self, filename=''):
        """ Get version information of specified pci.ids file. 
            Look for these lines:
                #       Version: 2019.02.23
                #       Date:    2019-02-23 03:15:02

            return version details as a string
        """
        if filename == '':
            get_file_ptr = self.pci_id_file_ptr
        else:
            get_file_ptr = open(filename, 'r')

        file_version = 'Unknown'
        file_date = 'Unknown'
        for line in get_file_ptr:
            if line[0] != '#':
                break
            searchObj = re.search('Version:', line.strip())
            if searchObj:
                lineItem = line.split(':', 1)
                if len(lineItem) > 1:
                    file_version = lineItem[1].strip()
            searchObj = re.search('Date:', line.strip())
            if searchObj:
                lineItem = line.split(':', 1)
                if len(lineItem) > 1:
                    file_date = lineItem[1].strip()
                break
        return 'Version: ' + file_version + ', Date: ' + file_date

    def download_pciid(self):
        """ download from https://pci-ids.ucw.cz/v2.2/pci.ids

            return the new downloaded data's filename as a string
        """
        file_name = self.pciid_file + datetime.utcnow().strftime('%m%d_%H%M%S') + '.txt'
        with urllib.request.urlopen(self.pciid_url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        if os.path.isfile(file_name):
            return file_name
        else:
            return None

    def update_pci_id(self, in_file_name, target=None):
        if not target:
            target = self.pciid_file_local
        if not os.path.isdir(env.gut_const.config_dir):
            os.mkdir(env.gut_const.config_dir)
        if not os.path.isdir(env.gut_const.config_dir):
            print('ERROR: could not create amdgpu-utils config directory: [{}]'.format(env.gut_const.config_dir))
            sys.exit(-1)
        self.pci_id_file_ptr.close()
        # self.extract_vendor_from_pci_id('0x1002', in_file_name, self.amdgpu_utils_file)
        self.extract_vendor_from_pci_id('0x1002', in_file_name, target)
        self.file_open_status = False
        self.amdgpu_utils_file = self.pciid_file_local
        self.pci_id_file_ptr = None
        return 0

    @staticmethod
    def extract_vendor_from_pci_id(vendor, in_file_name, out_file_name=''):
        """ For a given vendor id, extract all relevant entries.

            Write extracted entries to out_file_name if specified.
        """
        try:
            in_file_ptr = open(in_file_name, 'r')
        except FileNotFoundError:
            print('File [%s] not found. Exiting...' % in_file_name)
            sys.exit(-1)
        except OSError:
            print('Can not open [%s] to read. Exiting...' % in_file_name)
            sys.exit(-1)

        if out_file_name == '':
            file_ptr = sys.stdout
        else:
            if os.path.isfile(out_file_name):
                shutil.copy2(out_file_name, out_file_name + datetime.utcnow().strftime('%m%d_%H%M%S'))
            try:
                file_ptr = open(out_file_name, 'w')
            except OSError:
                print('Can not open [%s] to write. Exiting...' % out_file_name)
                sys.exit(-1)

        level = -1
        vendor_match = False
        for line_item in in_file_ptr:
            line = line_item.rstrip()
            if level == -1:
                if len(line) < 4:
                    print(line, file=file_ptr)
                    continue
                if line[0] == '#':
                    print(line, file=file_ptr)
                    continue
            if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                level = 0
                if vendor_match:
                    break
            if vendor_match:
                print(line, file=file_ptr)
                continue
            if line[:4] == vendor.replace('0x', ''):
                vendor_match = True
                print(line, file=file_ptr)
                continue
        in_file_ptr.close()
        return

    def get_model(self, dev_id):
        """ For a device id dict of the format:
            {"vendor":"","device":"","subsystem_vendor":"","subsystem_device":""}
            search a PCI ID file extract from the PCI ID Repository and return the
            resultant Model Name as a string.
        """

        self.pci_id_file_ptr = open(self.amdgpu_utils_file, 'r')
        model_str = ''
        level = 0
        for line_item in self.pci_id_file_ptr:
            line = line_item.rstrip()
            if len(line) < 4:
                continue
            if line[0] == '#':
                continue
            if level == 0:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[:4] == dev_id['vendor'].replace('0x', ''):
                        level += 1
                        continue
            elif level == 1:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[1:5] == dev_id['device'].replace('0x', ''):
                        model_str = line[5:]
                        level += 1
                        continue
            elif level == 2:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[2:6] == dev_id['subsystem_vendor'].replace('0x', ''):
                        if line[7:11] == dev_id['subsystem_device'].replace('0x', ''):
                            model_str = line[11:]
                            break
        return model_str.strip()


def about():
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
