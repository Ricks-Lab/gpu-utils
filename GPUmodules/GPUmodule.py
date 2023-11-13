#!/usr/bin/env python3
"""GPUmodules  -  Classes to represent GPUs and sets of GPUs used in
                  rickslab-gpu-utils.

    Copyright (C) 2019  RicksLab

    This program is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the Free
    Software Foundation, either version 3 of the License, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
    more details.

    You should have received a copy of the GNU General Public License along with
    this program.  If not, see <https://www.gnu.org/licenses/>.
"""
__author__ = 'RicksLab'
__copyright__ = 'Copyright (C) 2019 RicksLab'
__license__ = 'GNU General Public License'
__program_name__ = 'gpu-utils'
__maintainer__ = 'RicksLab'
__docformat__ = 'reStructuredText'

# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=bad-continuation

import re
import subprocess
from shlex import split as shlex_split
import os
import sys
import logging
from typing import Union, List, Dict, TextIO, IO, Generator, Any, Tuple, Set, Optional
from pathlib import Path
from uuid import uuid4
from glob import glob
from datetime import datetime
from numpy import nan as np_nan

from GPUmodules.env import GUT_CONST
from GPUmodules.GPUKeys import GpuEnum, GpuType, GpuCompatibility, GpuVendor, SensorSet, SensorType, OdMode


LOGGER = logging.getLogger('gpu-utils')
PATTERNS = GUT_CONST.PATTERNS


class ObjDict(dict):
    """
    Allow access of dictionary keys by key name.
    """
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    def __getattr__(self, name) -> str:
        if name in self:
            return self[name]
        raise AttributeError('No such attribute: {}'.format(name))

    def __setattr__(self, name, value) -> None:
        self[name] = value

    def __delattr__(self, name) -> None:
        if name in self:
            del self[name]
        else:
            raise AttributeError('No such attribute: {}'.format(name))


class GpuItem:
    """An object to store GPU details.
    """
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    mark_up_codes = GUT_CONST.mark_up_codes

    _finalized: bool = False
    _button_labels: Dict[str, str] = {'loading':     'Load%',
                                      'power':       'Power',
                                      'power_cap':   'PowerCap',
                                      'temp_val':    'Temp',
                                      'vddgfx_val':  'VddGfx',
                                      'sclk_ps_val': 'SCLK Pstate',
                                      'sclk_f_val':  'SCLK',
                                      'mclk_ps_val': 'MCLK Pstate',
                                      'mclk_f_val':  'MCLK'}

    _fan_item_list: Set[str] = {'fan_enable', 'fan_target', 'fan_speed', 'fan_speed_range',
                                'pwm_mode', 'fan_pwm', 'fan_pwm_range'}
    _apu_gpus: Set[str] = {'Carrizo', 'Renoir', 'Cezanne', 'Wrestler', 'Llano', 'Ontario', 'Trinity',
                           'Richland', 'Kabini', 'Kaveri', 'Picasso', 'Bristol Ridge', 'Raven Ridge',
                           'Hondo', 'Desna', 'Zacate', 'Weatherford', 'Godavari', 'Temash', 'WinterPark',
                           'BeaverCreek', 'Lucienne', 'Rembrandt', 'Dali', 'Stoney Ridge', 'Pollock',
                           'Barcelo', 'Beema', 'Mullins'}

    # List of parameters for non-compatible AMD GPUs.
    short_list: Set[str] = {'vendor', 'pp_features', 'readable', 'writable', 'compute', 'card_num', 'id',
                            'model_device_decode', 'gpu_type', 'card_path', 'sys_card_path', 'hwmon_path', 'pcie_id'}
    GPU_NC_Param_List: Set[str] = {*short_list, 'model', 'driver', 'model_device_decode'}

    # Define table parameters labels.
    table_parameters: List[str] = ['model_display', 'loading', 'mem_loading', 'mem_vram_usage', 'mem_gtt_usage',
                                   'power', 'power_cap', 'energy', 'temp_val', 'vddgfx_val',
                                   'fan_pwm', 'sclk_f_val', 'sclk_ps_val', 'mclk_f_val', 'mclk_ps_val', 'ppm']
    short_table_parameters: List[str] = ['model_display', 'power', 'energy', 'temp_val', 'vddgfx_val',
                                         'sclk_f_val', 'sclk_ps_val', 'mclk_f_val', 'mclk_ps_val', 'ppm']
    table_param_labels: Dict[str, str] = {
        'model_display':  'Model',
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

    # Complete GPU print items, use skip lists where appropriate.
    _GPU_CLINFO_Labels: Dict[str, str] = {
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
    _GPU_Param_Labels: Dict[str, str] = {
        'card_num':            'Card Number',
        'vendor':              'Vendor',
        'pp_features':         'PP Features',
        'readable':            'Readable',
        'writable':            'Writable',
        'compute':             'Compute',
        'unique_id':           'GPU UID',
        'serial_number':       'GPU S/N',
        'id':                  'Device ID',
        'model_device_decode': 'Decoded Device ID',
        'model':               'Card Model',
        'model_display':       'Display Card Model',
        'card_index':          'Card Index',
        'pcie_id':             'PCIe ID',
        'link_spd':            '   Link Speed',
        'link_wth':            '   Link Width',
        'sep1':                '#',
        'driver':              'Driver',
        'vbios':               'vBIOS Version',
        'compute_platform':    'Compute Platform',
        'compute_mode':        'Compute Mode',
        'gpu_type':            'GPU Type',
        'hwmon_path':          'HWmon',
        'card_path':           'Card Path',
        'sys_card_path':       'System Card Path',
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
        'vddgfx_offset':       '   Vddgfx Offset (mV)',
        'vddgfx_offset_range': '   Vddgfx Offset Range (mV)',
        'frequencies':         'Current Clk Frequencies (MHz)',
        'frequencies_max':     'Maximum Clk Frequencies (MHz)',
        'sclk_ps':             'Current SCLK P-State',
        'sclk_f_range':        '   SCLK Range',
        'mclk_ps':             'Current MCLK P-State',
        'mclk_f_range':        '   MCLK Range',
        'ppm':                 'Power Profile Mode',
        'power_dpm_state':     'Power DPM State',
        'power_dpm_force':     'Power DPM Force Performance Level'}

    # Skip list initialization
    _unsupported_skip_list: Set = set(_GPU_Param_Labels) - GPU_NC_Param_List
    # AMD Type skip lists.
    amd_type_skip_lists: Dict[GpuType, Set] = {}
    for amd_gpu_type in GpuType:
        amd_type_skip_lists.update({amd_gpu_type: set()})
    amd_type_skip_lists[GpuType.Undefined] = _unsupported_skip_list
    amd_type_skip_lists[GpuType.Unsupported] = _unsupported_skip_list
    amd_type_skip_lists[GpuType.Offset] = {'vddc_range'}
    amd_type_skip_lists[GpuType.CurvePts] = {'vddgfx_offset', 'vddgfx_offset_range'}
    amd_type_skip_lists[GpuType.PStatesNE] = {'vddc_range', 'sclk_f_range', 'mclk_f_range', 'vddgfx_offset',
                                              'vddgfx_offset_range'}
    amd_type_skip_lists[GpuType.PStates] = {'vddgfx_offset', 'vddgfx_offset_range'}
    amd_type_skip_lists[GpuType.Legacy] = {'vbios', 'loading', 'mem_loading', 'sclk_ps', 'mclk_ps', 'ppm', 'power',
                                           'power_cap', 'power_cap_range', 'mem_vram_total', 'mem_vram_used',
                                           'mem_gtt_total', 'mem_gtt_used', 'mem_vram_usage', 'mem_gtt_usage',
                                           'fan_speed_range', 'fan_enable', 'fan_target', 'fan_speed', 'vddc_range',
                                           'frequencies', 'sclk_f_range', 'mclk_f_range', 'vddgfx_offset',
                                           'vddgfx_offset_range'}
    amd_type_skip_lists[GpuType.LegacyAPU] = {'unique_id', 'vbios', 'loading', 'sclk_ps', 'mclk_ps', 'ppm',
                                              'vddc_range', 'mem_vram_total', 'mem_gtt_total', 'mem_vram_used',
                                              'mem_gtt_used', 'power_cap_range', 'power', 'power_cap', 'vddgfx_offset',
                                              'vddgfx_offset_range', *_fan_item_list}
    amd_type_skip_lists[GpuType.APU] = {'unique_id', 'loading', 'ppm', 'pwm_mode', 'fan_pwm', 'vddc_range',
                                        'power_cap_range', 'power_cap', 'vddgfx_offset', 'vddgfx_offset_range',
                                        *_fan_item_list}

    # Vendor specific skip lists.
    vendor_skip_lists: Dict[GpuVendor, Set] = {}
    for vendor in GpuVendor:
        vendor_skip_lists.update({vendor: set()})
    vendor_skip_lists[GpuVendor.ASPEED] = _unsupported_skip_list
    vendor_skip_lists[GpuVendor.MATROX] = _unsupported_skip_list
    vendor_skip_lists[GpuVendor.AMD] = {'frequencies_max', 'compute_mode', 'serial_number', 'card_index'}
    vendor_skip_lists[GpuVendor.NVIDIA] = {'fan_enable', 'fan_speed', 'fan_pwm_range', 'fan_speed_range', 'pwm_mode',
                                           'mem_gtt_total', 'mem_gtt_used', 'mem_gtt_usage', 'pp_features',
                                           'mclk_ps', 'mclk_f_range', 'sclk_f_range', 'vddc_range', 'power_dpm_force',
                                           'temp_crits', 'voltages', 'vddgfx_offset'}

    # GPU sensor reading details
    sensor_sets = {SensorSet.Static:       {'HWMON':  ['power_cap_range', 'temp_crits',
                                                       'fan_speed_range', 'fan_pwm_range']},
                   SensorSet.Dynamic:      {'HWMON':  ['power', 'power_cap', 'temperatures', 'voltages',
                                                       'frequencies', 'fan_enable', 'fan_target',
                                                       'fan_speed', 'pwm_mode', 'fan_pwm']},
                   SensorSet.Info:         {'DEVICE': ['unique_id', 'vbios', 'mem_vram_total', 'mem_gtt_total']},
                   SensorSet.State:        {'DEVICE': ['loading', 'mem_loading', 'mem_gtt_used', 'mem_vram_used',
                                                       'link_spd', 'link_wth', 'sclk_ps', 'mclk_ps', 'ppm',
                                                       'power_dpm_force', 'power_dpm_state']},
                   SensorSet.Monitor:      {'HWMON':  ['power', 'power_cap', 'temperatures', 'voltages',
                                                       'frequencies', 'fan_pwm'],
                                            'DEVICE': ['loading', 'mem_loading', 'mem_gtt_used', 'mem_vram_used',
                                                       'sclk_ps', 'mclk_ps', 'ppm']},
                   SensorSet.All:          {'DEVICE': ['unique_id', 'vbios', 'loading', 'mem_loading',
                                                       'link_spd', 'link_wth', 'sclk_ps', 'mclk_ps', 'pstates',
                                                       'ppm', 'power_dpm_force', 'power_dpm_state',
                                                       'mem_vram_total', 'mem_gtt_total',
                                                       'mem_vram_used', 'mem_gtt_used'],
                                            'HWMON':  ['power_cap_range', 'temp_crits', 'power', 'power_cap',
                                                       'temperatures', 'voltages', 'frequencies',
                                                       'fan_speed_range', 'fan_pwm_range', 'fan_enable', 'fan_target',
                                                       'fan_speed', 'pwm_mode', 'fan_pwm']}}

    _gbcf: float = 1.0/(1024*1024*1024)
    _sensor_details = {GpuVendor.AMD: {
                               'HWMON': {
                                   'power':           {'type': SensorType.SingleParam,
                                                       'cf': 0.000001, 'sensor': ('power1_average', )},
                                   'power_cap':       {'type': SensorType.SingleParam,
                                                       'cf': 0.000001, 'sensor': ('power1_cap', )},
                                   'power_cap_range': {'type': SensorType.MinMax,
                                                       'cf': 0.000001, 'sensor': ('power1_cap_min', 'power1_cap_max')},
                                   'fan_enable':      {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ('fan1_enable', )},
                                   'fan_target':      {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ('fan1_target', )},
                                   'fan_speed':       {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ('fan1_input', )},
                                   'fan_speed_range': {'type': SensorType.MinMax,
                                                       'cf': 1, 'sensor': ('fan1_min', 'fan1_max')},
                                   'pwm_mode':        {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ('pwm1_enable', )},
                                   'fan_pwm':         {'type': SensorType.SingleParam,
                                                       'cf': 0.39216, 'sensor': ('pwm1', )},
                                   'fan_pwm_range':   {'type': SensorType.MinMax,
                                                       'cf': 0.39216, 'sensor': ('pwm1_min', 'pwm1_max')},
                                   'temp_crits':      {'type': SensorType.InputLabelX,
                                                       'cf': 0.001, 'sensor': ('temp*_crit', )},
                                   'frequencies':     {'type': SensorType.InputLabelX,
                                                       'cf': 0.000001, 'sensor': ('freq*_input', )},
                                   'voltages':        {'type': SensorType.InputLabelX,
                                                       'cf': 1, 'sensor': ('in*_input', )},
                                   'temperatures':    {'type': SensorType.InputLabelX,
                                                       'cf': 0.001, 'sensor': ('temp*_input', )},
                                   'vddgfx':          {'type': SensorType.InputLabelX,
                                                       'cf': 0.001, 'sensor': ('in*_input', )}},
                               'DEVICE': {
                                   'id':              {'type': SensorType.MLMS,
                                                       'cf': None, 'sensor': ('vendor', 'device',
                                                                              'subsystem_vendor', 'subsystem_device')},
                                   'unique_id':       {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ('unique_id', )},
                                   'loading':         {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ('gpu_busy_percent', )},
                                   'mem_loading':     {'type': SensorType.SingleParam,
                                                       'cf': 1, 'sensor': ('mem_busy_percent', )},
                                   'mem_vram_total':  {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ('mem_info_vram_total', )},
                                   'mem_vram_used':   {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ('mem_info_vram_used', )},
                                   'mem_gtt_total':   {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ('mem_info_gtt_total', )},
                                   'mem_gtt_used':    {'type': SensorType.SingleParam,
                                                       'cf': _gbcf, 'sensor': ('mem_info_gtt_used', )},
                                   'link_spd':        {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ('current_link_speed', )},
                                   'link_wth':        {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ('current_link_width', )},
                                   'sclk_ps':         {'type': SensorType.MLSS,
                                                       'cf': None, 'sensor': ('pp_dpm_sclk', )},
                                   'mclk_ps':         {'type': SensorType.MLSS,
                                                       'cf': None, 'sensor': ('pp_dpm_mclk', )},
                                   'pstates':         {'type': SensorType.AllPStates,
                                                       'cf': None, 'sensor': ('pp_dpm_*clk', )},
                                   'power_dpm_state': {'type': SensorType.SingleString,
                                                       'cf': None,
                                                       'sensor': ('power_dpm_state', )},
                                   'power_dpm_force': {'type': SensorType.SingleString,
                                                       'cf': None,
                                                       'sensor': ('power_dpm_force_performance_level', )},
                                   'ppm':             {'type': SensorType.SingleStringSelect,
                                                       'cf': None, 'sensor': ('pp_power_profile_mode', )},
                                   'vbios':           {'type': SensorType.SingleString,
                                                       'cf': None, 'sensor': ('vbios_version', )}}},
                       GpuVendor.PCIE: {
                               'DEVICE': {
                                   'id':              {'type': SensorType.MLMS,
                                                       'cf': None, 'sensor': ('vendor', 'device',
                                                                              'subsystem_vendor',
                                                                              'subsystem_device')}}}}

    nv_query_items = {SensorSet.Static: {
                                   'power_cap':        ('power.limit', ),
                                   'power_cap_range':  ('power.min_limit', 'power.max_limit'),
                                   'mem_vram_total':   ('memory.total', ),
                                   'frequencies_max':  ('clocks.max.gr', 'clocks.max.sm', 'clocks.max.mem'),
                                   'vbios':            ('vbios_version', ),
                                   'compute_mode':     ('compute_mode', ),
                                   'driver':           ('driver_version', ),
                                   'model':            ('name', ),
                                   'serial_number':    ('serial', ),
                                   'card_index':       ('index', ),
                                   'unique_id':        ('gpu_uuid', )},
                      SensorSet.Dynamic: {
                                   'power':            ('power.draw', ),
                                   'temperatures':     ('temperature.gpu', 'temperature.memory'),
                                   'frequencies':      ('clocks.gr', 'clocks.sm', 'clocks.mem', 'clocks.video'),
                                   'loading':          ('utilization.gpu', ),
                                   'mem_loading':      ('utilization.memory', ),
                                   'mem_vram_used':    ('memory.used', ),
                                   'fan_speed':        ('fan.speed', ),
                                   'ppm':              ('gom.current', ),
                                   'link_wth':         ('pcie.link.width.current', ),
                                   'link_spd':         ('pcie.link.gen.current', ),
                                   'pstates':          ('pstate', )},
                      SensorSet.Monitor: {
                                   'power':            ('power.draw', ),
                                   'power_cap':        ('power.limit', ),
                                   'temperatures':     ('temperature.gpu', ),
                                   'frequencies':      ('clocks.gr', 'clocks.mem'),
                                   'loading':          ('utilization.gpu', ),
                                   'mem_loading':      ('utilization.memory', ),
                                   'mem_vram_used':    ('memory.used', ),
                                   'fan_speed':        ('fan.speed', ),
                                   'ppm':              ('gom.current', ),
                                   'pstates':          ('pstate', )},
                      SensorSet.All: {
                                   'power_cap':        ('power.limit', ),
                                   'power_cap_range':  ('power.min_limit', 'power.max_limit'),
                                   'mem_vram_total':   ('memory.total', ),
                                   'vbios':            ('vbios_version', ),
                                   'driver':           ('driver_version', ),
                                   'compute_mode':     ('compute_mode', ),
                                   'model':            ('name', ),
                                   'serial_number':    ('serial', ),
                                   'card_index':       ('index', ),
                                   'unique_id':        ('gpu_uuid', ),
                                   'power':            ('power.draw', ),
                                   'temperatures':     ('temperature.gpu', 'temperature.memory'),
                                   'frequencies':      ('clocks.gr', 'clocks.sm', 'clocks.mem', 'clocks.video'),
                                   'frequencies_max':  ('clocks.max.gr', 'clocks.max.sm', 'clocks.max.mem'),
                                   'loading':          ('utilization.gpu', ),
                                   'mem_loading':      ('utilization.memory', ),
                                   'mem_vram_used':    ('memory.used', ),
                                   'fan_speed':        ('fan.speed', ),
                                   'ppm':              ('gom.current', ),
                                   'link_wth':         ('pcie.link.width.current', ),
                                   'link_spd':         ('pcie.link.gen.current', ),
                                   'pstates':          ('pstate', )}}

    pp_od_clk_voltage_headers = ['OD_SCLK', 'OD_MCLK', 'OD_VDDC_CURVE', 'OD_RANGE', 'OD_VDDGFX_OFFSET']

    def __repr__(self) -> str:
        """
        Return dictionary representing all parts of the GpuItem object.

        :return: Dictionary of core GPU parameters.
        """
        return str({'params': self.prm, 'clinfo': self.clinfo,
                    'sclk_state': self.sclk_state, 'mclk_state': self.mclk_state,
                    'vddc_curve': self.vddc_curve, 'vddc_curve_range': self.vddc_curve_range,
                    'ppm_modes': self.ppm_modes})

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
        time_0 = GUT_CONST.now(GUT_CONST.useltz)
        self.validated_sensors: bool = False
        self.read_time = GUT_CONST.now(GUT_CONST.useltz)
        self.energy: Dict[str, Any] = {'t0': time_0, 'tn': time_0, 'cumulative': 0.0}
        self.read_skip: tuple = ()    # List of parameters that are to be skipped.
        self.read_disabled: List[str] = []    # List of parameters that failed during read.
        self.write_disabled: List[str] = []   # List of parameters that failed during write.
        self.prm: ObjDict = ObjDict({
            'uuid': item_id,
            'unique_id': '',
            'card_num': None,
            'pcie_id': '',
            'driver': '',
            'vendor': GpuVendor.Undefined,
            'pp_features': '',
            'readable': False,
            'writable': False,
            'compute': 'Unkown',
            'compute_platform': None,
            'compute_mode': None,
            'gpu_type': GpuType.Undefined,
            'id': {'vendor': '', 'device': '', 'subsystem_vendor': '', 'subsystem_device': ''},
            'model_device_decode': 'UNDETERMINED',
            'model': '',
            'model_display': '',
            'serial_number': '',
            'card_index': '',
            'card_path': '',
            'sys_card_path': '',
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
            'vddgfx_offset': 0,
            'vddgfx_offset_range': [-25, 25],
            'vddgfx': None,
            'vddc_range': ['', ''],
            'temperatures': None,
            'voltages': None,
            'frequencies': None,
            'frequencies_max': None,
            'loading': None,
            'mem_loading': None,
            'mem_vram_total': None,
            'mem_vram_used': None,
            'mem_vram_usage': None,
            'mem_gtt_total': None,
            'mem_gtt_used': None,
            'mem_gtt_usage': None,
            'pstate': None,
            'mclk_ps': ['', ''],
            'mclk_f_range': ['', ''],
            'mclk_mask': '',
            'sclk_ps': ['', ''],
            'sclk_f_range': ['', ''],
            'sclk_mask': '',
            'link_spd': '',
            'link_wth': '',
            'ppm': '',
            'power_dpm_state': '',
            'power_dpm_force': '',
            'vbios': ''})
        self.clinfo: ObjDict = ObjDict({
            'device_name': '',
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
        self.all_pstates: Dict[str, Dict[int, dict]] = {}  # 'CLK': {N: {'value': 'MHz', 'state': bool}}
        self.sclk_dpm_state: Dict[int, str] = {}           # {1: 'Mhz'}
        self.mclk_dpm_state: Dict[int, str] = {}           # {1: 'Mhz'}
        self.sclk_state: Dict[int, List[str]] = {}         # {1: ['Mhz', 'mV']}
        self.mclk_state: Dict[int, List[str]] = {}         # {1: ['Mhz', 'mV']}
        self.vddc_curve: Dict[int, List[str]] = {}         # {1: ['Mhz', 'mV']}
        self.vddc_curve_range: Dict[int, dict] = {}        # {1: {'SCLK': ['val1', 'val2'], 'VOLT': ['val1', 'val2']}
        self.ppm_modes: Dict[str, List[str]] = {}          # {'1': ['Name', 'Description']}
        self.raw: Dict[str, dict] = {'DEVICE': {}, 'HWMON': {}}
        self.table_parameters_status: Dict[str, bool] = {}
        for item in self.table_parameters:
            self.table_parameters_status.update({item: True})

        self.finalize_fan_option()

    @classmethod
    def finalize_fan_option(cls) -> None:
        """
        Finalize class variables of gpu parameters based on command line options. This must be
        done after setting of env.  Doing it at the instantiation of a GpuItem assures that.
        """
        if cls._finalized: return
        cls._finalized = True
        if not GUT_CONST.show_fans:
            for fan_item in cls._fan_item_list:
                # Remove fan params from GPU_Param_Labels
                if fan_item in cls._GPU_Param_Labels:
                    del cls._GPU_Param_Labels[fan_item]
                # Remove fan params from Table_Param_Labels
                if fan_item in cls.table_param_labels:
                    del cls.table_param_labels[fan_item]
                # Remove fan params from SensorSets
                for sensor_set in (SensorSet.Static, SensorSet.Dynamic, SensorSet.Monitor, SensorSet.All):
                    if fan_item in cls.sensor_sets[sensor_set]['HWMON']:
                        try:
                            cls.sensor_sets[sensor_set]['HWMON'].remove(fan_item)
                        except ValueError: pass
                # Remove fan params from table param list
                if fan_item in cls.table_parameters:
                    try:
                        cls.short_table_parameters.remove(fan_item)
                        cls.table_parameters.remove(fan_item)
                    except ValueError: pass

    @classmethod
    def is_apu(cls, name: str) -> bool:
        """
        Check if given GPU name is an APU.

        :param name: Target GPU name
        :return: True if name matches APU name
        """
        if not name: return False
        for apu_name in cls._apu_gpus:
            if re.search(apu_name, name, re.IGNORECASE):
                return True
        return False

    @classmethod
    def get_button_label(cls, name: str) -> str:
        """
        Return button label for given parameter name.

        :param name: Parameter name
        :return:  Button label
        """
        if name not in cls._button_labels:
            raise KeyError('{} not in button_label dict'.format(name))
        return cls._button_labels[name]

    def set_params_value(self, name: str, value: Union[int, float, str, list, None]) -> None:
        """
        Set parameter value for give name.

        :param name:  Parameter name
        :param value:  parameter value
        """
        self.read_time = GUT_CONST.now(GUT_CONST.useltz)
        LOGGER.debug('Set param value: [%s], type: [%s]', value, type(value))
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
            if isinstance(value, (int, float)):
                time_n = GUT_CONST.now(GUT_CONST.useltz)
                self.prm[name] = value
                delta_hrs = ((time_n - self.energy['tn']).total_seconds()) / 3600
                self.energy['tn'] = time_n
                self.energy['cumulative'] += delta_hrs * value / 1000
                self.prm['energy'] = round(self.energy['cumulative'], 6)
            else:
                GUT_CONST.process_message('Error: Invalid power value read [{}]'.format(value), log_flag=True)
                self.disable_param_read('power')
                self.disable_param_read('energy')
        elif name == 'sclk_ps':
            mask = ''
            ps_key = 'NA'
            for ps_val in value:
                if not mask:
                    mask = ps_val.split(':')[0].strip()
                else:
                    mask += ',' + ps_val.split(':')[0].strip()
                sclk_ps = ps_val.strip('*').strip().split(': ')
                if len(sclk_ps) < 2:
                    LOGGER.debug('sclk_ps value error: [%s]', sclk_ps)
                else:
                    if sclk_ps[0].isnumeric():
                        ps_key = int(sclk_ps[0])
                    self.sclk_dpm_state.update({ps_key: sclk_ps[1]})
                    if '*' in ps_val:
                        self.prm.sclk_ps[0] = ps_key
                        self.prm.sclk_ps[1] = sclk_ps[1]
                    self.prm.sclk_mask = mask
            LOGGER.debug('Mask: [%s], ps: [%s, %s]', mask, self.prm.sclk_ps[0], self.prm.sclk_ps[1])
        elif name == 'mclk_ps':
            mask = ''
            ps_key = 'NA'
            for ps_val in value:
                if not mask:
                    mask = ps_val.split(':')[0].strip()
                else:
                    mask += ',' + ps_val.split(':')[0].strip()
                mclk_ps = ps_val.strip('*').strip().split(': ')
                if len(mclk_ps) < 2:
                    LOGGER.debug('mclk_ps value error: [%s]', mclk_ps)
                else:
                    if mclk_ps[0].isnumeric():
                        ps_key = int(mclk_ps[0])
                    self.mclk_dpm_state.update({ps_key: mclk_ps[1]})
                    if '*' in ps_val:
                        self.prm.mclk_ps[0] = ps_key
                        self.prm.mclk_ps[1] = mclk_ps[1]
                    self.prm.mclk_mask = mask
            LOGGER.debug('Mask: [%s], ps: [%s, %s]', mask, self.prm.mclk_ps[0], self.prm.mclk_ps[1])
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
            self.prm.id = dict(zip(('vendor', 'device', 'subsystem_vendor', 'subsystem_device'), list(value)))
            self.prm.model_device_decode = self.read_pciid_model()
            self.prm.model_display = self.fit_display_name(self.prm.model_device_decode)
        else:
            self.prm[name] = value

    @staticmethod
    def fit_display_name(name: str, length: int = GUT_CONST.mon_field_width) -> str:
        """
        Convert the given name to a display name which is optimally simplified and truncated.

        :param name: The GPU name to be converted.
        :param length: The target length, default is the monitor field width.
        :return: Simplified and truncated string
        """
        fit_name = ''
        model_display_components = re.sub(PATTERNS['GPU_GENERIC'], '', name).split()
        for name_component in model_display_components:
            if len(name_component) + len(fit_name) + 1 > length:
                break
            fit_name = re.sub(r'\s*/\s*', '/', '{} {}'.format(fit_name, name_component))
        return fit_name

    def param_is_active(self, parameter_name: str) -> bool:
        """
        Return True if given parameter is not skipped and not disabled.

        :param parameter_name:
        :return:
        """
        if parameter_name in self.read_disabled: return False
        if parameter_name in self.read_skip: return False
        return True

    def disable_param_read(self, parameter_name: Union[Tuple[str, ...], str, None]) -> None:
        """
        Disable further reading of the specified parameter.

        :param parameter_name: A single parameter name to be disabled.
        :return:
        """
        if isinstance(parameter_name, str): parameter_name = (parameter_name, )
        for target_param in parameter_name:
            if self.param_is_active(target_param):
                message = 'Warning: Can not read parameter: {}, ' \
                          'disabling for this GPU: {}'.format(target_param, self.prm.card_num)
                GUT_CONST.process_message(message, log_flag=True)
                self.read_disabled.append(target_param)

    def get_params_value(self, name: str, num_as_int: bool = False) -> Optional[Union[int, float, str, list, GpuEnum, datetime]]:
        """
        Get parameter value for given name.

        :param name:  Parameter name
        :param num_as_int: Convert float to int if True
        :return: Parameter value
        """
        if name == 'read_time':
            if self.param_is_active('energy') and self.param_is_active('power'):
                return self.energy['tn']
            return self.read_time
        # Parameters with '_val' as a suffix are derived from a direct source.
        if re.fullmatch(PATTERNS['VAL_ITEM'], name):
            if name == 'temp_val':
                if not self.prm['temperatures']:
                    return None
                for temp_name in ('edge', 'temperature.gpu', 'temp1_input'):
                    if temp_name in self.prm['temperatures']:
                        if self.prm['temperatures'][temp_name]:
                            if num_as_int:
                                return int(self.prm['temperatures'][temp_name])
                            return round(self.prm['temperatures'][temp_name], 1)
                for value in self.prm['temperatures'].values():
                    return value
                return None
            if name == 'vddgfx_val':
                if not self.prm['voltages']:
                    return np_nan
                if 'vddgfx' in self.prm['voltages']:
                    if isinstance(self.prm['voltages']['vddgfx'], str):
                        return int(self.prm['voltages']['vddgfx'])
                for value in self.prm['voltages'].values():
                    return value
            if name == 'sclk_ps_val':
                return self.prm['sclk_ps'][0]
            if name == 'sclk_f_val':
                if self.prm['frequencies']:
                    for clock_name in ('sclk', 'clocks.gr'):
                        if clock_name in self.prm['frequencies']:
                            if isinstance(self.prm['frequencies'][clock_name], str) and\
                                    self.prm['frequencies'][clock_name].isnumeric():
                                return int(self.prm['frequencies'][clock_name])
                if self.prm['sclk_ps'][1]:
                    return self.prm['sclk_ps'][1]
                if self.prm['frequencies']:
                    for value in self.prm['frequencies'].values():
                        return value
                return None
            if name == 'mclk_ps_val':
                return self.prm['mclk_ps'][0]
            if name == 'mclk_f_val':
                if self.prm['frequencies']:
                    for clock_name in ('mclk', 'clocks.mem'):
                        if clock_name in self.prm['frequencies']:
                            if isinstance(self.prm['frequencies'][clock_name], str) and\
                                    self.prm['frequencies'][clock_name].isnumeric():
                                return int(self.prm['frequencies'][clock_name])
                if self.prm['mclk_ps'][1]:
                    return self.prm['mclk_ps'][1]
                return None

        # Set type for params that could be float or int
        if name in {'fan_pwm', 'fan_speed', 'power_cap', 'power', 'vddgfx_offset'}:
            if num_as_int:
                if isinstance(self.prm[name], int):
                    return self.prm[name]
                if isinstance(self.prm[name], float):
                    return int(self.prm[name])
                if isinstance(self.prm[name], str):
                    return int(self.prm[name]) if self.prm[name].isnumeric() else None
                return None
        if name in self.prm:
            return self.prm[name]
        return None

    def set_memory_usage(self) -> None:
        """
        Set system and vram memory usage percentage.
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
        if not GUT_CONST.sys_pciid:
            message = 'Error: pciid file not defined'
            GUT_CONST.process_message(message, log_flag=True)
            return ''
        if not os.path.isfile(GUT_CONST.sys_pciid):
            message = 'Error: Can not access system pci.ids file [{}]'.format(GUT_CONST.sys_pciid)
            GUT_CONST.process_message(message, log_flag=True)
            return ''
        with open(GUT_CONST.sys_pciid, 'r', encoding='utf8') as pci_id_file_ptr:
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

    def populate_prm_from_dict(self, params: Dict[str, any]) -> None:
        """
        Populate elements of a GpuItem with items from a dict with keys that align to elements of GpuItem.

        :param params: A dictionary of parameters with keys that align to GpuItem elements.
        """
        LOGGER.debug('prm dict:\n%s', params)
        set_ocl_ver = None
        for source_name, source_value in params.items():
            # Set primary parameter
            if source_name not in self.prm:
                raise KeyError('Populate dict contains unmatched key: {}'.format(source_name))
            self.prm[source_name] = source_value

            # Set secondary parameters
            if source_name == 'card_path' and source_value:
                card_num_str = source_value.replace('{}card'.format(GUT_CONST.card_root), '').replace('/device', '')
                self.prm.card_num = int(card_num_str) if card_num_str.isnumeric() else None
            elif source_name == 'compute_platform':
                set_ocl_ver = source_value
            elif source_name == 'gpu_type' and source_value:
                self.prm.gpu_type = source_value
                try:
                    self.read_skip = self.amd_type_skip_lists[self.prm.gpu_type]
                except KeyError:
                    pass

        # Compute platform requires that compute bool be set first
        if set_ocl_ver:
            self.prm.compute_platform = set_ocl_ver if self.prm.compute else 'None'

    def set_clinfo_values(self, ocl_dict: Dict[str, Union[int, str, list]]) -> None:
        """
        Set clinfo values in GPU item dictionary.

        :param ocl_dict: dictionary of opencl name and values.
        """
        for ocl_name, ocl_val in ocl_dict.items():
            if ocl_name in self.clinfo:
                self.clinfo[ocl_name] = ocl_val

    def get_clinfo_value(self, name: str) -> Union[int, str, list, None]:
        """
        Get clinfo parameter value for give name.

        :param name:  clinfo Parameter name
        :return: clinfo Parameter value
        """
        try:
            return self.clinfo[name]
        except KeyError:
            return None

    def is_valid_power_cap(self, power_cap: int) -> bool:
        """
        Check if a given power_cap value is valid.

        :param power_cap: Target power cap value to be tested.
        :return: True if valid
        """
        power_cap_range = self.prm.power_cap_range
        if power_cap_range[0] <= power_cap <= power_cap_range[1]:
            return True
        if power_cap < 0:
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
        if pwm_value < 0:
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
        try:
            mclk_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(mclk_range[0])))
            mclk_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(mclk_range[1])))
        except TypeError:
            return False

        if pstate[1] < mclk_min or pstate[1] > mclk_max:
            return False
        if self.prm.gpu_type in (GpuType.PStatesNE, GpuType.PStates):
            try:
                vddc_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddc_range[0])))
                vddc_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddc_range[1])))
            except TypeError:
                return False
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
        if self.prm.gpu_type in {GpuType.PStatesNE, GpuType.PStates}:
            try:
                vddc_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddc_range[0])))
                vddc_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddc_range[1])))
            except TypeError:
                return False
            print('{}:{} {}:{}'.format(pstate[2], vddc_min, pstate[2], vddc_max))
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
        if self.prm.gpu_type in (GpuType.PStatesNE, GpuType.PStates):
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
        if self.prm.gpu_type in (GpuType.PStatesNE, GpuType.PStates):
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

    def is_changed_vddgfx_offset(self, test_vddgfx_offset: int) -> bool:
        """
        Check if given vddgfx_offset value is changed.

        :param test_vddgfx_offset: Integer vddgfx_offset value to be tested
        :return: Return True if changed
        """
        if not isinstance(test_vddgfx_offset, int): return False
        if test_vddgfx_offset == self.prm.vddgfx_offset:
            return False
        return True

    def is_valid_vddgfx_offset(self, test_vddgfx_offset: int) -> bool:
        """
        Check if given vddgfx_offset value is valid.

        :param test_vddgfx_offset: Integer vddgfx_offset value to be tested
        :return: Return True if valid
        """
        if not isinstance(test_vddgfx_offset, int): return False
        vgo_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddgfx_offset_range[0])))
        vgo_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddgfx_offset_range[1])))
        if test_vddgfx_offset < vgo_min or test_vddgfx_offset > vgo_max:
            return False
        return True

    def is_valid_vddc_curve_pts(self, curve_pts: List[int]) -> bool:
        """
        Check if given sclk pstate value is valid.

        :param curve_pts: curve_point = [point_number, clk_value, vddc_value]
        :return: Return True if valid
        """
        sclk_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.vddc_curve_range[curve_pts[0]]['SCLK'][0])))
        sclk_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.vddc_curve_range[curve_pts[0]]['SCLK'][1])))
        if curve_pts[1] < sclk_min or curve_pts[1] > sclk_max:
            return False
        vddc_min = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddc_range[0])))
        vddc_max = int(re.sub(PATTERNS['END_IN_ALPHA'], '', str(self.prm.vddc_range[1])))
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
        for ps_val in ps_str.split():
            if ps_val not in ps_list:
                return False
        return True

    def get_current_ppm_mode(self) -> Union[None, List[Union[int, str]]]:
        """
        Read GPU ppm definitions and current settings from driver files.

        :return: ppm state
        """
        if self.prm.vendor != GpuVendor.AMD:
            return None
        if self.prm.power_dpm_force.lower() == 'auto':
            return [-1, 'AUTO']
        ppm_item = self.prm.ppm.split('-')
        return [int(ppm_item[0]), ppm_item[1]]

    def read_raw_sensors(self) -> None:
        """
        Read all possible device driver files and populate self's raw dictionary.
        """
        for (sensor_type, path) in {'DEVICE': self.prm.card_path, 'HWMON': self.prm.hwmon_path}.items():
            if path and os.path.isdir(path):
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    if not os.path.isfile(file_path): continue
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file_ptr:
                            contents = file_ptr.read().strip()
                    except PermissionError:
                        contents = 'PermissionError'
                    except OSError:
                        contents = 'OSError'
                    except UnicodeDecodeError:
                        contents = 'BINARY'
                    self.raw[sensor_type].update({file: contents})
            GUT_CONST.process_message('Invalid path for {} path: [{}]'.format(sensor_type, path))

    def is_amd_readable(self) -> bool:
        """
        Check if GPU is AMD and readable and readable type.

        :return: True if is AMD and readable.
        """
        if self.prm.vendor != GpuVendor.AMD:
            return False
        if not GUT_CONST.force_all:
            # Originally APU was also disabled for pstates but not ppm
            if not self.prm.readable or self.prm.gpu_type in (GpuType.Legacy, GpuType.Unsupported):
                return False
        return True

    def read_gpu_pp_features(self, return_data: bool = False) -> Optional[str]:
        """
        Read amdgpu PP Feature enablement.

        :param return_data: Return raw file read data if True
        :return:  Raw file read data or None
        """
        if not self.is_amd_readable(): return None
        parameter_file = 'pp_features'
        if not self.param_is_active(parameter_file): return None

        rdata = ''
        file_path = os.path.join(self.prm.card_path, parameter_file)
        if not os.path.isfile(file_path):
            GUT_CONST.process_message('Error: pp_features file does not exist: {}'.format(file_path))
            self.disable_param_read(parameter_file)
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as feature_file:
                for line in feature_file:
                    if return_data: rdata += line
                    line_str = line.strip()
                    if not self.prm.pp_features:
                        if re.search(GUT_CONST.PATTERNS['AMD_FEATURES'], line_str):
                            self.prm.pp_features = re.sub(GUT_CONST.PATTERNS['AMD_FEATURES'], '', line_str)
        except OSError as except_err:
            LOGGER.debug('Error: system support issue for %s, error: [%s]', self.prm.pcie_id, except_err)
            print('Error: System support issue for GPU [{}]'.format(self.prm.pcie_id))
            self.disable_param_read(parameter_file)
            return None

        return rdata if return_data else None

    def read_gpu_ppm_table(self, return_data: bool = False) -> Optional[str]:
        """
        Read the ppm table.

        :param return_data: flag to indicate if read data should be returned
        :return: return data or None if False
        """
        if not self.is_amd_readable(): return None
        parameter_file = 'pp_power_profile_mode'
        if not self.param_is_active(parameter_file): return None

        rdata = ''
        file_path = os.path.join(self.prm.card_path, parameter_file)
        if not os.path.isfile(file_path):
            GUT_CONST.process_message('Error: ppm table file does not exist: {}'.format(file_path))
            self.disable_param_read(parameter_file)
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as card_file:
                for line in card_file:
                    if return_data: rdata += line
                    linestr = line.strip()
                    # Check for mode name: begins with '[ ]+[0-9].*'
                    if re.fullmatch(r'\s+\d.*', line[0:3]):
                        linestr = re.sub(r'\s*[*]*:', ' ', linestr)
                        line_items = linestr.split()
                        LOGGER.debug('PPM line: %s', linestr)
                        if len(line_items) < 2:
                            GUT_CONST.process_message('Error: invalid ppm: {}'.format(linestr))
                            continue
                        LOGGER.debug('Valid ppm line: %s', linestr)
                        self.ppm_modes[line_items[0]] = line_items[1:]
                self.ppm_modes['-1'] = ['AUTO', 'Auto']
        except OSError as except_err:
            LOGGER.debug('Error: system support issue for %s, error: [%s]', self.prm.pcie_id, except_err)
            print('Error: System support issue for GPU [{}]'.format(self.prm.pcie_id))
            self.disable_param_read(parameter_file)
            return None

        return rdata if return_data else None

    def read_gpu_pstates(self) -> None:
        """
        Read GPU pstate definitions and parameter ranges from driver files.
        Set card type based on pstate configuration
        """
        if not self.is_amd_readable(): return
        parameter_file = 'pp_od_clk_voltage'
        if not self.param_is_active(parameter_file): return

        file_path = os.path.join(self.prm.card_path, parameter_file)
        if not os.path.isfile(file_path):
            GUT_CONST.process_message('Error getting p-states: {}'.format(file_path))
            self.disable_param_read(parameter_file)
            return
        current_mode = OdMode.none
        try:
            with open(file_path, 'r', encoding='utf-8') as card_file:
                for line in card_file:
                    if not isinstance(line, str):
                        GUT_CONST.process_message('Read non-string item [{}] from {}'.format(line, parameter_file))
                        self.disable_param_read(parameter_file)
                        return
                    line = line.strip()
                    line = line.strip('\x00')
                    if not line:
                        LOGGER.debug('Null data received, usually caused by invalid pp_feature mask.')
                        continue

                    # Determine data type from header value. Also set card type from header types.
                    if re.fullmatch('OD_.*:$', line):
                        if re.fullmatch('OD_.CLK:$', line):
                            current_mode = OdMode.value
                            clk_name = line.strip()
                        elif re.fullmatch('OD_VDDC_CURVE:$', line):
                            current_mode = OdMode.curve
                            self.prm.gpu_type = GpuType.CurvePts
                            clk_name = ''
                        elif re.fullmatch('OD_VDDGFX_OFFSET:$', line):
                            current_mode = OdMode.offset
                            self.prm.gpu_type = GpuType.Offset
                            clk_name = ''
                        elif re.fullmatch('OD_RANGE:$', line):
                            current_mode = OdMode.range
                            clk_name = ''
                        continue

                    # Split data line.
                    line = re.sub(r'@', ' ', line)
                    lineitems: List[any] = line.split()
                    if not lineitems: continue
                    lineitems_len = len(lineitems)

                    if current_mode == OdMode.value:
                        # Verify if data format matches pstate type.
                        if self.prm.gpu_type not in (GpuType.PStates, GpuType.PStatesNE, GpuType.APU,
                                                     GpuType.CurvePts, GpuType.Offset):
                            if lineitems_len == 3:
                                self.prm.gpu_type = GpuType.PStates
                            if lineitems_len == 2:
                                self.prm.gpu_type = GpuType.APU
                            elif lineitems_len > 3 or lineitems_len < 2:
                                GUT_CONST.process_message('Error: Invalid pstate entry length {} for {}: '.format(
                                    lineitems_len, os.path.join(self.prm.card_path, 'pp_od_clk_voltage')))
                                LOGGER.debug('Invalid line length for pstate line item: %s', line)
                                continue

                        # Read in data based on data type.
                        lineitems[0] = int(re.sub(':', '', lineitems[0]))
                        if lineitems_len == 2: lineitems.append('-')
                        if clk_name == 'OD_SCLK:':
                            self.sclk_state[lineitems[0]] = [lineitems[1], lineitems[2]]
                        elif clk_name == 'OD_MCLK:':
                            self.mclk_state[lineitems[0]] = [lineitems[1], lineitems[2]]

                    elif current_mode == OdMode.curve:
                        lineitems[0] = int(re.sub(':', '', lineitems[0]))
                        self.vddc_curve[lineitems[0]] = [lineitems[1], lineitems[2]]

                    elif current_mode == OdMode.offset:
                        if isinstance(lineitems[0], str):
                            if lineitems[0].isnumeric():
                                self.prm.vddgfx_offset = int(lineitems[0])
                            elif re.fullmatch(GUT_CONST.PATTERNS['NUM_END_IN_ALPHA'], lineitems[0]):
                                self.prm.vddgfx_offset = int(re.sub(PATTERNS['END_IN_ALPHA'], '', lineitems[0]))
                        elif isinstance(lineitems[0], int):
                            self.prm.vddgfx_offset = lineitems[0]

                    elif current_mode == OdMode.range:
                        if lineitems[0] == 'SCLK:':
                            self.prm.sclk_f_range = [lineitems[1], lineitems[2]]
                        elif lineitems[0] == 'MCLK:':
                            self.prm.mclk_f_range = [lineitems[1], lineitems[2]]
                        elif lineitems[0] == 'VDDC:':
                            self.prm.vddc_range = [lineitems[1], lineitems[2]]
                        elif re.fullmatch('VDDC_CURVE_.*', line):
                            if len(lineitems) == 3:
                                index = re.sub(r'VDDC_CURVE_.*\[', '', lineitems[0])
                                index = re.sub(r'].*', '', index)
                                if not index.isnumeric():
                                    GUT_CONST.process_message('Error: Invalid index for line item: {}'.format(line))
                                    LOGGER.debug('Invalid index for pstate line item: %s', line)
                                    continue
                                index = int(index)
                                param = re.sub(r'VDDC_CURVE_', '', lineitems[0])
                                param = re.sub(r'\[\d]:', '', param)
                                LOGGER.debug('Curve: index: %s param: %s, val1 %s, val2: %s',
                                             index, param, lineitems[1], lineitems[2])
                                if index in self.vddc_curve_range:
                                    self.vddc_curve_range[index].update({param: [lineitems[1], lineitems[2]]})
                                else:
                                    self.vddc_curve_range[index] = {}
                                    self.vddc_curve_range[index].update({param: [lineitems[1], lineitems[2]]})
                            else:
                                GUT_CONST.process_message('Error: Invalid CURVE entry: {}'.format(file_path))

        except OSError as except_err:
            LOGGER.debug('Error: system support issue for %s error: [%s]', self.prm.pcie_id, except_err)
            print('Error: System support issue for GPU [{}]'.format(self.prm.pcie_id))
            self.disable_param_read(parameter_file)

        if self.prm.gpu_type == GpuType.CurvePts:
            try:
                max_state = max(self.vddc_curve)
                min_lim = min(self.vddc_curve_range[0]['VOLT'][0], self.vddc_curve[0][1])
                max_lim = max(self.vddc_curve_range[max_state]['VOLT'][1], self.vddc_curve[max_state][1])
                self.prm.vddc_range = [min_lim, max_lim]
            except (KeyError, ValueError):
                self.prm.vddc_range = [None, None]

    def read_gpu_sensor(self, parameter: str, vendor: GpuVendor = GpuVendor.AMD,
                        sensor_type: str = 'HWMON') -> Union[None, bool, int, str, tuple, list, dict]:
        """
        Read sensor for the given parameter name.  Process per sensor_details dict using the specified
        vendor name and sensor_type.

        :param parameter: GpuItem parameter name (AMD)
        :param vendor: GPU vendor name enum object
        :param sensor_type: GPU sensor name (HWMON or DEVICE)
        :return: Value from reading sensor.
        """
        if vendor in (GpuVendor.AMD, GpuVendor.PCIE):
            return self.read_gpu_sensor_generic(parameter, vendor, sensor_type)
        if vendor == GpuVendor.NVIDIA:
            return self.read_gpu_sensor_nv(parameter)
        GUT_CONST.process_message('Error: Invalid vendor [{}]'.format(vendor))
        return None

    def read_gpu_sensor_nv(self, parameter: str) -> Union[None, bool, int, str, tuple, list, dict]:
        """
        Function to read a single sensor from NV GPU.

        :param parameter:  Target parameter for reading
        :return: read results
        """
        if not self.param_is_active(parameter):
            return False
        cmd_str = '{} -i {} --query-gpu={} --format=csv,noheader,nounits'.format(
                  GUT_CONST.cmd_nvidia_smi, self.prm.pcie_id, parameter)
        LOGGER.debug('NV command:\n%s', cmd_str)
        nsmi_item = None
        try:
            nsmi_item = subprocess.check_output(shlex_split(cmd_str), shell=False).decode().split('\n')
            LOGGER.debug('NV raw query response: [%s]', nsmi_item)
        except (subprocess.CalledProcessError, OSError) as except_err:
            LOGGER.debug('NV query %s error: [%s]', nsmi_item, except_err)
            self.disable_param_read(parameter)
            return False
        return_item = nsmi_item[0].strip() if nsmi_item else None
        LOGGER.debug('NV query result: [%s]', return_item)
        return return_item

    def read_gpu_sensor_generic(self, parameter: str, vendor: GpuVendor = GpuVendor.AMD,
                                sensor_type: str = 'HWMON') -> Union[None, bool, int, str, tuple, list, dict]:
        """
        Read sensor for the given parameter name.  Process per sensor_details dict using the specified
        vendor name and sensor_type.

        :param parameter: GpuItem parameter name (AMD)
        :param vendor: GPU vendor name enum object
        :param sensor_type: GPU sensor name (HWMON or DEVICE)
        :return: Value from reading sensor.
        """
        if not GUT_CONST.force_all:
            if self.prm.gpu_type == GpuType.Unsupported and parameter != 'id':
                return None
            if not self.prm.readable and parameter != 'id':
                return None
        if sensor_type not in self._sensor_details[vendor]:
            GUT_CONST.process_message('Error: Invalid sensor_type [{}]'.format(sensor_type))
            return None
        sensor_dict = self._sensor_details[vendor][sensor_type]
        if parameter not in sensor_dict:
            GUT_CONST.process_message('Error: Invalid parameter [{}]'.format(parameter))
            return None
        if not self.param_is_active(parameter):
            return None

        device_sensor_path = self.prm.card_path if self.prm.card_path else self.prm.sys_card_path
        LOGGER.debug('sensor path set to [%s]', device_sensor_path)
        sensor_path = self.prm.hwmon_path if sensor_type == 'HWMON' else device_sensor_path
        values = []
        ret_value = []
        ret_dict = {}
        target_sensor = sensor_dict[parameter]
        if target_sensor['type'] in (SensorType.InputLabelX, SensorType.AllPStates):
            sensor_files = glob(os.path.join(sensor_path, target_sensor['sensor'][0]))
        else:
            sensor_files = target_sensor['sensor']
        for sensor_file in sensor_files:
            file_path = os.path.join(sensor_path, sensor_file)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as hwmon_file:
                        if target_sensor['type'] in (SensorType.SingleStringSelect,
                                                     SensorType.MLSS,
                                                     SensorType.InputLabelX,
                                                     SensorType.AllPStates):
                            lines = hwmon_file.readlines()
                            for line in lines:
                                values.append(line.strip())
                        else:
                            values.append(hwmon_file.readline().strip())
                    if target_sensor['type'] == SensorType.AllPStates:
                        # clock_name: {ps_num: {'value': ps_val, 'state': ps_sts}}
                        clock_name = re.sub(r'.*pp_dpm_', '', sensor_file)
                        if clock_name not in self.all_pstates:
                            self.all_pstates.update({clock_name: {}})
                        for ps_value in values:
                            ps_val_list = re.sub(':', '', ps_value).split()
                            if len(ps_val_list) > 1:
                                ps_num = int(ps_val_list[0]) if ps_val_list[0].isnumeric() else ps_val_list[0]
                                ps_val = ps_val_list[1]
                                ps_sts = False
                                if len(ps_val_list) > 2:
                                    ps_sts = True
                                if ps_num not in self.all_pstates[clock_name]:
                                    self.all_pstates[clock_name].update({ps_num: {'value': ps_val, 'state': ps_sts}})
                                else:
                                    self.all_pstates[clock_name][ps_num]['value'] = ps_val
                                    self.all_pstates[clock_name][ps_num]['state'] = ps_sts
                    elif target_sensor['type'] == SensorType.InputLabelX:
                        label_file_path: str = ''
                        if '_input' in file_path:
                            label_file_path = file_path.replace('_input', '_label')
                        elif '_crit' in file_path:
                            label_file_path = file_path.replace('_crit', '_label')
                        else:
                            GUT_CONST.process_message('Error in sensor label pair: {}'.format(target_sensor))
                        if os.path.isfile(label_file_path):
                            with open(label_file_path, 'r', encoding='utf-8') as sensor_label_file:
                                values.append(sensor_label_file.readline().strip())
                        else:
                            values.append(os.path.basename(sensor_file))
                except OSError as err:
                    LOGGER.debug('Exception [%s]: Can not read HW file: %s', err, file_path)
                    self.disable_param_read(parameter)
                    return False
            else:
                LOGGER.debug('HW file does not exist: %s', file_path)
                self.disable_param_read(parameter)
                return False

        if target_sensor['type'] == SensorType.SingleParam:
            if target_sensor['cf'] == 1:
                return int(values[0])
            return int(values[0]) * target_sensor['cf']
        if target_sensor['type'] == SensorType.InputLabel:
            ret_value.append(int(values[0]) * target_sensor['cf'])
            ret_value.append(values[1])
            return tuple(ret_value)
        if target_sensor['type'] in (SensorType.MLSS, SensorType.MLMS):
            return values
        if target_sensor['type'] == SensorType.MinMax:
            ret_value.append(int(int(values[0]) * target_sensor['cf']))
            ret_value.append(int(int(values[1]) * target_sensor['cf']))
            return tuple(ret_value)
        if target_sensor['type'] == SensorType.AllPStates:
            # Already set dict in object
            return None
        if target_sensor['type'] == SensorType.InputLabelX:
            for i in range(0, len(values), 2):
                ret_dict.update({values[i+1]: int(values[i]) * target_sensor['cf']})
            return ret_dict
        if target_sensor['type'] == SensorType.SingleStringSelect:
            for item in values:
                if '*' in item:
                    return item
            return None
        if target_sensor['type'] == SensorType.SingleString:
            return values[0]
        raise ValueError('Invalid sensor type: {}'.format(target_sensor['type']))

    def read_gpu_sensor_set(self, data_type: SensorSet = SensorSet.All) -> bool:
        """
        Read GPU sensor data from HWMON and DEVICE sensors using the sensor set defined
        by data_type.

        :param data_type: Specifies the sensor set: Dynamic, Static, Info, State, All Monitor
        :return: True on success.
        """
        if self.prm.vendor == GpuVendor.AMD:
            return_stat = self.read_gpu_sensor_set_amd(data_type)
            self.update_table_items_status()
            return return_stat
        if self.prm.vendor == GpuVendor.NVIDIA:
            return_stat = self.read_gpu_sensor_set_nv(data_type)
            self.update_table_items_status()
            return return_stat
        return False

    def update_table_items_status(self) -> None:
        """
        Update the readable status of table related parameters.
        """
        if GUT_CONST.debug:
            print('### read_time_val: {}'.format(
                self.get_params_value('read_time').strftime(GUT_CONST.TIME_FORMAT)))
        for table_item, status in self.table_parameters_status.items():
            if GUT_CONST.debug:
                print('{}: {}: {}'.format(table_item, status, self.get_params_value(table_item)))
            if format_table_value(self.get_params_value(table_item), table_item) in {None, '', np_nan, '---'}:
                self.table_parameters_status[table_item] = False
        if GUT_CONST.debug:
            print('')

    def read_gpu_sensor_set_nv(self, data_type: SensorSet = SensorSet.All) -> bool:
        """
        Use the nvidia_smi tool to query GPU parameters.

        :param data_type: specifies the set of sensors to read
        :return: True if successful, else False and card will have read disabled
        """
        if data_type not in self.nv_query_items:
            raise TypeError('Invalid SensorSet value: [{}]'.format(data_type))

        sensor_dict = GpuItem.nv_query_items[data_type]
        nsmi_items = []
        query_list = [item for sublist in sensor_dict.values() for item in sublist]
        query_list = [item for item in query_list if not self.param_is_active(item)]

        if self.validated_sensors:
            qry_string = ','.join(query_list)
            cmd_str = '{} -i {} --query-gpu={} --format=csv,noheader,nounits'.format(
                        GUT_CONST.cmd_nvidia_smi, self.prm.pcie_id, qry_string)
            LOGGER.debug('NV command:\n%s', cmd_str)
            try:
                nsmi_items = subprocess.check_output(shlex_split(cmd_str), shell=False).decode().split('\n')
                LOGGER.debug('NV query (single-call) result: [%s]', nsmi_items)
            except (subprocess.CalledProcessError, OSError) as except_err:
                LOGGER.debug('NV query %s error: [%s]', nsmi_items, except_err)
                return False
            if nsmi_items:
                nsmi_items = nsmi_items[0].split(',')
                nsmi_items = [item.strip() for item in nsmi_items]
        else:
            # Read sensors one at a time if SensorSet.All has not been validated
            if data_type == SensorSet.All:
                self.validated_sensors = True
            for query_item in query_list:
                query_data = self.read_gpu_sensor_nv(query_item)
                nsmi_items.append(query_data)
                LOGGER.debug('NV query (each-call) query item [%s], result: [%s]', query_item, query_data)
            if not nsmi_items:
                LOGGER.debug('NV query (each-call) failed for all sensors, disabling read for card [%s]',
                             self.prm.card_num)
                self.prm.readable = False
                return False

        results = dict(zip(query_list, nsmi_items))
        LOGGER.debug('NV query result: %s', results)

        # Populate GpuItem data from results dictionary
        for param_name, sensor_list in sensor_dict.items():
            if param_name == 'power_cap_range':
                if results['power.min_limit'] and re.fullmatch(PATTERNS['IS_FLOAT'], results['power.min_limit']):
                    power_min = float(results['power.min_limit'])
                else:
                    power_min = results['power.min_limit']
                if results['power.max_limit'] and re.fullmatch(PATTERNS['IS_FLOAT'], results['power.max_limit']):
                    power_max = float(results['power.max_limit'])
                else:
                    power_max = results['power.max_limit']
                self.prm.power_cap_range = [power_min, power_max]
            elif param_name == 'power':
                if results['power.draw'] and re.fullmatch(PATTERNS['IS_FLOAT'], results['power.draw']):
                    power = float(results['power.draw'])
                else:
                    self.disable_param_read('power')
                    self.disable_param_read('energy')
                    power = None
                self.set_params_value('power', power)
            elif param_name == 'pstates':
                pstate_str = re.sub(PATTERNS['ALPHA'], '', results['pstate'])
                pstate = int(pstate_str) if pstate_str.isnumeric() else None
                self.prm['sclk_ps'][0] = pstate
                self.prm['mclk_ps'][0] = pstate
            elif param_name in {'temperatures', 'voltages', 'frequencies', 'frequencies_max'}:
                self.prm[param_name] = {}
                for sn_k in sensor_list:
                    if sn_k not in results: continue
                    if results[sn_k] and re.fullmatch(PATTERNS['IS_FLOAT'], results[sn_k]):
                        param_val = float(results[sn_k])
                    else:
                        param_val = None
                    self.prm[param_name].update({sn_k: param_val})
            elif re.fullmatch(PATTERNS['GPUMEMTYPE'], param_name):
                for sn_k in sensor_list:
                    if sn_k not in results: continue
                    mem_value = int(results[sn_k]) if results[sn_k].isnumeric else None
                    self.prm[param_name] = mem_value / 1024.0
                self.set_memory_usage()
            elif param_name == 'fan_speed':
                sn_k = sensor_list[0]
                if re.fullmatch(PATTERNS['IS_FLOAT'], results[sn_k]):
                    self.prm[param_name] = float(results[sn_k])
                    self.prm.fan_pwm = self.prm[param_name]
            elif param_name == 'link_spd':
                self.prm.link_spd = 'GEN{}'.format(results['pcie.link.gen.current'])
            elif param_name == 'model':
                self.prm.model = results['name']
                self.prm.model_display = self.prm.model_device_decode
                if results['name'] and len(results['name']) < len(self.prm.model_device_decode):
                    self.prm.model_display = results['name']
                self.prm.model_display = self.fit_display_name(self.prm.model_display)
            elif len(sensor_list) == 1:
                sn_k = sensor_list[0]
                if re.fullmatch(PATTERNS['IS_FLOAT'], results[sn_k]):
                    self.prm[param_name] = float(results[sn_k])
                elif not results[sn_k]:
                    self.prm[param_name] = None
                self.prm[param_name] = results[sn_k]
        return True

    def read_gpu_sensor_set_amd(self, data_type: SensorSet = SensorSet.All) -> bool:
        """
        Read GPU sensor data from HWMON and DEVICE sensors using the sensor set defined
        by data_type.

        :param data_type: Specifies the sensor set: Dynamic, Static, Info, State, All Monitor
        :return: True if successful
        """
        if not GUT_CONST.force_all:
            if not self.prm.readable:
                return False

        return_status = False
        param_list = self.sensor_sets[data_type]

        for sensor_type, param_names in param_list.items():
            for param in param_names:
                LOGGER.debug('Processing parameter: %s', param)
                rdata = self.read_gpu_sensor(param, vendor=self.prm.vendor, sensor_type=sensor_type)
                if rdata is False:
                    if param != 'unique_id':
                        self.disable_param_read('unique_id')
                elif rdata is None:
                    LOGGER.debug('Read data [%s], Invalid or disabled parameter: %s', rdata, param)
                else:
                    LOGGER.debug('Valid data [%s] for parameter: %s', rdata, param)
                    self.set_params_value(param, rdata)
                    return_status = True
        return return_status

    def print_disabled_params(self) -> None:
        """
        Print list of disabled parameters.
        """
        param_lists = []
        if GUT_CONST.verbose and self.read_skip:
            param_lists.append('Skipped')
        if self.read_disabled:
            param_lists.append('Disabled')
        if not param_lists:
            return
        param_lists = tuple(param_lists[:],)

        color = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['data']
        color_reset = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['reset']
        pre = '   '
        for param_list_name in param_lists:
            param_list = self.read_disabled if param_list_name == 'Disabled' else self.read_skip
            label = '{} Parameters: '.format(param_list_name)
            print('{}{}{}'.format(pre, '', '#'.ljust(50, '#')))
            print('{}{}'.format(pre, label), end='')
            print('{}'.format(color), end='')
            for i, parameter in enumerate(param_list):
                if i == 0:
                    print('{}'.format(parameter), end='')
                elif not i % 4:
                    print(',\n{}{}{}'.format(pre, ' '.ljust(len(label), ' '), parameter), end='')
                else:
                    print(', {}'.format(parameter), end='')
            print('{}'.format(color_reset))

    def print_param_table(self, param_name: str, short: bool = True) -> None:
        """
        Print human friendly table of specified parameters.

        :param param_name: Target parameter key name.
        :param short: Print short gpu first if True
        """
        if not self.is_amd_readable(): return
        param_table_definitions = {'pp_features': {'func': self.read_gpu_pp_features, 'name': 'PP Feature'},
                                   'clinfo': {'func': None, 'name': 'CLINFO'},
                                   'pstate': {'func': None, 'name': 'P-State'},
                                   'ppm': {'func': self.read_gpu_ppm_table, 'name': 'PPM'}}
        if param_name not in param_table_definitions: return

        pre = '   '
        color = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['data']
        color_reset = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['reset']

        param_details = param_table_definitions[param_name]
        read_data = param_details['func'](return_data=True) if param_details['func'] else None

        if short: self.print(short=True, newline=False)
        title_str = '{} {} Table Data '.format('#'.ljust(3, '#'), param_details['name'])
        print('{}{}{}'.format(pre, title_str, '#'.ljust(50 - len(title_str), '#')))
        if param_name == 'clinfo':
            item_count = 0
            if self.prm.compute:
                for ocl_param_name, ocl_param_label in self._GPU_CLINFO_Labels.items():
                    if self.get_clinfo_value(ocl_param_name):
                        item_count += 1
                        print('{}: {}{}{}'.format(ocl_param_label, color,
                                                  self.get_clinfo_value(ocl_param_name), color_reset))
            if not item_count:
                print('{}{}No {} Data Available{}'.format(pre, color, param_details['name'], color_reset))
            return
        if param_name == 'pstate':
            self.read_gpu_pstates()
            self.print_pstates()
            return
        if read_data:
            for line in read_data.split('\n'):
                if line.strip('\n'):
                    print('{}{}{}{}'.format(pre, color, line.strip('\n'), color_reset))
        else:
            print('{}{}No {} Data Available{}'.format(pre, color, param_details['name'], color_reset))

    def print_pstates(self) -> None:
        """
        Print human friendly table of p-states.
        """
        if not self.is_amd_readable(): return

        info_printed = False
        color = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['data']
        active_color = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['green']
        color_reset = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['reset']
        pre = '   '
        # DPM States
        if self.param_is_active('pp_od_clk_voltage'):
            info_printed = True
            if self.prm.gpu_type == GpuType.CurvePts:
                print('{}{}{}'.format(pre, '', '#'.ljust(50, '#')))
                print('{}DPM States:'.format(pre))
                print('{}SCLK: {:<17} MCLK:{}'.format(pre, ' ', color))
                for ps_num, ps_freq in self.sclk_dpm_state.items():
                    print('{} {:>1}:  {:<8}            '.format(pre, ps_num, ps_freq), end='')
                    if ps_num in self.mclk_dpm_state:
                        print('{:3>}:  {:<8}'.format(ps_num, self.mclk_dpm_state[ps_num]))
                    else:
                        print('')

            # pp_od_clk_voltage states
            print('{}{}{}{}'.format(pre, color_reset, '', '#'.ljust(50, '#')))
            print('{}PP OD States:'.format(pre))
            print('{}SCLK: {:<17} MCLK:{}'.format(pre, ' ', color))
            for ps_num, ps_vals in self.sclk_state.items():
                print('{} {:>1}:  {:<8}  {:<8}  '.format(pre, ps_num, ps_vals[0], ps_vals[1]), end='')
                if ps_num in self.mclk_state:
                    print('{:3>}:  {:<8}  {:<8}'.format(ps_num, self.mclk_state[ps_num][0], self.mclk_state[ps_num][1]))
                else:
                    print('')
            if self.prm.gpu_type == GpuType.CurvePts:
                # Curve points
                print('{}{}{}{}'.format(pre, color_reset, '', '#'.ljust(50, '#')))
                print('{}VDDC_CURVE:{}'.format(pre, color))
                for vc_index, vc_vals in self.vddc_curve.items():
                    print('{} {}: {}'.format(pre, vc_index, vc_vals))
            print('{}'.format(color_reset), end='')
        if self.all_pstates:
            # clock_name: {ps_num: {'value': ps_val, 'state': ps_sts}}
            info_printed = True
            print('{}{}{}{}'.format(pre, color_reset, '', '#'.ljust(50, '#')))
            print('{}All Pstates:'.format(pre))
            for clock_name, pstates in self.all_pstates.items():
                print('{}{}:{}'.format(pre, clock_name, color))
                for i, (ps, ps_data) in enumerate(pstates.items()):
                    cur_color = active_color if ps_data['state'] else color
                    freq = '*' + ps_data['value'] if GUT_CONST.no_markup and ps_data['state'] else ps_data['value']
                    if not i: print('{}{}{}{}: {}{}'.format(pre, pre, cur_color, ps, freq, color), end='')
                    else: print(', {}{}: {}{}'.format(cur_color, ps, freq, color), end='')
                print('{}'.format(color_reset))
            print('{}'.format(color_reset), end='')
        if not info_printed:
            print('{}{}No P-State Data Available{}'.format(pre, color, color_reset))

    def get_key_description(self, filename: str) -> Tuple[str, str]:
        """
        Used in the printing of raw reading of GPU.  It adds details about key word and descriptions for
        file found in driver related paths.

        :param filename: Name of driver file.
        :return: Tuple of the key and description as color annotated strings.
        """
        active_color = color = self.mark_up_codes['none']
        color_reset = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['reset']
        if not GUT_CONST.no_markup: active_color = self.mark_up_codes['green']
        if filename == 'pp_od_clk_voltage':
            return 'pp_od_clk_voltage', '{}read/write driver file{}'.format(active_color, color_reset)
        for sensor_dict in self._sensor_details.values():
            for sensor_type_dict in sensor_dict.values():
                for (sensor_key, sensor_key_dict) in sensor_type_dict.items():
                    for sensor_files in sensor_key_dict['sensor']:
                        if re.match(PATTERNS['InputLabelX'], filename):
                            for sensor_filename in sensor_files:
                                if re.match(PATTERNS['InputLabelX'], sensor_filename):
                                    if not GUT_CONST.no_markup: color = self.mark_up_codes['green']
                                    description = 'Input/Label Pair'
                                    return sensor_key, '{}{}{}'.format(color, description, color_reset)
                        else:
                            if filename in sensor_files:
                                if sensor_key in self._GPU_Param_Labels:
                                    if not GUT_CONST.no_markup: color = self.mark_up_codes['green']
                                    description = self._GPU_Param_Labels[sensor_key]
                                    return sensor_key, '{}{}{}'.format(color, description.strip(), color_reset)
                                if not GUT_CONST.no_markup: color = self.mark_up_codes['yellow']
                                description = '{}Ignored by gpu-utils{}'.format(color, color_reset)
                                return sensor_key, description
        if not GUT_CONST.no_markup: color = self.mark_up_codes['yellow']
        return 'None', '{}Not defined in gpu-utils{}'.format(color, color_reset)

    def print_raw(self) -> None:
        """
        Formatted print of raw read of all available GPU driver files.
        """
        color = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['data']
        label_color = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['label']
        color_reset = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['reset']
        self.print(short=True)
        print('{} Raw Diver File Data {}'.format('#'.ljust(3, '#'), '#'.ljust(26, '#')))
        for sensor_type, sensors in self.raw.items():
            label_length = len(sensor_type) + 2 + 3
            print('{}{} {} {}{}'.format('#'.ljust(3, '#'), label_color, sensor_type, color_reset,
                                        '#'.ljust(50 - label_length, '#')))
            for name, value in sensors.items():
                (sensor_key, description) = self.get_key_description(name)
                print('### File: {}, SensorKey: {}, Label: {}'.format(name, sensor_key, description))
                for line in value.split('\n'):
                    print('{}    {}{}'.format(color, line, color_reset))
        print('{}\n'.format('#'.ljust(50, '#')))

    def print(self, short: bool = False, newline: bool = True) -> None:
        """
        Display ls like listing function for GPU parameters.

        :param short:  Display short listing
        :param newline:  Display terminating newline if True
        """
        color_reset: str = ''
        for param_name, param_label in self._GPU_Param_Labels.items():
            if short and param_name not in self.short_list:
                continue

            # Hard limits on what types/vendors can print what params
            try:
                if param_name in GpuItem.vendor_skip_lists[self.prm.vendor]:
                    continue
            except KeyError:
                pass
            if self.prm.gpu_type in (GpuType.LegacyAPU, GpuType.APU):
                if param_name in self._fan_item_list:
                    continue

            # Situations where parameter limits can be overridden by force_all
            if not GUT_CONST.force_all:
                if param_name in GpuItem.amd_type_skip_lists[self.prm.gpu_type]:
                    continue
                if not self.prm.readable and param_name not in self.GPU_NC_Param_List:
                    continue
                if not self.param_is_active(param_name):
                    continue

            color = self.mark_up_codes['none']
            color_reset = self.mark_up_codes['none'] if GUT_CONST.no_markup else self.mark_up_codes['reset']
            pre = '' if param_name == 'card_num' else '   '
            if re.search(r'sep\d', param_name):
                print('{}{}'.format(pre, param_label.ljust(50, param_label)))
                continue
            if param_name == 'unique_id':
                if self.prm.unique_id is None:
                    continue
            if isinstance(self.get_params_value(param_name), float):
                if not GUT_CONST.no_markup: color = self.mark_up_codes['data']
                print('{}{}: {}{:.3f}{}'.format(pre, param_label, color,
                                                self.get_params_value(param_name), color_reset))
            elif isinstance(self.get_params_value(param_name), dict):
                if not GUT_CONST.no_markup: color = self.mark_up_codes['data']
                param_dict = self.get_params_value(param_name)
                print('{}{}: {}{}{}'.format(pre, param_label, color,
                                            {key: param_dict[key] for key in sorted(param_dict)}, color_reset))
            elif param_name == 'vendor':
                vendor = self.get_params_value(param_name)
                if not GUT_CONST.no_markup:
                    if vendor.name == 'AMD': color = self.mark_up_codes['amd']
                    elif vendor.name == 'NVIDIA': color = self.mark_up_codes['nvidia']
                    elif vendor.name == 'INTEL': color = self.mark_up_codes['intel']
                    else: color = self.mark_up_codes['other']
                print('{}{}: {} {} {}'.format(pre, param_label, color, vendor, color_reset))
            elif self.get_params_value(param_name) == '':
                if not GUT_CONST.no_markup: color = self.mark_up_codes['data']
                print('{}{}: {}{}{}'.format(pre, param_label, color, None, color_reset))
            else:
                if not GUT_CONST.no_markup: color = self.mark_up_codes['data']
                print('{}{}: {}{}{}'.format(pre, param_label, color, self.get_params_value(param_name), color_reset))
        self.print_disabled_params()
        print('{}'.format(color_reset), end='')
        if newline: print('')

    def get_plot_data(self) -> dict:
        """
        Return a dictionary of dynamic gpu parameters used by gpu-plot to populate a df.

        :return: Dictionary of GPU state info for plot data.
        """
        gpu_state = {'Time': str(self.get_params_value('read_time').strftime(GUT_CONST.TIME_FORMAT)),
                     'Card#': int(self.prm.card_num)}

        for table_item in self.table_parameters:
            gpu_state[table_item] = format_table_value(self.get_params_value(table_item), table_item)
        return gpu_state


class GpuList:
    """
    A list of GpuItem indexed with uuid.  It also contains a table of parameters used for status reporting.
    """
    def __init__(self) -> None:
        self.list: Dict[str, GpuItem] = {}
        self.opencl_map: dict = {}
        self.amd_featuremask: Optional[int] = None
        self.current_amd_featuremask: Union[str, int, None] = None
        self.amd_wattman: bool = False
        self.amd_writable: bool = False
        self.nv_readwritable: bool = False

    def __repr__(self) -> str:
        return str(self.list)

    def __str__(self) -> str:
        num_gpus = self.num_gpus()

        def num_is_are(num: int, singular: str = 'is', plural: str = 'are') -> Tuple[int, str]:
            """
            Determine if singular or plural references are needed.  Return correct version.

            :param num: Quantity
            :param singular: Singular version of word
            :param plural: Plural version of word
            :return: Either singular or plural version of word.
            """
            return num, plural if num != 1 else singular

        return 'Total of {} {}: {} {} rw, {} {} r-only, and {} {} w-only\n'.format(
            *num_is_are(num_gpus['total'], 'GPU', 'GPUs'),
            *num_is_are(num_gpus['rw']),
            *num_is_are(num_gpus['r-only']),
            *num_is_are(num_gpus['w-only']))

    def __getitem__(self, uuid: str) -> GpuItem:
        if uuid in self.list:
            return self.list[uuid]
        raise KeyError('KeyError: invalid uuid: {}'.format(uuid))

    def __setitem__(self, uuid: str, value: GpuItem) -> None:
        self.list[uuid] = value

    def __iter__(self) -> Generator[GpuItem, None, None]:
        for value in self.list.values():
            yield value

    def items(self) -> Generator[Union[str, GpuItem], None, None]:
        """
        Get uuid, gpu pairs from a GpuList object.

        :return:  uuid, gpu pair
        """
        for key, value in self.list.items():
            yield key, value

    def uuids(self) -> Generator[str, None, None]:
        """
        Get uuids of the GpuList object.

        :return: uuids from the GpuList object.
        """
        for key in self.list:
            yield key

    def gpus(self) -> Generator[GpuItem, None, None]:
        """
        Get GpuItems from a GpuList object.

        :return: GpuUItem
        """
        return self.__iter__()

    def add(self, gpu_item: GpuItem) -> None:
        """
        Add given GpuItem to the GpuList.

        :param gpu_item:  Item to be added
        """
        self[gpu_item.prm.uuid] = gpu_item
        LOGGER.debug('Added GPU Item %s to GPU List', gpu_item.prm.uuid)

    def get_pcie_map(self) -> dict:
        """
        Get mapping of card number to pcie address as dict.

        :return: dict of num: pcieid
        """
        pcie_dict = {}
        for gpu in self.gpus():
            pcie_dict.update({gpu.prm.card_num: gpu.prm.pcie_id})
        return pcie_dict

    def wattman_status(self) -> str:
        """
        Display Wattman status.

        :return:  Status string
        """
        LOGGER.debug('AMD featuremask: %s', hex(self.amd_featuremask))
        if self.amd_wattman:
            return 'Wattman features enabled: {}'.format(hex(self.amd_featuremask))
        return 'Wattman features not enabled: {}, See README file.'.format(hex(self.amd_featuremask))

    @staticmethod
    def get_gpu_pci_list() -> Optional[List[str]]:
        """
        Use call to lspci to get a list of pci addresses of all GPUs.

        :return: List of GPU pci addresses or None.
        """
        pci_list = []
        try:
            lspci_output = subprocess.check_output(GUT_CONST.cmd_lspci, shell=False).decode().split('\n')
        except (subprocess.CalledProcessError, OSError) as except_err:
            print('Error [{}]: lspci failed to find GPUs'.format(except_err))
            return None

        for lspci_line in lspci_output:
            if re.search(PATTERNS['PCI_GPU'], lspci_line):
                if re.search(PATTERNS['NOT_PCI_GPU'], lspci_line):
                    LOGGER.debug('Excluded possible GPU pci: %s', lspci_line)
                    continue
                LOGGER.debug('Found GPU pci: %s', lspci_line)
                pciid = re.search(GUT_CONST.PATTERNS['PCI_ADD'], lspci_line)
                if pciid: pci_list.append(pciid.group(0))
        return pci_list

    def set_gpu_list(self, clinfo_flag: bool = False) -> bool:
        """
        Use lspci to populate list of all installed GPUs.

        :return: True on success
        """
        if not GUT_CONST.cmd_lspci: return False
        if clinfo_flag:
            self.read_gpu_opencl_data()
            LOGGER.debug('OpenCL map: %s', self.opencl_map)

        # Check AMD writability
        try:
            self.amd_featuremask = GUT_CONST.read_amdfeaturemask()
        except FileNotFoundError:
            self.amd_wattman = self.amd_writable = False

        # TODO: Need to research on specifically which bits are required to write to GPU.
        #self.amd_wattman = self.amd_writable = self.amd_featuremask & 0x4000
        self.amd_wattman = self.amd_writable = (self.amd_featuremask == int(0xffff7fff) or
                                                self.amd_featuremask == int(0xfff7ffff) or
                                                self.amd_featuremask == int(0xffffffff) or
                                                self.amd_featuremask == int(0xfffd7fff))

        # Check NV read/writability
        if GUT_CONST.cmd_nvidia_smi:
            self.nv_readwritable = True

        pcie_ids = self.get_gpu_pci_list()
        if not pcie_ids:
            print('Error [empty list]: lspci failed to find GPUs')
            return False

        LOGGER.debug('Found %s GPUs', len(pcie_ids))
        for pcie_id in pcie_ids:
            # Initial GPU Item
            gpu_uuid = uuid4().hex
            self.add(GpuItem(gpu_uuid))
            LOGGER.debug('GPU: %s', pcie_id)
            gpu_name = 'UNKNOWN'
            driver_module = 'UNKNOWN'
            card_path = ''
            sys_card_path = ''
            hwmon_path = ''
            readable = writable = compute = False
            gpu_type = GpuType.Undefined
            vendor = GpuVendor.Undefined
            opencl_device_version = None if clinfo_flag else 'UNKNOWN'

            # Get more GPU details from lspci -k -s
            cmd_str = '{} -k -s {}'.format(GUT_CONST.cmd_lspci, pcie_id)
            try:
                lspci_items = subprocess.check_output(shlex_split(cmd_str), shell=False).decode().split('\n')
            except (subprocess.CalledProcessError, OSError) as except_err:
                message = 'Fatal Error [{}]: Can not get GPU details with lspci.'.format(except_err)
                LOGGER.debug(message)
                print(message, file=sys.stderr)
                sys.exit(-1)
            LOGGER.debug('lspci output items:\n %s', lspci_items)

            # Get Long GPU Name
            gpu_name_items = lspci_items[0].split(': ', maxsplit=1)
            if len(gpu_name_items) >= 2:
                gpu_name = gpu_name_items[1]
            # Check for Fiji ProDuo
            if re.search('Fiji', gpu_name):
                if re.search(r'Radeon Pro Duo', lspci_items[1].split('[AMD/ATI]')[1]):
                    gpu_name = 'Radeon Fiji Pro Duo'
            LOGGER.debug('gpu_name: [%s]', gpu_name)

            # Get GPU brand: AMD, INTEL, NVIDIA, ASPEED
            if re.search(PATTERNS['AMD_GPU'], gpu_name):
                vendor = GpuVendor.AMD
                gpu_type = GpuType.Supported
            elif re.search(PATTERNS['NV_GPU'], gpu_name):
                vendor = GpuVendor.NVIDIA
                if GUT_CONST.cmd_nvidia_smi:
                    readable = True
                gpu_type = GpuType.Supported
            elif re.search(PATTERNS['INTC_GPU'], gpu_name):
                vendor = GpuVendor.INTEL
                gpu_type = GpuType.Unsupported
            elif re.search(PATTERNS['ASPD_GPU'], gpu_name):
                vendor = GpuVendor.ASPEED
                gpu_type = GpuType.Unsupported
                readable = True
            elif re.search(PATTERNS['MTRX_GPU'], gpu_name):
                vendor = GpuVendor.MATROX
                gpu_type = GpuType.Unsupported

            # Set compute flag
            if self.opencl_map:
                if pcie_id in self.opencl_map:
                    if 'device_version' in self.opencl_map[pcie_id]:
                        opencl_device_version = self.opencl_map[pcie_id]['device_version']
                        compute = True
                    else:
                        compute = False
            else:
                compute = 'Unknown' if not GUT_CONST.cmd_clinfo else False

            # Get Driver Name
            for lspci_line in lspci_items:
                if re.search(r'([kK]ernel)', lspci_line):
                    driver_module_items = lspci_line.split(': ')
                    if len(driver_module_items) >= 2:
                        driver_module = driver_module_items[1].strip()

            # Get full card path
            device_dirs = glob(os.path.join(GUT_CONST.card_root, 'card?/device'))
            # Match system device directory to pcie ID.
            for device_dir in device_dirs:
                sysfspath = str(Path(device_dir).resolve())
                LOGGER.debug('sysfpath: %s\ndevice_dir: %s', sysfspath, device_dir)
                if pcie_id in (sysfspath[-7:], sysfspath[-12:]):
                    card_path = device_dir
                    sys_card_path = sysfspath
                    LOGGER.debug('card_path set to: %s', device_dir)

            # No card path could be found.  Set readable/writable to False and type to Unsupported
            if not card_path:
                LOGGER.debug('card_path not set for: %s', pcie_id)
                LOGGER.debug('GPU[%s] type set to Unsupported', gpu_uuid)
                gpu_type = GpuType.Unsupported
                readable = writable = False
                try_path = '/sys/devices/pci*:*/'
                sys_pci_dirs = None
                for _ in range(6):
                    if re.fullmatch(GUT_CONST.PATTERNS['PCI_ADD_SHRT'], pcie_id):
                        search_path = os.path.join(try_path, '????:{}'.format(pcie_id))
                    else:
                        search_path = os.path.join(try_path, pcie_id)
                    sys_pci_dirs = glob(search_path)
                    if sys_pci_dirs:
                        # Found a match
                        break
                    try_path = os.path.join(try_path, '????:??:??.?')
                if not sys_pci_dirs:
                    LOGGER.debug('/sys/device file search found no match to pcie_id: %s', pcie_id)
                else:
                    if len(sys_pci_dirs) > 1:
                        LOGGER.debug('/sys/device file search found multiple matches to pcie_id %s:\n%s',
                                     pcie_id, sys_pci_dirs)
                    else:
                        LOGGER.debug('/sys/device file search found match to pcie_id %s:\n%s',
                                     pcie_id, sys_pci_dirs)
                    sys_card_path = sys_pci_dirs[0]

            # Get full hwmon path
            if card_path:
                LOGGER.debug('Card dir [%s] contents:\n%s', card_path, list(os.listdir(card_path)))
                hw_file_srch = glob(os.path.join(card_path, GUT_CONST.hwmon_sub) + '?')
                LOGGER.debug('HW file search: %s', hw_file_srch)
                if len(hw_file_srch) > 1:
                    GUT_CONST.process_message('More than one hwmon file found: {}'.format(hw_file_srch))
                    LOGGER.debug('More than one hwmon file found: %s', hw_file_srch)
                elif len(hw_file_srch) == 1:
                    hwmon_path = hw_file_srch[0]
                    LOGGER.debug('HW dir [%s] contents:\n%s', hwmon_path, list(os.listdir(hwmon_path)))

            # Check AMD write capability
            if vendor == GpuVendor.AMD and card_path:
                pp_od_clk_voltage_file = os.path.join(card_path, 'pp_od_clk_voltage')
                if os.path.isfile(pp_od_clk_voltage_file):
                    pp_od_file_details = 'Exists'
                    try:
                        with open(pp_od_clk_voltage_file, 'r', encoding='utf-8') as file_ptr:
                            pp_od_file_details = file_ptr.read()
                    except OSError as except_err:
                        pp_od_file_details = '{} not readable'.format(pp_od_clk_voltage_file)
                        self[gpu_uuid].disable_param_read(('pp_od_clk_voltage', 'sclk_f_range',
                                                           'mclk_f_range', 'vddc_range'))
                        message = 'Error: system support issue for {}: [{}]'.format(pcie_id, except_err)
                        LOGGER.debug(message)
                        print(message)
                        gpu_type = GpuType.Unsupported
                        writable = False
                    else:
                        LOGGER.debug('%s exists, opened, and read.', pp_od_clk_voltage_file)
                        if not pp_od_file_details.strip().strip('\n'):
                            self[gpu_uuid].disable_param_read(('pp_od_clk_voltage', 'sclk_f_range',
                                                               'mclk_f_range', 'vddc_range'))
                            LOGGER.debug('%s exists, but empty on read.', pp_od_clk_voltage_file)
                            gpu_type = GpuType.Unsupported
                            readable = True
                            writable = False
                        else:
                            LOGGER.debug('%s exists, and is readable.', pp_od_clk_voltage_file)
                            gpu_type = GpuType.Supported
                            readable = True
                            if self.amd_writable:
                                writable = True
                    finally:
                        LOGGER.debug('%s contents:\n%s', pp_od_clk_voltage_file, pp_od_file_details)
                if GpuItem.is_apu(gpu_name):
                    readable = True
                    gpu_type = GpuType.LegacyAPU
                if os.path.isfile(os.path.join(card_path, 'power_dpm_state')):
                    if os.path.isfile(os.path.join(card_path, 'pp_dpm_sclk')):
                        # if no pp_od_clk_voltage but has pp_dpm_sclk, assume modern
                        readable = True
                        gpu_type = GpuType.APU if GpuItem.is_apu(gpu_name) else GpuType.Modern
                    else:
                        # if no pp_od_clk_voltage or pp_dpm_sclk but has power_dpm_state, assume legacy
                        if not GpuItem.is_apu(gpu_name):
                            readable = True
                            gpu_type = GpuType.Legacy

                if not os.path.isfile(pp_od_clk_voltage_file):
                    self[gpu_uuid].disable_param_read(('pp_od_clk_voltage', 'sclk_f_range',
                                                       'mclk_f_range', 'vddc_range'))
                    LOGGER.debug('%s file does not exist', pp_od_clk_voltage_file)

            # Set GPU parameters
            self[gpu_uuid].populate_prm_from_dict({'pcie_id': pcie_id, 'model': gpu_name,
                                                   'vendor': vendor,
                                                   'driver': driver_module, 'card_path': card_path,
                                                   'sys_card_path': sys_card_path, 'gpu_type': gpu_type,
                                                   'hwmon_path': hwmon_path, 'readable': readable,
                                                   'writable': writable, 'compute': compute,
                                                   'compute_platform': opencl_device_version})
            LOGGER.debug('Card flags: readable: %s, writable: %s, type: %s',
                         readable, writable, self[gpu_uuid].prm.gpu_type)

            self[gpu_uuid].read_gpu_pp_features()
            # Read GPU ID
            rdata = self[gpu_uuid].read_gpu_sensor('id', vendor=GpuVendor.PCIE, sensor_type='DEVICE')
            if rdata:
                self[gpu_uuid].set_params_value('id', rdata)
            if clinfo_flag:
                if pcie_id in self.opencl_map:
                    self[gpu_uuid].set_clinfo_values(self.opencl_map[pcie_id])
        return True

    def read_gpu_opencl_data(self) -> bool:
        """
        Use clinfo system call to get openCL details for relevant GPUs.

        :return:  Returns True if successful
        """
        # Check access to clinfo command
        if not GUT_CONST.cmd_clinfo: return False

        # Run the clinfo command
        with subprocess.Popen(shlex_split('{} --raw'.format(GUT_CONST.cmd_clinfo)),
                              shell=False, stdout=subprocess.PIPE) as cmd:

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
            ocl_pcie_id: Optional[str] = None
            ocl_index: Optional[str] = None
            ocl_vendor: Optional[str] = None
            ocl_pcie_slot_id: Optional[str] = None
            ocl_pcie_bus_id: Optional[str] = None
            temp_map = init_temp_map()

            # Read each line from clinfo --raw
            for line in cmd.stdout:
                linestr = line.decode('utf-8').strip()
                if not linestr: continue
                if linestr[0] != '[': continue
                line_items = linestr.split(maxsplit=2)
                if len(line_items) != 3: continue
                cl_vendor, cl_index = tuple(re.sub(r'[\[\]]', '', line_items[0]).split('/'))
                if cl_index == '*': continue
                if not ocl_index:
                    ocl_index = cl_index
                    ocl_vendor = cl_vendor
                    ocl_pcie_slot_id = ocl_pcie_bus_id = None

                # If new cl_index, then update opencl_map
                if cl_vendor != ocl_vendor or cl_index != ocl_index:
                    # Update opencl_map with dict variables when new index is encountered.
                    self.opencl_map.update({ocl_pcie_id: temp_map})
                    LOGGER.debug('cl_vendor: %s, cl_index: %s, pcie_id: %s',
                                 ocl_vendor, ocl_index, self.opencl_map[ocl_pcie_id])

                    # Initialize dict variables
                    ocl_index = cl_index
                    ocl_vendor = cl_vendor
                    ocl_pcie_id = ocl_pcie_bus_id = ocl_pcie_slot_id = None
                    temp_map = init_temp_map()

                param_str = line_items[1]
                # Check item in clinfo_keywords
                for clinfo_keyword, opencl_map_keyword in ocl_keywords.items():
                    if clinfo_keyword in param_str:
                        temp_map[opencl_map_keyword] = line_items[2].strip()
                        LOGGER.debug('openCL map %s: [%s]', clinfo_keyword, temp_map[opencl_map_keyword])
                        continue

                # PCIe ID related clinfo_keywords
                # Check for AMD pcie_id details
                if 'CL_DEVICE_TOPOLOGY' in param_str:
                    ocl_pcie_id = (line_items[2].split()[1]).strip()
                    LOGGER.debug('AMD ocl_pcie_id [%s]', ocl_pcie_id)
                    continue

                # Check for NV pcie_id details
                if 'CL_DEVICE_PCI_BUS_ID_NV' in param_str:
                    ocl_pcie_bus_id: Optional[str] = str(hex(int(line_items[2].strip())))
                    if ocl_pcie_slot_id is not None:
                        ocl_pcie_id = '{}:{}.0'.format(ocl_pcie_bus_id[2:].zfill(2), ocl_pcie_slot_id[2:].zfill(2))
                        ocl_pcie_slot_id = ocl_pcie_bus_id = None
                        LOGGER.debug('NV ocl_pcie_id [%s]', ocl_pcie_id)
                    continue
                if 'CL_DEVICE_PCI_SLOT_ID_NV' in param_str:
                    ocl_pcie_slot_id = hex(int(line_items[2].strip()))
                    if ocl_pcie_bus_id is not None:
                        ocl_pcie_id = '{}:{}.0'.format(ocl_pcie_bus_id[2:].zfill(2), ocl_pcie_slot_id[2:].zfill(2))
                        ocl_pcie_slot_id = ocl_pcie_bus_id = None
                        LOGGER.debug('NV ocl_pcie_id [%s]', ocl_pcie_id)
                    continue

                # Check for INTEL pcie_id details
                # TODO: Don't know how extract Intel pcie_id details.

        self.opencl_map.update({ocl_pcie_id: temp_map})
        return True

    def num_vendor_gpus(self, compatibility: GpuCompatibility = GpuCompatibility.ALL) -> Dict[str, int]:
        """
        Return the count of GPUs by vendor.  Counts total by default, but can also by rw, ronly, or wonly.

        :param compatibility: Only count vendor GPUs if True.
        :return: Dictionary of GPU counts
        """
        try:
            _ = compatibility.name
        except AttributeError as error:
            raise AttributeError('Error: {} not a valid compatibility name: [{}]'.format(
                                 compatibility, GpuCompatibility)) from error
        results_dict = {}
        for gpu in self.gpus():
            if compatibility == GpuCompatibility.ReadWrite:
                if not gpu.prm.readable or not gpu.prm.writable:
                    continue
            if compatibility == GpuCompatibility.ReadOnly:
                if not gpu.prm.readable:
                    continue
            if compatibility == GpuCompatibility.WriteOnly:
                if not gpu.prm.writable:
                    continue
            if gpu.prm.vendor.name not in results_dict:
                results_dict.update({gpu.prm.vendor.name: 1})
            else:
                results_dict[gpu.prm.vendor.name] += 1
        return results_dict

    def num_gpus(self, vendor: GpuVendor = GpuVendor.ALL) -> Dict[str, int]:
        """
        Return the count of GPUs by total, rw, r-only or w-only.

        :param vendor: Only count vendor GPUs of specific vendor or all vendors by default.
        :return: Dictionary of GPU counts
        """
        try:
            vendor_name = vendor.name
        except AttributeError as error:
            raise AttributeError('Error: {} not a valid vendor name: [{}]'.format(
                vendor, GpuVendor.list())) from error
        results_dict = {'vendor': vendor_name, 'total': 0, 'rw': 0, 'r-only': 0, 'w-only': 0}
        for gpu in self.gpus():
            if vendor != GpuVendor.ALL:
                if vendor != gpu.prm.vendor:
                    continue
            if gpu.prm.readable and gpu.prm.writable:
                results_dict['rw'] += 1
            elif gpu.prm.readable:
                results_dict['r-only'] += 1
            elif gpu.prm.writable:
                results_dict['w-only'] += 1
            results_dict['total'] += 1
        return results_dict

    def list_gpus(self, reverse: bool = False, vendor: GpuVendor = GpuVendor.ALL, gpu_type: GpuType = GpuType.ALL,
                  compatibility: GpuCompatibility = GpuCompatibility.ALL) -> 'class GpuList':
        """
        Return GPU_Item of GPUs.  Contains all by default, but can be a subset with vendor and compatibility args.
        Only one flag should be set.

        :param reverse: return items not matching conditions.
        :param vendor: Only count vendor GPUs or ALL by default.
        :param gpu_type: Only count type GPUs or ALL by default.
        :param compatibility: Only count GPUs with specified compatibility (all, readable, writable)
        :return: GpuList of compatible GPUs
        """
        try:
            _ = compatibility.name
        except AttributeError as error:
            raise AttributeError('Error: {} not a valid compatibility name: {}'.format(
                compatibility, GpuCompatibility.list())) from error
        try:
            _ = gpu_type.name
        except AttributeError as error:
            raise AttributeError('Error: {} not a valid type name: [{}]'.format(
                gpu_type, GpuType.list())) from error
        try:
            _ = vendor.name
        except AttributeError as error:
            raise AttributeError('Error: {} not a valid vendor name: [{}]'.format(
                vendor, GpuVendor.list())) from error

        result_list = GpuList()
        for uuid, gpu in self.items():
            if vendor != GpuVendor.ALL:
                if ((reverse and (vendor == gpu.prm.vendor)) or
                   (not reverse and (vendor != gpu.prm.vendor))): continue
            if gpu_type != GpuType.ALL:
                if ((reverse and (gpu_type == gpu.prm.gpu_type)) or
                   (not reverse and (gpu_type != gpu.prm.gpu_type))): continue
            if compatibility != GpuCompatibility.ALL:
                if compatibility == GpuCompatibility.Readable:
                    if ((reverse and gpu.prm.readable) or
                       (not reverse and not gpu.prm.readable)): continue
                elif compatibility == GpuCompatibility.Writable:
                    if ((reverse and gpu.prm.writable) or
                       (not reverse and not gpu.prm.writable)): continue
            result_list[uuid] = gpu

        return result_list

    def read_raw_sensors(self) -> None:
        """
        Raw read of all driver files for all GPUs.
        """
        for gpu in self.gpus():
            gpu.read_raw_sensors()

    def read_gpu_ppm_table(self) -> None:
        """
        Read GPU ppm data and populate GpuItem.
        """
        for gpu in self.gpus():
            if gpu.prm.readable:
                gpu.read_gpu_ppm_table()

    def print_param_table(self, param_name) -> None:
        """
        Print the GpuItem ppm data.
        """
        for gpu in self.gpus():
            gpu.print_param_table(param_name=param_name)

    def print_pstates(self) -> None:
        """
        Print the GpuItem pstates data.
        """
        for gpu in self.gpus():
            gpu.print_pstates()

    def read_gpu_pstates(self) -> None:
        """
        Read GPU p-state data and populate GpuItem.
        """
        for gpu in self.gpus():
            if gpu.prm.readable:
                gpu.read_gpu_pstates()

    def read_gpu_sensor_set(self, data_type: SensorSet = SensorSet.All) -> None:
        """
        Read sensor data from all GPUs in self.list.

        :param data_type: Specifies the sensor set to use in the read.
        """
        for gpu in self.gpus():
            if gpu.prm.readable or GUT_CONST.force_all:
                gpu.read_gpu_sensor_set(data_type)

    # Printing Methods follow.
    def print_raw(self) -> None:
        """
        Print raw read data for all GPUs.
        """
        for gpu in self.gpus():
            gpu.print_raw()

    def print(self, short: bool = False, long: bool = False) -> None:
        """
        Print all GpuItem.

        :param short: If true, print short report
        :param long: If true, print long report
        """
        for gpu in self.gpus():
            if short: gpu.print(short=short)
            elif long:
                gpu.print(newline=False)
                for report_name in ('pp_features', 'ppm', 'pstate', 'clinfo'):
                    gpu.print_param_table(report_name, short=False)
                print('')
            else: gpu.print()

    def print_table(self, title: Optional[str] = None) -> bool:
        """
        Print table of parameters.

        :return: True if success
        """
        color = GpuItem.mark_up_codes['bold'] + GpuItem.mark_up_codes['cyan']
        color_reset = GpuItem.mark_up_codes['reset']
        table_width: int = 20
        if self.num_gpus()['total'] < 1: return False

        if title: print('{}{}{}'.format(color, title, color_reset))

        print('┌', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.gpus():
            print('┬', '─'.ljust(table_width, '─'), sep='', end='')
        print('┐')

        print('│{}{}{}'.format(color, 'Card #'.ljust(13, ' '), color_reset), sep='', end='')
        for gpu in self.gpus():
            card_str = 'card{}'.format(gpu.prm.card_num).center(table_width)
            print('│{}{:<20}{}'.format(color, card_str, color_reset), end='')
        print('│')

        print('├', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.gpus():
            print('┼', '─'.ljust(table_width, '─'), sep='', end='')
        print('┤')

        for table_item in GpuItem.table_parameters:
            print('│{}{:<13}{}'.format(color, str(GpuItem.table_param_labels[table_item])[:13], color_reset), end='')
            for gpu in self.gpus():
                data_value_raw = gpu.get_params_value(table_item)
                data_value_raw = format_table_value(data_value_raw, table_item)
                print('│{:<20}'.format(str(data_value_raw)[:table_width].center(table_width)), end='')
            print('│')

        print('└', '─'.ljust(13, '─'), sep='', end='')
        for _ in self.gpus():
            print('┴', '─'.ljust(table_width, '─'), sep='', end='')
        print('┘')
        return True

    def print_log_header(self, log_file_ptr: TextIO) -> bool:
        """
        Print the log header.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
        """
        if self.num_gpus()['total'] < 1: return False

        # Print Header
        print('Time|Card#', end='', file=log_file_ptr)
        for table_item in GpuItem.table_parameters:
            print('|{}'.format(table_item), end='', file=log_file_ptr)
        print('', file=log_file_ptr)
        return True

    def print_log(self, log_file_ptr: TextIO) -> bool:
        """
        Print the log data.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
        """
        if self.num_gpus()['total'] < 1: return False

        # Print Data
        for gpu in self.gpus():
            print('{}|{}'.format(gpu.get_params_value('read_time').strftime(GUT_CONST.TIME_FORMAT), gpu.prm.card_num),
                  sep='', end='', file=log_file_ptr)
            for table_item in GpuItem.table_parameters:
                print('|{}'.format(re.sub(PATTERNS['MHz'], '', str(gpu.get_params_value(table_item)).strip())),
                      sep='', end='', file=log_file_ptr)
            print('', file=log_file_ptr)
        return True

    def print_plot_header(self, log_file_ptr: IO[Union[str, bytes]]) -> bool:
        """
        Print the plot header.

        :param log_file_ptr: File pointer for target output.
        :return: True if success
        """
        if self.num_gpus()['total'] < 1: return False

        # Print Header
        line_str_item = ['Time|Card#']
        for table_item in GpuItem.table_parameters:
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
        :return: True on success
        """
        if self.num_gpus()['total'] < 1: return False

        # Print Data
        for gpu in self.gpus():
            line_str_item = ['{}|{}'.format(str(gpu.get_params_value('read_time').strftime(GUT_CONST.TIME_FORMAT)),
                                            gpu.prm.card_num)]
            for table_item in GpuItem.table_parameters:
                line_str_item.append('|' + re.sub(PATTERNS['MHz'], '', str(gpu.get_params_value(table_item))).strip())
            line_str_item.append('\n')
            line_str = ''.join(line_str_item)
            log_file_ptr.write(line_str.encode('utf-8'))
        log_file_ptr.flush()
        return True

    def select_gpu(self, card_number: int) -> Optional[GpuItem]:
        """
        Select GPU that matches the given card number.

        :param card_number:  The integer that identifies the GPU.
        :return: GpuItem of the matching GPU or None if no match.
        """
        for gpu in self.gpus():
            if gpu.prm.card_num == card_number:
                return gpu
        return None


# Utility Helper Functions
def print_driver_vendor_summary(gpu_list: GpuList) -> None:
    """
    Display vendor and driver details.

    :param gpu_list: Target list of GPUs for the summary.
    """
    num_gpus = gpu_list.num_vendor_gpus()
    print('Detected GPUs: ', end='')
    for i, (type_name, type_value) in enumerate(num_gpus.items()):
        if i:
            print(', {}: {}'.format(type_name, type_value), end='')
        else:
            print('{}: {}'.format(type_name, type_value), end='')
    print('')
    if 'AMD' in num_gpus:
        GUT_CONST.read_amd_driver_version()
        print('AMD: {}'.format(gpu_list.wattman_status()))
    if 'NV' in num_gpus:
        if GUT_CONST.cmd_nvidia_smi:
            print('NV: nvidia smi: [{}]'.format(GUT_CONST.cmd_nvidia_smi))
        else:
            print('NV: Addon package [nvidia-smi] executable not found.')


def set_mon_plot_compatible_gpu_list(gpu_list: GpuList) -> GpuList:
    """
    Function to select only Monitor/Plot compatible GPUs.

    :return: The resultant list of GPUs
    """
    com_gpu_list = gpu_list.list_gpus(compatibility=GpuCompatibility.Readable)
    com_gpu_list = com_gpu_list.list_gpus(gpu_type=GpuType.Unsupported, reverse=True)
    com_gpu_list = com_gpu_list.list_gpus(gpu_type=GpuType.Undefined, reverse=True)

    return com_gpu_list


def format_table_value(data_value_raw: Any, data_name: str) -> Union[str, int, float]:
    """
    Format fields for monitor table.

    :param data_value_raw:
    :param data_name:
    :return: Formatted data value
    """
    if data_value_raw == 'nan':
        return np_nan
    if isinstance(data_value_raw, float):
        if data_name == 'energy': return '{:.3e}'.format(data_value_raw) if data_value_raw > 0.0000001 else '---'
        return round(data_value_raw, 3)
    if isinstance(data_value_raw, int):
        return data_value_raw
    if isinstance(data_value_raw, str):
        data_value_raw = re.sub(PATTERNS['MHz'], '', data_value_raw).strip()
        if data_value_raw.isnumeric():
            return int(data_value_raw)
    if data_value_raw in {'', None, '-1', 'NA'}:
        return '---'
    return str(data_value_raw)
