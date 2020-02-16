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
__author__ = 'RueiKe'
__copyright__ = 'Copyright (C) 2019 RueiKe'
__credits__ = ['Craig Echt - Testing, Debug, and Verification']
__license__ = 'GNU General Public License'
__program_name__ = 'amdgpu-utils'
__version__ = 'v3.0.0'
__maintainer__ = 'RueiKe'
__status__ = 'Complete rewrite under development - Please use an official release.'
__docformat__ = 'reStructuredText'

# pylint: disable=multiple-statements
# pylint: disable=line-too-long

import re
import subprocess
import shlex
import os
import sys
from pathlib import Path
from uuid import uuid4
import glob
try:
    from GPUmodules import env
except ImportError:
    import env
try:
    from GPUmodules import PCImodule
except ImportError:
    import PCImodule


class ObjDict(dict):
    """
    Allow access of dictionary keys by key name.
    """
    # pylint: disable=attribute-defined-outside-init
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


class GpuItem:
    """An object to store GPU details.
    .. note:: GPU Frequency/Voltage Control Type: 0 = None, 1 = P-states, 2 = Curve
    """
    # pylint: disable=attribute-defined-outside-init
    _GPU_NC_Param_List = ['uuid', 'vendor', 'model', 'card_num', 'card_path', 'pcie_id', 'driver']
    # Define Class Labels
    _GPU_CLINFO_Labels = {'device_name': 'Device Name',
                          'device_version': 'Device Version',
                          'driver_version': 'Driver Version',
                          'opencl_version': 'Device OpenCL C Version',
                          'max_cu': 'Max Compute Units',
                          'simd_per_cu': 'SIMD per CU',
                          'simd_width': 'SIMD Width',
                          'simd_ins_width': 'SIMD Instruction Width',
                          'max_mem_allocation': 'CL Max Memory Allocation',
                          'max_wi_dim': 'Max Work Item Dimensions',
                          'max_wi_sizes': 'Max Work Item Sizes',
                          'max_wg_size': 'Max Work Group Size',
                          'prf_wg_multiple': 'Preferred Work Group Multiple'}

    _GPU_Param_Labels = {'uuid': 'UUID',
                         'vendor': 'Vendor',
                         'id': 'Device ID',
                         'gpu_type': 'GPU Frequency/Voltage Control Type',
                         'model_device_decode': 'Decoded Device ID',
                         'model': 'Card Model',
                         'model_short': 'Short Card Model',
                         'model_display': 'Display Card Model',
                         'card_num': 'Card Number',
                         'card_path': 'Card Path',
                         'pcie_id': 'PCIe ID',
                         'driver': 'Driver',
                         'vbios': 'vBIOS Version',
                         'hwmon_path': 'HWmon',
                         'power': 'Current Power (W)',
                         'power_cap': 'Power Cap (W)',
                         'power_cap_range': 'Power Cap Range (W)'}
    if env.GUT_CONST.show_fans:
        _GPU_Param_Labels.update({'fan_enable': 'Fan Enable',
                                  'pwm_mode': 'Fan PWM Mode',
                                  'fan_pwm': 'Current Fan PWM (%)',
                                  'fan_speed': 'Current Fan Speed (rpm)',
                                  'fan_target': 'Fan Target Speed (rpm)',
                                  'fan_speed_range': 'Fan Speed Range (rpm)',
                                  'fan_pwm_range': 'Fan PWM Range (%)'})
    _GPU_Param_Labels.update({'temp': 'Current Temp (C)',
                              'temp_crit': 'Critical Temp (C)',
                              'vddgfx': 'Current VddGFX (mV)',
                              'vddc_range': 'Vddc Range',
                              'loading': 'Current Loading (%)',
                              'link_spd': 'Link Speed',
                              'link_wth': 'Link Width',
                              'sclk_ps': 'Current SCLK P-State',
                              'sclk_f': 'Current SCLK',
                              'sclk_f_range': 'SCLK Range',
                              'mclk_ps': 'Current MCLK P-State',
                              'mclk_f': 'Current MCLK',
                              'mclk_f_range': 'MCLK Range',
                              'ppm': 'Power Performance Mode',
                              'power_dpm_force': 'Power Force Performance Level'})

    def __repr__(self):
        """
        Return dictionary representing all parts of the GpuItem object.
        :return:
        :rtype: dict
        """
        return {'params': self.prm, 'clinfo': self.clinfo,
                'sclk_state': self.sclk_state, 'mclk_state': self.mclk_state,
                'vddc_curve': self.vddc_curve, 'vddc_curve_range': self.vddc_curve_range,
                'ppm_modes': self.ppm_modes}

    def __str__(self):
        """
        Return  simple string representing the GpuItem object.
        :return:
        :rtype: str
        """
        return 'GPU_Item: uuid={}'.format(self.prm.uuid)

    def __init__(self, item_id):
        """
        Initialize GpuItem object.
        :param item_id:  UUID of the new item.
        :type item_id: str
        """
        time_0 = env.GUT_CONST.now(env.GUT_CONST.USELTZ)
        self.energy = {'t0': time_0, 'tn': time_0, 'cumulative': 0.0}
        self.hwmon_disabled = []
        self.prm = ObjDict({'uuid': item_id,
                            'card_num': '',
                            'pcie_id': '',
                            'driver': '',
                            'vendor': '',
                            'compatible': False,
                            'readable': False,
                            'writable': False,
                            'compute': False,
                            'gpu_type': 0,
                            'id': {'vendor': '', 'device': '', 'subsystem_vendor': '', 'subsystem_device': ''},
                            'model_device_decode': 'UNDETERMINED',
                            'model': '',
                            'model_short': '',
                            'model_display': '',
                            'card_path': '',
                            'hwmon_path': '',
                            'energy': 0.0,
                            'power': None,
                            'power_cap': None,
                            'power_cap_range': [None, None],
                            'fan_enable': None,
                            'pwm_mode': [None, 'UNK'],
                            'fan_pwm': None,
                            'fan_speed': None,
                            'fan_speed_range': [None, None],
                            'fan_pwm_range': [None, None],
                            'fan_target': None,
                            'temp': None,
                            'temp_crit': None,
                            'vddgfx': None,
                            'vddc_range': ['', ''],
                            'loading': None,
                            'mclk_ps': None,
                            'mclk_f': '',
                            'mclk_f_range': ['', ''],
                            'sclk_ps': None,
                            'sclk_f': '',
                            'sclk_f_range': ['', ''],
                            'link_spd': '',
                            'link_wth': '',
                            'ppm': '',
                            'power_dpm_force': '',
                            'vbios': ''})
        self.clinfo = ObjDict({'device_name': '',
                               'device_version': '',
                               'driver_version': '',
                               'opencl_version': '',
                               'pcie_id': '',
                               'max_cu': '',
                               'simd_per_cu': '',
                               'simd_width': '',
                               'simd_ins_width': '',
                               'max_mem_allocation': '',
                               'max_wi_dim': '',
                               'max_wi_sizes': '',
                               'max_wg_size': '',
                               'prf_wg_multiple': ''})
        self.sclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.mclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve_range = {}  # {'1': {SCLK:['val1', 'val2'], VOLT: ['val1', 'val2']}
        self.ppm_modes = {}         # {'1': ['Name', 'Description']}

    def set_params_value(self, name, value):
        """
        Get parameter value for give name.
        :param name:  Parameter name
        :type name: str
        :param value:  parameter value
        :type value: Union[int, str, list]
        :return: Parameter value
        :rtype: Union[int, str, list]
        """
        self.prm[name] = value

    def get_params_value(self, name):
        """
        Get parameter value for give name.
        :param name:  Parameter name
        :type name: str
        :return: Parameter value
        :rtype: Union[int, str, list]
        """
        return self.prm[name]

    def populate(self, pcie_id, gpu_name, short_gpu_name, vendor, driver_module, card_path, hwmon_path,
                 readable, writeable, compute, compatible, ocl_dev, ocl_ver, ocl_index):
        """
        Populate elements of a GpuItem.
        :param pcie_id: The pcid ID of the GPU.
        :type pcie_id: str
        :param gpu_name:  Model name of the GPU
        :type gpu_name: str
        :param short_gpu_name:  Short Model name of the GPU
        :type short_gpu_name: str
        :param vendor:  The make of the GPU (AMD, NVIDIA, ...)
        :type vendor: str
        :param driver_module: The name of the driver.
        :type driver_module: str
        :param card_path: The path to the GPU.
        :type card_path: str
        :param hwmon_path: Path to the hardware monitor files.
        :type hwmon_path: str
        :param readable: readable compatibility flag
        :type readable: bool
        :param writeable: writeable compatibility flag
        :type writeable: bool
        :param compute: Compute compatibility flag
        :type compute: bool
        :param compatible: util compatibility flag
        :type compatible: bool
        :param ocl_dev:  openCL device
        :type ocl_dev: str
        :param ocl_ver: openCL version
        :type ocl_ver: str
        :param ocl_index: openCL index
        :type ocl_index: str
        :return: None
        :rtype: None
        """
        self.prm.pcie_id = pcie_id
        self.prm.model = gpu_name
        self.prm.model_short = short_gpu_name
        self.prm.vendor = vendor
        self.prm.driver = driver_module
        self.prm.card_path = card_path
        self.prm.card_num = int(card_path.replace('{}card'.format(env.GUT_CONST.card_root), '').replace('/device', ''))
        self.prm.hwmon_path = hwmon_path
        self.prm.readable = readable
        self.prm.writeable = writeable
        self.prm.compute = compute
        self.prm.compatible = compatible
        #self.ocl_device_name = ocl_dev
        #self.ocl_device_version = ocl_ver

    def set_clinfo_value(self, name, value):
        """
        Set clinfo values in GPU item dictionary.
        :param name: clinfo parameter name
        :type name: str
        :param value:  parameter value
        :type value: Union[int, str, list]
        :return: None
        :rtype: None
        """
        self.clinfo.name = value

    def get_clinfo_value(self, name):
        """
        Get clinfo parameter value for give name.
        :param name:  clinfo Parameter name
        :type name: str
        :return: clinfo Parameter value
        :rtype: Union[int, str, list]
        """
        return self.clinfo.name

    def copy_clinfo_values(self, gpu_item):
        """
        Copy values of one gpu_item to another.
        :param gpu_item:
        :type gpu_item: GpuItem
        :return: None
        :rtype: None
        """
        for k, v in gpu_item.clinfo.items():
            self.clinfo[k] = v

    def get_nc_params_list(self):
        """
        Get list of parameter names for use with non-compatible cards.
        :return: List of parameter names
        :rtype: list
        """
        return self._GPU_NC_Param_List

    def get_all_params_labels(self):
        """
        Get human friendly labels for params keys.
        :return: Dictionary of label names and Labels
        :rtype: dict
        """
        return self._GPU_Param_Labels

    def get_all_clinfo_labels(self):
        """
        Get human friendly labels for clinfo keys.
        :return: Dictionary of label names and labels
        :rtype: dict
        """
        return self._GPU_CLINFO_Labels

    def is_valid_power_cap(self, power_cap):
        """
        Check if a given power_cap value is valid.
        :param power_cap: Target power cap value to be tested.
        :type power_cap: int
        :return: True if valid
        :rtype: bool
        """
        power_cap_range = self.prm.power_cap_range
        if power_cap_range[0] <= power_cap <= power_cap_range[1]:
            return True
        elif power_cap < 0:
            # negative values will be interpreted as reset request
            return True
        return False

    def is_valid_fan_pwm(self, pwm_value):
        """
        Check if a given fan_pwm value is valid.
        :param pwm_value: Target fan_pwm value to be tested.
        :type pwm_value: int
        :return: True if valid
        :rtype: bool
        """
        pwm_range = self.prm.fan_pwm_range
        if pwm_range[0] <= pwm_value <= pwm_range[1]:
            return True
        elif pwm_value < 0:
            # negative values will be interpreted as reset request
            return True
        return False

    def is_valid_mclk_pstate(self, pstate):
        """
        Check if given mclk pstate value is valid.
        .. note:: pstate = [pstate_number, clk_value, vddc_value]
        :param pstate:
        :type pstate: list[int]
        :return: Return True if valid
        :rtype: bool
        """
        mclk_range = self.prm.mclk_f_range
        mclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(mclk_range[0])))
        mclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(mclk_range[1])))
        if pstate[1] < mclk_min or pstate[1] > mclk_max:
            return False
        if self.prm.gpu_type != 2:
            vddc_range = self.prm.vddc_range
            vddc_min = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[0])))
            vddc_max = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[1])))
            if pstate[2] < vddc_min or pstate[2] > vddc_max:
                return False
        return True

    def is_valid_sclk_pstate(self, pstate):
        """
        Check if given sclk pstate value is valid.
            pstate = [pstate_number, clk_value, vddc_value]
        :param pstate:
        :type pstate: list[int]
        :return: Return True if valid
        :rtype: bool
        """
        sclk_range = self.prm.sclk_f_range
        sclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(sclk_range[0])))
        sclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(sclk_range[1])))
        if pstate[1] < sclk_min or pstate[1] > sclk_max:
            return False
        if self.prm.gpu_type != 2:
            vddc_range = self.prm.vddc_range
            vddc_min = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[0])))
            vddc_max = int(re.sub(r'[a-z,A-Z]*', '', str(vddc_range[1])))
            if pstate[2] < vddc_min or pstate[2] > vddc_max:
                return False
        return True

    def is_changed_sclk_pstate(self, pstate):
        """
        Check if given sclk pstate value different from current.
            pstate = [pstate_number, clk_value, vddc_value]
        :param pstate:
        :type pstate: list[int]
        :return: Return True if changed
        :rtype: bool
        """
        if int(re.sub(r'[a-z,A-Z]*', '', self.sclk_state[pstate[0]][0])) != pstate[1]:
            return True
        if self.prm.gpu_type != 2:
            if int(re.sub(r'[a-z,A-Z]*', '', self.sclk_state[pstate[0]][1])) != pstate[2]:
                return True
        return False

    def is_changed_mclk_pstate(self, pstate):
        """
        Check if given mclk pstate value different from current.
            pstate = [pstate_number, clk_value, vddc_value]
        :param pstate:
        :type pstate: list[int]
        :return: Return True if changed
        :rtype: bool
        """
        if int(re.sub(r'[a-z,A-Z]*', '', self.mclk_state[pstate[0]][0])) != pstate[1]:
            return True
        if self.prm.gpu_type != 2:
            if int(re.sub(r'[a-z,A-Z]*', '', self.mclk_state[pstate[0]][1])) != pstate[2]:
                return True
        return False

    def is_changed_vddc_curve_pt(self, pstate):
        """
        Check if given vddc curve point value different from current.
            curve_point = [point_number, clk_value, vddc_value]
        :param pstate:
        :type pstate: list[int]
        :return: Return True if changed
        :rtype: bool
        """
        if int(re.sub(r'[a-z,A-Z]*', '', self.vddc_curve[pstate[0]][0])) != pstate[1]:
            return True
        if int(re.sub(r'[a-z,A-Z]*', '', self.vddc_curve[pstate[0]][1])) != pstate[2]:
            return True
        return False

    def is_valid_vddc_curve_pts(self, curve_pts):
        """
        Check if given sclk pstate value is valid.
            curve_point = [point_number, clk_value, vddc_value]
        :param curve_pts:
        :type curve_pts: list[int]
        :return: Return True if valid
        :rtype: bool
        """
        sclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(self.vddc_curve_range[str(curve_pts[0])]['SCLK'][0])))
        sclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(self.vddc_curve_range[str(curve_pts[0])]['SCLK'][1])))
        if curve_pts[1] < sclk_min or curve_pts[1] > sclk_max:
            return False
        vddc_min = int(re.sub(r'[a-z,A-Z]*', '', str('650mV')))
        vddc_max = int(re.sub(r'[a-z,A-Z]*', '', str(self.vddc_curve_range[str(curve_pts[0])]['VOLT'][1])))
        if curve_pts[2] < vddc_min or curve_pts[2] > vddc_max:
            return False
        return True

    def is_valid_pstate_list_str(self, ps_str, clk_name):
        """
         Check if the given p-states are valid for the given clock.
        :param ps_str: String of comma separated pstate numbers
        :type ps_str: str
        :param clk_name: The target clock name
        :type clk_name: str
        :return: True if valid
        :rtype: bool
        """
        if ps_str == '':
            return True
        for ps in ps_str.split():
            ps_list = self.get_pstate_list(clk_name)
            try:
                ps_list.index(int(ps))
            except ValueError as except_err:
                print('Error [{}]: Invalid pstate {} for {}.'.format(except_err, ps, clk_name), file=sys.stderr)
                return False
        return True

    def get_pstate_list_str(self, clk_name):
        """
        Get list of pstate numbers and return as a string.
        :param clk_name: Name of clock (SCLK or MCLK)
        :type clk_name: str
        :return:
        :rtype: str
        """
        ps_list = self.get_pstate_list(clk_name)
        return ','.join(str(ps) for ps in ps_list)

    def get_pstate_list(self, clk_name):
        """
        Get list of pstate numbers and return as a list.
        :param clk_name: Name of clock (SCLK or MCLK)
        :type clk_name: str
        :return:
        :rtype: list
        """
        if clk_name == 'SCLK':
            return list(self.sclk_state.keys())
        elif clk_name == 'MCLK':
            return list(self.mclk_state.keys())
        return []

    def get_current_ppm_mode(self):
        """
        Read GPU ppm definitions and current settings from driver files.
        :return: ppm state
        :rtype: list
        """
        if self.prm.power_dpm_force.lower() == 'auto':
            return [-1, 'AUTO']
        ppm_item = self.prm.ppm.split('-')
        return [int(ppm_item[0]), ppm_item[1]]

    def read_gpu_ppm_table(self):
        """
        Read the ppm table.
        :return: None
        """
        file_path = os.path.join(self.prm.card_path, 'pp_power_profile_mode')
        if not os.path.isfile(file_path):
            print('Error getting power profile modes: {}'.format(file_path), file=sys.stderr)
            sys.exit(-1)
        with open(file_path) as card_file:
            for line in card_file:
                linestr = line.strip()
                # Check for mode name: begins with '[ ]+[0-9].*'
                if re.fullmatch(r'[ ]+[0-9].*', line[0:3]):
                    linestr = re.sub(r'[ ]*[*]*:', ' ', linestr)
                    line_items = linestr.split()
                    if env.GUT_CONST.DEBUG: print('Debug: ppm line: {}'.format(linestr), file=sys.stderr)
                    if len(line_items) < 2:
                        print('Error: invalid ppm: {}'.format(linestr), file=sys.stderr)
                        continue
                    if env.GUT_CONST.DEBUG: print('Debug: valid ppm: {}'.format(linestr), file=sys.stderr)
                    self.ppm_modes[line_items[0]] = line_items[1:]
            self.ppm_modes['-1'] = ['AUTO', 'Auto']

        file_path = os.path.join(self.prm.card_path, 'power_dpm_force_performance_level')
        if os.path.isfile(file_path):
            with open(file_path) as card_file:
                self.prm.power_dpm_force = card_file.readline().strip()
        else:
            print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
            self.prm.compatible = False

    def read_gpu_pstates(self):
        """
        Read GPU pstate definitions and parameter ranges from driver files.
        Set card type based on pstate configuration
        :return: None
        """
        range_mode = False
        type_unknown = True

        file_path = os.path.join(self.prm.card_path, 'power_dpm_state')
        if not os.path.isfile(file_path):
            print('Error: Looks like DPM is not enabled: {} does not exist'.format(file_path), file=sys.stderr)
            self.prm.compatible = False
            return
        file_path = os.path.join(self.prm.card_path, 'pp_od_clk_voltage')
        if not os.path.isfile(file_path):
            print('Error getting p-states: {}'.format(file_path), file=sys.stderr)
            self.prm.compatible = False
            return
        with open(file_path) as card_file:
            for line in card_file:
                line = line.strip()
                if re.fullmatch('OD_.*:$', line):
                    if re.fullmatch('OD_.CLK:$', line):
                        clk_name = line.strip()
                    elif re.fullmatch('OD_VDDC_CURVE:$', line):
                        clk_name = line.strip()
                    elif re.fullmatch('OD_RANGE:$', line):
                        clk_name = ''
                        range_mode = True
                    continue
                lineitems = line.split()
                lineitems_len = len(lineitems)
                if type_unknown:
                    if len(lineitems) == 3:
                        # type 1 GPU
                        self.prm.gpu_type = 1
                    elif len(lineitems) == 2:
                        self.prm.gpu_type = 2
                    type_unknown = False
                if lineitems_len < 2 or lineitems_len > 3:
                    print('Error: Invalid pstate entry: {}pp_od_clk_voltage'.format(self.prm.card_path),
                          file=sys.stderr)
                    continue
                if not range_mode:
                    lineitems[0] = int(re.sub(':', '', lineitems[0]))
                    if self.prm.gpu_type == 0 or self.prm.gpu_type == 1:
                        if clk_name == 'OD_SCLK:':
                            self.sclk_state[lineitems[0]] = [lineitems[1], lineitems[2]]
                        elif clk_name == 'OD_MCLK:':
                            self.mclk_state[lineitems[0]] = [lineitems[1], lineitems[2]]
                    else:
                        # Type 2
                        if clk_name == 'OD_SCLK:':
                            self.sclk_state[lineitems[0]] = [lineitems[1], '-']
                        elif clk_name == 'OD_MCLK:':
                            self.mclk_state[lineitems[0]] = [lineitems[1], '-']
                        elif clk_name == 'OD_VDDC_CURVE:':
                            self.vddc_curve[lineitems[0]] = [lineitems[1], lineitems[2]]
                else:
                    if lineitems[0] == 'SCLK:':
                        self.prm.sclk_f_range = [lineitems[1], lineitems[2]]
                    elif lineitems[0] == 'MCLK:':
                        self.prm.mclk_f_range = [lineitems[1], lineitems[2]]
                    elif lineitems[0] == 'VDDC:':
                        self.prm.vddc_range = [lineitems[1], lineitems[2]]
                    elif re.fullmatch('VDDC_CURVE_.*', line):
                        if len(lineitems) == 3:
                            index = re.sub(r'VDDC_CURVE_.*\[', '', lineitems[0])
                            index = re.sub(r'\].*', '', index)
                            param = re.sub(r'VDDC_CURVE_', '', lineitems[0])
                            param = re.sub(r'\[[0-9]\]:', '', param)
                            if env.GUT_CONST.DEBUG:
                                print('Curve: index: {} param: {}, val1 {}, val2: {}'.format(index, param,
                                                                                             lineitems[1],
                                                                                             lineitems[2]))
                            if index in self.vddc_curve_range.keys():
                                self.vddc_curve_range[index].update({param: [lineitems[1], lineitems[2]]})
                            else:
                                self.vddc_curve_range[index] = {}
                                self.vddc_curve_range[index].update({param: [lineitems[1], lineitems[2]]})
                        else:
                            print('Error: Invalid CURVE entry: {}'.format(file_path), file=sys.stderr)

    def read_gpu_sensor_static_data(self):
        """
        Read GPU static data from HWMON path.
        :return: None
        """
        try:
            file_path = os.path.join(self.prm.hwmon_path, 'power1_cap_max')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    power1_cap_max_value = int(int(hwmon_file.readline())/1000000)
                file_path = os.path.join(self.prm.hwmon_path, 'power1_cap_min')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        power1_cap_min_value = int(int(hwmon_file.readline())/1000000)
                    self.prm.power_cap_range = [power1_cap_min_value, power1_cap_max_value]
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.hwmon_path, 'temp1_crit')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    self.prm.temp_crit = int(hwmon_file.readline())/1000
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            # Get fan data if --no_fan flag is not set
            if env.GUT_CONST.show_fans:
                file_path = os.path.join(self.prm.hwmon_path, 'fan1_max')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        fan1_max_value = int(hwmon_file.readline())
                    file_path = os.path.join(self.prm.hwmon_path, 'fan1_min')
                    if os.path.isfile(file_path):
                        with open(file_path) as hwmon_file:
                            fan1_min_value = int(hwmon_file.readline())
                        self.prm.fan_speed_range = [fan1_min_value, fan1_max_value]
                    else:
                        print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)

                file_path = os.path.join(self.prm.hwmon_path, 'pwm1_max')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        pwm1_max_value = int(100*(int(hwmon_file.readline())/255))
                    file_path = os.path.join(self.prm.hwmon_path, 'pwm1_min')
                    if os.path.isfile(file_path):
                        with open(file_path) as hwmon_file:
                            pwm1_pmin_value = int(100*(int(hwmon_file.readline())/255))
                        self.prm.fan_pwm_range = [pwm1_pmin_value, pwm1_max_value]
                    else:
                        print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                    self.prm.compatible = False
        except (FileNotFoundError, OSError) as except_err:
            print('Error [{}]: Problem reading static data from GPU HWMON: {}'.format(except_err, self.prm.hwmon_path),
                  file=sys.stderr)
            self.prm.compatible = False

    def read_gpu_sensor_data(self):
        """
        Read GPU sensor data from HWMON path.
        :return: None
        """
        try:
            file_path = os.path.join(self.prm.hwmon_path, 'power1_cap')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    self.prm.power_cap = int(hwmon_file.readline())/1000000
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.hwmon_path, 'power1_average')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    power_uw = int(hwmon_file.readline())
                    time_n = env.GUT_CONST.now(env.GUT_CONST.USELTZ)
                    self.prm.power = int(power_uw)/1000000
                    delta_hrs = ((time_n - self.energy['tn']).total_seconds())/3600
                    self.energy['tn'] = time_n
                    self.energy['cumulative'] += delta_hrs * power_uw/1000000000
                    self.prm.energy = round(self.energy['cumulative'], 6)
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.hwmon_path, 'temp1_input')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    self.prm.temp = int(hwmon_file.readline())/1000
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
        except (FileNotFoundError, OSError) as except_err:
            print('Error [{}]: Problem reading sensor [power/temp] from GPU HWMON: {}'.format(except_err,
                  self.prm.hwmon_path), file=sys.stderr)
            self.prm.compatible = False

        # Get fan data if --no_fan flag is not set
        if env.GUT_CONST.show_fans:
            # First non-critical fan data
            # On error will be disabled, but still compatible
            name_hwfile = ('fan1_enable', 'fan1_target', 'fan1_input')
            name_param = ('fan_enable', 'fan_target', 'fan_speed')
            for nh, np in zip(name_hwfile, name_param):
                if nh not in self.hwmon_disabled:
                    file_path = os.path.join(self.prm.hwmon_path, nh)
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path) as hwmon_file:
                                self.set_params_value(np, hwmon_file.readline().strip())
                        except (FileNotFoundError, OSError) as except_err:
                            print('Warning [{}]: Problem reading sensor [{}] data from GPU HWMON: {}'.format(except_err,
                                  nh, self.prm.hwmon_path), file=sys.stderr)
                            self.hwmon_disabled.append(nh)
                    else:
                        print('Warning: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                        self.hwmon_disabled.append(nh)

            # Now critical fan data
            try:
                file_path = os.path.join(self.prm.hwmon_path, 'pwm1_enable')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        pwm_mode_value = int(hwmon_file.readline().strip())
                        if pwm_mode_value == 0:
                            pwm_mode_name = 'None'
                        elif pwm_mode_value == 1:
                            pwm_mode_name = 'Manual'
                        elif pwm_mode_value == 2:
                            pwm_mode_name = 'Dynamic'
                        self.prm.pwm_mode = [pwm_mode_value, pwm_mode_name]
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                    self.prm.compatible = False

                file_path = os.path.join(self.prm.hwmon_path, 'pwm1')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        self.prm.fan_pwm = int(100*(int(hwmon_file.readline())/255))
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                    self.prm.compatible = False
            except (FileNotFoundError, OSError) as except_err:
                print('Error [{}]: Problem reading sensor [pwm] data from GPU HWMON: {}'.format(except_err,
                      self.prm.hwmon_path), file=sys.stderr)
                print('Try running with --no_fan option', file=sys.stderr)
                self.prm.compatible = False

        try:
            file_path = os.path.join(self.prm.hwmon_path, 'in0_label')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    if hwmon_file.readline().rstrip() == 'vddgfx':
                        with open(os.path.join(self.prm.hwmon_path, 'in0_input')) as hwmon_file2:
                            self.prm.vddgfx = int(hwmon_file2.readline())
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
        except (FileNotFoundError, OSError) as except_err:
            print('Error [{}]: Problem reading sensor [in0_label] data from GPU HWMON: {}'.format(except_err,
                  self.prm.hwmon_path), file=sys.stderr)
            self.prm.compatible = False

    def read_gpu_driver_info(self):
        """
        Read GPU current driver information from card path directory.
        :return: None
        """
        try:
            # get all device ID information
            file_path = os.path.join(self.prm.card_path, 'device')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    device_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
            file_path = os.path.join(self.prm.card_path, 'vendor')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    vendor_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
            file_path = os.path.join(self.prm.card_path, 'subsystem_device')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    subsystem_device_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
            file_path = os.path.join(self.prm.card_path, 'subsystem_vendor')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    subsystem_vendor_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
            # store device_id information
            self.prm.id = {'vendor': vendor_id,
                           'device': device_id,
                           'subsystem_vendor': subsystem_vendor_id,
                           'subsystem_device': subsystem_device_id}
            # use device info to set model
            if self.prm.model_device_decode == 'UNDETERMINED':
                pcid = PCImodule.PCI_ID()
                self.prm.model_device_decode = pcid.get_model(self.prm.id)
            # set display model to model_device_decode if shorter than model short
            if (self.prm.model_device_decode != 'UNDETERMINED' and
                    len(self.prm.model_device_decode) < 1.2*len(self.prm.model_short)):
                self.prm.model_display = self.prm.model_device_decode
            else:
                self.prm.model_display = self.prm.model_short

            file_path = os.path.join(self.prm.card_path, 'vbios_version')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.prm.vbios = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
        except (FileNotFoundError, OSError) as except_err:
            print('Error [{}]: Problem reading GPU driver information for Card Path: {}'.format(except_err,
                  self.prm.card_path), file=sys.stderr)
            self.prm.compatible = False

    def read_gpu_state_data(self):
        """
        Read GPU current state information from card path directory.
        :return: None
        """
        try:
            file_path = os.path.join(self.prm.card_path, 'gpu_busy_percent')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.prm.loading = int(card_file.readline())
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.card_path, 'current_link_speed')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.prm.link_spd = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.card_path, 'current_link_width')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.prm.link_wth = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.card_path, 'pp_dpm_sclk')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    for line in card_file:
                        if line[len(line)-2] == '*':
                            lineitems = line.split(sep=':')
                            self.prm.sclk_ps = lineitems[0].strip()
                            self.prm.sclk_f = lineitems[1].strip().strip('*')
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.card_path, 'pp_dpm_mclk')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    for line in card_file:
                        if line[len(line)-2] == '*':
                            lineitems = line.split(sep=':')
                            self.prm.mclk_ps = lineitems[0].strip()
                            self.prm.mclk_f = lineitems[1].strip().strip('*')
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.card_path, 'pp_power_profile_mode')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    for line in card_file:
                        linestr = line.strip()
                        srch_obj = re.search(r'\*:', linestr)
                        if srch_obj:
                            lineitems = linestr.split(sep='*:')
                            mode_str = lineitems[0].strip()
                            mode_str = re.sub(r'[ ]+', '-', mode_str)
                            self.prm.ppm = mode_str
                            break
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False

            file_path = os.path.join(self.prm.card_path, 'power_dpm_force_performance_level')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.prm.power_dpm_force = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.prm.compatible = False
        except (FileNotFoundError, OSError) as except_err:
            print('Error [{}]: getting data from GPU Card Path: {}'.format(except_err, self.prm.card_path),
                  file=sys.stderr)
            self.prm.compatible = False

    def print_ppm_table(self):
        """
        Print human friendly table of ppm parameters.
        :return: None
        """
        if not self.prm.compatible:
            return
        print('Card: {}'.format(self.prm.card_path))
        print('Power Performance Mode: {}'.format(self.prm.power_dpm_force))
        for k, v in self.ppm_modes.items():
            print('{:<3}: {:>15}'.format(k, v[0]), end='')
            for v_item in v[1:]:
                print('{:>18}'.format(v_item), end='')
            print('')
        print('')

    def print_pstates(self):
        """
        Print human friendly table of p-states.
        :return: None
        """
        if not self.prm.compatible:
            return
        print('Card: {}'.format(self.prm.card_path))
        print('SCLK: {:<17} MCLK:'.format(' '))
        for k, v in self.sclk_state.items():
            print('{:>1}:  {:<8}  {:<8}'.format(k, v[0], v[1]), end='')
            if k in self.mclk_state.keys():
                print('{:3>}:  {:<8}  {:<8}'.format(k, self.mclk_state[k][0], self.mclk_state[k][1]))
            else:
                print('')
        if self.prm.gpu_type == 2:
            print('VDDC_CURVE')
            for k, v in self.vddc_curve.items():
                print('{}: {}'.format(k, v))
        print('')

    def print(self, clflag=False):
        """
        Display ls like listing function for GPU parameters.
        :return: None
        """
        for i, (k, v) in enumerate(self.get_all_params_labels().items()):
            if i == 1:
                if self.prm.compatible:
                    print('{} Compatibility: Yes'.format(__program_name__))
                else:
                    print('{} Compatibility: NO'.format(__program_name__))
            if not self.prm.compatible:
                if k not in self.get_nc_params_list():
                    continue
            print('{}: {}'.format(v, self.get_params_value(k)))
        if clflag:
            for k, v in self.get_all_clinfo_labels().items():
                print('{}: {}'.format(v, self.get_clinfo_value(k)))
        print('')

    def get_plot_data(self, gpu_list):
        """
        Return a dictionary of dynamic gpu parameters used by amdgpu-plot to populate a df.
        :param gpu_list: GpuList object
        :type gpu_list: GpuList
        :return: Dictionary of GPU state info for plot data.
        :rtype: dict
        """
        gpu_state = {'Time': str(self.energy['tn'].strftime('%c')).strip(), 'Card#': int(self.prm.card_num)}

        for table_item in gpu_list.table_parameters():
            gpu_state_str = str(re.sub('M[Hh]z', '', str(self.get_params_value(table_item)))).strip()
            if gpu_state_str.isnumeric():
                gpu_state[table_item] = int(gpu_state_str)
            elif re.fullmatch(r'[0-9]+.[0-9]*', gpu_state_str) or re.fullmatch(r'[0-9]*.[0-9]+', gpu_state_str):
                gpu_state[table_item] = float(gpu_state_str)
            elif gpu_state_str == '' or gpu_state_str == '-1' or gpu_state_str == 'NA' or gpu_state_str is None:
                gpu_state[table_item] = 'NA'
            else:
                gpu_state[table_item] = gpu_state_str
        return gpu_state


class GpuList:
    """
    A list of GpuItem indexed with uuid.  It also contains a table of parameters used for tabular printouts
    """
    # Table parameters labels.
    if env.GUT_CONST.show_fans:
        _table_parameters = ['model_display', 'loading', 'power', 'power_cap', 'energy', 'temp', 'vddgfx',
                             'fan_pwm', 'sclk_f', 'sclk_ps', 'mclk_f', 'mclk_ps', 'ppm']
        _table_param_labels = {'model_display': 'Model',
                               'loading': 'Load %',
                               'power': 'Power (W)',
                               'power_cap': 'Power Cap (W)',
                               'energy': 'Energy (kWh)',
                               'temp': 'T (C)',
                               'vddgfx': 'VddGFX (mV)',
                               'fan_pwm': 'Fan Spd (%)',
                               'sclk_f': 'Sclk (MHz)',
                               'sclk_ps': 'Sclk Pstate',
                               'mclk_f': 'Mclk (MHz)',
                               'mclk_ps': 'Mclk Pstate',
                               'ppm': 'Perf Mode'}
    else:
        _table_parameters = ['model_display', 'loading', 'power', 'power_cap', 'energy', 'temp', 'vddgfx',
                             'sclk_f', 'sclk_ps', 'mclk_f', 'mclk_ps', 'ppm']
        _table_param_labels = {'model_display': 'Model',
                               'loading': 'Load %',
                               'power': 'Power (W)',
                               'power_cap': 'Power Cap (W)',
                               'energy': 'Energy (kWh)',
                               'temp': 'T (C)',
                               'vddgfx': 'VddGFX (mV)',
                               'sclk_f': 'Sclk (MHz)',
                               'sclk_ps': 'Sclk Pstate',
                               'mclk_f': 'Mclk (MHz)',
                               'mclk_ps': 'Mclk Pstate',
                               'ppm': 'Perf Mode'}

    def __repr__(self):
        return self.list

    def __str__(self):
        return 'GPU_List: Number of GPUs: {}'.format(self.num_gpus())

    def __init__(self):
        self.list = {}
        self.opencl_map = {}

    def add(self, gpu_item):
        """
        Add given GpuItem to the GpuList
        :param gpu_item:  Item to be added
        :type gpu_item: GpuItem
        :return: None
        """
        self.list[gpu_item.prm.uuid] = gpu_item

    def table_param_labels(self):
        """
        Get dictionary of parameter labels to be used in table reports.
        :return: Dictionary of table parameters/labels
        :rtype: dict
        """
        return self._table_param_labels

    def table_parameters(self):
        """
        Get list of parameters to be used in table reports.
        :return: List of table parameters
        :rtype: list
        """
        return self._table_parameters

    def set_gpu_list(self):
        """
        Use lspci to populate list of all installed GPUs.
        :return: True on success
        :rtype: bool
        """
        if not env.GUT_CONST.cmd_lspci:
            return False
        self.read_gpu_opencl_data()
        if env.GUT_CONST.DEBUG: print('openCL map: {}'.format(self.opencl_map))

        try:
            pcie_ids = subprocess.check_output('{} | grep -E \"^.*(VGA|3D|Display).*$\" | grep -Eo \
                                               \"^([0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F])\"'.format(
                                               env.GUT_CONST.cmd_lspci), shell=True).decode().split()
        except (subprocess.CalledProcessError, OSError) as except_err:
            print('Error [{}]: lspci failed to find GPUs'.format(except_err))
            return False

        if env.GUT_CONST.DEBUG: print('Found {} GPUs'.format(len(pcie_ids)))
        for pcie_id in pcie_ids:
            gpu_uuid = uuid4().hex
            self.add(GpuItem(gpu_uuid))
            if env.GUT_CONST.DEBUG: print('GPU: {}'.format(pcie_id))
            readable = writeable = compatible = compute = False
            try:
                lspci_items = subprocess.check_output('{} -k -s {}'.format(env.GUT_CONST.cmd_lspci, pcie_id),
                                                      shell=True).decode().split('\n')
            except (subprocess.CalledProcessError, OSError) as except_err:
                print('Fatal Error [{}]: Can not get GPU details with lspci'.format(except_err))
                sys.exit(-1)
            if env.GUT_CONST.DEBUG: print(lspci_items)

            # Get Long GPU Name
            gpu_name = 'UNKNOWN'
            gpu_name_items = lspci_items[0].split(': ', maxsplit=1)
            if len(gpu_name_items) >= 2:
                gpu_name = gpu_name_items[1]
            try:
                short_gpu_name = gpu_name.split('[AMD/ATI]')[1]
            except:
                short_gpu_name = 'UNKNOWN'
            # Check for Fiji ProDuo
            srch_obj = re.search('Fiji', gpu_name)
            if srch_obj:
                srch_obj = re.search(r'Radeon Pro Duo', lspci_items[1].split('[AMD/ATI]')[1])
                if srch_obj:
                    gpu_name = 'Radeon Fiji Pro Duo'

            # Get GPU brand: AMD, INTEL, NVIDIA, ASPEED
            vendor = 'UNKNOWN'
            opencl_device_name = None
            opencl_device_version = None
            opencl_device_index = None
            srch_obj = re.search(r'(AMD|amd|ATI|ati)', gpu_name)
            if srch_obj:
                vendor = 'AMD'
                compatible = True
                compute = False
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        opencl_device_name = self.opencl_map[pcie_id][0]
                        opencl_device_version = self.opencl_map[pcie_id][1]
                        opencl_device_index = self.opencl_map[pcie_id][2]
                        compute = True
                else:
                    compute = True
            srch_obj = re.search(r'(NVIDIA|nvidia|nVidia)', gpu_name)
            if srch_obj:
                vendor = 'NVIDIA'
                compatible = False
                compute = False
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        opencl_device_name = self.opencl_map[pcie_id][0]
                        opencl_device_version = self.opencl_map[pcie_id][1]
                        opencl_device_index = self.opencl_map[pcie_id][2]
                        compute = True
                else:
                    compute = True
            srch_obj = re.search(r'(INTEL|intel|Intel)', gpu_name)
            if srch_obj:
                vendor = 'INTEL'
                compatible = False
                compute = False
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        opencl_device_name = self.opencl_map[pcie_id][0]
                        opencl_device_version = self.opencl_map[pcie_id][1]
                        opencl_device_index = self.opencl_map[pcie_id][2]
                        compute = True
                else:
                    srch_obj = re.search(r' 530', gpu_name)
                    if srch_obj:
                        compute = False
                    else:
                        compute = True
            srch_obj = re.search(r'(ASPEED|aspeed|Aspeed)', gpu_name)
            if srch_obj:
                vendor = 'ASPEED'
                compute = False
                compatible = False
            srch_obj = re.search(r'(MATROX|matrox|Matrox)', gpu_name)
            if srch_obj:
                vendor = 'MATROX'
                compute = False
                compatible = False

            # Get Driver Name
            driver_module = 'UNKNOWN'
            for lspci_line in lspci_items:
                srch_obj = re.search(r'(Kernel|kernel)', lspci_line)
                if srch_obj:
                    driver_module_items = lspci_line.split(': ')
                    if len(driver_module_items) >= 2:
                        driver_module = driver_module_items[1].strip()

            # Get full card path
            card_path = None
            device_dirs = glob.glob(os.path.join(env.GUT_CONST.card_root, 'card?/device'))
            for device_dir in device_dirs:
                sysfspath = str(Path(device_dir).resolve())
                if pcie_id == sysfspath[-7:]:
                    card_path = device_dir

            # Get full hwmon path
            hwmon_path = None
            hw_file_srch = glob.glob(os.path.join(card_path, env.GUT_CONST.hwmon_sub) + '?')
            if env.GUT_CONST.DEBUG: print('hw_file_search: ', hw_file_srch)
            if len(hw_file_srch) > 1:
                print('More than one hwmon file found: ', hw_file_srch)
            elif len(hw_file_srch) == 1:
                hwmon_path = hw_file_srch[0]

            self.list[gpu_uuid].populate(pcie_id, gpu_name, short_gpu_name, vendor, driver_module,
                                         card_path, hwmon_path, readable, writeable, compute, compatible,
                                         opencl_device_name, opencl_device_version, opencl_device_index)

            # Set energy compatibility TODO need to set read compatibility instead
            #self.list[gpu_uuid].get_power(set_energy_compatibility=True)
        return True

    def read_gpu_opencl_data(self):
        """
        Use clinfo system call to get openCL details for relevant GPUs.
        :return:  Returns True if successful
        :rtype:  bool
        .. todo:: Read of Intel pcie_id is not working.
        """
        # Check access to clinfo command
        if not env.GUT_CONST.cmd_clinfo:
            print('OS Command [clinfo] not found.  Use sudo apt-get install clinfo to install', file=sys.stderr)
            return False
        cmd = subprocess.Popen(shlex.split('{} --raw'.format(env.GUT_CONST.cmd_clinfo)), shell=False,
                               stdout=subprocess.PIPE)
        ocl_pcie_id = ''
        ocl_device_name = ''
        ocl_device_version = ''
        ocl_index = ''
        ocl_pcie_slot_id = ocl_pcie_bus_id = None
        for line in cmd.stdout:
            linestr = line.decode('utf-8').strip()
            if len(linestr) < 1:
                continue
            if linestr[0] != '[':
                continue
            line_items = linestr.split(maxsplit=2)
            if len(line_items) != 3:
                continue
            cl_vender, cl_index = tuple(re.sub(r'[\[\]]', '', line_items[0]).split('/'))
            if cl_index == '*':
                continue
            if ocl_index == '':
                ocl_index = cl_index
                ocl_pcie_slot_id = ocl_pcie_bus_id = None

            # If new cl_index, then update opencl_map
            if cl_index != ocl_index:
                self.opencl_map.update({ocl_pcie_id: [ocl_device_name, ocl_device_version, ocl_index]})
                if env.GUT_CONST.DEBUG: print('cl_index: {}'.format(self.opencl_map[ocl_pcie_id]))
                ocl_index = cl_index
                ocl_pcie_id = ''
                ocl_device_name = ''
                ocl_device_version = ''
                ocl_pcie_slot_id = ocl_pcie_bus_id = None

            param_str = line_items[1]
            srch_obj = re.search('CL_DEVICE_NAME', param_str)
            if srch_obj:
                ocl_device_name = line_items[2].strip()
                if env.GUT_CONST.DEBUG: print('ocl_device_name [{}]'.format(ocl_device_name))
                continue
            srch_obj = re.search('CL_DEVICE_VERSION', param_str)
            if srch_obj:
                ocl_device_version = line_items[2].strip()
                if env.GUT_CONST.DEBUG: print('ocl_device_version [{}]'.format(ocl_device_version))
                continue
            srch_obj = re.search('CL_DEVICE_TOPOLOGY', param_str)
            if srch_obj:
                ocl_pcie_id = (line_items[2].split()[1]).strip()
                if env.GUT_CONST.DEBUG: print('ocl_pcie_id [{}]'.format(ocl_pcie_id))
                continue
            srch_obj = re.search('CL_DEVICE_PCI_BUS_ID_NV', param_str)
            if srch_obj:
                ocl_pcie_bus_id = hex(int(line_items[2].strip()))
                if ocl_pcie_slot_id is not None:
                    ocl_pcie_id = '{}:{}.0'.format(ocl_pcie_bus_id[2:].zfill(2), ocl_pcie_slot_id[2:].zfill(2))
                    ocl_pcie_slot_id = ocl_pcie_bus_id = None
                    if env.GUT_CONST.DEBUG: print('ocl_pcie_id [{}]'.format(ocl_pcie_id))
                continue
            srch_obj = re.search('CL_DEVICE_PCI_SLOT_ID_NV', param_str)
            if srch_obj:
                ocl_pcie_slot_id = hex(int(line_items[2].strip()))
                if ocl_pcie_bus_id is not None:
                    ocl_pcie_id = '{}:{}.0'.format(ocl_pcie_bus_id[2:].zfill(2), ocl_pcie_slot_id[2:].zfill(2))
                    ocl_pcie_slot_id = ocl_pcie_bus_id = None
                    if env.GUT_CONST.DEBUG: print('ocl_pcie_id [{}]'.format(ocl_pcie_id))
                continue

        self.opencl_map.update({ocl_pcie_id: [ocl_device_name, ocl_device_version, ocl_index]})
        if env.GUT_CONST.DEBUG: print('cl_index: {}'.format(self.opencl_map[ocl_pcie_id]))
        return True

    def num_gpus(self, vendor=None, compatible=False, readable=False, writeable=False):
        """
        Return the count of GPUs.  Counts all by default, but can also count compatible, readable or writeable.
        Only one flag should be set.
        :param vendor: Only count vendor GPUs if True.
        :type vendor: str
        :param compatible: Only count compatible GPUs if True.
        :type compatible: bool
        :param readable: Only count readable GPUs if True.
        :type readable: bool
        :param writeable: Only count writeable GPUs if True.
        :type readable: bool
        :return: Number of GPUs
        :rtype: int
        """
        cnt = 0
        for v in self.list.values():
            if vendor:
                if vendor != v.prm.vendor:
                    continue
            if compatible:
                if v.prm.compatible:
                    cnt += 1
            elif readable:
                if v.prm.readable:
                    cnt += 1
            elif writeable:
                if v.prm.writeable:
                    cnt += 1
            else:
                cnt += 1
        return cnt

    def list_gpus(self, vendor=None, compatible=False, readable=False, writeable=False):
        """
        Return GPU_Item of GPUs.  Contains all by default, but can also count compatible, readable or writeable.
        Only one flag should be set.
        :param vendor: Only count vendor GPUs if True.
        :type vendor: str
        :param compatible: Only count compatible GPUs if True.
        :type compatible: bool
        :param readable: Only count readable GPUs if True.
        :type readable: bool
        :param writeable: Only count writeable GPUs if True.
        :type readable: bool
        :return: GpuList of compatible GPUs
        :rtype: GpuList
        """
        result_list = GpuList()
        for k, v in self.list.items():
            if vendor:
                if vendor != v.prm.vendor:
                    continue
            if compatible:
                if v.prm.compatible:
                    result_list.list[k] = v
            elif readable:
                if v.prm.readable:
                    result_list.list[k] = v
            elif writeable:
                if v.prm.writeable:
                    result_list.list[k] = v
            else:
                result_list.list[k] = v
        return result_list

    def read_gpu_ppm_table(self):
        """
        Read GPU ppm data and populate GpuItem
        :return: None
        """
        for v in self.list.values():
            if v.prm.compatible:
                v.read_gpu_ppm_table()

    def print_ppm_table(self):
        """
        Print the GpuItem ppm data.
        :return: None
        """
        for v in self.list.values():
            v.print_ppm_table()

    def read_gpu_pstates(self):
        """
        Read GPU p-state data and populate GpuItem
        :return: None
        """
        for v in self.list.values():
            if v.prm.compatible:
                v.read_gpu_pstates()

    def print_pstates(self):
        """
        Print the GpuItem p-state data.
        :return: None
        """
        for v in self.list.values():
            v.print_pstates()

    def read_gpu_state_data(self):
        """Read dynamic state data from GPUs"""
        for v in self.list.values():
            if v.prm.compatible:
                v.read_gpu_state_data()

    def read_gpu_sensor_static_data(self):
        """Read dynamic sensor data from GPUs"""
        for v in self.list.values():
            if v.prm.compatible:
                v.read_gpu_sensor_static_data()

    def read_gpu_sensor_data(self):
        """Read dynamic sensor data from GPUs"""
        for v in self.list.values():
            if v.prm.compatible:
                v.read_gpu_sensor_data()

    def read_gpu_driver_info(self):
        """Read data static driver information for GPUs"""
        for v in self.list.values():
            if v.prm.compatible:
                v.read_gpu_driver_info()

    # Printing Methods follow.
    def print(self, clflag=False):
        """
        Print all GpuItem.
        :param clflag: If true, print clinfo
        :type clflag: bool
        :return:
        """
        for v in self.list.values():
            v.print(clflag)

    def print_table(self):
        """
        Print table of parameters.
        :return: True if success
        :rtype: bool
        """
        if self.num_gpus() < 1:
            return False

        print('┌', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.list.values():
            print('┬', '─'.ljust(16, '─'), sep='', end='')
        print('┐')

        print('│', '\x1b[1;36m' + 'Card #'.ljust(13, ' ') + '\x1b[0m', sep='', end='')
        for v in self.list.values():
            print('│', '\x1b[1;36m' + ('card' + v.prm.card_num).ljust(16, ' ') + '\x1b[0m',
                  sep='', end='')
        print('│')

        print('├', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.list.values():
            print('┼', '─'.ljust(16, '─'), sep='', end='')
        print('┤')

        for table_item in self.table_parameters():
            print('│', '\x1b[1;36m' + self.table_param_labels()[table_item].ljust(13, ' ')[:13] + '\x1b[0m',
                  sep='', end='')
            for v in self.list.values():
                print('│', str(v.get_params_value(table_item)).ljust(16, ' ')[:16], sep='', end='')
            print('│')

        print('└', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.list.values():
            print('┴', '─'.ljust(16, '─'), sep='', end='')
        print('┘')
        return True

    def print_log_header(self, log_file_ptr):
        """
        Print the log header.
        :param log_file_ptr: File pointer for target output.
        :type log_file_ptr: file
        :return: True if success
        :rtype: bool
        """
        if self.num_gpus() < 1:
            return False

        # Print Header
        print('Time|Card#', end='', file=log_file_ptr)
        for table_item in self.table_parameters():
            print('|{}'.format(table_item), end='', file=log_file_ptr)
        print('', file=log_file_ptr)
        return True

    def print_log(self, log_file_ptr):
        """
        Print the log data.
        :param log_file_ptr: File pointer for target output.
        :type log_file_ptr: file
        :return: True if success
        :rtype: bool
        """
        if self.num_gpus() < 1:
            return False

        # Print Data
        for v in self.list.values():
            print('{}|{}'.format(v.energy['tn'].strftime('%c').strip(), v.card_num),
                  sep='', end='', file=log_file_ptr)
            for table_item in self.table_parameters():
                print('|{}'.format(re.sub('M[Hh]z', '', str(v.get_params_value(table_item)).strip())),
                      sep='', end='', file=log_file_ptr)
            print('', file=log_file_ptr)
        return True

    def print_plot_header(self, log_file_ptr):
        """
        Print the plot header.
        :param log_file_ptr: File pointer for target output.
        :type log_file_ptr: file
        :return: True if success
        :rtype: bool
        """
        if self.num_gpus() < 1:
            return False

        # Print Header
        line_str_item = ['Time|Card#']
        for table_item in self.table_parameters():
            line_str_item.append('|' + table_item)
        line_str_item.append('\n')
        line_str = ''.join(line_str_item)
        log_file_ptr.write(line_str.encode('utf-8'))
        log_file_ptr.flush()
        return True

    def print_plot(self, log_file_ptr):
        """
        Print the plot data.
        :param log_file_ptr: File pointer for target output.
        :type log_file_ptr: file
        :return: True if success
        :rtype: bool
        """
        if self.num_gpus() < 1:
            return False

        # Print Data
        for v in self.list.values():
            line_str_item = [str(v.energy['tn'].strftime('%c')).strip() + '|' + str(v.card_num)]
            for table_item in self.table_parameters():
                line_str_item.append('|' + str(re.sub('M[Hh]z', '', str(v.get_params_value(table_item)))).strip())
            line_str_item.append('\n')
            line_str = ''.join(line_str_item)
            log_file_ptr.write(line_str.encode('utf-8'))
        log_file_ptr.flush()
        return True


def about():
    """
    Print details about this module.
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
