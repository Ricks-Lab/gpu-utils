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
__program_name__ = "amdgpu-utils"
__version__ = "v2.0.0"
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


class GUT_CONST:
    def __init__(self):
        self.featuremask = "/sys/module/amdgpu/parameters/ppfeaturemask"
        self.card_root = "/sys/class/drm/"
        self.hwmon_sub = "hwmon/hwmon"
        self.DEBUG = False
        self.SLEEP = 2
        self.PATH = "."
        self.amdfeaturemask = ""

    def read_amdfeaturemask(self):
        with open(gut_const.featuremask) as fm_file:
            self.amdfeaturemask = int(fm_file.readline())
            return (self.amdfeaturemask)

    def check_env(self):
        # Check python version
        (python_major, python_minor, python_patch) = platform.python_version_tuple()
        if python_major < "3":
            print("Using python" + python_major + ", but benchMT requires python3.", file=sys.stderr)
            return(-1)
        if python_minor < "6":
            print("Using python " + python_major +"."+ python_minor +"."+ python_patch +
                    " but, benchMT requires python 3.6 and up.", file=sys.stderr)
            return(-1)

        # Check Linux Kernel version
        linux_version = platform.release()
        if int(linux_version.split(".")[0]) < 4:
            print(f"Using Linux Kernel {linux_version} but benchMT requires > 4.17.", file=sys.stderr)
            return(-2)
        if int(linux_version.split(".")[1]) < 8:
            print(f"Using Linux Kernel {linux_version} but benchMT requires > 4.17.", file=sys.stderr)
            return(-2)
        return(0)


gut_const = GUT_CONST()

class GPU_ITEM:
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
        "power_cap" : -1,
        "power_cap_min" : -1,
        "power_cap_max" : -1,
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
        "ppm" : "",
        "power_dpm_force" : "",
        "vbios" : ""
        }
        self.clinfo = {
        "device_name" : "",
        "device_version" : "",
        "driver_version" : "",
        "opencl_version" : "",
        "pcie_id" : "",
        "max_cu" : "",
        "simd_per_cu" : "",
        "simd_width" : "",
        "simd_ins_width" : "",
        "graphics_ip" : "",
        "max_wi_dim" : "",
        "max_wi_sizes" : "",
        "max_wg_size" : "",
        "prf_wg_multiple" : ""
        }
        self.sclk_state = {} #{"1":["Mhz","mV]}
        self.mclk_state = {}

    def set_params_value(self, name, value):
        # update params dictionary
        self.params[name] = value
        if name == "card_num":
            self.card_num = value
        if name == "card_path":
            self.card_path = value
        if name == "hwmon_path":
            self.hwmon_path = value

    def get_params_value(self, name):
        # reads params dictionary
        return(self.params[name])

    def set_clinfo_value(self, name, value):
        # update clinfo dictionary
        self.clinfo[name] = value

    def get_clinfo_value(self, name):
        # reads clinfo dictionary
        return(self.clinfo[name])

    def copy_clinfo_values(self, gpu_item):
        for k, v in gpu_item.clinfo.items():
            self.clinfo[k] = v

    def get_all_params_labels(self):
        # Human friendly labels for params keys
        GPU_Param_Labels = {"uuid": "UUID",
                "model" : "Card Model",
                "card_num" : "Card Number",
                "card_path" : "Card Path",
                "pcie_id" : "PCIe ID",
                "driver" : "Driver",
                "hwmon_path" : "HWmon",
                "power" : "Current Power (W)",
                "power_cap" : "Power Cap (W)",
                "power_cap_min" : "Min Power Cap (W)",
                "power_cap_max" : "Max Power Cap (W)",
                "temp" : "Current Temp (C)",
                "vddgfx" : "Current VddGFX (mV)",
                "vddc_range" : "Vddc Range",
                "loading" : "Current Loading (%)",
                "link_spd" : "Link Speed",
                "link_wth" : "Link Width",
                "vbios" : "vBIOS Version",
                "sclk_ps" : "Current SCLK P-State",
                "sclk_f" : "Current SCLK",
                "sclk_f_range" : "SCLK Range",
                "mclk_ps" : "Current MCLK P-State",
                "mclk_f" : "Current MCLK",
                "mclk_f_range" : "MCLK Range",
                "ppm" : "Power Performance Mode",
                "power_dpm_force" : "Power Force Performance Level"
                }
        return(GPU_Param_Labels)

    def get_all_clinfo_labels(self):
        # Human friendly labels for clinfo keys
        GPU_CLINFO_Labels = { "device_name" : "Device Name",
                "device_version" : "Device Version",
                "driver_version" : "Driver Version",
                "opencl_version" : "Device OpenCL C Version",
                "max_cu" : "Max Compute Units",
                "simd_per_cu" : "SIMD per CU",
                "simd_width" : "SIMD Width",
                "simd_ins_width" : "SIMD Instruction Width",
                "graphics_ip" : "Graphics IP",
                "max_wi_dim" : "Max Work Item Dimensions",
                "max_wi_sizes" : "Max Work Item Sizes",
                "max_wg_size" : "Max Work Group Size",
                "prf_wg_multiple" : "Preferred Work Group Multiple"
                }
        return(GPU_CLINFO_Labels)

    def write_pstates(self):
        # Sample commands to set p states.  Problem is that the file that needs to
        # be written to, is only writeable by root.  Maybe the best approach is to 
        # create a script for the user to execute with sudo.
        #
        # Write p-state details
        # echo "m 0 155 900" > /sys/class/drm/card0/device/pp_od_clk_voltage
        # echo "s 7 975 1180" > /sys/class/drm/card0/device/pp_od_clk_voltage
        # Reset
        # echo "r" > /sys/class/drm/card0/device/pp_od_clk_voltage 
        # Commit Changes
        # echo "c" > /sys/class/drm/card0/device/pp_od_clk_voltage

        if(os.path.isfile(self.card_path + "pp_od_clk_voltage") == False):
            print("Can not access card{self.card_num} file: ", self.card_path + "pp_od_clk_voltage", file=sys.stderr)
        # TODO write the code to do this!
        return

    def get_pstates(self):
        range_mode = False
        if(os.path.isfile(self.card_path + "pp_od_clk_voltage") == False):
            print("Error getting pstates: ", self.card_path, file=sys.stderr)
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
                        self.sclk_state[lineitems[0]] = [lineitems[1],lineitems[2]]
                        #print(self.sclk_state)
                    elif clk_name == "OD_MCLK:":
                        self.mclk_state[lineitems[0]] = [lineitems[1],lineitems[2]]
                        #print(self.mclk_state)
                else:
                    if lineitems[0] == "SCLK:":
                        self.set_params_value("sclk_f_range", [lineitems[1],lineitems[2]])
                    elif lineitems[0] == "MCLK:":
                        self.set_params_value("mclk_f_range", [lineitems[1],lineitems[2]])
                    elif lineitems[0] == "VDDC:":
                        self.set_params_value("vddc_range", [lineitems[1],lineitems[2]])

    def read_hw_data(self):
        if(os.path.isfile(self.hwmon_path + "power1_cap_max") == True):
            with open(self.hwmon_path + "power1_cap_max") as hwmon_file:
                self.set_params_value("power_cap_max", int(hwmon_file.readline())/1000000)
        if(os.path.isfile(self.hwmon_path + "power1_cap_min") == True):
            with open(self.hwmon_path + "power1_cap_min") as hwmon_file:
                self.set_params_value("power_cap_min", int(hwmon_file.readline())/1000000)
        if(os.path.isfile(self.hwmon_path + "power1_cap") == True):
            with open(self.hwmon_path + "power1_cap") as hwmon_file:
                self.set_params_value("power_cap", int(hwmon_file.readline())/1000000)
        if(os.path.isfile(self.hwmon_path + "power1_average") == True):
            with open(self.hwmon_path + "power1_average") as hwmon_file:
                self.set_params_value("power", int(hwmon_file.readline())/1000000)
        if(os.path.isfile(self.hwmon_path + "temp1_input") == True):
            with open(self.hwmon_path + "temp1_input") as hwmon_file:
                self.set_params_value("temp",  int(hwmon_file.readline())/1000)
        if(os.path.isfile(self.hwmon_path + "in0_label") == True):
            with open(self.hwmon_path + "in0_label") as hwmon_file:
                if hwmon_file.readline().rstrip() == "vddgfx":
                    with open(self.hwmon_path + "in0_input") as hwmon_file2:
                        self.set_params_value("vddgfx",  int(hwmon_file2.readline()))

    def read_device_data(self):
        if(os.path.isfile(self.card_path + "gpu_busy_percent") == True):
            with open(self.card_path + "gpu_busy_percent") as card_file:
                self.set_params_value("loading", int(card_file.readline()))
        if(os.path.isfile(self.card_path + "current_link_speed") == True):
            with open(self.card_path + "current_link_speed") as card_file:
                self.set_params_value("link_spd", card_file.readline().strip())
        if(os.path.isfile(self.card_path + "current_link_width") == True):
            with open(self.card_path + "current_link_width") as card_file:
                self.set_params_value("link_wth", card_file.readline().strip())
        if(os.path.isfile(self.card_path + "vbios_version") == True):
            with open(self.card_path + "vbios_version") as card_file:
                self.set_params_value("vbios", card_file.readline().strip())
        if(os.path.isfile(self.card_path + "pp_dpm_sclk") == True):
            with open(self.card_path + "pp_dpm_sclk") as card_file:
                for line in card_file:
                    if line[len(line)-2] == "*":
                        lineitems = line.split(sep=':')
                        self.set_params_value("sclk_ps", lineitems[0].strip())
                        self.set_params_value("sclk_f", lineitems[1].strip().strip('*'))
        if(os.path.isfile(self.card_path + "pp_dpm_mclk") == True):
            with open(self.card_path + "pp_dpm_mclk") as card_file:
                for line in card_file:
                    if line[len(line)-2] == "*":
                        lineitems = line.split(sep=':')
                        self.set_params_value("mclk_ps", lineitems[0].strip())
                        self.set_params_value("mclk_f", lineitems[1].strip().strip('*'))
        if(os.path.isfile(self.card_path + "pp_power_profile_mode") == True):
            with open(self.card_path + "pp_power_profile_mode") as card_file:
                for line in card_file:
                    linestr = line.strip()
                    searchObj = re.search('\*:', linestr)
                    if(searchObj != None):
                        lineitems = linestr.split(sep='*:')
                        mode_str = re.sub(r'[ ]+','-',lineitems[0]).strip()
                        self.set_params_value("ppm", mode_str)
                        break
        if(os.path.isfile(self.card_path + "power_dpm_force_performance_level") == True):
            with open(self.card_path + "power_dpm_force_performance_level") as card_file:
                self.set_params_value("power_dpm_force", card_file.readline().strip())

    def print_pstates(self):
        print(f"Card: {self.card_path}")
        print("SCLK:" + " ".ljust(19,' ') + "MCLK:")
        for k, v in self.sclk_state.items():
            print(f"{str(k)}:  {v[0].ljust(8,' ')}  {v[1].ljust(8,' ')}", end='')
            if k in self.mclk_state.keys():
                print(f"  {str(k)}:  {self.mclk_state[k][0].ljust(8,' ')}  {self.mclk_state[k][1].ljust(8,' ')}")
            else:
                print("")
        print("")

    def print(self, clflag=False):
        #for k, v in GPU_Param_Labels.items():
        for k, v in self.get_all_params_labels().items():
            print(v +": "+ str(self.get_params_value(k)))
        if clflag:
            for k, v in self.get_all_clinfo_labels().items():
                print(v +": "+ str(self.get_clinfo_value(k)))
        print("")

class GPU_LIST:
    def __init__(self):
        self.list = {}
        self.table_parameters = ["model_short", "loading", "power", "power_cap",
                "temp", "vddgfx", "sclk_f", "sclk_ps", "mclk_f",
                "mclk_ps", "ppm"]
        self.table_param_labels = {"model_short":"Model", "loading":"Load %","power":"Power (W)", "power_cap":"MaxPower (W)",
                "temp":"T (C)", "vddgfx":"VddGFX (mV)", "sclk_f":"Sclk (MHz)", "sclk_ps":"Sclk Pstate", "mclk_f":"Mclk (MHz)",
                "mclk_ps":"Mclk Pstate", "ppm":"Perf Mode"}

    def get_gpu_list(self):
        for card_names in glob.glob(gut_const.card_root + "card?/device/pp_od_clk_voltage"):
            gpu_item = GPU_ITEM(uuid4().hex)
            gpu_item.set_params_value("card_path",  card_names.replace("pp_od_clk_voltage",''))
            gpu_item.set_params_value("card_num",  card_names.replace("/device/pp_od_clk_voltage",'').replace(gut_const.card_root + "card", ''))
            gpu_item.set_params_value("hwmon_path",  gpu_item.get_params_value("card_path") + gut_const.hwmon_sub + gpu_item.get_params_value("card_num") + "/")
            self.list[gpu_item.uuid] = gpu_item

    def get_pstates(self):
        for k, v in self.list.items():
            v.get_pstates()

    def print_pstates(self):
        for k, v in self.list.items():
            v.print_pstates()

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
            driver_module = (lspci_items[2].split(':')[1]).strip()
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
                            v.set_params_value("pcie_id", pcie_id)
                            v.set_params_value("driver",  driver_module)
                            v.set_params_value("model", gpu_name)
                            v.set_params_value("model_short",  (re.sub(r'.*Radeon', '', gpu_name)).replace(']',''))
                            break
                    break

    def read_opencl_data(self):
        # Check access to clinfo command
        if shutil.which("/usr/bin/clinfo") == None:
            print("OS Command [clinfo] not found.  Use sudo apt-get install clinfo to install", file=sys.stderr)
            return(-1)
        cmd = subprocess.Popen('/usr/bin/clinfo', shell=False, stdout=subprocess.PIPE)
        for line in cmd.stdout:
            linestr = line.decode("utf-8").strip()
            linestr = re.sub(r'      [ ]*',':-:', linestr)
            searchObj = re.search('Device Name', linestr)
            if(searchObj != None):
                # Found a new device
                tmp_gpu = GPU_ITEM(uuid4().hex)
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("device_name", lineItem[1].strip())
                continue
            searchObj = re.search('Device Version', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("device_version", lineItem[1].strip())
                continue
            searchObj = re.search('Driver Version', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("driver_version", lineItem[1].strip())
                continue
            searchObj = re.search('Device OpenCL C Version', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("opencl_version", lineItem[1].strip())
                continue
            searchObj = re.search('Device Topology', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                pcie_id_str = lineItem[1].split(',')[1].strip()
                tmp_gpu.set_clinfo_value("pcie_id", pcie_id_str)
                continue
            searchObj = re.search('Max compute units', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_cu", lineItem[1].strip())
                continue
            searchObj = re.search('SIMD per compute unit', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("simd_per_cu", lineItem[1].strip())
                continue
            searchObj = re.search('SIMD width', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("simd_width", lineItem[1].strip())
                continue
            searchObj = re.search('SIMD instruction width', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("simd_ins_width", lineItem[1].strip())
                continue
            searchObj = re.search('Graphics IP', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("graphics_ip", lineItem[1].strip())
                continue
            searchObj = re.search('Max work item dimensions', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_wi_dim", lineItem[1].strip())
                continue
            searchObj = re.search('Max work item sizes', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_wi_sizes", lineItem[1].strip())
                continue
            searchObj = re.search('Max work group size', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_wg_size", lineItem[1].strip())
                continue
            searchObj = re.search('Preferred work group size multiple', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("prf_wg_multiple", lineItem[1].strip())
                continue
            searchObj = re.search('Device Extensions', linestr)
            if(searchObj != None):
                # End of Device 
                target_gpu_uuid = self.find_gpu_by_pcie_id(tmp_gpu.get_clinfo_value("pcie_id"))
                self.list[target_gpu_uuid].copy_clinfo_values(tmp_gpu)
        return(0)

    def find_gpu_by_pcie_id(self, pcie_id):
        for k, v in self.list.items():
            if v.get_params_value("pcie_id") == pcie_id:
                return(v.uuid)
        return(-1)

    def num_gpus(self):
        cnt = 0
        for k, v in self.list.items():
            cnt += 1
        return(cnt)

    def num_compatible_gpus(self):
        cnt = 0
        for k, v in self.list.items():
            if v.get_params_value("driver") == "amdgpu":
                cnt += 1
        return(cnt)

    def print(self, clflag=False):
        for k, v in self.list.items():
            v.print(clflag)

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
            print("│", '\x1b[1;36m'+("card"+ v.get_params_value("card_num")).ljust(12,' ') + '\x1b[0m', sep="", end="")
        print("│")

        print("├", "─".ljust(12,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┼", "─".ljust(12,'─'), sep="", end="")
        print("┤")

        for table_item in self.table_parameters:
            print("│", '\x1b[1;36m'+self.table_param_labels[table_item].ljust(12,' ')[:12]+'\x1b[0m', sep="", end="")
            for k, v in self.list.items():
                print("│", str(v.get_params_value(table_item)).ljust(12,' ')[:12], sep="", end="")
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

