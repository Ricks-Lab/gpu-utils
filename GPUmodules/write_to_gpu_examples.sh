#!/bin/sh
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

sudo sh -c "echo 'manual' > /sys/class/drm/card1/device/power_dpm_force_performance_level" 
sudo sh -c "echo '4' > /sys/class/drm/card1/device/pp_power_profile_mode" 
sudo sh -c "echo '150000000' > /sys/class/drm/card1/device/hwmon/hwmon1/power1_cap"
