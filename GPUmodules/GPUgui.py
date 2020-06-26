#!/usr/bin/env python3
""" gpu-utils: GPUgui module to support gui in rickslab-gpu-utils.

    Copyright (C) 2020  RicksLab

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
__copyright__ = 'Copyright (C) 2020 RicksLab'
__credits__ = ['@berturion - Testing and Verification']
__license__ = 'GNU General Public License'
__program_name__ = 'gpu-utils'
__maintainer__ = 'RueiKe'
__docformat__ = 'reStructuredText'
# pylint: disable=multiple-statements
# pylint: disable=line-too-long
# pylint: disable=bad-continuation

from typing import Tuple, Dict
import sys
import re
import logging
import warnings

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk
except ModuleNotFoundError as error:
    print('gi import error: {}'.format(error))
    print('gi is required for {}'.format(__program_name__))
    print('   In a venv, first install vext:  pip install --no-cache-dir vext')
    print('   Then install vext.gi:  pip install --no-cache-dir vext.gi')
    sys.exit(0)

try:
    from GPUmodules import env
except ImportError:
    import env
from GPUmodules import __version__, __status__

ColorDict = Dict[str, str]
LOGGER = logging.getLogger('gpu-utils')
PATTERNS = env.GutConst.PATTERNS


def get_color(value: str) -> str:
    """
    Get the rgb hex string for the provided color name.

    :param value: A valid project color name.
    :return: rrb value as a hex string.
    """
    return GuiProps.color_name_to_hex(value)


class GuiProps:
    """
    Class to manage style properties of Gtk widgets.
    """
    _colors: ColorDict = {'white':     '#FFFFFF',
                          'white_off': '#FCFCFC',
                          'white_pp':  '#F0E5D3',
                          'cream':     '#FFFDD1',
                          'gray20':    '#CCCCCC',
                          'gray50':    '#7F7F7F',
                          'gray60':    '#666666',
                          'gray70':    '#4D4D4D',
                          'gray80':    '#333333',
                          'gray95':    '#0D0D0D',
                          'gray_dk':   '#6A686E',
                          'black':     '#000000',
                          # Colors Low Contrast - For table fields
                          'green':     '#8EC3A7',
                          'green_dk':  '#6A907C',
                          'teal':      '#218C8D',
                          'olive':     '#6C9040',
                          'red':       '#B73743',
                          'orange':    '#E86850',
                          'yellow':    '#C9A100',
                          'blue':      '#587498',
                          'purple':    '#6264A7',
                          # Colors Bright - For plot lines
                          'br_red':    '#FF2D2D',
                          'br_orange': '#FF6316',
                          'br_blue':   '#66CCFF',
                          'br_pink':   '#CC00FF',
                          'br_green':  '#99FF99',
                          'br_yellow': '#FFFF66',
                          # Slate - For table fields
                          'slate_lt':  '#A0A0AA',
                          'slate_md':  '#80808d',
                          'slate_dk':  '#5D5D67',
                          'slate_vdk': '#3A3A40'}

    @staticmethod
    def color_name_to_hex(value: str) -> str:
        """
        Return the hex code for the given string.  The specified string must exist in the project color list.
        :param value: Color name
        :return: Color hex code
        """
        if value not in GuiProps._colors.keys():
            raise ValueError('Invalid color name {} not in {}'.format(value, GuiProps._colors))
        return GuiProps._colors[value]

    @staticmethod
    def color_name_to_rgba(value: str) -> Tuple[float, ...]:
        """
        Convert the given color name to a color tuple.  The given color string mus exist in the project
        color list.

        :param value:  Color name
        :return: Color tuple
        """
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
        if not re.fullmatch(PATTERNS['HEXRGB'], value):
            raise ValueError('Invalid hex color format in {}'.format(value))
        value = value.lstrip('#')
        if len(value) != 6:
            raise ValueError('Invalid hex color format in {}'.format(value))
        (r_1, g_1, b_1, a_1) = tuple(int(value[i:i + 2], 16) for i in range(0, 6, 2)) + (1,)
        (r_1, g_1, b_1, a_1) = (r_1 / 255.0, g_1 / 255.0, b_1 / 255.0, a_1)
        return tuple([r_1, g_1, b_1, a_1])

    @staticmethod
    def set_gtk_prop(gui_item, top: int = None, bottom: int = None, right: int = None,
                     left: int = None, width: int = None, width_chars: int = None, width_max: int = None,
                     max_length: int = None, align: tuple = None, xalign: float = None) -> None:
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

    @classmethod
    def set_style(cls, css_str=None) -> None:
        """
        Set the specified css style, or set default styles if no css string is specified.

        :param css_str: A valid css format string.
        """
        css_list = []
        if css_str is None:
            # Initialize formatting colors.
            css_list.append("grid { background-image: image(%s); }" % cls._colors['gray80'])
            css_list.append("#light_grid { background-image: image(%s); }" % cls._colors['gray20'])
            css_list.append("#dark_grid { background-image: image(%s); }" % cls._colors['gray70'])
            css_list.append("#dark_box { background-image: image(%s); }" % cls._colors['slate_dk'])
            css_list.append("#med_box { background-image: image(%s); }" % cls._colors['slate_md'])
            css_list.append("#light_box { background-image: image(%s); }" % cls._colors['slate_lt'])
            css_list.append("#head_box { background-image: image(%s); }" % cls._colors['blue'])
            css_list.append("#warn_box { background-image: image(%s); }" % cls._colors['red'])
            css_list.append("#button_box { background-image: image(%s); }" % cls._colors['slate_dk'])
            css_list.append("#message_box { background-image: image(%s); }" % cls._colors['gray50'])
            css_list.append("#message_label { color: %s; }" % cls._colors['white_off'])
            css_list.append("#warn_label { color: %s; }" % cls._colors['white_pp'])
            css_list.append("#white_label { color: %s; }" % cls._colors['white_off'])
            css_list.append("#black_label { color: %s; }" % cls._colors['gray95'])
            css_list.append("#ppm_combo { background-image: image(%s); color: %s; }" %
                            (cls._colors['green'], cls._colors['black']))
            css_list.append("button { background-image: image(%s); color: %s; }" %
                            (cls._colors['slate_lt'], cls._colors['black']))
            css_list.append("entry { background-image: image(%s); color: %s; }" %
                            (cls._colors['green'], cls._colors['gray95']))
            # Below format does not work.
            css_list.append("entry:selected { background-image: image(%s); color: %s; }" %
                            (cls._colors['yellow'], cls._colors['white']))
        else:
            css_list.append(css_str)
        LOGGER.info('css %s', css_list)

        screen = Gdk.Screen.get_default()

        for css_item in css_list:
            provider = Gtk.CssProvider()
            css = css_item.encode('utf-8')
            provider.load_from_data(css)
            style_context = Gtk.StyleContext()
            style_context.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def about() -> None:
    """
    Display details of this module.
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('Credits: ', *['\n      {}'.format(item) for item in __credits__])
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
