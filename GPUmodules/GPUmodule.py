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
__status__ = 'Alpha Release'
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
            raise AttributeError('No such attribute: ' + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError('No such attribute: ' + name)


class GpuItem:
    """An object to store GPU details.
    .. note:: GPU Frequency/Voltage Control Type: 0 = None, 1 = P-states, 2 = Curve
    """
    # pylint: disable=attribute-defined-outside-init
    _GPU_NC_Param_List = ['compute', 'readable', 'writable', 'vendor', 'model', 'card_num',
                          'card_path', 'pcie_id', 'driver']
    # Define Class Labels
    _GPU_CLINFO_Labels = {'sep4': '#',
                          'opencl_version': '   Device OpenCL C Version',
                          'device_name': '   Device Name',
                          'device_version': '   Device Version',
                          'driver_version': '   Driver Version',
                          'max_cu': '   Max Compute Units',
                          'simd_per_cu': '   SIMD per CU',
                          'simd_width': '   SIMD Width',
                          'simd_ins_width': '   SIMD Instruction Width',
                          'max_mem_allocation': '   CL Max Memory Allocation',
                          'max_wi_dim': '   Max Work Item Dimensions',
                          'max_wi_sizes': '   Max Work Item Sizes',
                          'max_wg_size': '   Max Work Group Size',
                          'prf_wg_size': '   Preferred Work Group Size',
                          'prf_wg_multiple': '   Preferred Work Group Multiple'}
    _GPU_Param_Labels = {'card_num': 'Card Number',
                         'vendor': 'Vendor',
                         'readable': 'Readable',
                         'writable': 'Writable',
                         'compute': 'Compute',
                         'unique_id': 'GPU UID',
                         'id': 'Device ID',
                         'model_device_decode': 'Decoded Device ID',
                         'model': 'Card Model',
                         'model_display': 'Display Card Model',
                         'pcie_id': 'PCIe ID',
                         'link_spd': '   Link Speed',
                         'link_wth': '   Link Width',
                         'sep1': '#',
                         'driver': 'Driver',
                         'vbios': 'vBIOS Version',
                         'compute_platform': 'Compute Platform',
                         'gpu_type': 'GPU Frequency/Voltage Control Type',
                         'hwmon_path': 'HWmon',
                         'card_path': 'Card Path',
                         'sep2': '#',
                         'power': 'Current Power (W)',
                         'power_cap': 'Power Cap (W)',
                         'power_cap_range': '   Power Cap Range (W)'}
    if env.GUT_CONST.show_fans:
        _GPU_Param_Labels.update({'fan_enable': 'Fan Enable',
                                  'pwm_mode': 'Fan PWM Mode',
                                  'fan_target': 'Fan Target Speed (rpm)',
                                  'fan_speed': 'Current Fan Speed (rpm)',
                                  'fan_pwm': 'Current Fan PWM (%)',
                                  'fan_speed_range': '   Fan Speed Range (rpm)',
                                  'fan_pwm_range': '   Fan PWM Range (%)'})
    _GPU_Param_Labels.update({'sep3': '#',
                              'loading': 'Current GPU Loading (%)',
                              'mem_loading': 'Current Memory Loading (%)',
                              'temperatures': 'Current Temps (C)',
                              'temp_crit': '   Critical Temp (C)',
                              'voltages': 'Current Voltages (V)',
                              'vddc_range': '   Vddc Range',
                              'frequencies': 'Current Clk Frequencies (MHz)',
                              'sclk_ps': 'Current SCLK P-State',
                              'sclk_f_range': '   SCLK Range',
                              'mclk_ps': 'Current MCLK P-State',
                              'mclk_f_range': '   MCLK Range',
                              'ppm': 'Power Performance Mode',
                              'power_dpm_force': 'Power Force Performance Level'})

    # HWMON sensor reading details
    _sensor_details = {'AMD': {'HWMON': {
                                   'power': {'type': 'sp', 'cf': 0.000001, 'sensor': ['power1_average']},
                                   'power_cap': {'type': 'sp', 'cf': 0.000001, 'sensor': ['power1_cap']},
                                   'power_cap_range': {'type': 'mm', 'cf': 0.000001,
                                                       'sensor': ['power1_cap_min', 'power1_cap_max']},
                                   'fan_enable': {'type': 'sp', 'cf': 1, 'sensor': ['fan1_enable']},
                                   'fan_target': {'type': 'sp', 'cf': 1, 'sensor': ['fan1_target']},
                                   'fan_speed': {'type': 'sp', 'cf': 1, 'sensor': ['fan1_input']},
                                   'fan_speed_range': {'type': 'mm', 'cf': 1, 'sensor': ['fan1_min', 'fan1_max']},
                                   'pwm_mode': {'type': 'sp', 'cf': 1, 'sensor': ['pwm1_enable']},
                                   'fan_pwm': {'type': 'sp', 'cf': 0.39216, 'sensor': ['pwm1']},
                                   'fan_pwm_range': {'type': 'mm', 'cf': 0.39216, 'sensor': ['pwm1_min', 'pwm1_max']},
                                   'temp': {'type': 'sp', 'cf': 0.001, 'sensor': ['temp1_input']},
                                   'temp_crit': {'type': 'sp', 'cf': 0.001, 'sensor': ['temp1_crit']},
                                   'freq1': {'type': 'sl', 'cf': 0.000001, 'sensor': ['freq1_input', 'freq1_label']},
                                   'freq2': {'type': 'sl', 'cf': 0.000001, 'sensor': ['freq2_input', 'freq2_label']},
                                   'frequencies': {'type': 'sl*', 'cf': 0.000001, 'sensor': ['freq*_input']},
                                   'voltages': {'type': 'sl*', 'cf': 1, 'sensor': ['in*_input']},
                                   'temperatures': {'type': 'sl*', 'cf': 0.001, 'sensor': ['temp*_input']},
                                   'vddgfx': {'type': 'sl', 'cf': 0.001, 'sensor': ['in0_input', 'in0_label']}},
                               'DEVICE': {
                                   'id': {'type': 'mt', 'cf': None,
                                          'sensor': ['vendor', 'device', 'subsystem_vendor', 'subsystem_device']},
                                   'unique_id': {'type': 'st', 'cf': None, 'sensor': ['unique_id']},
                                   'loading': {'type': 'st', 'cf': None, 'sensor': ['gpu_busy_percent']},
                                   'mem_loading': {'type': 'st', 'cf': None, 'sensor': ['mem_busy_percent']},
                                   'link_spd': {'type': 'st', 'cf': None, 'sensor': ['current_link_speed']},
                                   'link_wth': {'type': 'st', 'cf': None, 'sensor': ['current_link_width']},
                                   'sclk_ps': {'type': 'st*', 'cf': None, 'sensor': ['pp_dpm_sclk']},
                                   'mclk_ps': {'type': 'st*', 'cf': None, 'sensor': ['pp_dpm_mclk']},
                                   'power_dpm_force': {'type': 'st', 'cf': None,
                                                       'sensor': ['power_dpm_force_performance_level']},
                                   'ppm': {'type': 'st*', 'cf': None, 'sensor': ['pp_power_profile_mode']},
                                   'vbios': {'type': 'st', 'cf': None, 'sensor': ['vbios_version']}}}}

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
        self.read_disabled = []    # List of parameters that failed during read.
        self.write_disabled = []   # List of parameters that failed during write.
        self.prm = ObjDict({'uuid': item_id,
                            'unique_id': '',
                            'card_num': '',
                            'pcie_id': '',
                            'driver': '',
                            'vendor': '',
                            'readable': False,
                            'writable': False,
                            'compute': False,
                            'compute_platform': None,
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
                            'temperatures': None,
                            'voltages': None,
                            'frequencies': None,
                            'loading': None,
                            'mem_loading': None,
                            'mclk_ps': ['', ''],
                            'mclk_f_range': ['', ''],
                            'sclk_ps': ['', ''],
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
                               'prf_wg_size': '',
                               'prf_wg_multiple': ''})
        self.sclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.mclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve_range = {}  # {'1': {SCLK: ['val1', 'val2'], VOLT: ['val1', 'val2']}
        self.ppm_modes = {}         # {'1': ['Name', 'Description']}

    def set_params_value(self, name, value):
        """
        Set parameter value for give name.
        :param name:  Parameter name
        :type name: str
        :param value:  parameter value
        :type value: Union[int, str, list]
        :return: None
        """
        if isinstance(value, tuple):
            self.prm[name] = list(value)
        elif name == 'pwm_mode':
            self.prm[name][0] = value
            if value == 0: self.prm[name][1] = 'None'
            elif value == 1: self.prm[name][1] = 'Manual'
            else: self.prm[name][1] = 'Dynamic'
        elif name == 'ppm':
            self.prm[name] = re.sub(r'[*].*', '', value).strip()
            self.prm[name] = re.sub(r'[ ]+', '-', self.prm[name])
        elif name == 'power':
            time_n = env.GUT_CONST.now(env.GUT_CONST.USELTZ)
            self.prm[name] = round(value, 1)
            delta_hrs = ((time_n - self.energy['tn']).total_seconds()) / 3600
            self.energy['tn'] = time_n
            self.energy['cumulative'] += delta_hrs * value / 1000
            self.prm['energy'] = round(self.energy['cumulative'], 6)
        elif name == 'sclk_ps':
            self.prm.sclk_ps = value.strip('*').strip().split(': ')
            self.prm.sclk_ps[0] = int(self.prm.sclk_ps[0])
        elif name == 'mclk_ps':
            self.prm.mclk_ps = value.strip('*').strip().split(': ')
            self.prm.mclk_ps[0] = int(self.prm.mclk_ps[0])
        elif name == 'fan_pwm':
            self.prm.fan_pwm = int(value)
        elif name == 'id':
            self.prm.id = dict(zip(['vendor', 'device', 'subsystem_vendor', 'subsystem_device'], list(value)))
            pcid = PCImodule.PCI_ID()
            self.prm.model_device_decode = pcid.get_model(self.prm.id)
            if (self.prm.model_device_decode != 'UNDETERMINED' and
                    len(self.prm.model_device_decode) < 1.2*len(self.prm.model_short)):
                self.prm.model_display = self.prm.model_device_decode
        else:
            self.prm[name] = value

    def get_params_value(self, name):
        """
        Get parameter value for give name.
        :param name:  Parameter name
        :type name: str
        :return: Parameter value
        :rtype: Union[int, str, list]
        """
        if re.fullmatch(r'.*_val', name):
            if name == 'temp_val':
                if 'edge' in self.prm['temperatures'].keys():
                    return round(self.prm['temperatures']['edge'], 1)
                return self.prm['temperatures'].keys()[0]
            if name == 'vddgfx_val':
                return int(self.prm['voltages']['vddgfx'])
            if name == 'sclk_ps_val':
                return self.prm['sclk_ps'][0]
            if name == 'sclk_f_val':
                if 'sclk' in self.prm['frequencies'].keys():
                    return int(self.prm['frequencies']['sclk'])
                return self.prm['sclk_ps'][1]
            if name == 'mclk_ps_val':
                return self.prm['mclk_ps'][0]
            if name == 'mclk_f_val':
                if 'mclk' in self.prm['frequencies'].keys():
                    return int(self.prm['frequencies']['mclk'])
                return self.prm['mclk_ps'][1]
        return self.prm[name]

    def populate(self, pcie_id, gpu_name, short_gpu_name, vendor, driver_module, card_path, hwmon_path,
                 readable, writable, compute, ocl_ver):
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
        :param writable: writable compatibility flag
        :type writable: bool
        :param compute: Compute compatibility flag
        :type compute: bool
        :param ocl_ver: Compute platform Name
        :type ocl_ver: str
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
        self.prm.writable = writable
        self.prm.compute = compute
        self.prm.compute_platform = ocl_ver if compute else 'None'

    def populate_ocl(self, ocl_dict):
        """
        Populate ocl parameters in GpuItem
        :param ocl_dict: Dictionary of parameters for specific pcie_id
        :type ocl_dict: dict
        :return: None
        """
        for k, v in ocl_dict.items():
            if k in self.clinfo.keys():
                self.set_clinfo_value(k, v)

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
        .. note: Maybe not needed
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

    def get_nc_params_list(self):
        """
        Get list of parameter names for use with non-readable cards.
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
        if not self.prm.readable:
            return
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

        rdata = self.read_gpu_sensor('power_dpm_force', vendor='AMD', sensor_type='DEVICE')
        if rdata is False:
            print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
            self.prm.readable = False
        else:
            self.set_params_value('power_dpm_force', rdata)

    def read_gpu_pstates(self):
        """
        Read GPU pstate definitions and parameter ranges from driver files.
        Set card type based on pstate configuration
        :return: None
        """
        if not self.prm.readable:
            return
        range_mode = False
        type_unknown = True

        file_path = os.path.join(self.prm.card_path, 'pp_od_clk_voltage')
        if not os.path.isfile(file_path):
            print('Error getting p-states: {}'.format(file_path), file=sys.stderr)
            self.prm.readable = False
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

    def read_gpu_sensor(self, parameter, vendor='AMD', sensor_type='HWMON'):
        """
        Read sensor for the given parameter name.  Process per sensor_details dict using the specified
        vendor name and sensor_type.
        :param parameter: GpuItem parameter name (AMD)
        :type parameter: str
        :param vendor: GPU vendor name
        :type vendor: str
        :param sensor_type: GPU sensor name (HWMON or DEVICE)
        :type sensor_type: str
        :return:
        """
        if vendor not in self._sensor_details.keys():
            print('Error: Invalid vendor [{}]'.format(vendor))
            return None
        if sensor_type not in self._sensor_details[vendor].keys():
            print('Error: Invalid sensor_type [{}]'.format(sensor_type))
            return None
        sensor_dict = self._sensor_details[vendor][sensor_type]
        if parameter not in sensor_dict.keys():
            print('Error: Invalid parameter [{}]'.format(parameter))
            return None
        if parameter in self.read_disabled:
            return None

        sensor_path = self.prm.hwmon_path if sensor_type == 'HWMON' else self.prm.card_path
        values = []
        ret_value = []
        ret_dict = {}
        if sensor_dict[parameter]['type'] == 'sl*':
            sensor_files = glob.glob(os.path.join(sensor_path, sensor_dict[parameter]['sensor'][0]))
        else:
            sensor_files = sensor_dict[parameter]['sensor']
        for sensor_file in sensor_files:
            file_path = os.path.join(sensor_path, sensor_file)
            if os.path.isfile(file_path):
                try:
                    with open(file_path) as hwmon_file:
                        if sensor_dict[parameter]['type'] == 'st*':
                            lines = hwmon_file.readlines()
                            for line in lines:
                                values.append(line.strip())
                        else:
                            values.append(hwmon_file.readline().strip())
                    if sensor_dict[parameter]['type'] == 'sl*':
                        with open(file_path.replace('input', 'label')) as hwmon_file:
                            values.append(hwmon_file.readline().strip())
                except OSError as err:
                    if env.GUT_CONST.DEBUG:
                        print('Error [{}]: Can not read HW file: {}'.format(err, file_path), file=sys.stderr)
                    self.read_disabled.append(parameter)
                    return False
            else:
                if env.GUT_CONST.DEBUG: print('Error: HW file does not exist: {}'.format(file_path), file=sys.stderr)
                self.read_disabled.append(parameter)
                return False

        if sensor_dict[parameter]['type'] == 'sp':
            if sensor_dict[parameter]['cf'] == 1:
                return int(values[0])
            return int(values[0])*sensor_dict[parameter]['cf']
        elif sensor_dict[parameter]['type'] == 'sl':
            ret_value.append(int(values[0])*sensor_dict[parameter]['cf'])
            ret_value.append(values[1])
            return tuple(ret_value)
        elif sensor_dict[parameter]['type'] == 'mt':
            return values
        elif sensor_dict[parameter]['type'] == 'mm':
            ret_value.append(int(int(values[0])*sensor_dict[parameter]['cf']))
            ret_value.append(int(int(values[1])*sensor_dict[parameter]['cf']))
            return tuple(ret_value)
        elif sensor_dict[parameter]['type'] == 'sl*':
            for i in range(0, len(values), 2):
                ret_dict.update({values[i+1]: int(values[i])*sensor_dict[parameter]['cf']})
            return ret_dict
        elif sensor_dict[parameter]['type'] == 'st*':
            for item in values:
                if re.search(r'\*', item):
                    return item
            return None
        else:  # 'st or st*'
            return values[0]

    def read_gpu_sensor_data(self, data_type='All'):
        """
        Read GPU static data from HWMON path.
        :param data_type: Test, Static, Dynamic, Info, State, or All
        :type data_type: str
        :return: None
        """
        if not self.prm.readable:
            return None

        def concat_sensor_dicts(dict1, dict2):
            """
            Concatenate dict2 onto dict1
            :param dict1:
            :type dict1: dict
            :param dict2:
            :type dict2: dict
            :return: None
            """
            for st in dict2.keys():
                if st in dict1.keys():
                    dict1[st] += dict2[st]
                else:
                    dict1.update({st: dict2[st]})

        param_list_static = {'HWMON': ['power_cap_range', 'temp_crit']}
        param_list_static_fan = {'HWMON': ['fan_speed_range', 'fan_pwm_range']}
        param_list_dynamic = {'HWMON': ['power', 'power_cap', 'temperatures', 'voltages', 'frequencies']}
        param_list_dynamic_fan = {'HWMON': ['fan_enable', 'fan_target', 'fan_speed', 'pwm_mode', 'fan_pwm']}
        param_list_info = {'DEVICE': ['id', 'unique_id', 'vbios']}
        param_list_state = {'DEVICE': ['loading', 'mem_loading', 'link_spd', 'link_wth', 'sclk_ps', 'mclk_ps', 'ppm',
                                       'power_dpm_force']}
        param_list_all = {'DEVICE': ['id', 'unique_id', 'vbios', 'loading', 'mem_loading', 'link_spd', 'link_wth',
                                     'sclk_ps', 'mclk_ps', 'ppm', 'power_dpm_force'],
                          'HWMON': ['power_cap_range', 'temp_crit', 'power', 'power_cap', 'temperatures',
                                    'voltages', 'frequencies']}
        param_list_all_fan = {'HWMON': ['fan_speed_range', 'fan_pwm_range', 'fan_enable', 'fan_target', 'fan_speed',
                                        'pwm_mode', 'fan_pwm']}

        if data_type == 'Static':
            param_list = param_list_static.copy()
            if env.GUT_CONST.show_fans:
                concat_sensor_dicts(param_list, param_list_static_fan)
        elif data_type == 'Dynamic':
            param_list = param_list_dynamic.copy()
            if env.GUT_CONST.show_fans:
                concat_sensor_dicts(param_list, param_list_dynamic_fan)
        elif data_type == 'Info':
            param_list = param_list_info
        elif data_type == 'State':
            param_list = param_list_state
        else:   # '== All'
            param_list = param_list_all.copy()
            if env.GUT_CONST.show_fans:
                concat_sensor_dicts(param_list, param_list_all_fan)

        for sensor_type, param_names in param_list.items():
            for param in param_names:
                if env.GUT_CONST.DEBUG: print('Processing parameter: {}'.format(param))
                rdata = self.read_gpu_sensor(param, vendor=self.prm.vendor, sensor_type=sensor_type)
                if rdata is False:
                    if param != 'unique_id':
                        print('Warning: Error reading parameter: {}, disabling for this GPU: {}'.format(param,
                              self.prm.card_num))
                elif rdata is None:
                    if env.GUT_CONST.DEBUG: print('Warning: Invalid or disabled parameter: {}'.format(param))
                else:
                    if env.GUT_CONST.DEBUG: print('Valid data [{}] for parameter: {}'.format(rdata, param))
                    self.set_params_value(param, rdata)
        return None

    def print_ppm_table(self):
        """
        Print human friendly table of ppm parameters.
        :return: None
        """
        if not self.prm.readable:
            print('PPM for card number {} not readable.'.format(self.prm.card_num))
            return
        print('Card Number: {}'.format(self.prm.card_num))
        print('   Card Model: {}'.format(self.prm.model_display))
        print('   Card: {}'.format(self.prm.card_path))
        print('   Power Performance Mode: {}'.format(self.prm.power_dpm_force))
        for k, v in self.ppm_modes.items():
            print('   {:<3}: {:>15}'.format(k, v[0]), end='')
            for v_item in v[1:]:
                print('{:>18}'.format(v_item), end='')
            print('')
        print('')

    def print_pstates(self):
        """
        Print human friendly table of p-states.
        :return: None
        """
        if not self.prm.readable:
            print('P-States for card number {} not readable.'.format(self.prm.card_num))
            return
        print('Card Number: {}'.format(self.prm.card_num))
        print('   Card Model: {}'.format(self.prm.model_display))
        print('   Card: {}'.format(self.prm.card_path))
        print('   SCLK: {:<17} MCLK:'.format(' '))
        for k, v in self.sclk_state.items():
            print('   {:>1}:  {:<8}  {:<8}  '.format(k, v[0], v[1]), end='')
            if k in self.mclk_state.keys():
                print('{:3>}:  {:<8}  {:<8}'.format(k, self.mclk_state[k][0], self.mclk_state[k][1]))
            else:
                print('')
        if self.prm.gpu_type == 2:
            print('   VDDC_CURVE')
            for k, v in self.vddc_curve.items():
                print('   {}: {}'.format(k, v))
        print('')

    def print(self, clflag=False):
        """
        Display ls like listing function for GPU parameters.
        :param clflag:  Display clinfo data if True
        :type clflag: bool
        :return: None
        """
        for k, v in self.get_all_params_labels().items():
            if not self.prm.readable:
                if k not in self.get_nc_params_list():
                    continue
            pre = '' if k == 'card_num' else '   '

            if re.search(r'sep[0-9]', k):
                print('{}{}'.format(pre, v.ljust(50, v)))
                continue
            if k == 'unique_id':
                if self.prm.unique_id is None:
                    continue
            if self.prm.gpu_type == 2 and k == 'vddc_range':
                continue
            print('{}{}: {}'.format(pre, v, self.get_params_value(k)))
        if clflag and self.prm.compute:
            for k, v in self.get_all_clinfo_labels().items():
                if re.search(r'sep[0-9]', k):
                    print('{}{}'.format(pre, v.ljust(50, v)))
                    continue
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
        _table_parameters = ['model_display', 'loading', 'mem_loading', 'power', 'power_cap', 'energy', 'temp_val',
                             'vddgfx_val', 'fan_pwm', 'sclk_f_val', 'sclk_ps_val', 'mclk_f_val', 'mclk_ps_val', 'ppm']
        _table_param_labels = {'model_display': 'Model',
                               'loading': 'Load %',
                               'mem_loading': 'Mem Load %',
                               'power': 'Power (W)',
                               'power_cap': 'Power Cap (W)',
                               'energy': 'Energy (kWh)',
                               'temp_val': 'T (C)',
                               'vddgfx_val': 'VddGFX (mV)',
                               'fan_pwm': 'Fan Spd (%)',
                               'sclk_f_val': 'Sclk (MHz)',
                               'sclk_ps_val': 'Sclk Pstate',
                               'mclk_f_val': 'Mclk (MHz)',
                               'mclk_ps_val': 'Mclk Pstate',
                               'ppm': 'Perf Mode'}
    else:
        _table_parameters = ['model_display', 'loading', 'mem_loading', 'power', 'power_cap', 'energy', 'temp_val',
                             'vddgfx_val', 'sclk_f_val', 'sclk_ps_val', 'mclk_f_val', 'mclk_ps_val', 'ppm']
        _table_param_labels = {'model_display': 'Model',
                               'loading': 'Load %',
                               'mem_loading': 'Mem Load %',
                               'power': 'Power (W)',
                               'power_cap': 'Power Cap (W)',
                               'energy': 'Energy (kWh)',
                               'temp_val': 'T (C)',
                               'vddgfx_val': 'VddGFX (mV)',
                               'sclk_f_val': 'Sclk (MHz)',
                               'sclk_ps_val': 'Sclk Pstate',
                               'mclk_f_val': 'Mclk (MHz)',
                               'mclk_ps_val': 'Mclk Pstate',
                               'ppm': 'Perf Mode'}

    def __repr__(self):
        return self.list

    def __str__(self):
        return 'GPU_List: Number of GPUs: {}'.format(self.num_gpus())

    def __init__(self):
        self.list = {}
        self.opencl_map = {}
        self.amd_featuremask = None
        self.amd_wattman = False
        self.amd_writable = False
        self.nv_writable = False

    def wattman_status(self):
        """
        Display Wattman status.
        :return:  Status string
        :rtype: str
        """
        if self.amd_wattman:
            return 'Wattman features enabled: {}'.format(hex(self.amd_featuremask))
        return 'Wattman features not enabled: {}, See README file.'.format(hex(self.amd_featuremask))

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

    def set_gpu_list(self, clinfo_flag=False):
        """
        Use lspci to populate list of all installed GPUs.
        :return: True on success
        :rtype: bool
        """
        if not env.GUT_CONST.cmd_lspci:
            return False
        if clinfo_flag:
            self.read_gpu_opencl_data()
            if env.GUT_CONST.DEBUG: print('openCL map: {}'.format(self.opencl_map))

        # Check AMD writability
        try:
            self.amd_featuremask = env.GUT_CONST.read_amdfeaturemask()
        except FileNotFoundError:
            self.amd_wattman = self.amd_writable = False

        self.amd_wattman = self.amd_writable = True if (self.amd_featuremask == int(0xffff7fff) or
                                                        self.amd_featuremask == int(0xffffffff) or
                                                        self.amd_featuremask == int(0xfffd7fff)) else False

        # Check NV writability
        if env.GUT_CONST.cmd_nvidia_smi:
            self.nv_writable = True

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
            readable = writable = compute = False
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
            except IndexError:
                short_gpu_name = 'UNKNOWN'
            # Check for Fiji ProDuo
            srch_obj = re.search('Fiji', gpu_name)
            if srch_obj:
                srch_obj = re.search(r'Radeon Pro Duo', lspci_items[1].split('[AMD/ATI]')[1])
                if srch_obj:
                    gpu_name = 'Radeon Fiji Pro Duo'

            # Get GPU brand: AMD, INTEL, NVIDIA, ASPEED
            vendor = 'UNKNOWN'
            opencl_device_version = None if clinfo_flag else 'UNKNOWN'
            srch_obj = re.search(r'(AMD|amd|ATI|ati)', gpu_name)
            if srch_obj:
                vendor = 'AMD'
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        if 'device_version' in self.opencl_map[pcie_id].keys():
                            opencl_device_version = self.opencl_map[pcie_id]['device_version']
                            compute = True
                else:
                    compute = True
            srch_obj = re.search(r'(NVIDIA|nvidia|nVidia)', gpu_name)
            if srch_obj:
                vendor = 'NVIDIA'
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        if 'device_version' in self.opencl_map[pcie_id].keys():
                            opencl_device_version = self.opencl_map[pcie_id]['device_version']
                            compute = True
                else:
                    compute = True
            srch_obj = re.search(r'(INTEL|intel|Intel)', gpu_name)
            if srch_obj:
                vendor = 'INTEL'
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        if 'device_version' in self.opencl_map[pcie_id].keys():
                            opencl_device_version = self.opencl_map[pcie_id]['device_version']
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
            srch_obj = re.search(r'(MATROX|matrox|Matrox)', gpu_name)
            if srch_obj:
                vendor = 'MATROX'

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

            # Check AMD write capability
            if vendor == 'AMD':
                pp_od_clk_voltage_file = os.path.join(card_path, 'pp_od_clk_voltage')
                if os.path.isfile(pp_od_clk_voltage_file):
                    readable = True
                    if self.amd_writable:
                        writable = True

            self.list[gpu_uuid].populate(pcie_id, gpu_name, short_gpu_name, vendor, driver_module,
                                         card_path, hwmon_path, readable, writable, compute, opencl_device_version)
            if clinfo_flag:
                if pcie_id in self.opencl_map.keys():
                    self.list[gpu_uuid].populate_ocl(self.opencl_map[pcie_id])
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

        # Run the clinfo command
        cmd = subprocess.Popen(shlex.split('{} --raw'.format(env.GUT_CONST.cmd_clinfo)), shell=False,
                               stdout=subprocess.PIPE)

        # Clinfo Keywords and related opencl_map key.
        ocl_keywords = {'CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE': 'prf_wg_multiple',
                        'CL_DEVICE_MAX_WORK_GROUP_SIZE': 'max_wg_size',
                        'CL_DEVICE_PREFERRED_WORK_GROUP_SIZE': 'prf_wg_size',
                        'CL_DEVICE_MAX_WORK_ITEM_SIZES': 'max_wi_sizes',
                        'CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS': 'max_wi_dim',
                        'CL_DEVICE_MAX_MEM_ALLOC_SIZE': 'max_mem_allocation',
                        'CL_DEVICE_SIMD_INSTRUCTION_WIDTH': 'simd_ins_width',
                        'CL_DEVICE_SIMD_WIDTH': 'simd_width',
                        'CL_DEVICE_SIMD_PER_COMPUTE_UNIT': 'simd_per_cu',
                        'CL_DEVICE_MAX_COMPUTE_UNITS': 'max_cu',
                        'CL_DEVICE_NAME': 'device_name',
                        'CL_DEVICE_OPENCL_C_VERSION': 'opencl_version',
                        'CL_DRIVER_VERSION': 'driver_version',
                        'CL_DEVICE_VERSION': 'device_version'}

        def init_temp_map():
            """
            Return an initialized clinfo dict.
            :return:  Initialized clinfo dict
            :rtype: dict
            """
            t_dict = {}
            for temp_keys in ocl_keywords.values():
                t_dict[temp_keys] = None
            return t_dict

        # Initialize dict variables
        ocl_index = ocl_pcie_id = ocl_pcie_bus_id = ocl_pcie_slot_id = None
        temp_map = init_temp_map()

        # Read each line from clinfo --raw
        for line in cmd.stdout:
            linestr = line.decode('utf-8').strip()
            if len(linestr) < 1:
                continue
            if linestr[0] != '[':
                continue
            line_items = linestr.split(maxsplit=2)
            if len(line_items) != 3:
                continue
            _cl_vendor, cl_index = tuple(re.sub(r'[\[\]]', '', line_items[0]).split('/'))
            if cl_index == '*':
                continue
            if not ocl_index:
                ocl_index = cl_index
                ocl_pcie_slot_id = ocl_pcie_bus_id = None

            # If new cl_index, then update opencl_map
            if cl_index != ocl_index:
                # Update opencl_map with dict variables when new index is encountered.
                self.opencl_map.update({ocl_pcie_id: temp_map})
                if env.GUT_CONST.DEBUG: print('cl_index: {}'.format(self.opencl_map[ocl_pcie_id]))

                # Initialize dict variables
                ocl_index = cl_index
                ocl_pcie_id = ocl_pcie_bus_id = ocl_pcie_slot_id = None
                temp_map = init_temp_map()

            param_str = line_items[1]
            # Check item in clinfo_keywords
            for clinfo_keyword, opencl_map_keyword in ocl_keywords.items():
                srch_obj = re.search(clinfo_keyword, param_str)
                if srch_obj:
                    temp_map[opencl_map_keyword] = line_items[2].strip()
                    if env.GUT_CONST.DEBUG: print('{}: [{}]'.format(clinfo_keyword, temp_map[opencl_map_keyword]))
                    continue

            # PCIe ID related clinfo_keywords
            # Check for AMD pcie_id details
            srch_obj = re.search('CL_DEVICE_TOPOLOGY', param_str)
            if srch_obj:
                ocl_pcie_id = (line_items[2].split()[1]).strip()
                if env.GUT_CONST.DEBUG: print('ocl_pcie_id [{}]'.format(ocl_pcie_id))
                continue

            # Check for NV pcie_id details
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

            # Check for INTEL pcie_id details
            # TODO don't know how to do this yet.

        self.opencl_map.update({ocl_pcie_id: temp_map})
        if env.GUT_CONST.DEBUG: print('cl_index: {}'.format(self.opencl_map[ocl_pcie_id]))
        return True

    def num_vendor_gpus(self, compatibility='total'):
        """
        Return the count of GPUs by vendor.  Counts total by default, but can also by rw, ronly, or wonly.
        :param compatibility: Only count vendor GPUs if True.
        :type compatibility: str
        :return: Dictionary of GPU counts
        :rtype: dict
        """
        results_dict = {}
        for v in self.list.values():
            if compatibility == 'rw':
                if not v.prm.readable or not v.prm.writable:
                    continue
            if compatibility == 'r-only':
                if not v.prm.readable:
                    continue
            if compatibility == 'w-only':
                if not v.prm.writable:
                    continue
            if v.prm.vendor not in results_dict.keys():
                results_dict.update({v.prm.vendor: 1})
            else:
                results_dict[v.prm.vendor] += 1
        return results_dict

    def num_gpus(self, vendor='All'):
        """
        Return the count of GPUs by total, rw, r-only or w-only.
        :param vendor: Only count vendor GPUs if True.
        :type vendor: str
        :return: Dictionary of GPU counts
        :rtype: dict
        """
        results_dict = {'vendor': vendor, 'total': 0, 'rw': 0, 'r-only': 0, 'w-only': 0}
        for v in self.list.values():
            if vendor != 'All':
                if vendor != v.prm.vendor:
                    continue
            if v.prm.readable and v.prm.writable:
                results_dict['rw'] += 1
            elif v.prm.readable:
                results_dict['r-only'] += 1
            elif v.prm.writable:
                results_dict['w-only'] += 1
            results_dict['total'] += 1
        return results_dict

    def list_gpus(self, vendor='All', compatibility='total'):
        """
        Return GPU_Item of GPUs.  Contains all by default, but can be a subset with vendor and compatibility args.
        Only one flag should be set.
        :param vendor: Only count vendor GPUs or All by default (All, AMD, INTEL, NV, ...)
        :type vendor: str
        :param compatibility: Only count GPUs with specified compatibility (total, readable, writable)
        :type compatibility: str
        :return: GpuList of compatible GPUs
        :rtype: GpuList
        """
        result_list = GpuList()
        for k, v in self.list.items():
            if vendor != 'All':
                if vendor != v.prm.vendor:
                    continue
            if compatibility == 'readable':
                if v.prm.readable:
                    result_list.list[k] = v
            elif compatibility == 'writable':
                if v.prm.writable:
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
            if v.prm.readable:
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
            if v.prm.readable:
                v.read_gpu_pstates()

    def print_pstates(self):
        """
        Print the GpuItem p-state data.
        :return: None
        """
        for v in self.list.values():
            v.print_pstates()

    def read_gpu_sensor_data(self, data_type='All'):
        """Read sensor data from GPUs"""
        for v in self.list.values():
            if v.prm.readable:
                v.read_gpu_sensor_data(data_type)

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

    def print_table(self, title=None):
        """
        Print table of parameters.
        :return: True if success
        :rtype: bool
        """
        if self.num_gpus()['total'] < 1:
            return False

        if title:
            print('\x1b[1;36m{}\x1b[0m'.format(title))

        print('┌', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.list.values():
            print('┬', '─'.ljust(16, '─'), sep='', end='')
        print('┐')

        print('│\x1b[1;36m' + 'Card #'.ljust(13, ' ') + '\x1b[0m', sep='', end='')
        for v in self.list.values():
            print('│\x1b[1;36mcard{:<12}\x1b[0m'.format(v.prm.card_num), end='')
        print('│')

        print('├', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.list.values():
            print('┼', '─'.ljust(16, '─'), sep='', end='')
        print('┤')

        for table_item in self.table_parameters():
            #print('│', '\x1b[1;36m' + self.table_param_labels()[table_item].ljust(13, ' ')[:13] + '\x1b[0m',
            print('│\x1b[1;36m{:<13}\x1b[0m'.format(str(self.table_param_labels()[table_item])[:13]),  end='')
            for v in self.list.values():
                #print('│', str(v.get_params_value(table_item)).ljust(16, ' ')[:16], sep='', end='')
                print('│{:<16}'.format(str(v.get_params_value(table_item))[:16]), end='')
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
        if self.num_gpus()['total'] < 1:
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
        if self.num_gpus()['total'] < 1:
            return False

        # Print Data
        for v in self.list.values():
            print('{}|{}'.format(v.energy['tn'].strftime('%c').strip(), v.prm.card_num),
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
        if self.num_gpus()['total'] < 1:
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
        if self.num_gpus()['total'] < 1:
            return False

        # Print Data
        for v in self.list.values():
            line_str_item = ['{}|{}'.format(str(v.energy['tn'].strftime('%c')).strip(), v.prm.card_num)]
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
