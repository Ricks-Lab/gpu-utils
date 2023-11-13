#!/usr/bin/env python3
""" Project Keys as Enum Classes

    Copyright (C) 2023  RicksLab

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
__copyright__ = 'Copyright (C) 2023 RicksLab'
__license__ = 'GNU General Public License'
__program_name__ = 'gpu-utils'
__maintainer__ = 'RicksLab'
__docformat__ = 'reStructuredText'

# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=logging-format-interpolation
# pylint: disable=consider-using-f-string
# pylint: disable=invalid-name

from enum import Enum, auto
from typing import List


class GpuEnum(Enum):
    """ Define Critical dictionary/dataFrame keys and Enum objects. Be careful when modifying. A change
        in enum value could invalidate saved pickled model parameters.
    """
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def list(cls) -> List[str]:
        """ Return a list of name from current UpsEnum object """
        return list(map(lambda c: c.name, cls))


class GpuType(GpuEnum):
    """ Enum object to define keys for GPU type.
    """
    ALL = auto()
    Undefined = auto()
    Unsupported = auto()
    Supported = auto()
    Legacy = auto()
    LegacyAPU = auto()
    APU = auto()
    Modern = auto()
    PStatesNE = auto()
    PStates = auto()
    CurvePts = auto()
    Offset = auto()
    NotSet = auto()


class GpuCompatibility(GpuEnum):
    """ Enum object to define keys for GPU Compatibility.
    """
    ALL = auto()
    ReadWrite = auto()
    ReadOnly = auto()
    WriteOnly = auto()
    Readable = auto()
    Writable = auto()
    Not = auto()


class GpuVendor(GpuEnum):
    """ Enum object to define keys for GPU Vendor.
    """
    ALL = auto()
    Undefined = auto()
    AMD = auto()
    NVIDIA = auto()
    INTEL = auto()
    ASPEED = auto()
    MATROX = auto()
    PCIE = auto()


class SensorSet(GpuEnum):
    """ Enum object to define keys for GPU Sensor Sets.
    """
    Static = auto()
    Dynamic = auto()
    Info = auto()
    State = auto()
    Monitor = auto()
    All = auto()


class SensorType(GpuEnum):
    """ Enum object to define keys for GPU Sensor Types.
    """
    SingleParam = auto()
    SingleString = auto()
    SingleStringSelect = auto()
    MinMax = auto()
    MLSS = auto()
    InputLabel = auto()
    InputLabelX = auto()
    MLMS = auto()
    AllPStates = auto()


class OdMode(GpuEnum):
    """ Enum object to define keys for GPU overdrive modes.
    """
    none = auto()
    value = auto()
    range = auto()
    curve = auto()
    offset = auto()
