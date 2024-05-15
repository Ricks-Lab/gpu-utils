#!/usr/bin/env python3
""" Implementation of Regex expressions for the project.  Expressions will be compiled
    first use.

    Copyright (C) 2024  RicksLab

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
__credits__ = ['']
__copyright__ = 'Copyright (C) 2024 RicksLab'
__license__ = 'GNU General Public License'
__program_name__ = 'gpu-utils'
__maintainer__ = 'RicksLab'
__docformat__ = 'reStructuredText'

import re
# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=logging-format-interpolation
# pylint: disable=consider-using-f-string
# pylint: disable=invalid-name

from enum import Enum, auto
from typing import Dict, Any, Pattern



class PatternKeys(Enum):
    """ Enum object to define keys Patterns.
    """
    HEXRGB = auto()
    PCIIID_L0 = auto()
    PCIIID_L1 = auto()
    PCIIID_L2 = auto()
    NUM_END_IN_ALPHA = auto()
    END_IN_ALPHA = auto()
    ALPHA = auto()
    AMD_FEATURES = auto()
    AMD_GPU = auto()
    NV_GPU = auto()
    INTC_GPU = auto()
    ASPD_GPU = auto()
    MTRX_GPU = auto()
    InputLabelX = auto()
    MHz = auto()
    PPM_CHK = auto()
    PCI_GPU = auto()
    NOT_PCI_GPU = auto()
    PCI_ADD = auto()
    PCI_ADD_LONG = auto()
    PCI_ADD_SHRT = auto()
    PPM_NOTCHK = auto()
    VALID_PS_STR = auto()
    IS_FLOAT = auto()
    DIGITS = auto()
    VAL_ITEM = auto()
    GPU_GENERIC = auto()
    GPUMEMTYPE = auto()

class RegexPatterns:
    """ Class for compile on first use common project regex.
    """
    def __init__(self):
        self.patterns: Dict[PatternKeys, Dict[str, Any]] = {
        PatternKeys.HEXRGB:           {'compiled': None, 'regex': r'^#[\da-f]{6}', 'flags': re.IGNORECASE},
        PatternKeys.PCIIID_L0:        {'compiled': None, 'regex': r'^[\da-f]{4}.*', 'flags': re.IGNORECASE},
        PatternKeys.PCIIID_L1:        {'compiled': None, 'regex': r'^\t[\da-f]{4}.*', 'flags': re.IGNORECASE},
        PatternKeys.PCIIID_L2:        {'compiled': None, 'regex': r'^\t\t[\da-f]{4}.*', 'flags': re.IGNORECASE},
        PatternKeys.NUM_END_IN_ALPHA: {'compiled': None, 'regex': r'\d+[a-z]+$', 'flags': re.IGNORECASE},
        PatternKeys.END_IN_ALPHA:     {'compiled': None, 'regex': r'[a-z]+$', 'flags': re.IGNORECASE},
        PatternKeys.ALPHA:            {'compiled': None, 'regex': r'[a-z]+', 'flags': re.IGNORECASE},
        PatternKeys.AMD_FEATURES:     {'compiled': None, 'regex': r'^(Current pp)*\s*:*\s*features:*\s+', 'flags': re.IGNORECASE},
        PatternKeys.AMD_GPU:          {'compiled': None, 'regex': r'(AMD|ATI)', 'flags': None},
        PatternKeys.NV_GPU:           {'compiled': None, 'regex': r'NVIDIA', 'flags': re.IGNORECASE},
        PatternKeys.INTC_GPU:         {'compiled': None, 'regex': r'INTEL', 'flags': re.IGNORECASE},
        PatternKeys.ASPD_GPU:         {'compiled': None, 'regex': r'ASPEED', 'flags': re.IGNORECASE},
        PatternKeys.MTRX_GPU:         {'compiled': None, 'regex': r'MATROX', 'flags': re.IGNORECASE},
        PatternKeys.InputLabelX:      {'compiled': None, 'regex': r'[a-zA-Z]*(\d|\*)_(input|label)', 'flags': None},
        PatternKeys.MHz:              {'compiled': None, 'regex': r'M[Hh]z', 'flags': None},
        PatternKeys.PPM_CHK:          {'compiled': None, 'regex': r'[*].*', 'flags': None},
        PatternKeys.PCI_GPU:          {'compiled': None, 'regex': r'(VGA|3D|Display)', 'flags': re.IGNORECASE},
        PatternKeys.NOT_PCI_GPU:      {'compiled': None, 'regex': r'Non-?VGA', 'flags': re.IGNORECASE},
        PatternKeys.PCI_ADD:          {'compiled': None, 'regex': r'^(([\da-fA-F]{4}:)?[\da-fA-F]{2}:[\da-fA-F]{2}.[\da-fA-F])', 'flags': None},
        PatternKeys.PCI_ADD_LONG:     {'compiled': None, 'regex': r'^([\da-fA-F]{4}:[\da-fA-F]{2}:[\da-fA-F]{2}.[\da-fA-F])', 'flags': None},
        PatternKeys.PCI_ADD_SHRT:     {'compiled': None, 'regex': r'^([\da-fA-F]{2}:[\da-fA-F]{2}.[\da-fA-F])', 'flags': None},
        PatternKeys.PPM_NOTCHK:       {'compiled': None, 'regex': r'\s+', 'flags': None},
        PatternKeys.VALID_PS_STR:     {'compiled': None, 'regex': r'\d+(\s\d)*', 'flags': None},
        PatternKeys.IS_FLOAT:         {'compiled': None, 'regex': r'[-+]?\d*\.?\d+|[-+]?\d+', 'flags': None},
        PatternKeys.DIGITS:           {'compiled': None, 'regex': r'^\d+\d*$', 'flags': None},
        PatternKeys.VAL_ITEM:         {'compiled': None, 'regex': r'.*_val$', 'flags': None},
        PatternKeys.GPU_GENERIC:      {'compiled': None, 'regex': r'(^\s|intel|amd|nvidia|amd/ati|ati|radeon|\[|])', 'flags': re.IGNORECASE},
        PatternKeys.GPUMEMTYPE:       {'compiled': None, 'regex': r'^mem_(gtt|vram)_.*', 'flags': None}}
        
    def __getitem__(self, key: PatternKeys) -> Pattern:

        if key in self.patterns:
            if self.patterns[key]['compiled']: return self.patterns[key]['compiled']
            if self.patterns[key]['flags']:
                self.patterns[key]['compiled'] = re.compile(self.patterns[key]['regex'], self.patterns[key]['flags'])
            else:
                self.patterns[key]['compiled'] = re.compile(self.patterns[key]['regex'])
            return self.patterns[key]['compiled']
        raise AttributeError('No such attribute: {}'.format(key))

