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
__credits__ = ["Craig Echt - Testing, Debug, and Verification"]
__license__ = "GNU General Public License"
__program_name__ = "amdgpu-utils"
__version__ = "v2.3.1"
__maintainer__ = "RueiKe"
__status__ = "Stable Release"

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
try:
    from GPUmodules import env 
except:
    import env 
try:
    from GPUmodules import PCImodule 
except:
    import PCImodule 


class GPU_ITEM:
    """An object to store GPU details."""
    # GPU Frequency/Voltage Control Type: 0 = None, 1 = P-states, 2 = Curve
    def __init__(self, item_id):
        self.uuid = item_id
        self.card_num = -1
        self.card_path = ""
        self.hwmon_path = ""
        self.compatible = True
        time_0 = datetime.utcnow()
        self.energy = {"t0": time_0, "tn": time_0, "cummulative": 0.0}

        self.params = {
        "uuid" : item_id,
        "card_num" : "",
        "pcie_id" : "",
        "driver" : "",
        "gpu_type" : 0,
        "id" : {"vendor":"","device":"","subsystem_vendor":"","subsystem_device":""},
        "model_device_decode" : "UNDETERMINED",
        "model" : "",
        "model_short" : "",
        "model_display" : "",
        "card_path" : "",
        "hwmon_path" : "",
        "energy": 0.0,
        "power" : -1,
        "power_cap" : -1,
        "power_cap_range" : [-1,-1],
        "fan_enable" : -1,
        "pwm_mode" : [-1,"UNK"],
        "fan_pwm" : -1,
        "fan_speed" : -1,
        "fan_speed_range" : [-1,-1],
        "fan_pwm_range" : [-1,-1],
        "fan_target" : -1,
        "temp" : -1,
        "temp_crit" : -1,
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
        "max_mem_allocation" : "",
        "max_wi_dim" : "",
        "max_wi_sizes" : "",
        "max_wg_size" : "",
        "prf_wg_multiple" : ""
        }
        self.sclk_state = {} #{"1":["Mhz","mV"]}
        self.mclk_state = {} #{"1":["Mhz","mV"]}
        self.vddc_curve = {} #{"1":{SCLK:["val1","val2"], VOLT:["val1","val2"]}
        self.ppm_modes = {}  #{"1":["Name","Description"]}

    def set_params_value(self, name, value):
        # update params dictionary
        self.params[name] = value
        if name == "driver" and value != "amdgpu":
            self.compatible = False
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
                "id" : "Device ID",
                "gpu_type" : "GPU Frequency/Voltage Control Type",
                "model_device_decode" : "Decoded Device ID",
                "model" : "Card Model",
                "model_short" : "Short Card Model",
                "model_display" : "Display Card Model",
                "card_num" : "Card Number",
                "card_path" : "Card Path",
                "pcie_id" : "PCIe ID",
                "driver" : "Driver",
                "vbios" : "vBIOS Version",
                "hwmon_path" : "HWmon",
                "power" : "Current Power (W)",
                "power_cap" : "Power Cap (W)",
                "power_cap_range" : "Power Cap Range (W)"
                }
        if env.gut_const.show_fans == True:
            GPU_Param_Labels.update({
                    "fan_enable" : "Fan Enable",
                    "pwm_mode" : "Fan PWM Mode",
                    "fan_pwm" : "Current Fan PWM (%)",
                    "fan_speed" : "Current Fan Speed (rpm)",
                    "fan_target" : "Fan Target Speed (rpm)",
                    "fan_speed_range" : "Fan Speed Range (rpm)",
                    "fan_pwm_range" : "Fan PWM Range (%)"
                    })
        GPU_Param_Labels.update({
                "temp" : "Current Temp (C)",
                "temp_crit" : "Critical Temp (C)",
                "vddgfx" : "Current VddGFX (mV)",
                "vddc_range" : "Vddc Range",
                "loading" : "Current Loading (%)",
                "link_spd" : "Link Speed",
                "link_wth" : "Link Width",
                "sclk_ps" : "Current SCLK P-State",
                "sclk_f" : "Current SCLK",
                "sclk_f_range" : "SCLK Range",
                "mclk_ps" : "Current MCLK P-State",
                "mclk_f" : "Current MCLK",
                "mclk_f_range" : "MCLK Range",
                "ppm" : "Power Performance Mode",
                "power_dpm_force" : "Power Force Performance Level"
                })
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
                "max_mem_allocation" : "CL Max Memory Allocation",
                "max_wi_dim" : "Max Work Item Dimensions",
                "max_wi_sizes" : "Max Work Item Sizes",
                "max_wg_size" : "Max Work Group Size",
                "prf_wg_multiple" : "Preferred Work Group Multiple"
                }
        return(GPU_CLINFO_Labels)

    def is_valid_power_cap(self, power_cap):
        power_cap_range = self.get_params_value("power_cap_range")
        if power_cap >= power_cap_range[0] and power_cap <= power_cap_range[1]:
            return(True)
        elif power_cap < 0:
            # negative values will be interpretted as reset request
            return(True)
        else:
            return(False)

    def is_valid_fan_pwm(self, pwm_value):
        pwm_range = self.get_params_value("fan_pwm_range")
        if pwm_value >= pwm_range[0] and pwm_value <= pwm_range[1]:
            return(True)
        elif pwm_value < 0:
            # negative values will be interpretted as reset request
            return(True)
        else:
            return(False)

    def is_valid_mclk_pstate(self, pstate):
        mclk_range = self.get_params_value("mclk_f_range")
        mclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(mclk_range[0])))
        mclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(mclk_range[1])))
        vddc_range = self.get_params_value("vddc_range")
        vddc_min = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[0])))
        vddc_max = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[1])))
        if pstate[1] >= mclk_min and pstate[1] <= mclk_max:
            if pstate[2] >= vddc_min and pstate[2] <= vddc_max:
                return(True)
        return(False)

    def is_valid_sclk_pstate(self, pstate):
        sclk_range = self.get_params_value("sclk_f_range")
        sclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(sclk_range[0])))
        sclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(sclk_range[1])))
        vddc_range = self.get_params_value("vddc_range")
        vddc_min = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[0])))
        vddc_max = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[1])))
        if pstate[1] >= sclk_min and pstate[1] <= sclk_max:
            if pstate[2] >= vddc_min and pstate[2] <= vddc_max:
                return(True)
        return(False)

    def is_valid_pstate_list_str(self, ps_str, clk_name):
        if ps_str == "":
            return(True)
        for ps in ps_str.split():
            ps_list = self.get_pstate_list(clk_name)
            try:
                ps_list.index(int(ps))
            except:
                print("Error: Invalid pstate %s for %s." % (ps, clk_name), file=sys.stderr)
                return(False)
        return(True)

    def get_pstate_list_str(self, clk_name):
        """Get list of pstate numbers and return as a string."""
        ps_list = self.get_pstate_list(clk_name)
        return(','.join(str(ps) for ps in ps_list))

    def get_pstate_list(self, clk_name):
        """Get list of pstate numbers and return as a list."""
        if clk_name == "SCLK":
            return(list(self.sclk_state.keys()))
        elif clk_name == "MCLK":
            return(list(self.mclk_state.keys()))
        return([])

    def get_current_ppm_mode(self):
        """Read GPU ppm definitions and current settings from driver files."""
        if self.get_params_value("power_dpm_force").lower() == "auto":
            return([-1,"AUTO"])
        ppm_item = self.get_params_value("ppm").split('-')
        return([int(ppm_item[0]), ppm_item[1]])

    def read_gpu_ppm_table(self):
        if(os.path.isfile(self.card_path + "pp_power_profile_mode") == False):
            print("Error getting power profile modes: ", self.card_path, file=sys.stderr)
            sys.exit(-1)
        with open(self.card_path + "pp_power_profile_mode") as card_file:
            for line in card_file:
                linestr = line.strip()
                # Check for mode name: begins with '[ ]+[0-9].*'
                if re.fullmatch(r'[ ]+[0-9].*', line[0:3]):
                    linestr = re.sub(r'[ ]*[*]*:',' ', linestr)
                    lineItems = linestr.split()
                    if env.gut_const.DEBUG: print("Debug: ppm line: %s"  % linestr, file=sys.stderr)
                    if len(lineItems) < 2:
                        print("Error: invalid ppm: %s"  % linestr, file=sys.stderr)
                        continue
                    if env.gut_const.DEBUG: print("Debug: valid ppm: %s"  % linestr, file=sys.stderr)
                    self.ppm_modes[lineItems[0]] = lineItems[1:]
            self.ppm_modes["-1"] = ["AUTO","Auto"]
        card_file.close()

        if(os.path.isfile(self.card_path + "power_dpm_force_performance_level") == True):
            with open(self.card_path + "power_dpm_force_performance_level") as card_file:
                self.set_params_value("power_dpm_force", card_file.readline().strip())
            card_file.close()
        else:
            print("Error: card file doesn't exist: %s" % (self.card_path + "power_dpm_force_performance_level"), file=sys.stderr)

    def read_gpu_pstates(self):
        """Read GPU pstate definitions and parameter ranges from driver files.
           Set card type based on pstate configuration"""
        range_mode = False
        type_unknown = True
        if(os.path.isfile(self.card_path + "pp_od_clk_voltage") == False):
            print("Error getting pstates: ", self.card_path, file=sys.stderr)
            self.compatible = False
            sys.exit(-1)
        if(os.path.isfile(self.card_path + "power_dpm_state") == False):
            print("Error: Looks like DPM is not enabled: %s doesn't exist" % (self.card_path + "power_dpm_state"), file=sys.stderr)
            self.compatible = False
            sys.exit(-1)
        with open(self.card_path + "pp_od_clk_voltage") as card_file:
            for line in card_file:
                line = line.strip()
                if re.fullmatch('OD_.*:$', line):
                    if re.fullmatch('OD_.CLK:$', line):
                        clk_name = line.strip()
                    elif re.fullmatch('OD_RANGE:$', line):
                        range_mode = True
                    continue
                lineitems = line.split()
                lineitems_len = len(lineitems)
                if type_unknown:
                    if len(lineitems) == 3:
                        # type 1 GPU
                        self.set_params_value("gpu_type", 1)
                    elif len(lineitems) == 2:
                        self.set_params_value("gpu_type", 2)
                    type_unknown = False
                if lineitems_len <2 or lineitems_len >3:
                    print("Error: Invalid pstate entry: %s" % (self.card_path + "pp_od_clk_voltage"), file=sys.stderr)
                    #self.compatible = False
                    continue
                if range_mode == False:
                    lineitems[0] = int(re.sub(':','', lineitems[0]))
                    if self.get_params_value("gpu_type") == 1:
                        if clk_name == "OD_SCLK:":
                            self.sclk_state[lineitems[0]] = [lineitems[1],lineitems[2]]
                        elif clk_name == "OD_MCLK:":
                            self.mclk_state[lineitems[0]] = [lineitems[1],lineitems[2]]
                    else: #Type 2
                        if clk_name == "OD_SCLK:":
                            self.sclk_state[lineitems[0]] = [lineitems[1],'-']
                        elif clk_name == "OD_MCLK:":
                            self.mclk_state[lineitems[0]] = [lineitems[1],'-']
                        elif clk_name == "OD_VDDC_CURVE:":
                            self.vddc_curve[lineitems[0]] = [lineitems[1],lineitems[2]]
                else:
                    if lineitems[0] == "SCLK:":
                        self.set_params_value("sclk_f_range", [lineitems[1],lineitems[2]])
                    elif lineitems[0] == "MCLK:":
                        self.set_params_value("mclk_f_range", [lineitems[1],lineitems[2]])
                    elif lineitems[0] == "VDDC:":
                        self.set_params_value("vddc_range", [lineitems[1],lineitems[2]])
                    elif re.fullmatch('VDDC_CURVE_.*', line):
                        if len(lineitems) == 3:
                            index = re.sub(r'VDDC_CURVE_.*\[','', lineitems[0])
                            index = re.sub(r'\].*','', index)
                            param = re.sub(r'VDDC_CURVE_','', lineitems[0])
                            param = re.sub(r'\[[0-9]\]:','', param)
                            if env.gut_const.DEBUG:
                                print("Curve: index: %s param: %s, val1 %s, val2: %s" % (index, param, lineitems[1], lineitems[2]))
                            #self.vddc_curve = {} #{"1":{SCLK:["val1","val2"], VOLT:["val1","val2"]}
                            if index in self.vddc_curve.keys():
                                self.vddc_curve[index].update({param:[lineitems[1], lineitems[2]]})
                            else:
                                self.vddc_curve[index] = {}
                                self.vddc_curve[index].update({param:[lineitems[1], lineitems[2]]})
                        else:
                            print("Error: Invalid CURVE entry: %s" % (self.card_path + "pp_od_clk_voltage"), file=sys.stderr)
        card_file.close()

    def read_gpu_sensor_static_data(self):
        """Read GPU static data from HWMON path."""
        try:
            if(os.path.isfile(self.hwmon_path + "power1_cap_max") == True):
                with open(self.hwmon_path + "power1_cap_max") as hwmon_file:
                    power1_cap_max_value =  int(int(hwmon_file.readline())/1000000)
                hwmon_file.close()
                if(os.path.isfile(self.hwmon_path + "power1_cap_min") == True):
                    with open(self.hwmon_path + "power1_cap_min") as hwmon_file:
                        power1_cap_min_value =  int(int(hwmon_file.readline())/1000000)
                    self.set_params_value("power_cap_range", [power1_cap_min_value, power1_cap_max_value])
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "power1_cap_min"), file=sys.stderr)
                hwmon_file.close()
            else:
                print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "power1_cap_max"), file=sys.stderr)
                self.compatibility = False

            if(os.path.isfile(self.hwmon_path + "temp1_crit") == True):
                with open(self.hwmon_path + "temp1_crit") as hwmon_file:
                    self.set_params_value("temp_crit",  int(hwmon_file.readline())/1000)
                hwmon_file.close()
            else:
                print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "temp1_crit"), file=sys.stderr)
                self.compatibility = False

            # Get fan data if --no_fan flag is not set
            if env.gut_const.show_fans == True:
                if(os.path.isfile(self.hwmon_path + "fan1_max") == True):
                    with open(self.hwmon_path + "fan1_max") as hwmon_file:
                        fan1_max_value =  int(hwmon_file.readline())
                    hwmon_file.close()
                    if(os.path.isfile(self.hwmon_path + "fan1_min") == True):
                        with open(self.hwmon_path + "fan1_min") as hwmon_file:
                            fan1_min_value =  int(hwmon_file.readline())
                        self.set_params_value("fan_speed_range", [fan1_min_value, fan1_max_value])
                    else:
                        print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "fan1_min"), file=sys.stderr)
                    hwmon_file.close()
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "fan1_max"), file=sys.stderr)
                    self.compatibility = False

                if(os.path.isfile(self.hwmon_path + "pwm1_max") == True):
                    with open(self.hwmon_path + "pwm1_max") as hwmon_file:
                        pwm1_max_value =  int(100*(int(hwmon_file.readline())/255))
                    hwmon_file.close()
                    if(os.path.isfile(self.hwmon_path + "pwm1_min") == True):
                        with open(self.hwmon_path + "pwm1_min") as hwmon_file:
                            pwm1_pmin_value =  int(100*(int(hwmon_file.readline())/255))
                        self.set_params_value("fan_pwm_range", [pwm1_pmin_value, pwm1_max_value])
                        hwmon_file.close()
                    else:
                        print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "pwm1_min"), file=sys.stderr)
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "pwm1_max"), file=sys.stderr)
                    self.compatibility = False
        except:
            print("Error: problem reading static data from GPU HWMON: %s" % self.hwmon_path, file=sys.stderr)
            self.compatibility = False

    def read_gpu_sensor_data(self):
        """Read GPU sensor data from HWMON path."""
        try:
            if(os.path.isfile(self.hwmon_path + "power1_cap") == True):
                with open(self.hwmon_path + "power1_cap") as hwmon_file:
                    self.set_params_value("power_cap", int(hwmon_file.readline())/1000000)
                hwmon_file.close()
            else:
                print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "power1_cap"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.hwmon_path + "power1_average") == True):
                with open(self.hwmon_path + "power1_average") as hwmon_file:
                    power_uw = int(hwmon_file.readline())
                    time_n = datetime.utcnow()
                    self.set_params_value("power", int(power_uw)/1000000)
                    delta_hrs = ((time_n - self.energy["tn"]).total_seconds())/3600
                    self.energy["tn"] = time_n
                    self.energy["cummulative"] += delta_hrs * power_uw/1000000000
                    self.set_params_value("energy", round(self.energy["cummulative"], 6))
                hwmon_file.close()
            else:
                print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "power1_average"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.hwmon_path + "temp1_input") == True):
                with open(self.hwmon_path + "temp1_input") as hwmon_file:
                    self.set_params_value("temp",  int(hwmon_file.readline())/1000)
                hwmon_file.close()
            else:
                print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "temp1_input"), file=sys.stderr)
                self.compatibility = False
    
            # Get fan data if --no_fan flag is not set
            if env.gut_const.show_fans == True:
                if(os.path.isfile(self.hwmon_path + "fan1_enable") == True):
                    with open(self.hwmon_path + "fan1_enable") as hwmon_file:
                        self.set_params_value("fan_enable",  hwmon_file.readline().strip())
                    hwmon_file.close()
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "fan1_enable"), file=sys.stderr)
                    self.compatibility = False
    
                if(os.path.isfile(self.hwmon_path + "fan1_target") == True):
                    with open(self.hwmon_path + "fan1_target") as hwmon_file:
                        self.set_params_value("fan_target",  int(hwmon_file.readline()))
                    hwmon_file.close()
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "fan1_target"), file=sys.stderr)
                    self.compatibility = False
    
                if(os.path.isfile(self.hwmon_path + "fan1_input") == True):
                    with open(self.hwmon_path + "fan1_input") as hwmon_file:
                        self.set_params_value("fan_speed",  int(hwmon_file.readline()))
                    hwmon_file.close()
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "fan1_input"), file=sys.stderr)
                    self.compatibility = False

                if(os.path.isfile(self.hwmon_path + "pwm1_enable") == True):
                    with open(self.hwmon_path + "pwm1_enable") as hwmon_file:
                        pwm_mode_value = int(hwmon_file.readline().strip())
                        if pwm_mode_value == 0:
                            pwm_mode_name = "None"
                        elif pwm_mode_value == 1:
                            pwm_mode_name = "Manual"
                        elif pwm_mode_value == 2:
                            pwm_mode_name = "Dynamic"
                        self.set_params_value("pwm_mode", [pwm_mode_value, pwm_mode_name])
                    hwmon_file.close()
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "pwm1_enable"), file=sys.stderr)
                    self.compatibility = False

                if(os.path.isfile(self.hwmon_path + "pwm1") == True):
                    with open(self.hwmon_path + "pwm1") as hwmon_file:
                        self.set_params_value("fan_pwm",  int(100*(int(hwmon_file.readline())/255)))
                    hwmon_file.close()
                else:
                    print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "pwm1"), file=sys.stderr)
                    self.compatibility = False

            if(os.path.isfile(self.hwmon_path + "in0_label") == True):
                with open(self.hwmon_path + "in0_label") as hwmon_file:
                    if hwmon_file.readline().rstrip() == "vddgfx":
                        with open(self.hwmon_path + "in0_input") as hwmon_file2:
                            self.set_params_value("vddgfx",  int(hwmon_file2.readline()))
                        hwmon_file.close()
            else:
                print("Error: HW file doesn't exist: %s" % (self.hwmon_path + "in0_label"), file=sys.stderr)
                self.compatibility = False
        except:
            print("Error: problem reading sensor data from GPU HWMON: %s" % self.hwmon_path, file=sys.stderr)
            self.compatibility = False

    def read_gpu_driver_info(self):
        """Read GPU current driver information from card path directory."""
        try:
            # get all device ID information
            if(os.path.isfile(self.card_path + "device") == True):
                with open(self.card_path + "device") as card_file:
                    device_id = card_file.readline().strip()
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "device"), file=sys.stderr)
                self.compatibility = False
            if(os.path.isfile(self.card_path + "vendor") == True):
                with open(self.card_path + "vendor") as card_file:
                    vendor_id = card_file.readline().strip()
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "vendor"), file=sys.stderr)
                self.compatibility = False
            if(os.path.isfile(self.card_path + "subsystem_device") == True):
                with open(self.card_path + "subsystem_device") as card_file:
                    subsystem_device_id = card_file.readline().strip()
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "subsystem_device"), file=sys.stderr)
                self.compatibility = False
            if(os.path.isfile(self.card_path + "subsystem_vendor") == True):
                with open(self.card_path + "subsystem_vendor") as card_file:
                    subsystem_vendor_id = card_file.readline().strip()
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "subsystem_vendor"), file=sys.stderr)
                self.compatibility = False
            # store device_id information
            self.set_params_value("id", {"vendor":vendor_id,"device":device_id,
                "subsystem_vendor":subsystem_vendor_id,"subsystem_device":subsystem_device_id})
            # use device info to set model
            if self.get_params_value("model_device_decode") == "UNDETERMINED":
                pcid = PCImodule.PCI_ID()
                self.set_params_value("model_device_decode", pcid.get_model(self.get_params_value("id")))
            # set display model to model_device_decode if shorter than model short
            if (self.get_params_value("model_device_decode") != "UNDETERMINED" and
                        len(self.get_params_value("model_device_decode")) < 1.2*len(self.get_params_value("model_short"))):
                self.set_params_value("model_display",  self.get_params_value("model_device_decode"))
            else:
                self.set_params_value("model_display",  self.get_params_value("model_short"))

            if(os.path.isfile(self.card_path + "vbios_version") == True):
                with open(self.card_path + "vbios_version") as card_file:
                    self.set_params_value("vbios", card_file.readline().strip())
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "vbios_version"), file=sys.stderr)
                self.compatibility = False
        except:
            print("Error: problem reading GPU driver information for Card Path: %s" % self.card_path, file=sys.stderr)
            self.compatibility = False

    def read_gpu_state_data(self):
        """Read GPU current state information from card path directory."""
        try:
            if(os.path.isfile(self.card_path + "gpu_busy_percent") == True):
                with open(self.card_path + "gpu_busy_percent") as card_file:
                    self.set_params_value("loading", int(card_file.readline()))
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "gpu_busy_percent"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.card_path + "current_link_speed") == True):
                with open(self.card_path + "current_link_speed") as card_file:
                    self.set_params_value("link_spd", card_file.readline().strip())
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "current_link_speed"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.card_path + "current_link_width") == True):
                with open(self.card_path + "current_link_width") as card_file:
                    self.set_params_value("link_wth", card_file.readline().strip())
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "current_link_width"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.card_path + "pp_dpm_sclk") == True):
                with open(self.card_path + "pp_dpm_sclk") as card_file:
                    for line in card_file:
                        if line[len(line)-2] == "*":
                            lineitems = line.split(sep=':')
                            self.set_params_value("sclk_ps", lineitems[0].strip())
                            self.set_params_value("sclk_f", lineitems[1].strip().strip('*'))
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "pp_dpm_sclk"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.card_path + "pp_dpm_mclk") == True):
                with open(self.card_path + "pp_dpm_mclk") as card_file:
                    for line in card_file:
                        if line[len(line)-2] == "*":
                            lineitems = line.split(sep=':')
                            self.set_params_value("mclk_ps", lineitems[0].strip())
                            self.set_params_value("mclk_f", lineitems[1].strip().strip('*'))
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "pp_dpm_mclk"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.card_path + "pp_power_profile_mode") == True):
                with open(self.card_path + "pp_power_profile_mode") as card_file:
                    for line in card_file:
                        linestr = line.strip()
                        searchObj = re.search('\*:', linestr)
                        if(searchObj != None):
                            lineitems = linestr.split(sep='*:')
                            mode_str = lineitems[0].strip()
                            mode_str = re.sub(r'[ ]+','-', mode_str)
                            self.set_params_value("ppm", mode_str)
                            break
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "pp_power_profile_mode"), file=sys.stderr)
                self.compatibility = False
    
            if(os.path.isfile(self.card_path + "power_dpm_force_performance_level") == True):
                with open(self.card_path + "power_dpm_force_performance_level") as card_file:
                    self.set_params_value("power_dpm_force", card_file.readline().strip())
                card_file.close()
            else:
                print("Error: card file doesn't exist: %s" % (self.card_path + "power_dpm_force_performance_level"),
                        file=sys.stderr)
                self.compatibility = False
        except:
            print("Error: getting data from GPU Card Path: %s" % self.card_path, file=sys.stderr)
            self.compatibility = False


    def print_ppm_table(self):
        """print human friendly table of ppm parameters."""
        print(f"Card: {self.card_path}")
        print("Power Performance Mode: %s" % self.get_params_value("power_dpm_force"))
        for k, v in self.ppm_modes.items():
            print(str(k).rjust(3,' ') +": "+v[0].rjust(15,' ') , end='')
            for v_item in v[1:]:
                print(str(v_item).rjust(18,' '), end='')
            print("")
        print("")

    def print_pstates(self):
        """print human friendly table of pstates."""
        print(f"Card: {self.card_path}")
        print("SCLK:" + " ".ljust(19,' ') + "MCLK:")
        for k, v in self.sclk_state.items():
            print(f"{str(k)}:  {v[0].ljust(8,' ')}  {v[1].ljust(8,' ')}", end='')
            if k in self.mclk_state.keys():
                print(f"  {str(k)}:  {self.mclk_state[k][0].ljust(8,' ')}  {self.mclk_state[k][1].ljust(8,' ')}")
            else:
                print("")
        for k, v in self.vddc_curve.items():
            print(f"{str(k)}: {v}")
        print("")

    def print(self, clflag=False):
        """ls like listing function for GPU parameters."""
        i = 0
        for k, v in self.get_all_params_labels().items():
            if i==1:
                if self.compatible:
                    print(f"{__program_name__} Compatibility: Yes")
                else:
                    print(f"{__program_name__} Compatibility: NO")
            print(v +": "+ str(self.get_params_value(k)))
            i += 1
        if clflag:
            for k, v in self.get_all_clinfo_labels().items():
                print(v +": "+ str(self.get_clinfo_value(k)))
        print("")

class GPU_LIST:
    """A list of GPU_ITEMS indexed with uuid.  It also contains a table of parameters used for tabular printouts"""
    def __init__(self):
        self.list = {}
        if env.gut_const.show_fans == True:
            self.table_parameters = ["model_display", "loading", "power", "power_cap",
                    "energy",
                    "temp", "vddgfx", "fan_pwm", "sclk_f", "sclk_ps",
                    "mclk_f", "mclk_ps", "ppm"]
            self.table_param_labels = {"model_display":"Model", "loading":"Load %","power":"Power (W)", "power_cap":"Power Cap (W)",
                    "energy":"Energy (kWh)",
                    "temp":"T (C)", "vddgfx":"VddGFX (mV)", "fan_pwm":"Fan Spd (%)", "sclk_f":"Sclk (MHz)", "sclk_ps":"Sclk Pstate",
                    "mclk_f":"Mclk (MHz)", "mclk_ps":"Mclk Pstate", "ppm":"Perf Mode"}
        else:
            self.table_parameters = ["model_display", "loading", "power", "power_cap",
                    "energy",
                    "temp", "vddgfx", "sclk_f", "sclk_ps",
                    "mclk_f", "mclk_ps", "ppm"]
            self.table_param_labels = {"model_display":"Model", "loading":"Load %","power":"Power (W)", "power_cap":"Power Cap (W)",
                    "energy":"Energy (kWh)",
                    "temp":"T (C)", "vddgfx":"VddGFX (mV)", "sclk_f":"Sclk (MHz)", "sclk_ps":"Sclk Pstate",
                    "mclk_f":"Mclk (MHz)", "mclk_ps":"Mclk Pstate", "ppm":"Perf Mode"}

    def get_gpu_list(self):
        """ This method should be the first called to popultate the list with potentially compatible GPUs
            It doesn't read any driver files, just checks their existence and sets them in the GPU_ITEM object.
        """
        for card_name in glob.glob(env.gut_const.card_root + "card?/device/pp_od_clk_voltage"):
            gpu_item = GPU_ITEM(uuid4().hex)
            gpu_item.set_params_value("card_path",  card_name.replace("pp_od_clk_voltage",''))
            gpu_item.set_params_value("card_num", 
                    card_name.replace("/device/pp_od_clk_voltage",'').replace(env.gut_const.card_root + "card", ''))
            hw_file_srch = glob.glob(os.path.join(gpu_item.card_path, env.gut_const.hwmon_sub) +"?")
            if len(hw_file_srch) > 1:
                print("More than one hwmon file found: ", hw_file_srch)
            gpu_item.set_params_value("hwmon_path",  hw_file_srch[0] + "/")
            self.list[gpu_item.uuid] = gpu_item

    def list_compatible_gpus(self):
        compatible_list = GPU_LIST()
        for k, v in self.list.items():
            if v.compatible == True:
                compatible_list.list[k]=v
        return(compatible_list)

    def read_gpu_ppm_table(self):
        for k, v in self.list.items():
            if v.compatible:
                v.read_gpu_ppm_table()

    def print_ppm_table(self):
        for k, v in self.list.items():
            v.print_ppm_table()

    def read_gpu_pstates(self):
        for k, v in self.list.items():
            if v.compatible:
                v.read_gpu_pstates()

    def print_pstates(self):
        for k, v in self.list.items():
            v.print_pstates()

    def read_gpu_state_data(self):
        """Read dynamic state data from GPUs"""
        for k, v in self.list.items():
            if v.compatible:
                v.read_gpu_state_data()

    def read_gpu_sensor_static_data(self):
        """Read dynamic sensor data from GPUs"""
        for k, v in self.list.items():
            if v.compatible:
                v.read_gpu_sensor_static_data()

    def read_gpu_sensor_data(self):
        """Read dynamic sensor data from GPUs"""
        for k, v in self.list.items():
            if v.compatible:
                v.read_gpu_sensor_data()

    def read_gpu_driver_info(self):
        """Read data static driver information for GPUs"""
        for k, v in self.list.items():
            if v.compatible:
                v.read_gpu_driver_info()

    def read_allgpu_pci_info(self):
        """ This function uses lspci to get details for GPUs in the current list and 
            populates the data structure of each GPU_ITEM in the list.

            It gets GPU name variants and gets the pcie slot ID for each card ID.
            Special incompatible cases are determined here, like the Fiji Pro Duo.
            This is the first function that should be called after the intial list is populated.
        """
        pcie_ids = subprocess.check_output(
            'lspci | grep -E \"^.*(VGA|Display).*\[AMD\/ATI\].*$\" | grep -Eo \"^([0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F])\"',
            shell=True).decode().split()
        if env.gut_const.DEBUG: print("Found %s GPUs" % len(pcie_ids))
        for pcie_id in pcie_ids:
            if env.gut_const.DEBUG: print("GPU: ", pcie_id)
            lspci_items = subprocess.check_output("lspci -k -s " + pcie_id, shell=True).decode().split("\n")
            if env.gut_const.DEBUG: print(lspci_items)

            #Get Long GPU Name
            gpu_name = ""
            #Line 0 name
            gpu_name_0 = ""
            gpu_name_items = lspci_items[0].split('[AMD/ATI]')
            if len(gpu_name_items) < 2:
                gpu_name_0 = "UNKNOWN"
            else:
                gpu_name_0 = gpu_name_items[1]
            #Line 1 name
            gpu_name_1 = ""
            gpu_name_items = lspci_items[1].split('[AMD/ATI]')
            if len(gpu_name_items) < 2:
                gpu_name_1 = "UNKNOWN"
            else:
                gpu_name_1 = gpu_name_items[1]

            #Check for Fiji ProDuo
            searchObj = re.search('Fiji', gpu_name_0)
            if(searchObj != None):
                searchObj = re.search('Radeon Pro Duo', gpu_name_1)
                if(searchObj != None):
                    gpu_name = "Radeon Fiji Pro Duo"

            if len(gpu_name) == 0:
                if len(gpu_name_0) > len(gpu_name_1):
                    gpu_name = gpu_name_0
                else:
                    gpu_name = gpu_name_1
                if env.gut_const.DEBUG: print("gpu_name: %s" % gpu_name)

            #Get Driver Name
            driver_module_items = lspci_items[2].split(':')
            if len(driver_module_items) < 2:
                driver_module = "UNKNOWN"
            else:
                driver_module = driver_module_items[1].strip()

            # Find matching card
            device_dirs = glob.glob(env.gut_const.card_root + "card?/device")
            for device_dir in device_dirs:
                sysfspath = str(Path(device_dir).resolve())
                if env.gut_const.DEBUG: print("device_dir: ", device_dir)
                if env.gut_const.DEBUG: print("sysfspath: ", sysfspath)
                if env.gut_const.DEBUG: print("pcie_id: ", pcie_id)
                if env.gut_const.DEBUG: print("sysfspath-7: ", sysfspath[-7:])
                if pcie_id == sysfspath[-7:]:
                    for k, v in self.list.items():
                        if v.card_path == device_dir + '/':
                            if gpu_name == "Radeon Fiji Pro Duo": v.compatible = False
                            v.set_params_value("pcie_id", pcie_id)
                            v.set_params_value("driver",  driver_module)
                            v.set_params_value("model", gpu_name)
                            model_short = re.sub(r'^.*\[','', gpu_name)
                            model_short = re.sub(r'\].*$','', model_short)
                            model_short = re.sub(r'.*Radeon','', model_short)
                            v.set_params_value("model_short",  model_short)
                            break
                    break

    def read_gpu_opencl_data(self):
        # Check access to clinfo command
        if shutil.which("/usr/bin/clinfo") == None:
            print("OS Command [clinfo] not found.  Use sudo apt-get install clinfo to install", file=sys.stderr)
            return(-1)
        cmd = subprocess.Popen(shlex.split('/usr/bin/clinfo --raw'), shell=False, stdout=subprocess.PIPE)
        for line in cmd.stdout:
            linestr = line.decode("utf-8").strip()
            if len(linestr) < 1:
                continue
            if linestr[0] != "[":
                continue
            linestr = re.sub(r'   [ ]*',':-:', linestr)
            searchObj = re.search('CL_DEVICE_NAME', linestr)
            if(searchObj != None):
                # Found a new device
                tmp_gpu = GPU_ITEM(uuid4().hex)
                lineItem = linestr.split(':-:')
                dev_str = lineItem[0].split('/')[1]
                dev_num = int(re.sub(']','',dev_str))
                tmp_gpu.set_clinfo_value("device_name", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_VERSION', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("device_version", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DRIVER_VERSION', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("driver_version", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_OPENCL_C_VERSION', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("opencl_version", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_TOPOLOGY_AMD', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                pcie_id_str = (lineItem[2].split()[1]).strip()
                if env.gut_const.DEBUG: print(f"CL PCIE ID: [{pcie_id_str}]")
                tmp_gpu.set_clinfo_value("pcie_id", pcie_id_str)
                continue
            searchObj = re.search('CL_DEVICE_MAX_COMPUTE_UNITS', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_cu", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_SIMD_PER_COMPUTE_UNIT_AMD', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("simd_per_cu", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_SIMD_WIDTH_AMD', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("simd_width", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_SIMD_INSTRUCTION_WIDTH_AMD', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("simd_ins_width", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_MAX_MEM_ALLOC_SIZE', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_mem_allocation", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_wi_dim", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_MAX_WORK_ITEM_SIZES', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_wi_sizes", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_MAX_WORK_GROUP_SIZE', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("max_wg_size", lineItem[2].strip())
                continue
            searchObj = re.search('CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE', linestr)
            if(searchObj != None):
                lineItem = linestr.split(':-:')
                tmp_gpu.set_clinfo_value("prf_wg_multiple", lineItem[2].strip())
                continue
            searchObj = re.search('CL_DEVICE_EXTENSIONS', linestr)
            if(searchObj != None):
                # End of Device 
                if env.gut_const.DEBUG: print("finding gpu with pcie ID: ", tmp_gpu.get_clinfo_value("pcie_id"))
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
            if v.compatible == True:
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

        print("┌", "─".ljust(13,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┬", "─".ljust(16,'─'), sep="", end="")
        print("┐")

        print("│", '\x1b[1;36m'+"Card #".ljust(13,' ')+'\x1b[0m', sep="", end="")
        for k, v in self.list.items():
            print("│", '\x1b[1;36m'+("card"+ v.get_params_value("card_num")).ljust(16,' ') + '\x1b[0m', sep="", end="")
        print("│")

        print("├", "─".ljust(13,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┼", "─".ljust(16,'─'), sep="", end="")
        print("┤")

        for table_item in self.table_parameters:
            print("│", '\x1b[1;36m'+self.table_param_labels[table_item].ljust(13,' ')[:13]+'\x1b[0m', sep="", end="")
            for k, v in self.list.items():
                print("│", str(v.get_params_value(table_item)).ljust(16,' ')[:16], sep="", end="")
            print("│")

        print("└", "─".ljust(13,'─'), sep="", end="")
        for k, v in self.list.items():
                print("┴", "─".ljust(16,'─'), sep="", end="")
        print("┘")

    def print_log_header(self, log_file_ptr):
        num_gpus = self.num_gpus()
        if num_gpus < 1: return(-1)

        #Print Header
        print("Time|Card#", end="", file=log_file_ptr )
        for table_item in self.table_parameters:
            print("|" + table_item, end="", file=log_file_ptr)
        print("", file=log_file_ptr)

    def print_log(self, log_file_ptr):
        num_gpus = self.num_gpus()
        if num_gpus < 1: return(-1)

        #Print Data
        for k, v in self.list.items():
            print(str(v.energy["tn"].strftime('%c')) + "|" + str(v.card_num), end="", file=log_file_ptr)
            for table_item in self.table_parameters:
                print("|", str(v.get_params_value(table_item)), end="", file=log_file_ptr)
            print("", file=log_file_ptr)

def test():
    #env.gut_const.DEBUG = True

    try:
        featuremask = env.gut_const.read_amdfeaturemask()
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
    #gpu_list.print()
    com_list = gpu_list.list_compatible_gpus()
    print(gpu_list.list)
    print(com_list)
    exit()

    gpu_list.read_gpu_pstates()

    for k, v in gpu_list.list.items():
        print(v.get_pstate_list("MCLK"))


if __name__ == "__main__":
    test()

