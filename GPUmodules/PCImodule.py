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
__author__ = "RueiKe"
__copyright__ = "Copyright (C) 2019 RueiKe"
__credits__ = [""]
__license__ = "GNU General Public License"
__program_name__ = "amdgpu-utils"
__version__ = "v2.2.0"
__maintainer__ = "RueiKe"
__status__ = "Development"

import re
import socket
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import glob 
import shutil 


class PCI_ID:
    def __init__(self, file_name="amd_pci_id.txt"):
        try:
            self.pci_id_file_ptr = open(os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name), 'r')
        except:
            print("Can not open [%s] to read. Exiting..." % os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name))


    def get_model(self, dev_id):
        """ For a device id dict of the format:
            {"vendor":"","device":"","subsystem_vendor":"","subsystem_device":""}
            search a PCI ID file extract from the PCI ID Repository and return the
            resultant Model Name as a string.
        """

        model_str = ""
        level = 0
        for line_item in self.pci_id_file_ptr:
            line = line_item.rstrip()
            if len(line)<4: continue
            if line[0] == '#': continue
            if level == 0:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[:4] == dev_id["vendor"].replace('0x',''):
                        level += 1
                        continue
            elif level == 1:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[1:5] == dev_id["device"].replace('0x',''):
                        model_str = line[5:]
                        level += 1
                        continue
            elif level == 2:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[2:6] == dev_id["subsystem_vendor"].replace('0x',''):
                        model_str = line[6:]
                        level += 1
                        continue
            elif level == 3:
                if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    break
                if re.fullmatch(r'^\t\t\t[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                    if line[3:7] == dev_id["subsystem_device"].replace('0x',''):
                        model_str = line[7:]
                        level += 1
                        continue
        return(model_str.strip())


def test():

    test_id = {'vendor': '0x1002', 'device': '0x687f', 'subsystem_vendor': '0x1002', 'subsystem_device': '0x0b36'}
    print(test_id)
    pci_id_file_name = "amd_pci_id.txt"

    pcid = PCI_ID(pci_id_file_name)
    model_name = pcid.get_model(test_id)
    print("Model name: %s" % model_name)


if __name__ == "__main__":
    test()

