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

import re
import subprocess
import shlex
import os
import sys
from pathlib import Path
from uuid import uuid4
import glob
import shutil
try:
    from GPUmodules import env
except ImportError:
    import env
try:
    from GPUmodules import PCImodule
except ImportError:
    import PCImodule


class GpuItem:
    """An object to store GPU details.
    .. note:: GPU Frequency/Voltage Control Type: 0 = None, 1 = P-states, 2 = Curve
    """
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
    if env.gut_const.show_fans:
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
        return {'params': self.params, 'clinfo': self.clinfo,
                'sclk_state': self.sclk_state, 'mclk_state': self.mclk_state,
                'vddc_curve': self.vddc_curve, 'vddc_curve_range': self.vddc_curve_range,
                'ppm_modes': self.ppm_modes}

    def __str__(self):
        """
        Return  simple string representing the GpuItem object.
        :return:
        :rtype: str
        """
        return 'GPU_Item: uuid={}'.format(self.uuid)

    def __init__(self, item_id):
        """
        Initialize GpuItem object.
        :param item_id:  UUID of the new item.
        :type item_id: str
        """
        self.uuid = item_id
        self.card_num = None
        self.card_path = ''
        self.hwmon_path = ''
        self.compatible = True
        self.writeable = False
        self.readable = False
        time_0 = env.gut_const.now(env.gut_const.USELTZ)
        self.energy = {'t0': time_0, 'tn': time_0, 'cumulative': 0.0}
        self.hwmon_disabled = []

        self.params = {'uuid': item_id,
                       'card_num': '',
                       'pcie_id': '',
                       'driver': '',
                       'gpu_type': 0,
                       'id': {'vendor': '', 'device': '', 'subsystem_vendor': '', 'subsystem_device': ''},
                       'model_device_decode': 'UNDETERMINED',
                       'model': '',
                       'model_short': '',
                       'model_display': '',
                       'card_path': '',
                       'hwmon_path': '',
                       'energy': 0.0,
                       'power': -1,
                       'power_cap': -1,
                       'power_cap_range': [-1, -1],
                       'fan_enable': -1,
                       'pwm_mode': [-1, 'UNK'],
                       'fan_pwm': -1,
                       'fan_speed': -1,
                       'fan_speed_range': [-1, -1],
                       'fan_pwm_range': [-1, -1],
                       'fan_target': -1,
                       'temp': -1,
                       'temp_crit': -1,
                       'vddgfx': -1,
                       'vddc_range': ['', ''],
                       'loading': -1,
                       'mclk_ps': -1,
                       'mclk_f': '',
                       'mclk_f_range': ['', ''],
                       'sclk_ps': -1,
                       'sclk_f': '',
                       'sclk_f_range': ['', ''],
                       'link_spd': '',
                       'link_wth': '',
                       'ppm': '',
                       'power_dpm_force': '',
                       'vbios': ''}
        self.clinfo = {'device_name': '',
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
                       'prf_wg_multiple': ''}
        self.sclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.mclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve_range = {}  # {'1': {SCLK:['val1', 'val2'], VOLT: ['val1', 'val2']}
        self.ppm_modes = {}         # {'1': ['Name', 'Description']}

    def set_params_value(self, name, value):
        """
        Set param values in GPU item dictionary.
        :param name: parameter name
        :type name: str
        :param value:  parameter value
        :type value: Union[int, str, list]
        :return: None
        :rtype: None
        """
        self.params[name] = value
        if name == 'driver' and value != 'amdgpu':
            self.compatible = False
        elif name == 'card_num':
            self.card_num = value
        elif name == 'card_path':
            self.card_path = value
        elif name == 'hwmon_path':
            self.hwmon_path = value

    def get_params_value(self, name):
        """
        Get parameter value for give name.
        :param name:  Parameter name
        :type name: str
        :return: Parameter value
        :rtype: Union[int, str, list]
        """
        return self.params[name]

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
        self.clinfo[name] = value

    def get_clinfo_value(self, name):
        """
        Get clinfo parameter value for give name.
        :param name:  clinfo Parameter name
        :type name: str
        :return: clinfo Parameter value
        :rtype: Union[int, str, list]
        """
        return self.clinfo[name]

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
        power_cap_range = self.get_params_value('power_cap_range')
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
        pwm_range = self.get_params_value('fan_pwm_range')
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
        mclk_range = self.get_params_value('mclk_f_range')
        mclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(mclk_range[0])))
        mclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(mclk_range[1])))
        if pstate[1] < mclk_min or pstate[1] > mclk_max:
            return False
        if self.get_params_value('gpu_type') != 2:
            vddc_range = self.get_params_value('vddc_range')
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
        sclk_range = self.get_params_value('sclk_f_range')
        sclk_min = int(re.sub(r'[a-z,A-Z]*', '', str(sclk_range[0])))
        sclk_max = int(re.sub(r'[a-z,A-Z]*', '', str(sclk_range[1])))
        if pstate[1] < sclk_min or pstate[1] > sclk_max:
            return False
        if self.get_params_value('gpu_type') != 2:
            vddc_range = self.get_params_value('vddc_range')
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
        if self.get_params_value('gpu_type') != 2:
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
        if self.get_params_value('gpu_type') != 2:
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
            except ValueError:
                print('Error: Invalid pstate {} for {}.'.format(ps, clk_name), file=sys.stderr)
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
        if self.get_params_value('power_dpm_force').lower() == 'auto':
            return [-1, 'AUTO']
        ppm_item = self.get_params_value('ppm').split('-')
        return [int(ppm_item[0]), ppm_item[1]]

    def read_gpu_ppm_table(self):
        """
        Read the ppm table.
        :return: None
        """
        file_path = os.path.join(self.card_path, 'pp_power_profile_mode')
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
                    if env.gut_const.DEBUG: print('Debug: ppm line: {}'.format(linestr), file=sys.stderr)
                    if len(line_items) < 2:
                        print('Error: invalid ppm: {}'.format(linestr), file=sys.stderr)
                        continue
                    if env.gut_const.DEBUG: print('Debug: valid ppm: {}'.format(linestr), file=sys.stderr)
                    self.ppm_modes[line_items[0]] = line_items[1:]
            self.ppm_modes['-1'] = ['AUTO', 'Auto']

        file_path = os.path.join(self.card_path, 'power_dpm_force_performance_level')
        if os.path.isfile(file_path):
            with open(file_path) as card_file:
                self.set_params_value('power_dpm_force', card_file.readline().strip())
        else:
            print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
            self.compatible = False

    def read_gpu_pstates(self):
        """
        Read GPU pstate definitions and parameter ranges from driver files.
        Set card type based on pstate configuration
        :return: None
        """
        range_mode = False
        type_unknown = True

        file_path = os.path.join(self.card_path, 'power_dpm_state')
        if not os.path.isfile(file_path):
            print('Error: Looks like DPM is not enabled: {} does not exist'.format(file_path), file=sys.stderr)
            self.compatible = False
            return
        file_path = os.path.join(self.card_path, 'pp_od_clk_voltage')
        if not os.path.isfile(file_path):
            print('Error getting p-states: {}'.format(file_path), file=sys.stderr)
            self.compatible = False
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
                        self.set_params_value('gpu_type', 1)
                    elif len(lineitems) == 2:
                        self.set_params_value('gpu_type', 2)
                    type_unknown = False
                if lineitems_len < 2 or lineitems_len > 3:
                    print('Error: Invalid pstate entry: %s' % (self.card_path + 'pp_od_clk_voltage'), file=sys.stderr)
                    continue
                if not range_mode:
                    lineitems[0] = int(re.sub(':', '', lineitems[0]))
                    if self.get_params_value('gpu_type') == 0 or self.get_params_value('gpu_type') == 1:
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
                        self.set_params_value('sclk_f_range', [lineitems[1], lineitems[2]])
                    elif lineitems[0] == 'MCLK:':
                        self.set_params_value('mclk_f_range', [lineitems[1], lineitems[2]])
                    elif lineitems[0] == 'VDDC:':
                        self.set_params_value('vddc_range', [lineitems[1], lineitems[2]])
                    elif re.fullmatch('VDDC_CURVE_.*', line):
                        if len(lineitems) == 3:
                            index = re.sub(r'VDDC_CURVE_.*\[', '', lineitems[0])
                            index = re.sub(r'\].*', '', index)
                            param = re.sub(r'VDDC_CURVE_', '', lineitems[0])
                            param = re.sub(r'\[[0-9]\]:', '', param)
                            if env.gut_const.DEBUG:
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
            file_path = os.path.join(self.hwmon_path, 'power1_cap_max')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    power1_cap_max_value = int(int(hwmon_file.readline())/1000000)
                file_path = os.path.join(self.hwmon_path, 'power1_cap_min')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        power1_cap_min_value = int(int(hwmon_file.readline())/1000000)
                    self.set_params_value('power_cap_range', [power1_cap_min_value, power1_cap_max_value])
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.hwmon_path, 'temp1_crit')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    self.set_params_value('temp_crit', int(hwmon_file.readline())/1000)
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            # Get fan data if --no_fan flag is not set
            if env.gut_const.show_fans:
                file_path = os.path.join(self.hwmon_path, 'fan1_max')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        fan1_max_value = int(hwmon_file.readline())
                    file_path = os.path.join(self.hwmon_path, 'fan1_min')
                    if os.path.isfile(file_path):
                        with open(file_path) as hwmon_file:
                            fan1_min_value = int(hwmon_file.readline())
                        self.set_params_value('fan_speed_range', [fan1_min_value, fan1_max_value])
                    else:
                        print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)

                file_path = os.path.join(self.hwmon_path, 'pwm1_max')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        pwm1_max_value = int(100*(int(hwmon_file.readline())/255))
                    file_path = os.path.join(self.hwmon_path, 'pwm1_min')
                    if os.path.isfile(file_path):
                        with open(file_path) as hwmon_file:
                            pwm1_pmin_value = int(100*(int(hwmon_file.readline())/255))
                        self.set_params_value('fan_pwm_range', [pwm1_pmin_value, pwm1_max_value])
                    else:
                        print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                    self.compatible = False
        except:
            print('Error: problem reading static data from GPU HWMON: {}'.format(self.hwmon_path), file=sys.stderr)
            self.compatible = False

    def read_gpu_sensor_data(self):
        """
        Read GPU sensor data from HWMON path.
        :return: None
        """
        try:
            file_path = os.path.join(self.hwmon_path, 'power1_cap')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    self.set_params_value('power_cap', int(hwmon_file.readline())/1000000)
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.hwmon_path, 'power1_average')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    power_uw = int(hwmon_file.readline())
                    time_n = env.gut_const.now(env.gut_const.USELTZ)
                    self.set_params_value('power', int(power_uw)/1000000)
                    delta_hrs = ((time_n - self.energy['tn']).total_seconds())/3600
                    self.energy['tn'] = time_n
                    self.energy['cumulative'] += delta_hrs * power_uw/1000000000
                    self.set_params_value('energy', round(self.energy['cumulative'], 6))
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.hwmon_path, 'temp1_input')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    self.set_params_value('temp', int(hwmon_file.readline())/1000)
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
        except:
            print('Error: Problem reading sensor [power/temp] from GPU HWMON: {}'.format(self.hwmon_path),
                  file=sys.stderr)
            self.compatible = False

        # Get fan data if --no_fan flag is not set
        if env.gut_const.show_fans:
            # First non-critical fan data
            # On error will be disabled, but still compatible
            name_hwfile = ('fan1_enable', 'fan1_target', 'fan1_input')
            name_param = ('fan_enable', 'fan_target', 'fan_speed')
            for nh, np in zip(name_hwfile, name_param):
                if nh not in self.hwmon_disabled:
                    file_path = os.path.join(self.hwmon_path, nh)
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path) as hwmon_file:
                                self.set_params_value(np, hwmon_file.readline().strip())
                        except:
                            print('Warning: problem reading sensor [{}] data from GPU HWMON: {}'.format(
                                nh, self.hwmon_path), file=sys.stderr)
                            self.hwmon_disabled.append(nh)
                    else:
                        print('Warning: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                        self.hwmon_disabled.append(nh)

            # Now critical fan data
            try:
                file_path = os.path.join(self.hwmon_path, 'pwm1_enable')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        pwm_mode_value = int(hwmon_file.readline().strip())
                        if pwm_mode_value == 0:
                            pwm_mode_name = 'None'
                        elif pwm_mode_value == 1:
                            pwm_mode_name = 'Manual'
                        elif pwm_mode_value == 2:
                            pwm_mode_name = 'Dynamic'
                        self.set_params_value('pwm_mode', [pwm_mode_value, pwm_mode_name])
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                    self.compatible = False

                file_path = os.path.join(self.hwmon_path, 'pwm1')
                if os.path.isfile(file_path):
                    with open(file_path) as hwmon_file:
                        self.set_params_value('fan_pwm', int(100*(int(hwmon_file.readline())/255)))
                else:
                    print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                    self.compatible = False
            except:
                print('Error: problem reading sensor [pwm] data from GPU HWMON: {}'.format(self.hwmon_path),
                      file=sys.stderr)
                print('Try running with --no_fan option', file=sys.stderr)
                self.compatible = False

        try:
            file_path = os.path.join(self.hwmon_path, 'in0_label')
            if os.path.isfile(file_path):
                with open(file_path) as hwmon_file:
                    if hwmon_file.readline().rstrip() == 'vddgfx':
                        with open(os.path.join(self.hwmon_path, 'in0_input')) as hwmon_file2:
                            self.set_params_value('vddgfx', int(hwmon_file2.readline()))
            else:
                print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
        except:
            print('Error: problem reading sensor [in0_label] data from GPU HWMON: {}'.format(self.hwmon_path),
                  file=sys.stderr)
            self.compatible = False

    def read_gpu_driver_info(self):
        """
        Read GPU current driver information from card path directory.
        :return: None
        """
        try:
            # get all device ID information
            file_path = os.path.join(self.card_path, 'device')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    device_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
            file_path = os.path.join(self.card_path, 'vendor')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    vendor_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
            file_path = os.path.join(self.card_path, 'subsystem_device')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    subsystem_device_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
            file_path = os.path.join(self.card_path, 'subsystem_vendor')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    subsystem_vendor_id = card_file.readline().strip()
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
            # store device_id information
            self.set_params_value('id', {'vendor': vendor_id,
                                         'device': device_id,
                                         'subsystem_vendor': subsystem_vendor_id,
                                         'subsystem_device': subsystem_device_id})
            # use device info to set model
            if self.get_params_value('model_device_decode') == 'UNDETERMINED':
                pcid = PCImodule.PCI_ID()
                self.set_params_value('model_device_decode', pcid.get_model(self.get_params_value('id')))
            # set display model to model_device_decode if shorter than model short
            if (self.get_params_value('model_device_decode') != 'UNDETERMINED' and
                    len(self.get_params_value('model_device_decode')) < 1.2*len(self.get_params_value('model_short'))):
                self.set_params_value('model_display', self.get_params_value('model_device_decode'))
            else:
                self.set_params_value('model_display', self.get_params_value('model_short'))

            file_path = os.path.join(self.card_path, 'vbios_version')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.set_params_value('vbios', card_file.readline().strip())
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
        except:
            print('Error: problem reading GPU driver information for Card Path: {}'.format(self.card_path),
                  file=sys.stderr)
            self.compatible = False

    def read_gpu_state_data(self):
        """
        Read GPU current state information from card path directory.
        :return: None
        """
        try:
            file_path = os.path.join(self.card_path, 'gpu_busy_percent')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.set_params_value('loading', int(card_file.readline()))
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.card_path, 'current_link_speed')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.set_params_value('link_spd', card_file.readline().strip())
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.card_path, 'current_link_width')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.set_params_value('link_wth', card_file.readline().strip())
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.card_path, 'pp_dpm_sclk')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    for line in card_file:
                        if line[len(line)-2] == '*':
                            lineitems = line.split(sep=':')
                            self.set_params_value('sclk_ps', lineitems[0].strip())
                            self.set_params_value('sclk_f', lineitems[1].strip().strip('*'))
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.card_path, 'pp_dpm_mclk')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    for line in card_file:
                        if line[len(line)-2] == '*':
                            lineitems = line.split(sep=':')
                            self.set_params_value('mclk_ps', lineitems[0].strip())
                            self.set_params_value('mclk_f', lineitems[1].strip().strip('*'))
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.card_path, 'pp_power_profile_mode')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    for line in card_file:
                        linestr = line.strip()
                        srch_obj = re.search(r'\*:', linestr)
                        if srch_obj:
                            lineitems = linestr.split(sep='*:')
                            mode_str = lineitems[0].strip()
                            mode_str = re.sub(r'[ ]+', '-', mode_str)
                            self.set_params_value('ppm', mode_str)
                            break
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False

            file_path = os.path.join(self.card_path, 'power_dpm_force_performance_level')
            if os.path.isfile(file_path):
                with open(file_path) as card_file:
                    self.set_params_value('power_dpm_force', card_file.readline().strip())
            else:
                print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
                self.compatible = False
        except:
            print('Error: getting data from GPU Card Path: {}'.format(self.card_path), file=sys.stderr)
            self.compatible = False

    def print_ppm_table(self):
        """
        Print human friendly table of ppm parameters.
        :return: None
        """
        print('Card: {}'.format(self.card_path))
        print('Power Performance Mode: {}'.format(self.get_params_value('power_dpm_force')))
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
        print('Card: {}'.format(self.card_path))
        print('SCLK: {:<17} MCLK:'.format(' '))
        for k, v in self.sclk_state.items():
            print('{:>1}:  {:<8}  {:<8}'.format(k, v[0], v[1]), end='')
            if k in self.mclk_state.keys():
                print('{:3>}:  {:<8}  {:<8}'.format(k, self.mclk_state[k][0], self.mclk_state[k][1]))
            else:
                print('')
        if self.get_params_value('gpu_type') == 2:
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
                if self.compatible:
                    print('{} Compatibility: Yes'.format(__program_name__))
                else:
                    print('{} Compatibility: NO'.format(__program_name__))
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
        gpu_state = {'Time': str(self.energy['tn'].strftime('%c')).strip(), 'Card#': int(self.card_num)}

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
    if env.gut_const.show_fans:
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

    def get_gpu_list(self):
        """ This method should be the first called to popultate the list with potentially compatible GPUs
            It doesn't read any driver files, just checks their existence and sets them in the GpuItem object.
        """
        for card_name in glob.glob(env.gut_const.card_root + 'card?/device/pp_od_clk_voltage'):
            gpu_item = GpuItem(uuid4().hex)
            gpu_item.set_params_value('card_path', card_name.replace('pp_od_clk_voltage', ''))
            gpu_item.set_params_value('card_num', card_name.replace('/device/pp_od_clk_voltage', '').replace(
                env.gut_const.card_root + 'card', ''))
            hw_file_srch = glob.glob(os.path.join(gpu_item.card_path, env.gut_const.hwmon_sub) + '?')
            if len(hw_file_srch) > 1:
                print('More than one hwmon file found: ', hw_file_srch)
            gpu_item.set_params_value('hwmon_path', hw_file_srch[0] + '/')
            self.list[gpu_item.uuid] = gpu_item

    def num_gpus(self, compatible=False, readable=False, writeable=False):
        """
        Return the count of GPUs.  Counts all by default, but can also count compatible, readable or writeable.
        Only one flag should be set.
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
            if compatible:
                if v.compatible:
                    cnt += 1
            elif readable:
                if v.readable:
                    cnt += 1
            elif writeable:
                if v.writeable:
                    cnt += 1
            else:
                cnt += 1
        return cnt

    def list_gpus(self, compatible=False, readable=False, writeable=False):
        """
        Return GPU_Item of GPUs.  Contains all by default, but can also count compatible, readable or writeable.
        Only one flag should be set.
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
            if compatible:
                if v.compatible:
                    result_list.list[k] = v
            elif readable:
                if v.readable:
                    result_list.list[k] = v
            elif writeable:
                if v.writeable:
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
            if v.compatible:
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
            if v.compatible:
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
            if v.compatible:
                v.read_gpu_state_data()

    def read_gpu_sensor_static_data(self):
        """Read dynamic sensor data from GPUs"""
        for v in self.list.values():
            if v.compatible:
                v.read_gpu_sensor_static_data()

    def read_gpu_sensor_data(self):
        """Read dynamic sensor data from GPUs"""
        for v in self.list.values():
            if v.compatible:
                v.read_gpu_sensor_data()

    def read_gpu_driver_info(self):
        """Read data static driver information for GPUs"""
        for v in self.list.values():
            if v.compatible:
                v.read_gpu_driver_info()

    def read_allgpu_pci_info(self):
        """ This function uses lspci to get details for GPUs in the current list and populates the data
            structure of each GpuItem in the list.

            It gets GPU name variants and gets the pcie slot ID for each card ID.
            Special incompatible cases are determined here, like the Fiji Pro Duo.
            This is the first function that should be called after the intial list is populated.
        """
        pcie_ids = subprocess.check_output(
            'lspci | grep -E \'^.*(VGA|Display).*\[AMD\/ATI\].*$\' | grep -Eo \'^([0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F])\'',
            shell=True).decode().split()
        if env.gut_const.DEBUG: print('Found %s GPUs' % len(pcie_ids))
        for pcie_id in pcie_ids:
            if env.gut_const.DEBUG: print('GPU: ', pcie_id)
            lspci_items = subprocess.check_output('{} -k -s {}'.format(env.gut_const.cmd_lspci, pcie_id),
                                                  shell=True).decode().split('\n')
            if env.gut_const.DEBUG: print(lspci_items)

            # Get Long GPU Name
            gpu_name = ''
            # Line 0 name
            gpu_name_items = lspci_items[0].split('[AMD/ATI]')
            if len(gpu_name_items) < 2:
                gpu_name_0 = 'UNKNOWN'
            else:
                gpu_name_0 = gpu_name_items[1]
            # Line 1 name
            gpu_name_1 = ''
            gpu_name_items = lspci_items[1].split('[AMD/ATI]')
            if len(gpu_name_items) < 2:
                gpu_name_1 = 'UNKNOWN'
            else:
                gpu_name_1 = gpu_name_items[1]

            # Check for Fiji ProDuo
            srch_obj = re.search('Fiji', gpu_name_0)
            if srch_obj:
                srch_obj = re.search('Radeon Pro Duo', gpu_name_1)
                if srch_obj:
                    gpu_name = 'Radeon Fiji Pro Duo'

            if len(gpu_name) == 0:
                if len(gpu_name_0) > len(gpu_name_1):
                    gpu_name = gpu_name_0
                else:
                    gpu_name = gpu_name_1
            if env.gut_const.DEBUG: print('gpu_name: {}, 0: {}, 1: {}'.format(gpu_name,gpu_name_0, gpu_name_1))

            # Get Driver Name
            driver_module_items = lspci_items[2].split(':')
            if len(driver_module_items) < 2:
                driver_module = 'UNKNOWN'
            else:
                driver_module = driver_module_items[1].strip()

            # Find matching card
            device_dirs = glob.glob(env.gut_const.card_root + 'card?/device')
            for device_dir in device_dirs:
                sysfspath = str(Path(device_dir).resolve())
                if env.gut_const.DEBUG: print('device_dir: {}'.format(device_dir))
                if env.gut_const.DEBUG: print('sysfspath: {}'.format(sysfspath))
                if env.gut_const.DEBUG: print('pcie_id: {}'.format(pcie_id))
                if env.gut_const.DEBUG: print('sysfspath-7: {}'.format(sysfspath[-7:]))
                if pcie_id == sysfspath[-7:]:
                    for v in self.list.values():
                        if v.card_path == device_dir + '/':
                            if gpu_name == 'Radeon Fiji Pro Duo':
                                v.compatible = False
                            v.set_params_value('pcie_id', pcie_id)
                            v.set_params_value('driver', driver_module)
                            v.set_params_value('model', gpu_name)
                            model_short = re.sub(r'^.*\[', '', gpu_name)
                            model_short = re.sub(r'\].*$', '', model_short)
                            model_short = re.sub(r'.*Radeon', '', model_short)
                            v.set_params_value('model_short', model_short)
                            break
                    break

    def read_gpu_opencl_data(self):
        """
        Use call to clinfo to read opencl details for all GPUs.
        :return: True on success
        :rtype: bool
        """
        # Check access to clinfo command
        if not env.gut_const.cmd_clinfo:
            print('OS Command [clinfo] not found.  Use sudo apt-get install clinfo to install', file=sys.stderr)
            return False
        cmd = subprocess.Popen(shlex.split('{} --raw'.format(env.gut_const.cmd_clinfo)),
                               shell=False, stdout=subprocess.PIPE)
        for line in cmd.stdout:
            linestr = line.decode('utf-8').strip()
            if len(linestr) < 1:
                continue
            if linestr[0] != '[':
                continue
            linestr = re.sub(r'   [ ]*', ':-:', linestr)
            srch_obj = re.search('CL_DEVICE_NAME', linestr)
            if srch_obj:
                # Found a new device
                tmp_gpu = GpuItem(uuid4().hex)
                line_items = linestr.split(':-:')
                #dev_str = line_items[0].split('/')[1]
                #dev_num = int(re.sub(']', '', dev_str))
                tmp_gpu.set_clinfo_value('device_name', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_VERSION', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('device_version', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DRIVER_VERSION', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('driver_version', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_OPENCL_C_VERSION', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('opencl_version', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_TOPOLOGY_AMD', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                pcie_id_str = (line_items[2].split()[1]).strip()
                if env.gut_const.DEBUG: print('CL PCIE ID: [{}]'.format(pcie_id_str))
                tmp_gpu.set_clinfo_value('pcie_id', pcie_id_str)
                continue
            srch_obj = re.search('CL_DEVICE_MAX_COMPUTE_UNITS', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('max_cu', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_SIMD_PER_COMPUTE_UNIT_AMD', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('simd_per_cu', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_SIMD_WIDTH_AMD', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('simd_width', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_SIMD_INSTRUCTION_WIDTH_AMD', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('simd_ins_width', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_MAX_MEM_ALLOC_SIZE', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('max_mem_allocation', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('max_wi_dim', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_MAX_WORK_ITEM_SIZES', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('max_wi_sizes', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_MAX_WORK_GROUP_SIZE', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('max_wg_size', line_items[2].strip())
                continue
            srch_obj = re.search('CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE', linestr)
            if srch_obj:
                line_items = linestr.split(':-:')
                tmp_gpu.set_clinfo_value('prf_wg_multiple', line_items[2].strip())
                continue
            srch_obj = re.search('CL_DEVICE_EXTENSIONS', linestr)
            if srch_obj:
                # End of Device
                if env.gut_const.DEBUG: print('finding gpu with pcie ID: ', tmp_gpu.get_clinfo_value('pcie_id'))
                target_gpu_uuid = self.find_gpu_by_pcie_id(tmp_gpu.get_clinfo_value('pcie_id'))
                self.list[target_gpu_uuid].copy_clinfo_values(tmp_gpu)
        return True

    def find_gpu_by_pcie_id(self, pcie_id):
        """
        Find the GPU with the specified pcie_id.
        :param pcie_id: The pcie ID of the target GPU
        :type pcie_id: str
        :return: The GPU uuid or None
        :rtype: Union([str, None])
        """
        for v in self.list.values():
            if v.get_params_value('pcie_id') == pcie_id:
                return v.uuid
        return None

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
            print('│', '\x1b[1;36m' + ('card' + v.get_params_value('card_num')).ljust(16, ' ') + '\x1b[0m',
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
