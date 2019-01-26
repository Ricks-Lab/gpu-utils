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
from GPUmodules import GPUmodules
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
        self.hwmon = "/sys/class/hwmon/"
        self.cur_power = "power1_average"
        self.cur_temp = "temp1_average"
        self.DEBUG = False
gut_const = GUT_CONST()


class GPU_STAT:
    def __init__(self, item_id):
        self.uuid = item_id

    def read_amdfeaturemask():
        with open(gut_const.featuremask) as fm_file:
            return int(fm_file.readline())

class GPU_LIST:
    def __init__(self):
        self.list = {}


