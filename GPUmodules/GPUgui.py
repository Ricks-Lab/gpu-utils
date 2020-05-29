#!/usr/bin/env python3
""" amdgpu-utils: GPUgui module to support gui in amdgpu-utils.

    Copyright (C) 2020  RueiKe

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
__copyright__ = 'Copyright (C) 2020 RueiKe'
__credits__ = ['@berturion - Testing and Verification']
__license__ = 'GNU General Public License'
__program_name__ = 'amdgpu-utils'
__version__ = 'v3.1.0'
__maintainer__ = 'RueiKe'
__status__ = 'Stable Release'
__docformat__ = 'reStructuredText'
# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: bad-continuation

from typing import Tuple, Dict, Union
import sys
import re
import warnings
try:
    import gi
except ModuleNotFoundError as error:
    print('gi import error: {}'.format(error))
    print('gi is required for {}'.format(__program_name__))
    print('   In a venv, first install vext:  pip install --no-cache-dir vext')
    print('   Then install vext.gi:  pip install --no-cache-dir vext.gi')
    sys.exit(0)
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

GTK_Color = Tuple[Union[float, int], ...]
ColorDict = Dict[str, str]


class GuiProps:
    _colors: ColorDict = {'white':     '#FFFFFF',
                          'white_off': '#FDFDFD',
                          'cream':     '#FFFDD1',
                          'gray95':    '#0D0D0D',
                          'gray80':    '#333333',
                          'gray70':    '#4D4D4D',
                          'gray20':    '#CCCCCC',
                          'black':     '#000000',
                          'green':     '#8EC3A7',
                          'red_old':   '#DC5355',
                          'red':       '#B73743',
                          'orange':    '#E86850',
                          'yellow':    '#C9A100',
                          'blue':      '#587498',
                          'blue_old':  '#336699',
                          'purple':    '#6264A7',
                          'gray_dk':   '#6A686E',
                          'slate_lt':  '#A0A0AA',
                          'slate_md':  '#80808d',
                          'slate_dk':  '#5D5D67'}

    @staticmethod
    def color_name_to_rgba(value: str) -> Tuple[float, ...]:
        if value not in GuiProps._colors.keys():
            raise ValueError('Invalid color name {} not in {}'.format(value, GuiProps._colors))
        return GuiProps.hex_to_rgba(GuiProps._colors[value])

    @staticmethod
    def hex_to_rgba(value: str) -> Tuple[float, ...]:
        """
        Return rgba tuple for give hex color name.

        :param value: hex color value as string
        :return:  rgba tuple

        .. note:: Code copied from Stack Overflow
        """
        value = value.lstrip('#')
        if len(value) != 6:
            raise ValueError('Invalid hex color format in {}'.format(value))
        (r1, g1, b1, a1) = tuple(int(value[i:i + 2], 16) for i in range(0, 6, 2)) + (1,)
        (r1, g1, b1, a1) = (r1 / 255.00000, g1 / 255.00000, b1 / 255.00000, a1)
        return tuple([r1, g1, b1, a1])

    @staticmethod
    def set_gtk_prop(gui_item, top: int = None, bottom: int = None, right: int = None,
                     left: int = None, width: int = None, width_chars: int = None, width_max: int = None,
                     max_length: int = None, bg_color: str = None, color: str = None,
                     align: tuple = None, xalign: float = None) -> None:
        """
        Set properties of Gtk objects.

        :param gui_item: Gtk object
        :param top: Top margin
        :param bottom: Bottom margin
        :param right: Right margin
        :param left: Left margin
        :param width: Width of request field
        :param width_chars: Width of label
        :param width_max: Max Width of object
        :param max_length: max length of entry
        :param bg_color: Background color
        :param color: Font color
        :param align: Alignment parameters
        :param xalign: X Alignment parameter
        """
        if top:
            gui_item.set_property('margin-top', top)
        if bottom:
            gui_item.set_property('margin-bottom', bottom)
        if right:
            gui_item.set_property('margin-right', right)
        if left:
            gui_item.set_property('margin-left', left)
        if width:
            gui_item.set_property('width-request', width)
        if width_max:
            gui_item.set_max_width_chars(width_max)
        if width_chars:
            gui_item.set_width_chars(width_chars)
        if max_length:
            gui_item.set_max_length(max_length)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            if xalign:
                # FIXME - This is deprecated in latest Gtk, need to use halign
                gui_item.set_alignment(xalign=xalign)
            if align:
                # FIXME - This is deprecated in latest Gtk, need to use halign
                gui_item.set_alignment(*align)
            if bg_color:
                # FIXME - This is deprecated in latest Gtk, need to use css.
                if re.fullmatch(r'^#[0-9a-fA-F]+', bg_color):
                    gtk_color = GuiProps.hex_to_rgba(bg_color)
                else:
                    gtk_color = GuiProps.color_name_to_rgba(bg_color)
                gui_item.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(*gtk_color))
            if color:
                # FIXME - This is deprecated in latest Gtk, need to use css.
                if re.fullmatch(r'^#[0-9a-fA-F]+', color):
                    gtk_color = GuiProps.hex_to_rgba(color)
                else:
                    gtk_color = GuiProps.color_name_to_rgba(color)
                gui_item.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(*gtk_color))
