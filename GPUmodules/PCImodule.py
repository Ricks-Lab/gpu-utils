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
import urllib.request


class PCI_ID:
    def __init__(self, file_name="amd_pci_id.txt"):
        self.pciid_url = "https://pci-ids.ucw.cz/v2.2/pci.ids"
        self.pciid_file = "pci.ids"
        self.amdgpu_utils_file = os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name)
        try:
            #self.pci_id_file_ptr = open(os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name), 'r')
            self.pci_id_file_ptr = open(self.amdgpu_utils_file, 'r')
        except:
            print("Can not open [%s] to read. Exiting..." % os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name))


    def get_pciid_version(self, filename=""):
        """ Get version information of specified pci.ids file. 
            Look for these lines:
                #       Version: 2019.02.23
                #       Date:    2019-02-23 03:15:02

            return version details as a string
        """
        if filename == "":
            get_file_ptr = self.pci_id_file_ptr
        else:
            get_file_ptr = open(filename, 'r')

        file_version = "Unknown"
        file_date = "Unknown"
        for line in get_file_ptr:
            if line[0] != '#':
                break
            searchObj = re.search('Version:', line.strip())
            if(searchObj != None):
                lineItem = line.split(':')
                if len(lineItem) > 1:
                    file_version = lineItem[1].strip()
            searchObj = re.search('Date:', line.strip())
            if(searchObj != None):
                lineItem = line.split(':')
                if len(lineItem) > 1:
                    file_date = lineItem[1].strip()
                break
        return("Version: "+ file_version + ", Date: " + file_date)

    def download_pciid(self):
        """ download from https://pci-ids.ucw.cz/v2.2/pci.ids

            return the new downloaded data's filename as a string
        """
        file_name = self.pciid_file + datetime.utcnow().strftime('%m%d_%H%M%S') + ".txt"
        #response = urllib.request.urlretrieve(self.pciid_url, self.pciid_file)
        with urllib.request.urlopen(self.pciid_url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        return(file_name)

    def update_pci_id(self, in_file_name):
        self.pci_id_file_ptr.close()
        self.extract_vendor_from_pci_id("0x1002", in_file_name, self.amdgpu_utils_file)
        #self.pci_id_file_ptr = open(os.path.join(os.path.dirname(str(Path(__file__).resolve())), file_name), 'r')
        return(0)

    def extract_vendor_from_pci_id(self, vendor, in_file_name, out_file_name=""):
        """ For a given vendor id, extract all relevant entries.
        """
        try:
            in_file_ptr = open(in_file_name, 'r')
        except:
            print("Can not open [%s] to read. Exiting..." % in_file_name)
            sys.exit(-1)

        if out_file_name == "":
            file_ptr=sys.stdout
        else:
            shutil.copy2(out_file_name, out_file_name + datetime.utcnow().strftime('%m%d_%H%M%S'))
            try:
                file_ptr = open(out_file_name, 'w')
            except:
                print("Can not open [%s] to write. Exiting..." % out_file_name)
                sys.exit(-1)


        level = -1
        vendor_match = False
        for line_item in in_file_ptr:
            line = line_item.rstrip()
            if level == -1:
                if len(line)<4:
                    print(line, file=file_ptr)
                    continue
                if line[0] == '#':
                    print(line, file=file_ptr)
                    continue
            if re.fullmatch(r'^[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].*', line):
                level = 0
                if vendor_match == True:
                    break
            if vendor_match == True:
                print(line, file=file_ptr)
                continue
            if line[:4] == vendor.replace('0x',''):
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
                        if line[7:11] == dev_id["subsystem_device"].replace('0x',''):
                            model_str = line[11:]
                            break
        return(model_str.strip())


def test():

    test_id = {'vendor': '0x1002', 'device': '0x687f', 'subsystem_vendor': '0x1002', 'subsystem_device': '0x0b36'}
    #test_id = {'vendor': '0x1002', 'device': '0x67df', 'subsystem_vendor': '0x1462', 'subsystem_device': '0x3416'}
    test_id =  {'vendor': '0x1002', 'device': '0x67ef', 'subsystem_vendor': '0x103c', 'subsystem_device': '0x3421'}
    test_id =  {'vendor': '0x1002', 'device': '0x67df', 'subsystem_vendor': '0x1682', 'subsystem_device': '0xc570'}
    #print(test_id)
    pci_id_file_name = "amd_pci_id.txt"
    vendor = "0x1002"

    pciid = PCI_ID(pci_id_file_name)
    pciid.update_pci_id("pci.ids0302_084015.txt")
    #pciid.download_pciid()
    #model_name = pciid.get_model(test_id)
    #print("Model name: %s" % model_name)
    #pciid.extract_vendor_from_pci_id(vendor)


if __name__ == "__main__":
    test()

