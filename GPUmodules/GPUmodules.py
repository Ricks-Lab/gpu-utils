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
__version__ = "v0.3.0"
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
        self.SLEEP = 2
        self.PATH = "."
        self.amdfeaturemask = ""

    def read_amdfeaturemask(self):
        with open(gut_const.featuremask) as fm_file:
            self.amdfeaturemask = int(fm_file.readline())
            return (self.amdfeaturemask)

gut_const = GUT_CONST()

class GPU_STAT:
    def __init__(self, item_id):
        self.uuid = item_id
        self.card_num = -1
        self.card_path = ""
        self.hwmon_path = ""
        self.params = {
        "uuid" : item_id,
        "card_num" : "",
        "pcie_id" : "",
        "driver" : "",
        "model" : "",
        "model_short" : "",
        "card_path" : "",
        "hwmon_path" : "",
        "power" : -1,
        "temp" : -1,
        "vddgfx" : -1,
        "vddc_range" : ["",""],
        "loading" : -1,
        "mclk_ps" : -1,
        "mclk_f" : "",
        "mclk_f_range" : ["",""],
        "sclk_ps" : -1,
        "sclk_f" : "",
        "sclk_f_range" : ["",""],
        "link_spd" : "",
        "link_wth" : "",
        "vbios" : ""
        }
        self.sclk_state = {} #{"1":["Mhz","mV]}
        self.mclk_state = {}

    def set_value(self, name, value):
        self.params[name] = value
        if name == "card_num":
            self.card_num = value
        if name == "card_path":
            self.card_path = value
        if name == "hwmon_path":
            self.hwmon_path = value

    def get_value(self, name):
        return(self.params[name])

    def get_all_labels(self):
        GPU_Param_Labels = {"uuid": "UUID",
                "model" : "Card Model",
                "card_num" : "Card Number",
                "card_path" : "Card Path",
                "pcie_id" : "PCIe ID",
                "driver" : "Driver",
                "hwmon_path" : "HWmon",
                "power" : "Power",
                "temp" : "Temp",
                "vddgfx" : "VddGFX",
                "loading" : "Loading",
                "link_spd" : "Link Speed",
                "link_wth" : "Link Width",
                "vbios" : "vBIOS Version",
                "sclk_ps" : "SCLK P-State",
                "sclk_f" : "SCLK",
                "mclk_ps" : "MCLK P-State",
                "mclk_f" : "MCLK"
                }
        return(GPU_Param_Labels)

    def get_pstates(self):
        range_mode = False
        if(os.path.isfile(self.card_path + "pp_od_clk_voltage") == False):
            print("Error getting pstates: ", self.card_path)
            sys.exit(-1)
        with open(self.card_path + "pp_od_clk_voltage") as card_file:
            for line in card_file:
                if re.fullmatch('OD_.*:$', line.strip()):
                    if re.fullmatch('OD_.CLK:$', line.strip()):
                        clk_name = line.strip()
                    elif re.fullmatch('OD_RANGE:$', line.strip()):
                        range_mode = True
                    continue
                lineitems = line.split()
                if range_mode == False:
                    lineitems[0] = int(re.sub(':','', lineitems[0]))
                    if clk_name == "OD_SCLK:":
                        self.sclk_state = {lineitems[0]: [lineitems[1],lineitems[2]]}
                        #print(self.sclk_state)
                    elif clk_name == "OD_MCLK:":
                        self.mclk_state = {lineitems[0]: [lineitems[1],lineitems[2]]}
                        #print(self.mclk_state)
                else:
                    if lineitems[0] == "SCLK:":
                        self.sclk_f_range = [lineitems[1],lineitems[2]]
                    elif lineitems[0] == "MCLK:":
                        self.mclk_f_range = [lineitems[1],lineitems[2]]
                    elif lineitems[0] == "VDDC:":
                        self.vddc_range = [lineitems[1],lineitems[2]]


    def read_hw_data(self):
        if(os.path.isfile(self.hwmon_path + "power1_average") == True):
            with open(self.hwmon_path + "power1_average") as hwmon_file:
                self.set_value("power", int(hwmon_file.readline())/1000000)
        if(os.path.isfile(self.hwmon_path + "temp1_input") == True):
            with open(self.hwmon_path + "temp1_input") as hwmon_file:
                self.set_value("temp",  int(hwmon_file.readline())/1000)
        if(os.path.isfile(self.hwmon_path + "in0_label") == True):
            with open(self.hwmon_path + "in0_label") as hwmon_file:
                if hwmon_file.readline().rstrip() == "vddgfx":
                    with open(self.hwmon_path + "in0_input") as hwmon_file2:
                        self.set_value("vddgfx",  int(hwmon_file2.readline()))

    def read_device_data(self):
        if(os.path.isfile(self.card_path + "gpu_busy_percent") == True):
            with open(self.card_path + "gpu_busy_percent") as card_file:
                self.set_value("loading", int(card_file.readline()))
        if(os.path.isfile(self.card_path + "current_link_speed") == True):
            with open(self.card_path + "current_link_speed") as card_file:
                self.set_value("link_spd", card_file.readline().strip())
        if(os.path.isfile(self.card_path + "current_link_width") == True):
            with open(self.card_path + "current_link_width") as card_file:
                self.set_value("link_wth", card_file.readline().strip())
        if(os.path.isfile(self.card_path + "vbios_version") == True):
            with open(self.card_path + "vbios_version") as card_file:
                self.set_value("vbios", card_file.readline().strip())
        if(os.path.isfile(self.card_path + "pp_dpm_sclk") == True):
            with open(self.card_path + "pp_dpm_sclk") as card_file:
                for line in card_file:
                    if line[len(line)-2] == "*":
                        lineitems = line.split(sep=':')
                        self.set_value("sclk_ps", lineitems[0].strip())
                        self.set_value("sclk_f", lineitems[1].strip().strip('*'))
        if(os.path.isfile(self.card_path + "pp_dpm_mclk") == True):
            with open(self.card_path + "pp_dpm_mclk") as card_file:
                for line in card_file:
                    if line[len(line)-2] == "*":
                        lineitems = line.split(sep=':')
                        self.set_value("mclk_ps", lineitems[0].strip())
                        self.set_value("mclk_f", lineitems[1].strip().strip('*'))

    def print(self):
        #for k, v in GPU_Param_Labels.items():
        for k, v in self.get_all_labels().items():
            print(v +": "+ str(self.get_value(k)))
        print("")

class GPU_LIST:
    def __init__(self):
        self.list = {}
        self.table_parameters = ["model_short", "loading", "power", "temp", "vddgfx", "sclk_f", "sclk_ps", "mclk_f", "mclk_ps"]
        self.table_param_labels = {"model_short":"Model", "loading":"Load %","power": "Power (W)", "temp":"T (C)", "vddgfx":"VddGFX (mV)",
                "sclk_f":"Sclk (MHz)", "sclk_ps":"Sclk Pstate", "mclk_f":"Mclk (MHz)", "mclk_ps":"Mclk Pstate"}

    def get_gpu_list(self):
        for card_names in glob.glob(gut_const.card_root + "card?/device/pp_od_clk_voltage"):
            gpu_item = GPU_STAT(uuid4().hex)
            gpu_item.set_value("card_path",  card_names.replace("pp_od_clk_voltage",''))
            gpu_item.set_value("card_num",  card_names.replace("/device/pp_od_clk_voltage",'').replace(gut_const.card_root + "card", ''))
            gpu_item.set_value("hwmon_path",  gpu_item.get_value("card_path") + gut_const.hwmon_sub + gpu_item.get_value("card_num") + "/")
            self.list[gpu_item.uuid] = gpu_item

    def get_pstates(self):
        for k, v in self.list.items():
            v.get_pstates()

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
                            v.set_value("pcie_id", pcie_id)
                            v.set_value("driver",  driver_module)
                            v.set_value("model", gpu_name)
                            v.set_value("model_short",  (re.sub(r'.*Radeon', '', gpu_name)).replace(']',''))
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

    def num_table_rows(self):
        return(len(self.table_parameters))

    def print_table(self):
        num_gpus = self.num_gpus()
        if num_gpus < 1: return(-1)

        print("┌", "─".ljust(12,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┬", "─".ljust(12,'─'), sep="", end="")
        print("┐")

        print("│", " ".ljust(12,' '), sep="", end="")
        for k, v in self.list.items():
            print("│", '\x1b[1;36m'+("card"+ v.get_value("card_num")).ljust(12,' ') + '\x1b[0m', sep="", end="")
        print("│")

        print("├", "─".ljust(12,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┼", "─".ljust(12,'─'), sep="", end="")
        print("┤")

        for table_item in self.table_parameters:
            print("│", '\x1b[1;36m'+self.table_param_labels[table_item].ljust(12,' ')[:12]+'\x1b[0m', sep="", end="")
            for k, v in self.list.items():
                print("│", str(v.get_value(table_item)).ljust(12,' ')[:12], sep="", end="")
            print("│")

        print("└", "─".ljust(12,'─'), sep="", end="")
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

    gpu_list.get_pstates()


if __name__ == "__main__":
    test()

