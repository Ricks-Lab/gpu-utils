#!/bin/sh
############################################################
## example script to modify GPU configuration/settings
############################################################

############################################################
## WARNING - Do not execute this script without completely
## understanding appropriate value to write to your specific
## GPU.  This script is only meant as an example to show how
## it is done and is not useable without customization
############################################################

#    Copyright (C) 2019  RueiKe
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#/sys/class/drm/card1/device/
#sudo sh -c "echo 's 6 1450 1150' > /sys/class/drm/card1/device/pp_od_clk_voltage"
#sudo sh -c "echo 's 7 1550 1200' > /sys/class/drm/card1/device/pp_od_clk_voltage"
#sudo sh -c "echo 'm 3 900 1100' > /sys/class/drm/card1/device/pp_od_clk_voltage"
# Commit changes
#sudo sh -c "echo 'c' > /sys/class/drm/card1/device/pp_od_clk_voltage"
# Reset to defaults
#sudo sh -c "echo 'r' > /sys/class/drm/card1/device/pp_od_clk_voltage"

#sudo sh -c "echo 'manual' > /sys/class/drm/card0/device/power_dpm_force_performance_level" 
#sudo sh -c "echo '4' > /sys/class/drm/card0/device/pp_power_profile_mode" 
#sudo sh -c "echo '150000000' > /sys/class/drm/card0/device/hwmon/hwmon0/power1_cap"
#sudo sh -c "echo 'c' > /sys/class/drm/card0/device/pp_od_clk_voltage"

#sudo sh -c "echo 'manual' > /sys/class/drm/card1/device/power_dpm_force_performance_level" 
#sudo sh -c "echo '4' > /sys/class/drm/card1/device/pp_power_profile_mode" 
#sudo sh -c "echo '150000000' > /sys/class/drm/card1/device/hwmon/hwmon1/power1_cap"
#sudo sh -c "echo 'c' > /sys/class/drm/card1/device/pp_od_clk_voltage"
