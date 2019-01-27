#!/usr/bin/env python3
"""GPUmodules  -  classes used in amdgpu-utils


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
__credits__ = ""
__license__ = "GNU General Public License"
__program_name__ = "benchMT"
__version__ = "v0.1.0"
__maintainer__ = "RueiKe"
__status__ = "Development"

import re
import subprocess
import shlex
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

#/sys/class/drm/card0/device/pp_od_clk_voltage
#echo "m 0 155 900" > /sys/class/drm/card0/device/pp_od_clk_voltage
#echo "s 7 975 1180" > /sys/class/drm/card0/device/pp_od_clk_voltage
# commit the changes to the hw
#echo "c" > /sys/class/drm/card0/device/pp_od_clk_voltage
# reset to the default dpm states
#echo "r" > /sys/class/drm/card0/device/pp_od_clk_voltage
# commit the reset state to the hw
#echo "c" > /sys/class/drm/card0/device/pp_od_clk_voltage

class GUT_CONST:
    def __init__(self):
        self.featuremask = "/sys/module/amdgpu/parameters/ppfeaturemask"
        self.card_root = "/sys/class/drm/"
        self.hwmon_sub = "/hwmon/hwmon"
        self.cur_power = "power1_average"
        self.cur_temp = "temp1_average"
        self.DEBUG = False
        self.amdfeaturemask = ""

    def read_amdfeaturemask(self):
        with open(gut_const.featuremask) as fm_file:
            self.amdfeaturemask = int(fm_file.readline())
            return (self.amdfeaturemask)

gut_const = GUT_CONST()


class GPU_STAT:
    def __init__(self, item_id):
        self.uuid = item_id
        self.card_num = ""
        self.pcie_id = ""
        self.driver = ""
        self.model = ""
        self.card_path = ""
        self.hwmon_path = ""
        self.power = -1
        self.temp = -1
        self.vddgfx = -1
        self.loading = -1
        self.mclk_ps = -1
        self.mclk_f = ""
        self.sclk_ps = -1
        self.sclk_f = ""
        self.link_spd = ""
        self.link_wth = ""
        self.vbios = ""

    def read_hw_data(self):
        if(os.path.isfile(self.hwmon_path + "power1_average") == True):
            with open(self.hwmon_path + "power1_average") as hwmon_file:
                self.power = int(hwmon_file.readline())
        if(os.path.isfile(self.hwmon_path + "temp1_input") == True):
            with open(self.hwmon_path + "temp1_input") as hwmon_file:
                self.temp = int(hwmon_file.readline())
        if(os.path.isfile(self.hwmon_path + "in0_label") == True):
            with open(self.hwmon_path + "in0_label") as hwmon_file:
                if hwmon_file.readline().rstrip() == "vddgfx":
                    with open(self.hwmon_path + "in0_input") as hwmon_file2:
                        self.vddgfx = int(hwmon_file2.readline())

    def read_device_data(self):
        if(os.path.isfile(self.card_path + "gpu_busy_percent") == True):
            with open(self.card_path + "gpu_busy_percent") as card_file:
                self.loading = int(card_file.readline())
        if(os.path.isfile(self.card_path + "current_link_speed") == True):
            with open(self.card_path + "current_link_speed") as card_file:
                self.link_spd = card_file.readline().strip()
        if(os.path.isfile(self.card_path + "current_link_width") == True):
            with open(self.card_path + "current_link_width") as card_file:
                self.link_wth = card_file.readline().strip()
        if(os.path.isfile(self.card_path + "vbios_version") == True):
            with open(self.card_path + "vbios_version") as card_file:
                self.vbios = card_file.readline().strip()
        if(os.path.isfile(self.card_path + "pp_dpm_sclk") == True):
            with open(self.card_path + "pp_dpm_sclk") as card_file:
                for line in card_file:
                    if line[len(line)-2] == "*":
                        lineitems = line.split(sep=':')
                        self.sclk_ps = lineitems[0].strip()
                        self.sclk_f = lineitems[1].strip().strip('*')
        if(os.path.isfile(self.card_path + "pp_dpm_mclk") == True):
            with open(self.card_path + "pp_dpm_mclk") as card_file:
                for line in card_file:
                    if line[len(line)-2] == "*":
                        lineitems = line.split(sep=':')
                        self.mclk_ps = lineitems[0].strip()
                        self.mclk_f = lineitems[1].strip().strip('*')

    def print(self):
        print("UUID: ", self.uuid)
        print("Card Model: ", self.model)
        print("Card Number: ", self.card_num)
        print("Card Path: ", self.card_path)
        print("PCIe ID: ", self.pcie_id)
        print("Driver: ", self.driver)
        print("HWmon: ", self.hwmon_path)
        print("Power: ", self.power/1000000,"W")
        print("Temp: ", self.temp/1000, "C")
        print("VddGFX: ", self.vddgfx, "mV")
        print("Loading: ", self.loading, "%")
        print("Link Speed: ", self.link_spd)
        print("Link Width: ", self.link_wth)
        print("vBIOS Version: ", self.vbios)
        print("SCLK P-State: ", self.sclk_ps)
        print("SCLK: ", self.sclk_f)
        print("MCLK P-State: ", self.mclk_ps)
        print("MCLK: ", self.mclk_f)
        print("")


class GPU_LIST:
    def __init__(self):
        self.list = {}

    def get_gpu_list(self):
        for card_names in glob.glob(gut_const.card_root + "card?/device/pp_od_clk_voltage"):
            gpu_item = GPU_STAT(uuid4().hex)
            gpu_item.card_path = card_names.replace("pp_od_clk_voltage",'')
            gpu_item.card_num = card_names.replace("/device/pp_od_clk_voltage",'').replace(gut_const.card_root + "card", '')
            gpu_item.hwmon_path = gpu_item.card_path + gut_const.hwmon_sub + gpu_item.card_num + "/"
            self.list[gpu_item.uuid] = gpu_item

    def read_hw_data(self):
        for k, v in self.list.items():
            v.read_hw_data()

    def read_device_data(self):
        for k, v in self.list.items():
            v.read_device_data()

    def get_gpu_details(self):
        pcie_ids = subprocess.check_output(
            'lspci | grep -E \"^.*(VGA|Display).*\[AMD\/ATI\].*$\" | grep -Eo \"^([0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F])\"',
            shell=True).decode().split()
        if gut_const.DEBUG: print("Found %s GPUs" % len(pcie_ids))
        for pcie_id in pcie_ids:
            if gut_const.DEBUG: print("GPU: ", pcie_id)
            lspci_items = subprocess.check_output("lspci -k -s " + pcie_id, shell=True).decode().split("\n")
            #gpu_name = lspci_items[1].split('[')[2].replace(']','')
            gpu_name = lspci_items[1].split('[AMD/ATI]')[1]
            driver_module = lspci_items[2].split(':')[1]
            if gut_const.DEBUG: print(lspci_items)
            # Find matching card
            device_dirs = glob.glob(gut_const.card_root + "card?/device")
            for device_dir in device_dirs:
                sysfspath = str(Path(device_dir).resolve())
                if gut_const.DEBUG: print("device_dir: ", device_dir)
                if gut_const.DEBUG: print("sysfspath: ", sysfspath)
                if gut_const.DEBUG: print("pcie_id: ", pcie_id)
                if gut_const.DEBUG: print("sysfspath-7: ", sysfspath[-7:])
                if pcie_id == sysfspath[-7:]:
                    for k, v in self.list.items():
                        if v.card_path == device_dir + '/':
                            v.pcie_id = pcie_id
                            v.driver = driver_module
                            v.model = gpu_name
                            break
                    break

    def num_gpus(self):
        cnt = 0
        for k, v in self.list.items():
            cnt += 1
        return(cnt)

    def print(self):
        for k, v in self.list.items():
            v.print()

    def print_table(self):
        num_gpus = self.num_gpus()
        if num_gpus < 1: return(-1)

        print("┌", "─".ljust(8,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┬", "─".ljust(12,'─'), sep="", end="")
        print("┐")

        print("│", " ".ljust(8,' '), sep="", end="")
        for k, v in self.list.items():
            print("│", '\x1b[1;36m'+("card"+ v.card_num).ljust(12,' ') + '\x1b[0m', sep="", end="")
        print("│")

        print("├", "─".ljust(8,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┼", "─".ljust(12,'─'), sep="", end="")
        print("┤")

        print("│", '\x1b[1;36m'+"Model".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
            print("│", (v.model.replace("Radeon",'')).ljust(12,' ')[:12], sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Load".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", (str(v.loading) + "%").ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Power".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", (str(v.power/1000000) +"W").ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Temp".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", (str(v.temp/1000) + "C").ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"VddGFX".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", (str(v.vddgfx) + "mV").ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Sclk".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", str(v.sclk_f).ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Sclk-Pst".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", (str(v.sclk_ps)).ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Mclk".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", str(v.mclk_f).ljust(12,' '), sep="", end="")
        print("│")

        print("│", '\x1b[1;36m'+"Mclk-Pst".ljust(8,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
                print("│", (str(v.mclk_ps)).ljust(12,' '), sep="", end="")
        print("│")

        print("└", "─".ljust(8,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┴", "─".ljust(12,'─'), sep="", end="")
        print("┘")

        
def test():
    gut_const.DEBUG = True

    try:
        featuremask = gut_const.read_amdfeaturemask()
    except FileNotFoundError:
        print("Cannot read ppfeaturemask. Exiting...")
        sys.exit(-1)
    if featuremask == int(0xffff7fff) or featuremask == int(0xffffffff) :
        print("AMD Wattman features enabled: %s" % hex(featuremask))
    else:
        print("AMD Wattman features not enabled: %s, See README file." % hex(featuremask))
        sys.exit(-1)


    gpu_list = GPU_LIST()
    gpu_list.get_gpu_list()
    gpu_list.read_hw_data()
    gpu_list.read_device_data()
    gpu_list.get_gpu_details()
    gpu_list.print_table()
    gpu_list.print()


if __name__ == "__main__":
    test()

