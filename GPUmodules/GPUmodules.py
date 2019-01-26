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
__version__ = "v0.0.0"
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
gut_const = GUT_CONST()


class GPU_STAT:
    def __init__(self, item_id):
        self.uuid = item_id
        self.card_num = ""
        self.card_path = ""
        self.hwmon_path = ""
        self.power = -1
        self.temp = -1

    def read_hw_data(self):
        #power1_average
        with open(self.hwmon_path + "power1_average") as hwmon_file:
            self.power = int(hwmon_file.readline())
        with open(self.hwmon_path + "temp1_input") as hwmon_file:
            self.temp = int(hwmon_file.readline())
        #in0_input
        #in0_label
        #temp1_input

    def read_amdfeaturemask():
        with open(gut_const.featuremask) as fm_file:
            return int(fm_file.readline())

    def print(self):
        print("UUID: ", self.uuid)
        print("Card Number: ", self.card_num)
        print("Card Path: ", self.card_path)
        print("HWmon: ", self.hwmon_path)
        print("Power: ", self.power/1000000,"W")
        print("Temp: ", self.temp/1000, "C")


class GPU_LIST:
    def __init__(self):
        self.list = {}

    def get_gpu_list(self):
        for card_names in glob.glob(gut_const.card_root + "card*/device/pp_od_clk_voltage"):
            gpu_item = GPU_STAT(uuid4().hex)
            gpu_item.card_path = card_names.replace("pp_od_clk_voltage",'')
            gpu_item.card_num = card_names.replace("/device/pp_od_clk_voltage",'').replace(gut_const.card_root + "card", '')
            gpu_item.hwmon_path = gpu_item.card_path + gut_const.hwmon_sub + gpu_item.card_num + "/"
            self.list[gpu_item.uuid] = gpu_item

    def read_hw_data(self):
        for k, v in self.list.items():
            v.read_hw_data()


    def print(self):
        for k, v in self.list.items():
            v.print()
        
def main():
    #gut_const.DEBUG = True

    gpu_list = GPU_LIST()
    gpu_list.get_gpu_list()
    gpu_list.read_hw_data()
    gpu_list.print()


if __name__ == "__main__":
    main()

