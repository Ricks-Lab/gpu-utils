#!/usr/bin/env python3
"""GPUmodules  -  Classes to represent GPUs and sets of GPUs used in amdgpu-utils.


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
__version__ = 'v3.2.0'
__maintainer__ = 'RueiKe'
__status__ = 'Stable Release'
__docformat__ = 'reStructuredText'

# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=bad-continuation

import re
import subprocess
import shlex
import os
import sys
import logging
from typing import Union, List, Dict, TextIO, IO
from pathlib import Path
from uuid import uuid4
from enum import Enum
import glob

try:
    from GPUmodules import env
except ImportError:
    import env


logger = logging.getLogger('gpu-utils')
PATTERNS = env.GutConst.PATTERNS


class GpuEnum(Enum):
    """
    Replace __str__ method of Enum so that name excludes type and can be used as key in other dicts.
    """
    def __str__(self):
        return self.name


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
    """
    # pylint: disable=attribute-defined-outside-init
    _finalized = False
    _button_labels = {'loading':     'Load%',
                      'power':       'Power',
                      'power_cap':   'PowerCap',
                      'temp_val':    'Temp',
                      'vddgfx_val':  'VddGfx',
                      'sclk_ps_val': 'SCLK Pstate',
                      'sclk_f_val':  'SCLK',
                      'mclk_ps_val': 'MCLK Pstate',
                      'mclk_f_val':  'MCLK'}

    _fan_item_list = ['fan_enable', 'pwm_mode', 'fan_target',
                      'fan_speed', 'fan_pwm', 'fan_speed_range', 'fan_pwm_range']
    LEGACY_Skip_List = ['vbios', 'loading', 'mem_loading', 'sclk_ps', 'mclk_ps', 'ppm', 'power', 'power_cap',
                        'power_cap_range', 'mem_vram_total', 'mem_vram_used', 'mem_gtt_total', 'mem_gtt_used',
                        'mem_vram_usage', 'mem_gtt_usage', 'fan_speed_range', 'fan_enable', 'fan_target', 'fan_speed']
    _GPU_NC_Param_List = ['compute', 'readable', 'writable', 'vendor', 'model', 'card_num',
                          'card_path', 'hwmon_path', 'pcie_id', 'driver']
    # Define Class Labels
    GPU_Type = GpuEnum('type', 'Undefined Legacy PStatesNE PStates CurvePts')
    GPU_Comp = GpuEnum('Compatibility', 'None ALL ReadWrite ReadOnly WriteOnly Readable Writable')
    GPU_Vendor = GpuEnum('vendor', 'Undefined ALL AMD NVIDIA INTEL ASPEED MATROX')
    _GPU_CLINFO_Labels = {'sep4': '#',
                          'opencl_version':     '   Device OpenCL C Version',
                          'device_name':        '   Device Name',
                          'device_version':     '   Device Version',
                          'driver_version':     '   Driver Version',
                          'max_cu':             '   Max Compute Units',
                          'simd_per_cu':        '   SIMD per CU',
                          'simd_width':         '   SIMD Width',
                          'simd_ins_width':     '   SIMD Instruction Width',
                          'max_mem_allocation': '   CL Max Memory Allocation',
                          'max_wi_dim':         '   Max Work Item Dimensions',
                          'max_wi_sizes':       '   Max Work Item Sizes',
                          'max_wg_size':        '   Max Work Group Size',
                          'prf_wg_size':        '   Preferred Work Group Size',
                          'prf_wg_multiple':    '   Preferred Work Group Multiple'}
    _GPU_Param_Labels = {'card_num':            'Card Number',
                         'vendor':              'Vendor',
                         'readable':            'Readable',
                         'writable':            'Writable',
                         'compute':             'Compute',
                         'unique_id':           'GPU UID',
                         'id':                  'Device ID',
                         'model_device_decode': 'Decoded Device ID',
                         'model':               'Card Model',
                         'model_display':       'Display Card Model',
                         'pcie_id':             'PCIe ID',
                         'link_spd':            '   Link Speed',
                         'link_wth':            '   Link Width',
                         'sep1':                '#',
                         'driver':              'Driver',
                         'vbios':               'vBIOS Version',
                         'compute_platform':    'Compute Platform',
                         'gpu_type':            'GPU Frequency/Voltage Control Type',
                         'hwmon_path':          'HWmon',
                         'card_path':           'Card Path',
                         'sep2':                '#',
                         'power':               'Current Power (W)',
                         'power_cap':           'Power Cap (W)',
                         'power_cap_range':     '   Power Cap Range (W)',
                         'fan_enable':          'Fan Enable',
                         'pwm_mode':            'Fan PWM Mode',
                         'fan_target':          'Fan Target Speed (rpm)',
                         'fan_speed':           'Current Fan Speed (rpm)',
                         'fan_pwm':             'Current Fan PWM (%)',
                         'fan_speed_range':     '   Fan Speed Range (rpm)',
                         'fan_pwm_range':       '   Fan PWM Range (%)',
                         'sep3':                '#',
                         'loading':             'Current GPU Loading (%)',
                         'mem_loading':         'Current Memory Loading (%)',
                         'mem_gtt_usage':       'Current GTT Memory Usage (%)',
                         'mem_gtt_used':        '   Current GTT Memory Used (GB)',
                         'mem_gtt_total':       '   Total GTT Memory (GB)',
                         'mem_vram_usage':      'Current VRAM Usage (%)',
                         'mem_vram_used':       '   Current VRAM Used (GB)',
                         'mem_vram_total':      '   Total VRAM (GB)',
                         'temperatures':        'Current  Temps (C)',
                         'temp_crits':          'Critical Temps (C)',
                         'voltages':            'Current Voltages (V)',
                         'vddc_range':          '   Vddc Range',
                         'frequencies':         'Current Clk Frequencies (MHz)',
                         'sclk_ps':             'Current SCLK P-State',
                         'sclk_f_range':        '   SCLK Range',
                         'mclk_ps':             'Current MCLK P-State',
                         'mclk_f_range':        '   MCLK Range',
                         'ppm':                 'Power Profile Mode',
                         'power_dpm_force':     'Power DPM Force Performance Level'}

    # HWMON sensor reading details
    SensorSet = Enum('set', 'None Test Static Dynamic Info State Monitor All')
    sensor_sets = {SensorSet.Static:       {'HWMON':  ['power_cap_range', 'temp_crits',
                                                       'fan_speed_range', 'fan_pwm_range']},
                   SensorSet.Dynamic:      {'HWMON':  ['power', 'power_cap', 'temperatures', 'voltages',
                                                       'frequencies', 'fan_enable', 'fan_target',
                                                       'fan_speed', 'pwm_mode', 'fan_pwm']},
                   SensorSet.Info:         {'DEVICE': ['id', 'unique_id', 'vbios', 'mem_vram_total', 'mem_gtt_total']},
                   SensorSet.State:        {'DEVICE': ['loading', 'mem_loading', 'mem_gtt_used', 'mem_vram_used',
                                                       'link_spd', 'link_wth', 'sclk_ps', 'mclk_ps', 'ppm',
                                                       'power_dpm_force']},
                   SensorSet.Monitor:      {'HWMON':  ['power', 'power_cap', 'temperatures', 'voltages',
                                                       'frequencies', 'fan_pwm'],
                                            'DEVICE': ['loading', 'mem_loading', 'mem_gtt_used', 'mem_vram_used',
                                                       'sclk_ps', 'mclk_ps', 'ppm']},
                   SensorSet.All:          {'DEVICE': ['id', 'unique_id', 'vbios', 'loading', 'mem_loading',
                                                       'link_spd', 'link_wth', 'sclk_ps', 'mclk_ps', 'ppm',
                                                       'power_dpm_force', 'mem_vram_total', 'mem_gtt_total',
                                                       'mem_vram_used', 'mem_gtt_used'],
                                            'HWMON':  ['power_cap_range', 'temp_crits', 'power', 'power_cap',
                                                       'temperatures', 'voltages', 'frequencies',
                                                       'fan_speed_range', 'fan_pwm_range', 'fan_enable', 'fan_target',
                                                       'fan_speed', 'pwm_mode', 'fan_pwm']}}

    SensorType = Enum('type', 'SingleParam SingleString SingleStringSelect MinMax MLSS InputLabel InputLabelX MLMS')
    _gbcf = 1.0/(1024*1024*1024)
    _sensor_details = {GPU_Vendor.AMD: {
                               'HWMON': {
                                   'power':           {'type': SensorType.SingleParam,
                                                       'cf': 0.000001, 'sensor': ['power1_average']},
                                   'power_cap':       {'type': SensorType.SingleParam,
                                                       'cf': 0.000001, 'sensor': ['power1_cap']},
                                   'power_cap_range': {'type': SensorType.MinMax,
                                                       'cf': 0.000001, 'sensor': ['power1_cap_min', 'power1_cap_max']},
                                   'fan_enable':      {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ['fan1_enable']},
                                   'fan_target':      {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ['fan1_target']},
                                   'fan_speed':       {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ['fan1_input']},
                                   'fan_speed_range': {'type': SensorType.MinMax,
                                                       'cf': 1, 'sensor': ['fan1_min', 'fan1_max']},
                                   'pwm_mode':        {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ['pwm1_enable']},
                                   'fan_pwm':         {'type': SensorType.SingleParam,
                                                       'cf': 0.39216, 'sensor': ['pwm1']},
                                   'fan_pwm_range':   {'type': SensorType.MinMax,
                                                       'cf': 0.39216, 'sensor': ['pwm1_min', 'pwm1_max']},
                                   'temp_crits':      {'type': SensorType.InputLabelX,
                                                       'cf': 0.001, 'sensor': ['temp*_crit']},
                                   'frequencies':     {'type': SensorType.InputLabelX,
                                                       'cf': 0.000001, 'sensor': ['freq*_input']},
                                   'voltages':        {'type': SensorType.InputLabelX,
                                                       'cf': 1, 'sensor': ['in*_input']},
                                   'temperatures':    {'type': SensorType.InputLabelX,
                                                       'cf': 0.001, 'sensor': ['temp*_input']},
                                   'vddgfx':          {'type': SensorType.InputLabelX,
                                                       'cf': 0.001, 'sensor': ['in*_input']}},
                               'DEVICE': {
                                   'id':              {'type': SensorType.MLMS,
                                                       'cf': None, 'sensor': ['vendor', 'device',
                                                                              'subsystem_vendor', 'subsystem_device']},
                                   'unique_id':       {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ['unique_id']},
                                   'loading':         {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ['gpu_busy_percent']},
                                   'mem_loading':     {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ['mem_busy_percent']},
                                   'mem_vram_total':  {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ['mem_info_vram_total']},
                                   'mem_vram_used':   {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ['mem_info_vram_used']},
                                   'mem_gtt_total':   {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ['mem_info_gtt_total']},
                                   'mem_gtt_used':    {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ['mem_info_gtt_used']},
                                   'link_spd':        {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ['current_link_speed']},
                                   'link_wth':        {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ['current_link_width']},
                                   'sclk_ps':         {'type': SensorType.MLSS,
                                                       'cf': None, 'sensor': ['pp_dpm_sclk']},
                                   'mclk_ps':         {'type': SensorType.MLSS,
                                                       'cf': None, 'sensor': ['pp_dpm_mclk']},
                                   'power_dpm_force': {'type': SensorType.SingleString,
                                                       'cf': None,
                                                       'sensor': ['power_dpm_force_performance_level']},
                                   'ppm':             {'type': SensorType.SingleStringSelect,
                                                       'cf': None, 'sensor': ['pp_power_profile_mode']},
                                   'vbios':           {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ['vbios_version']}}}}

    def __repr__(self) -> dict:
        """
        Return dictionary representing all parts of the GpuItem object.

        :return: Dictionary of GPU item
        """
        return {'params': self.prm, 'clinfo': self.clinfo,
                'sclk_state': self.sclk_state, 'mclk_state': self.mclk_state,
                'vddc_curve': self.vddc_curve, 'vddc_curve_range': self.vddc_curve_range,
                'ppm_modes': self.ppm_modes}

    def __str__(self) -> str:
        """
        Return simple string representing the GpuItem object.

        :return: GPU_item informational string
        """
        return 'GPU_Item: uuid={}'.format(self.prm.uuid)

    def __init__(self, item_id: str):
        """
        Initialize GpuItem object.

        :param item_id:  UUID of the new item.
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
                            'vendor': self.GPU_Vendor.Undefined,
                            'readable': False,
                            'writable': False,
                            'compute': False,
                            'compute_platform': None,
                            'gpu_type': self.GPU_Type.Undefined,
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
                            'temp_crits': None,
                            'vddgfx': None,
                            'vddc_range': ['', ''],
                            'temperatures': None,
                            'voltages': None,
                            'frequencies': None,
                            'loading': None,
                            'mem_loading': None,
                            'mem_vram_total': None,
                            'mem_vram_used': None,
                            'mem_vram_usage': None,
                            'mem_gtt_total': None,
                            'mem_gtt_used': None,
                            'mem_gtt_usage': None,
                            'mclk_ps': ['', ''],
                            'mclk_f_range': ['', ''],
                            'mclk_mask': '',
                            'sclk_ps': ['', ''],
                            'sclk_f_range': ['', ''],
                            'sclk_mask': '',
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
        self.sclk_dpm_state = {}    # {'1': 'Mhz'}
        self.mclk_dpm_state = {}    # {'1': 'Mhz'}
        self.sclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.mclk_state = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve = {}        # {'1': ['Mhz', 'mV']}
        self.vddc_curve_range = {}  # {'1': {SCLK: ['val1', 'val2'], VOLT: ['val1', 'val2']}
        self.ppm_modes = {}         # {'1': ['Name', 'Description']}
        self.finalize_fan_option()

    @classmethod
    def finalize_fan_option(cls) -> None:
        """
        Finalize class variables of gpu parameters based on command line options.
        """
        if cls._finalized:
            return
        cls.finalized = True
        if not env.GUT_CONST.show_fans:
            for fan_item in cls._fan_item_list:
                # Remove fan params from GPU_Param_Labels
                if fan_item in cls._GPU_Param_Labels.keys():
                    del cls._GPU_Param_Labels[fan_item]
                # Remove fan params from SensorSets
                if fan_item in cls.sensor_sets[cls.SensorSet.Static]['HWMON']:
                    cls.sensor_sets[cls.SensorSet.Static]['HWMON'].remove(fan_item)
                if fan_item in cls.sensor_sets[cls.SensorSet.Dynamic]['HWMON']:
                    cls.sensor_sets[cls.SensorSet.Dynamic]['HWMON'].remove(fan_item)
                if fan_item in cls.sensor_sets[cls.SensorSet.Monitor]['HWMON']:
                    cls.sensor_sets[cls.SensorSet.Monitor]['HWMON'].remove(fan_item)
                if fan_item in cls.sensor_sets[cls.SensorSet.All]['HWMON']:
                    cls.sensor_sets[cls.SensorSet.All]['HWMON'].remove(fan_item)

    @classmethod
    def get_button_label(cls, name: str) -> str:
        """
        Return button label for given parameter name.

        :param name: Parameter name
        :return:  Button label
        """
        if name not in cls._button_labels.keys():
            raise KeyError('{} not in button_label dict'.format(name))
        return cls._button_labels[name]

    def set_params_value(self, name: str, value: Union[int, str, list]) -> None:
        """
        Set parameter value for give name.

        :param name:  Parameter name
        :param value:  parameter value
        """
        if isinstance(value, tuple):
            self.prm[name] = list(value)
        elif name == 'pwm_mode':
            self.prm[name][0] = value
            if value == 0: self.prm[name][1] = 'None'
            elif value == 1: self.prm[name][1] = 'Manual'
            else: self.prm[name][1] = 'Dynamic'
        elif name == 'ppm':
            self.prm[name] = re.sub(PATTERNS['PPM_CHK'], '', value).strip()
            self.prm[name] = re.sub(PATTERNS['PPM_NOTCHK'], '-', self.prm[name])
        elif name == 'power':
            time_n = env.GUT_CONST.now(env.GUT_CONST.USELTZ)
            self.prm[name] = round(value, 1)
            delta_hrs = ((time_n - self.energy['tn']).total_seconds()) / 3600
            self.energy['tn'] = time_n
            self.energy['cumulative'] += delta_hrs * value / 1000
            self.prm['energy'] = round(self.energy['cumulative'], 6)
        elif name == 'sclk_ps':
            mask = ''
            for ps in value:
                if not mask:
                    mask = ps.split(':')[0].strip()
                else:
                    mask += ',' + ps.split(':')[0].strip()
                sclk_ps = ps.strip('*').strip().split(': ')
                self.sclk_dpm_state.update({int(sclk_ps[0]): sclk_ps[1]})
                if '*' in ps:
                    self.prm.sclk_ps[0] = int(sclk_ps[0])
                    self.prm.sclk_ps[1] = sclk_ps[1]
                self.prm.sclk_mask = mask
            logger.debug('Mask: [%s], ps: [%s, %s]', mask, self.prm.sclk_ps[0], self.prm.sclk_ps[1])
        elif name == 'mclk_ps':
            mask = ''
            for ps in value:
                if not mask:
                    mask = ps.split(':')[0].strip()
                else:
                    mask += ',' + ps.split(':')[0].strip()
                mclk_ps = ps.strip('*').strip().split(': ')
                self.mclk_dpm_state.update({int(mclk_ps[0]): mclk_ps[1]})
                if '*' in ps:
                    self.prm.mclk_ps[0] = int(mclk_ps[0])
                    self.prm.mclk_ps[1] = mclk_ps[1]
                self.prm.mclk_mask = mask
            logger.debug('Mask: [%s], ps: [%s, %s]', mask, self.prm.mclk_ps[0], self.prm.mclk_ps[1])
        elif name == 'fan_pwm':
            if isinstance(value, int):
                self.prm.fan_pwm = value
            elif isinstance(value, float):
                self.prm.fan_pwm = int(value)
            elif isinstance(value, str):
                self.prm.fan_pwm = int(value) if value.isnumeric() else None
            else:
                self.prm.fan_pwm = None
        elif re.fullmatch(PATTERNS['GPUMEMTYPE'], name):
            self.prm[name] = value
            self.set_memory_usage()
        elif name == 'id':
            self.prm.id = dict(zip(['vendor', 'device', 'subsystem_vendor', 'subsystem_device'], list(value)))
            self.prm.model_device_decode = self.read_pciid_model()
            if (self.prm.model_device_decode != 'UNDETERMINED' and
                    len(self.prm.model_device_decode) < 1.2 * len(self.prm.model_short)):
                self.prm.model_display = self.prm.model_device_decode
        else:
            self.prm[name] = value

    def get_params_value(self, name: str, num_as_int: bool = False) -> Union[int, float, str, list, None]:
        """
        Get parameter value for give name.

        :param name:  Parameter name
        :param num_as_int: Convert float to in if True
        :return: Parameter value
        """
        # Parameters with '_val' as a suffix are derived from a direct source.
        if re.fullmatch(PATTERNS['VAL_ITEM'], name):
            if name == 'temp_val':
                if 'edge' in self.prm['temperatures'].keys():
                    if num_as_int:
                        return int(self.prm['temperatures']['edge'])
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

        # Set type for params that could be float or int
        if name in ['fan_pwm', 'fan_speed', 'power_cap', 'power']:
            if num_as_int:
                if isinstance(self.prm[name], int):
                    return self.prm[name]
                elif isinstance(self.prm[name], float):
                    return int(self.prm[name])
                elif isinstance(self.prm[name], str):
                    return int(self.prm[name]) if self.prm[name].isnumeric() else None
                return self.prm[name]
        return self.prm[name]

    def set_memory_usage(self) -> None:
        """
        Set system and vram memory usage percentage.

        :return: A tuple of the system and vram memory usage percentage.
        """
        if self.prm.mem_gtt_used is None or self.prm.mem_gtt_total is None:
            self.prm.mem_gtt_usage = None
        else:
            self.prm.mem_gtt_usage = 100.0 * self.prm.mem_gtt_used / self.prm.mem_gtt_total

        if self.prm.mem_vram_used is None or self.prm.mem_vram_total is None:
            self.prm.mem_vram_usage = None
        else:
            self.prm.mem_vram_usage = 100.0 * self.prm.mem_vram_used / self.prm.mem_vram_total

    def read_pciid_model(self) -> str:
        """
        Read the model name from the system pcid.ids file

        :return:  GPU model name
        """
        logger.debug('Logger active in module')
        if not os.path.isfile(env.GUT_CONST.sys_pciid):
            print('Error: Can not access system pci.ids file [{}]'.format(env.GUT_CONST.sys_pciid))
            return ''
        with open(env.GUT_CONST.sys_pciid, 'r', encoding='utf8') as pci_id_file_ptr:
            model_str = ''
            level = 0
            for line_item in pci_id_file_ptr:
                line = line_item.rstrip()
                if len(line) < 4:
                    continue
                if line[0] == '#':
                    continue
                if level == 0:
                    if re.fullmatch(PATTERNS['PCIIID_L0'], line):
                        if line[:4] == self.prm.id['vendor'].replace('0x', ''):
                            level += 1
                            continue
                elif level == 1:
                    if re.fullmatch(PATTERNS['PCIIID_L0'], line):
                        break
                    if re.fullmatch(PATTERNS['PCIIID_L1'], line):
                        if line[1:5] == self.prm.id['device'].replace('0x', ''):
                            model_str = line[5:]
                            level += 1
                            continue
                elif level == 2:
                    if re.fullmatch(PATTERNS['PCIIID_L0'], line):
                        break
                    if re.fullmatch(PATTERNS['PCIIID_L1'], line):
                        break
                    if re.fullmatch(PATTERNS['PCIIID_L2'], line):
                        if line[2:6] == self.prm.id['subsystem_vendor'].replace('0x', ''):
                            if line[7:11] == self.prm.id['subsystem_device'].replace('0x', ''):
                                model_str = line[11:]
                                break
        return model_str.strip()

    def populate(self, pcie_id: str, gpu_name: str, short_gpu_name: str, vendor: GpuEnum, driver_module: str,
                 card_path: str, hwmon_path: str, readable: bool, writable: bool, compute: bool, ocl_ver: str) -> None:
        """
        Populate elements of a GpuItem.

        :param pcie_id: The pcid ID of the GPU.
        :param gpu_name:  Model name of the GPU
        :param short_gpu_name:  Short Model name of the GPU
        :param vendor:  GpuEnum representation make of the GPU (AMD, NVIDIA, ...)
        :param driver_module: The name of the driver.
        :param card_path: The path to the GPU.
        :param hwmon_path: Path to the hardware monitor files.
        :param readable: readable compatibility flag
        :param writable: writable compatibility flag
        :param compute: Compute compatibility flag
        :param ocl_ver: Compute platform Name
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

    def populate_ocl(self, ocl_dict: dict) -> None:
        """
        Populate ocl parameters in GpuItem.

        :param ocl_dict: Dictionary of parameters for specific pcie_id
        """
        for k, v in ocl_dict.items():
            if k in self.clinfo.keys():
                self.set_clinfo_value(k, v)

    def set_clinfo_value(self, name: str, value: Union[int, str, list]) -> None:
        """
        Set clinfo values in GPU item dictionary.

        :param name: clinfo parameter name
        :param value:  parameter value
        """
        self.clinfo[name] = value

    def get_clinfo_value(self, name: str) -> Union[int, str, list]:
        """
        Get clinfo parameter value for give name.

        :param name:  clinfo Parameter name
        :return: clinfo Parameter value
        .. note: Maybe not needed
        """
        return self.clinfo[name]

    def get_nc_params_list(self) -> List[str]:
        """
        Get list of parameter names for use with non-readable cards.

        :return: List of parameter names
        """
        return self._GPU_NC_Param_List

    def is_valid_power_cap(self, power_cap: int) -> bool:
        """
        Check if a given power_cap value is valid.

        :param power_cap: Target power cap value to be tested.
        :return: True if valid
        """
        power_cap_range = self.prm.power_cap_range
        if power_cap_range[0] <= power_cap <= power_cap_range[1]:
            return True
        elif power_cap < 0:
            # negative values will be interpreted as reset request
            return True
        return False

    def is_valid_fan_pwm(self, pwm_value: int) -> bool:
        """
        Check if a given fan_pwm value is valid.

        :param pwm_value: Target fan_pwm value to be tested.
        :return: True if valid
        """
        pwm_range = self.prm.fan_pwm_range
        if pwm_range[0] <= pwm_value <= pwm_range[1]:
            return True
        elif pwm_value < 0:
            # negative values will be interpreted as reset request
            return True
        return False

    def is_valid_mclk_pstate(self, pstate: List[int]) -> bool:
        """
        Check if given mclk pstate value is valid.

        :param pstate: pstate = [pstate_number, clk_value, vddc_value]
        :return: Return True if valid
        """
        mclk_range = self.prm.mclk_f_range
        mclk_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(mclk_range[0])))
        mclk_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(mclk_range[1])))
        if pstate[1] < mclk_min or pstate[1] > mclk_max:
            return False
        if self.prm.gpu_type in [self.GPU_Type.PStatesNE, self.GPU_Type.PStates]:
            vddc_range = self.prm.vddc_range
            vddc_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(vddc_range[0])))
            vddc_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(vddc_range[1])))
            if pstate[2] < vddc_min or pstate[2] > vddc_max:
                return False
        return True

    def is_valid_sclk_pstate(self, pstate: List[int]) -> bool:
        """
        Check if given sclk pstate value is valid.

        :param pstate: pstate = [pstate_number, clk_value, vddc_value]
        :return: Return True if valid
        """
        sclk_range = self.prm.sclk_f_range
        sclk_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(sclk_range[0])))
        sclk_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(sclk_range[1])))
        if pstate[1] < sclk_min or pstate[1] > sclk_max:
            return False
        if self.prm.gpu_type in [self.GPU_Type.PStatesNE, self.GPU_Type.PStates]:
            vddc_range = self.prm.vddc_range
            vddc_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(vddc_range[0])))
            vddc_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(vddc_range[1])))
            if pstate[2] < vddc_min or pstate[2] > vddc_max:
                return False
        return True

    def is_changed_sclk_pstate(self, pstate: List[int]) -> bool:
        """
        Check if given sclk pstate value different from current.

        :param pstate: pstate = [pstate_number, clk_value, vddc_value]
        :return: Return True if changed
        """
        if int(re.sub(PATTERNS['END_IN_ALPHA'], '', self.sclk_state[pstate[0]][0])) != pstate[1]:
            return True
        if self.prm.gpu_type in [self.GPU_Type.PStatesNE, self.GPU_Type.PStates]:
            if int(re.sub(PATTERNS['END_IN_ALPHA'], '', self.sclk_state[pstate[0]][1])) != pstate[2]:
                return True
        return False

    def is_changed_mclk_pstate(self, pstate: List[int]) -> bool:
        """
        Check if given mclk pstate value different from current.

        :param pstate: pstate = [pstate_number, clk_value, vddc_value]
        :return: Return True if changed
        """
        if int(re.sub(PATTERNS['END_IN_ALPHA'], '', self.mclk_state[pstate[0]][0])) != pstate[1]:
            return True
        if self.prm.gpu_type in [self.GPU_Type.PStatesNE, self.GPU_Type.PStates]:
            if int(re.sub(PATTERNS['END_IN_ALPHA'], '', self.mclk_state[pstate[0]][1])) != pstate[2]:
                return True
        return False

    def is_changed_vddc_curve_pt(self, pstate: List[int]) -> bool:
        """
        Check if given vddc curve point value different from current.

        :param pstate: curve_point = [point_number, clk_value, vddc_value]
        :return: Return True if changed
        """
        if int(re.sub(PATTERNS['END_IN_ALPHA'], '', self.vddc_curve[pstate[0]][0])) != pstate[1]:
            return True
        if int(re.sub(PATTERNS['END_IN_ALPHA'], '', self.vddc_curve[pstate[0]][1])) != pstate[2]:
            return True
        return False

    def is_valid_vddc_curve_pts(self, curve_pts: List[int]) -> bool:
        """
        Check if given sclk pstate value is valid.

        :param curve_pts: curve_point = [point_number, clk_value, vddc_value]
        :return: Return True if valid
        """
        sclk_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.vddc_curve_range[str(curve_pts[0])]['SCLK'][0])))
        sclk_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.vddc_curve_range[str(curve_pts[0])]['SCLK'][1])))
        if curve_pts[1] < sclk_min or curve_pts[1] > sclk_max:
            return False
        vddc_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str('650mV')))
        vddc_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.vddc_curve_range[str(curve_pts[0])]['VOLT'][1])))
        if curve_pts[2] < vddc_min or curve_pts[2] > vddc_max:
            return False
        return True

    def is_valid_pstate_list_str(self, ps_str: str, clk_name: str) -> bool:
        """
        Check if the given p-states are valid for the given clock.

        :param ps_str: String of comma separated pstate numbers
        :param clk_name: The target clock name
        :return: True if valid
        """
        if ps_str == '':
            return True
        if not re.fullmatch(PATTERNS['VALID_PS_STR'], ps_str):
            return False
        ps_list = self.prm.mclk_mask.split(',') if clk_name == 'MCLK' else self.prm.sclk_mask.split(',')
        for ps in ps_str.split():
            if ps not in ps_list:
                return False
        return True

    def get_current_ppm_mode(self) -> List[Union[int, str]]:
        """
        Read GPU ppm definitions and current settings from driver files.
        :return: ppm state
        :rtype: list
        """
        if self.prm.power_dpm_force.lower() == 'auto':
            return [-1, 'AUTO']
        ppm_item = self.prm.ppm.split('-')
        return [int(ppm_item[0]), ppm_item[1]]

    def read_gpu_ppm_table(self) -> None:
        """
        Read the ppm table.
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
                    logger.debug('PPM line: %s', linestr)
                    if len(line_items) < 2:
                        print('Error: invalid ppm: {}'.format(linestr), file=sys.stderr)
                        continue
                    logger.debug('Valid ppm line: %s', linestr)
                    self.ppm_modes[line_items[0]] = line_items[1:]
            self.ppm_modes['-1'] = ['AUTO', 'Auto']

        rdata = self.read_gpu_sensor('power_dpm_force', vendor=GpuItem.GPU_Vendor.AMD, sensor_type='DEVICE')
        if rdata is False:
            print('Error: card file does not exist: {}'.format(file_path), file=sys.stderr)
            logger.debug('Card file does not exist: %s', file_path)
            self.prm.readable = False
        else:
            self.set_params_value('power_dpm_force', rdata)

    def read_gpu_pstates(self) -> None:
        """
        Read GPU pstate definitions and parameter ranges from driver files.
        Set card type based on pstate configuration
        """
        if not self.prm.readable or self.prm.gpu_type == GpuItem.GPU_Type.Legacy:
            return
        range_mode = False

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
                line = re.sub(r'@', ' ', line)
                lineitems: List[any] = line.split()
                lineitems_len = len(lineitems)
                if self.prm.gpu_type == self.GPU_Type.Undefined:
                    if len(lineitems) == 3:
                        self.prm.gpu_type = self.GPU_Type.PStates
                    elif len(lineitems) == 2:
                        self.prm.gpu_type = self.GPU_Type.CurvePts
                    else:
                        print('Error: Invalid pstate entry length {} for{}: '.format(lineitems_len,
                              os.path.join(self.prm.card_path, 'pp_od_clk_voltage')), file=sys.stderr)
                        logger.debug('Invalid line length for pstate line item: %s', line)
                        continue
                if not range_mode:
                    lineitems[0] = int(re.sub(':', '', lineitems[0]))
                    if self.prm.gpu_type in [self.GPU_Type.PStatesNE, self.GPU_Type.PStates]:
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
                            logger.debug('Curve: index: %s param: %s, val1 %s, val2: %s',
                                         index, param, lineitems[1], lineitems[2])
                            if index in self.vddc_curve_range.keys():
                                self.vddc_curve_range[index].update({param: [lineitems[1], lineitems[2]]})
                            else:
                                self.vddc_curve_range[index] = {}
                                self.vddc_curve_range[index].update({param: [lineitems[1], lineitems[2]]})
                        else:
                            print('Error: Invalid CURVE entry: {}'.format(file_path), file=sys.stderr)

    def read_gpu_sensor(self, parameter: str, vendor: GpuEnum = GPU_Vendor.AMD,
                        sensor_type: str = 'HWMON') -> Union[None, bool, int, str, tuple, list, dict]:
        """
        Read sensor for the given parameter name.  Process per sensor_details dict using the specified
        vendor name and sensor_type.

        :param parameter: GpuItem parameter name (AMD)
        :param vendor: GPU vendor name enum object
        :param sensor_type: GPU sensor name (HWMON or DEVICE)
        :return: Value from reading sensor.
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
        target_sensor = sensor_dict[parameter]
        if target_sensor['type'] == self.SensorType.InputLabelX:
            sensor_files = glob.glob(os.path.join(sensor_path, target_sensor['sensor'][0]))
        else:
            sensor_files = target_sensor['sensor']
        for sensor_file in sensor_files:
            file_path = os.path.join(sensor_path, sensor_file)
            if os.path.isfile(file_path):
                try:
                    with open(file_path) as hwmon_file:
                        if target_sensor['type'] in [self.SensorType.SingleStringSelect, self.SensorType.MLSS]:
                            lines = hwmon_file.readlines()
                            for line in lines:
                                values.append(line.strip())
                        else:
                            values.append(hwmon_file.readline().strip())
                    if target_sensor['type'] == self.SensorType.InputLabelX:
                        if '_input' in file_path:
                            file_path = file_path.replace('_input', '_label')
                        elif '_crit' in file_path:
                            file_path = file_path.replace('_crit', '_label')
                        else:
                            print('Error in sensor label pair: {}'.format(target_sensor))
                        if os.path.isfile(file_path):
                            with open(file_path) as hwmon_file:
                                values.append(hwmon_file.readline().strip())
                        else:
                            values.append('unnamed')
                except OSError as err:
                    logger.debug('Exception [%s]: Can not read HW file: %s', err, file_path)
                    self.read_disabled.append(parameter)
                    return False
            else:
                logger.debug('HW file does not exist: %s', file_path)
                self.read_disabled.append(parameter)
                return False

        if target_sensor['type'] == self.SensorType.SingleParam:
            if target_sensor['cf'] == 1:
                return int(values[0])
            return int(values[0]) * target_sensor['cf']
        elif target_sensor['type'] == self.SensorType.InputLabel:
            ret_value.append(int(values[0]) * target_sensor['cf'])
            ret_value.append(values[1])
            return tuple(ret_value)
        elif target_sensor['type'] in [self.SensorType.MLSS, self.SensorType.MLMS]:
            return values
        elif target_sensor['type'] == self.SensorType.MinMax:
            ret_value.append(int(int(values[0]) * target_sensor['cf']))
            ret_value.append(int(int(values[1]) * target_sensor['cf']))
            return tuple(ret_value)
        elif target_sensor['type'] == self.SensorType.InputLabelX:
            for i in range(0, len(values), 2):
                ret_dict.update({values[i+1]: int(values[i]) * target_sensor['cf']})
            return ret_dict
        elif target_sensor['type'] == self.SensorType.SingleStringSelect:
            for item in values:
                if '*' in item:
                    return item
            return None
        elif target_sensor['type'] == self.SensorType.SingleString:
            return values[0]
        else:
            raise ValueError('Invalid sensor type: {}'.format(target_sensor['type']))

    def read_gpu_sensor_data(self, data_type: Enum = SensorSet.All) -> None:
        """
        Read GPU sensor data from HWMON and DEVICE sensors using the sensor set defined
        by data_type.

        :param data_type: Specifies the sensor set: Dynamic, Static, Info, State, All Monitor
        """
        if not self.prm.readable:
            return None

        param_list = self.sensor_sets[data_type]

        for sensor_type, param_names in param_list.items():
            for param in param_names:
                logger.debug('Processing parameter: %s', param)
                rdata = self.read_gpu_sensor(param, vendor=self.prm.vendor, sensor_type=sensor_type)
                if rdata is False:
                    if param != 'unique_id':
                        logger.debug('Error reading parameter: %s disabling for %s', param, self.prm.card_num)
                        print('Warning: Error reading parameter: {}, disabling for this GPU: {}'.format(param,
                              self.prm.card_num))
                elif rdata is None:
                    logger.debug('Invalid or disabled parameter: %s', param)
                else:
                    logger.debug('Valid data [%s] for parameter: %s', rdata, param)
                    self.set_params_value(param, rdata)
        return None

    def print_ppm_table(self) -> None:
        """
        Print human friendly table of ppm parameters.
        """
        if not self.prm.readable:
            logger.debug('PPM for card number %s not readable.', self.prm.card_num)
            return
        print('{}: {}'.format(self._GPU_Param_Labels['card_num'], self.prm.card_num))
        print('   {}: {}'.format(self._GPU_Param_Labels['model'], self.prm.model))
        print('   {}: {}'.format(self._GPU_Param_Labels['card_path'], self.prm.card_path))
        print('   {}: {}'.format(self._GPU_Param_Labels['power_dpm_force'], self.prm.power_dpm_force))
        file_path = os.path.join(self.prm.card_path, 'pp_power_profile_mode')
        with open(file_path, 'r') as file_ptr:
            lines = file_ptr.readlines()
            for line in lines:
                print('   {}'.format(line.strip('\n')))

    def print_pstates(self) -> None:
        """
        Print human friendly table of p-states.
        """
        if not self.prm.readable:
            logger.debug('P-states for card number %s not readable.', self.prm.card_num)
            return
        pre = '   '
        print('{}: {}'.format(self._GPU_Param_Labels['card_num'], self.prm.card_num))
        print('{}{}: {}'.format(pre, self._GPU_Param_Labels['model'], self.prm.model))
        print('{}{}: {}'.format(pre, self._GPU_Param_Labels['card_path'], self.prm.card_path))
        print('{}{}: {}'.format(pre, self._GPU_Param_Labels['gpu_type'], self.prm.gpu_type.name))

        # DPM States
        if self.prm.gpu_type == self.GPU_Type.CurvePts:
            print('{}{}{}'.format(pre, '', '#'.ljust(50, '#')))
            print('{}DPM States:'.format(pre))
            print('{}SCLK: {:<17} MCLK:'.format(pre, ' '))
            for k, v in self.sclk_dpm_state.items():
                print('{} {:>1}:  {:<8}            '.format(pre, k, v), end='')
                if k in self.mclk_dpm_state.keys():
                    print('{:3>}:  {:<8}'.format(k, self.mclk_dpm_state[k]))
                else:
                    print('')

        # pp_od_clk_voltage states
        print('{}{}{}'.format(pre, '', '#'.ljust(50, '#')))
        print('{}PP OD States:'.format(pre))
        print('{}SCLK: {:<17} MCLK:'.format(pre, ' '))
        for k, v in self.sclk_state.items():
            print('{} {:>1}:  {:<8}  {:<8}  '.format(pre, k, v[0], v[1]), end='')
            if k in self.mclk_state.keys():
                print('{:3>}:  {:<8}  {:<8}'.format(k, self.mclk_state[k][0], self.mclk_state[k][1]))
            else:
                print('')
        if self.prm.gpu_type == self.GPU_Type.CurvePts:
            # Curve points
            print('{}{}{}'.format(pre, '', '#'.ljust(50, '#')))
            print('{}VDDC_CURVE:'.format(pre))
            for k, v in self.vddc_curve.items():
                print('{} {}: {}'.format(pre, k, v))
        print('')

    def print(self, clflag: bool = False) -> None:
        """
        Display ls like listing function for GPU parameters.

        :param clflag:  Display clinfo data if True
        """
        pre = ''
        for k, v in self._GPU_Param_Labels.items():
            if self.prm.gpu_type == self.GPU_Type.Legacy:
                if k in self.LEGACY_Skip_List:
                    continue
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
            if self.prm.gpu_type == self.GPU_Type.CurvePts and k == 'vddc_range':
                continue
            if isinstance(self.get_params_value(k), float):
                print('{}{}: {:.3f}'.format(pre, v, self.get_params_value(k)))
            else:
                print('{}{}: {}'.format(pre, v, self.get_params_value(k)))
        if clflag and self.prm.compute:
            for k, v in self._GPU_CLINFO_Labels.items():
                if re.search(r'sep[0-9]', k):
                    print('{}{}'.format(pre, v.ljust(50, v)))
                    continue
                print('{}: {}'.format(v, self.get_clinfo_value(k)))
        print('')

    def get_plot_data(self, gpu_list: 'class GpuList') -> dict:
        """
        Return a dictionary of dynamic gpu parameters used by amdgpu-plot to populate a df.

        :param gpu_list: GpuList object
        :return: Dictionary of GPU state info for plot data.
        """
        gpu_state = {'Time': str(self.energy['tn'].strftime(env.GUT_CONST.TIME_FORMAT)),
                     'Card#': int(self.prm.card_num)}

        for table_item in gpu_list.table_parameters():
            gpu_state_str = str(re.sub(PATTERNS['MHz'], '', str(self.get_params_value(table_item)))).strip()
            if gpu_state_str.isnumeric():
                gpu_state[table_item] = int(gpu_state_str)
            elif re.fullmatch(PATTERNS['IS_FLOAT'], gpu_state_str):
                gpu_state[table_item] = float(gpu_state_str)
            elif gpu_state_str == '' or gpu_state_str == '-1' or gpu_state_str == 'NA' or gpu_state_str is None:
                gpu_state[table_item] = 'NA'
            else:
                gpu_state[table_item] = gpu_state_str
        return gpu_state


GpuDict = Dict[str, GpuItem]


class GpuList:
    """
    A list of GpuItem indexed with uuid.  It also contains a table of parameters used for tabular printouts
    """
    # Table parameters labels.
    _finalized = False
    _table_parameters = ['model_display', 'loading', 'mem_loading', 'mem_vram_usage', 'mem_gtt_usage',
                         'power', 'power_cap', 'energy', 'temp_val', 'vddgfx_val',
                         'fan_pwm', 'sclk_f_val', 'sclk_ps_val', 'mclk_f_val', 'mclk_ps_val', 'ppm']
    _table_param_labels = {'model_display':  'Model',
                           'loading':        'GPU Load %',
                           'mem_loading':    'Mem Load %',
                           'mem_vram_usage': 'VRAM Usage %',
                           'mem_gtt_usage':  'GTT Usage %',
                           'power':          'Power (W)',
                           'power_cap':      'Power Cap (W)',
                           'energy':         'Energy (kWh)',
                           'temp_val':       'T (C)',
                           'vddgfx_val':     'VddGFX (mV)',
                           'fan_pwm':        'Fan Spd (%)',
                           'sclk_f_val':     'Sclk (MHz)',
                           'sclk_ps_val':    'Sclk Pstate',
                           'mclk_f_val':     'Mclk (MHz)',
                           'mclk_ps_val':    'Mclk Pstate',
                           'ppm':            'Perf Mode'}

    def __repr__(self) -> dict:
        return self.list

    def __str__(self) -> str:
        return 'GPU_List: Number of GPUs: {}'.format(self.num_gpus())

    def __init__(self) -> None:
        self.list: GpuDict = {}
        self.opencl_map = {}
        self.amd_featuremask = None
        self.amd_wattman = False
        self.amd_writable = False
        self.nv_writable = False
        self.finalize_table_params()

    @classmethod
    def finalize_table_params(cls) -> None:
        """
        Finalize class variable of table parameters based on command line options.
        """
        if cls._finalized:
            return
        cls._finalized = True
        if not env.GUT_CONST.show_fans:
            if 'fan_pwm' in cls._table_parameters:
                cls._table_parameters.remove('fan_pwm')
            if 'fan_pwm' in cls._table_param_labels.keys():
                del cls._table_param_labels['fan_pwm']

    def __getitem__(self, uuid: str) -> GpuItem:
        """
        Get GpuItem for specific uuid.

        :param uuid:  Key used in GpuItem dict
        :return: The matching GpuItem, else None
        """
        return self.list.get(uuid, None)

    def add(self, gpu_item: GpuItem) -> None:
        """
        Add given GpuItem to the GpuList.

        :param gpu_item:  Item to be added
        """
        self.list[gpu_item.prm.uuid] = gpu_item
        logger.debug('Added GPU Item %s to GPU List', gpu_item.prm.uuid)

    def wattman_status(self) -> str:
        """
        Display Wattman status.

        :return:  Status string
        """
        logger.debug('AMD featuremask: %s', hex(self.amd_featuremask))
        if self.amd_wattman:
            return 'Wattman features enabled: {}'.format(hex(self.amd_featuremask))
        return 'Wattman features not enabled: {}, See README file.'.format(hex(self.amd_featuremask))

    def table_param_labels(self) -> dict:
        """
        Get dictionary of parameter labels to be used in table reports.

        :return: Dictionary of table parameters/labels
        """
        return self._table_param_labels

    def table_parameters(self) -> List[str]:
        """
        Get list of parameters to be used in table reports.

        :return: List of table parameters
        """
        return self._table_parameters

    def set_gpu_list(self, clinfo_flag: bool = False) -> bool:
        """
        Use lspci to populate list of all installed GPUs.

        :return: True on success
        """
        if not env.GUT_CONST.cmd_lspci:
            return False
        if clinfo_flag:
            self.read_gpu_opencl_data()
            logger.debug('OpenCL map: %s', self.opencl_map)

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
            pcie_ids = subprocess.check_output(('{} | grep -E \"^.*(VGA|3D|Display).*$\" | grep -Eo '
                                                '\"^([0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F])\"').format(
                                               env.GUT_CONST.cmd_lspci), shell=True).decode().split()
        except (subprocess.CalledProcessError, OSError) as except_err:
            print('Error [{}]: lspci failed to find GPUs'.format(except_err))
            return False

        logger.debug('Found %s GPUs', len(pcie_ids))
        for pcie_id in pcie_ids:
            gpu_uuid = uuid4().hex
            self.add(GpuItem(gpu_uuid))
            logger.debug('GPU: %s', pcie_id)
            readable = writable = compute = False
            try:
                lspci_items = subprocess.check_output('{} -k -s {}'.format(env.GUT_CONST.cmd_lspci, pcie_id),
                                                      shell=True).decode().split('\n')
            except (subprocess.CalledProcessError, OSError) as except_err:
                logger.debug('Fatal error [%s]: Can not get GPU details with lspci.', except_err)
                print('Fatal Error [{}]: Can not get GPU details with lspci'.format(except_err))
                sys.exit(-1)
            logger.debug('lspci output items:\n %s', lspci_items)

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
            if re.search('Fiji', gpu_name):
                if re.search(r'Radeon Pro Duo', lspci_items[1].split('[AMD/ATI]')[1]):
                    gpu_name = 'Radeon Fiji Pro Duo'

            # Get GPU brand: AMD, INTEL, NVIDIA, ASPEED
            vendor = GpuItem.GPU_Vendor.Undefined
            opencl_device_version = None if clinfo_flag else 'UNKNOWN'
            if re.search(PATTERNS['AMD_GPU'], gpu_name):
                vendor = GpuItem.GPU_Vendor.AMD
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        if 'device_version' in self.opencl_map[pcie_id].keys():
                            opencl_device_version = self.opencl_map[pcie_id]['device_version']
                            compute = True
                else:
                    compute = True
            if re.search(PATTERNS['NV_GPU'], gpu_name):
                vendor = GpuItem.GPU_Vendor.NVIDIA
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        if 'device_version' in self.opencl_map[pcie_id].keys():
                            opencl_device_version = self.opencl_map[pcie_id]['device_version']
                            compute = True
                else:
                    compute = True
            if re.search(PATTERNS['INTC_GPU'], gpu_name):
                vendor = GpuItem.GPU_Vendor.INTEL
                if self.opencl_map:
                    if pcie_id in self.opencl_map.keys():
                        if 'device_version' in self.opencl_map[pcie_id].keys():
                            opencl_device_version = self.opencl_map[pcie_id]['device_version']
                            compute = True
                else:
                    compute = False if re.search(r' 530', gpu_name) else True
            if re.search(PATTERNS['ASPD_GPU'], gpu_name):
                vendor = GpuItem.GPU_Vendor.ASPEED
            if re.search(PATTERNS['MTRX_GPU'], gpu_name):
                vendor = GpuItem.GPU_Vendor.MATROX

            # Get Driver Name
            driver_module = 'UNKNOWN'
            for lspci_line in lspci_items:
                if re.search(r'(Kernel|kernel)', lspci_line):
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
            logger.debug('HW file search: %s', hw_file_srch)
            if len(hw_file_srch) > 1:
                print('More than one hwmon file found: ', hw_file_srch)
            elif len(hw_file_srch) == 1:
                hwmon_path = hw_file_srch[0]
                logger.debug('HW dir [%s] contents:\n%s', hwmon_path, list(os.listdir(hwmon_path)))

            # Check AMD write capability
            if vendor == GpuItem.GPU_Vendor.AMD:
                pp_od_clk_voltage_file = os.path.join(card_path, 'pp_od_clk_voltage')
                if os.path.isfile(pp_od_clk_voltage_file):
                    readable = True
                    if self.amd_writable:
                        writable = True
                elif os.path.isfile(os.path.join(card_path, 'power_dpm_state')):
                    readable = True
                    self[gpu_uuid].prm.gpu_type = GpuItem.GPU_Type.Legacy
                    self[gpu_uuid].read_disabled = GpuItem.LEGACY_Skip_List[:]
                if logger.getEffectiveLevel() == logging.DEBUG:
                    if os.path.isfile(pp_od_clk_voltage_file):
                        with open(pp_od_clk_voltage_file, 'r') as fp:
                            pp_od_file_details = fp.read()
                    else:
                        pp_od_file_details = 'The file {} does not exist'.format(pp_od_clk_voltage_file)
                    logger.debug('%s contents:\n%s', pp_od_clk_voltage_file, pp_od_file_details)
                    logger.debug('Card dir [%s] contents:\n%s', card_path, list(os.listdir(card_path)))

            self[gpu_uuid].populate(pcie_id, gpu_name, short_gpu_name, vendor, driver_module,
                                    card_path, hwmon_path, readable, writable, compute, opencl_device_version)
            if clinfo_flag:
                if pcie_id in self.opencl_map.keys():
                    self[gpu_uuid].populate_ocl(self.opencl_map[pcie_id])
        return True

    def read_gpu_opencl_data(self) -> bool:
        """
        Use clinfo system call to get openCL details for relevant GPUs.

        :return:  Returns True if successful
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
                        'CL_DEVICE_MAX_WORK_GROUP_SIZE':                'max_wg_size',
                        'CL_DEVICE_PREFERRED_WORK_GROUP_SIZE':          'prf_wg_size',
                        'CL_DEVICE_MAX_WORK_ITEM_SIZES':                'max_wi_sizes',
                        'CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS':           'max_wi_dim',
                        'CL_DEVICE_MAX_MEM_ALLOC_SIZE':                 'max_mem_allocation',
                        'CL_DEVICE_SIMD_INSTRUCTION_WIDTH':             'simd_ins_width',
                        'CL_DEVICE_SIMD_WIDTH':                         'simd_width',
                        'CL_DEVICE_SIMD_PER_COMPUTE_UNIT':              'simd_per_cu',
                        'CL_DEVICE_MAX_COMPUTE_UNITS':                  'max_cu',
                        'CL_DEVICE_NAME':                               'device_name',
                        'CL_DEVICE_OPENCL_C_VERSION':                   'opencl_version',
                        'CL_DRIVER_VERSION':                            'driver_version',
                        'CL_DEVICE_VERSION':                            'device_version'}

        def init_temp_map() -> dict:
            """
            Return an initialized clinfo dict.

            :return:  Initialized clinfo dict
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
                logger.debug('cl_index: %s', self.opencl_map[ocl_pcie_id])

                # Initialize dict variables
                ocl_index = cl_index
                ocl_pcie_id = ocl_pcie_bus_id = ocl_pcie_slot_id = None
                temp_map = init_temp_map()

            param_str = line_items[1]
            # Check item in clinfo_keywords
            for clinfo_keyword, opencl_map_keyword in ocl_keywords.items():
                if clinfo_keyword in param_str:
                    temp_map[opencl_map_keyword] = line_items[2].strip()
                    logger.debug('openCL map %s: [%s]', clinfo_keyword, temp_map[opencl_map_keyword])
                    continue

            # PCIe ID related clinfo_keywords
            # Check for AMD pcie_id details
            if 'CL_DEVICE_TOPOLOGY' in param_str:
                ocl_pcie_id = (line_items[2].split()[1]).strip()
                logger.debug('AMD ocl_pcie_id [%s]', ocl_pcie_id)
                continue

            # Check for NV pcie_id details
            if 'CL_DEVICE_PCI_BUS_ID_NV' in param_str:
                ocl_pcie_bus_id = hex(int(line_items[2].strip()))
                if ocl_pcie_slot_id is not None:
                    ocl_pcie_id = '{}:{}.0'.format(ocl_pcie_bus_id[2:].zfill(2), ocl_pcie_slot_id[2:].zfill(2))
                    ocl_pcie_slot_id = ocl_pcie_bus_id = None
                    logger.debug('NV ocl_pcie_id [%s]', ocl_pcie_id)
                continue
            if 'CL_DEVICE_PCI_SLOT_ID_NV' in param_str:
                ocl_pcie_slot_id = hex(int(line_items[2].strip()))
                if ocl_pcie_bus_id is not None:
                    ocl_pcie_id = '{}:{}.0'.format(ocl_pcie_bus_id[2:].zfill(2), ocl_pcie_slot_id[2:].zfill(2))
                    ocl_pcie_slot_id = ocl_pcie_bus_id = None
                    logger.debug('NV ocl_pcie_id [%s]', ocl_pcie_id)
                continue

            # Check for INTEL pcie_id details
            # TODO don't know how to do this yet.

        self.opencl_map.update({ocl_pcie_id: temp_map})
        return True

    def num_vendor_gpus(self, compatibility: Enum = GpuItem.GPU_Comp.ALL) -> Dict[str, int]:
        """
        Return the count of GPUs by vendor.  Counts total by default, but can also by rw, ronly, or wonly.

        :param compatibility: Only count vendor GPUs if True.
        :return: Dictionary of GPU counts
        """
        try:
            _ = compatibility.name
        except AttributeError:
            raise AttributeError('Error: {} not a valid compatibility name: [{}]'.format(
                                 compatibility, GpuItem.GPU_Comp))
        results_dict = {}
        for v in self.list.values():
            if compatibility == GpuItem.GPU_Comp.ReadWrite:
                if not v.prm.readable or not v.prm.writable:
                    continue
            if compatibility == GpuItem.GPU_Comp.ReadOnly:
                if not v.prm.readable:
                    continue
            if compatibility == GpuItem.GPU_Comp.WriteOnly:
                if not v.prm.writable:
                    continue
            if v.prm.vendor.name not in results_dict.keys():
                results_dict.update({v.prm.vendor.name: 1})
            else:
                results_dict[v.prm.vendor.name] += 1
        return results_dict

    def num_gpus(self, vendor: Enum = GpuItem.GPU_Vendor.ALL) -> Dict[str, int]:
        """
        Return the count of GPUs by total, rw, r-only or w-only.

        :param vendor: Only count vendor GPUs of specific vendor or all vendors by default.
        :return: Dictionary of GPU counts
        """
        try:
            vendor_name = vendor.name
        except AttributeError:
            raise AttributeError('Error: {} not a valid vendor name: [{}]'.format(vendor, GpuItem.GPU_Vendor))
        results_dict = {'vendor': vendor_name, 'total': 0, 'rw': 0, 'r-only': 0, 'w-only': 0}
        for v in self.list.values():
            if vendor != GpuItem.GPU_Vendor.ALL:
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

    def list_gpus(self, vendor: Enum = GpuItem.GPU_Vendor.ALL,
                  compatibility: Enum = GpuItem.GPU_Comp.ALL) -> 'class GpuList':
        """
        Return GPU_Item of GPUs.  Contains all by default, but can be a subset with vendor and compatibility args.
        Only one flag should be set.

        :param vendor: Only count vendor GPUs or ALL by default.
        :param compatibility: Only count GPUs with specified compatibility (all, readable, writable)
        :return: GpuList of compatible GPUs
        """
        try:
            _ = compatibility.name
        except AttributeError:
            raise AttributeError('Error: {} not a valid compatibility name: [{}]'.format(
                compatibility, GpuItem.GPU_Comp))
        try:
            _ = vendor.name
        except AttributeError:
            raise AttributeError('Error: {} not a valid vendor name: [{}]'.format(vendor, GpuItem.GPU_Vendor))
        result_list = GpuList()
        for k, v in self.list.items():
            if vendor != GpuItem.GPU_Vendor.ALL:
                if vendor != v.prm.vendor:
                    continue
            if compatibility == GpuItem.GPU_Comp.Readable:
                if v.prm.readable:
                    result_list.list[k] = v
            elif compatibility == GpuItem.GPU_Comp.Writable:
                if v.prm.writable:
                    result_list.list[k] = v
            else:
                result_list.list[k] = v
        return result_list

    def read_gpu_ppm_table(self) -> None:
        """
        Read GPU ppm data and populate GpuItem.
        """
        for v in self.list.values():
            if v.prm.readable:
                v.read_gpu_ppm_table()

    def print_ppm_table(self) -> None:
        """
        Print the GpuItem ppm data.
        """
        for v in self.list.values():
            v.print_ppm_table()

    def read_gpu_pstates(self) -> None:
        """
        Read GPU p-state data and populate GpuItem.
        """
        for v in self.list.values():
            if v.prm.readable:
                v.read_gpu_pstates()

    def print_pstates(self) -> None:
        """
        Print the GpuItem p-state data.
        """
        for v in self.list.values():
            v.print_pstates()

    def read_gpu_sensor_data(self, data_type: Enum = GpuItem.SensorSet.All) -> None:
        """
        Read sensor data from all GPUs in self.list.

        :param data_type: Specifies the sensor set to use in the read.
        """
        for v in self.list.values():
            if v.prm.readable:
                v.read_gpu_sensor_data(data_type)

    # Printing Methods follow.
    def print(self, clflag: bool = False) -> None:
        """
        Print all GpuItem.

        :param clflag: If true, print clinfo
        """
        for v in self.list.values():
            v.print(clflag)

    def print_table(self, title: Union[str, None] = None) -> bool:
        """
        Print table of parameters.

        :return: True if success
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
            print('│\x1b[1;36m{:<13}\x1b[0m'.format(str(self.table_param_labels()[table_item])[:13]), end='')
            for v in self.list.values():
                data_value_raw = v.get_params_value(table_item)
                if isinstance(data_value_raw, float):
                    data_value_raw = round(data_value_raw, 3)
                print('│{:<16}'.format(str(data_value_raw)[:16]), end='')
            print('│')

        print('└', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.list.values():
            print('┴', '─'.ljust(16, '─'), sep='', end='')
        print('┘')
        return True

    def print_log_header(self, log_file_ptr: TextIO) -> bool:
        """
        Print the log header.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
        """
        if self.num_gpus()['total'] < 1:
            return False

        # Print Header
        print('Time|Card#', end='', file=log_file_ptr)
        for table_item in self.table_parameters():
            print('|{}'.format(table_item), end='', file=log_file_ptr)
        print('', file=log_file_ptr)
        return True

    def print_log(self, log_file_ptr: TextIO) -> bool:
        """
        Print the log data.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
        """
        if self.num_gpus()['total'] < 1:
            return False

        # Print Data
        for v in self.list.values():
            print('{}|{}'.format(v.energy['tn'].strftime(env.GUT_CONST.TIME_FORMAT), v.prm.card_num),
                  sep='', end='', file=log_file_ptr)
            for table_item in self.table_parameters():
                print('|{}'.format(re.sub(PATTERNS['MHz'], '', str(v.get_params_value(table_item)).strip())),
                      sep='', end='', file=log_file_ptr)
            print('', file=log_file_ptr)
        return True

    def print_plot_header(self, log_file_ptr: IO[Union[str, bytes]]) -> bool:
        """
        Print the plot header.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
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

    def print_plot(self, log_file_ptr: IO[Union[str, bytes]]) -> bool:
        """
        Print the plot data.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
        """
        if self.num_gpus()['total'] < 1:
            return False

        # Print Data
        for v in self.list.values():
            line_str_item = ['{}|{}'.format(str(v.energy['tn'].strftime(env.GUT_CONST.TIME_FORMAT)), v.prm.card_num)]
            for table_item in self.table_parameters():
                line_str_item.append('|' +
                                     str(re.sub(PATTERNS['MHz'], '', str(v.get_params_value(table_item)))).strip())
            line_str_item.append('\n')
            line_str = ''.join(line_str_item)
            log_file_ptr.write(line_str.encode('utf-8'))
        log_file_ptr.flush()
        return True


def about() -> None:
    """
    Print details about this module.
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
