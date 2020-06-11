# amdgpu-utils - User Guide
A set of utilities for monitoring AMD GPU performance and modifying control settings.

## Current amdgpu-utils Version: 3.2.x
 - [Getting Started](#getting-started)
 - [Using amdgpu-ls](#using-amdgpu-ls)
 - [GPU Type Dependent Behavior](#gpu-type-dependent-behavior)
 - [Using amdgpu-monitor](#using-amdgpu-monitor)
 - [Using amdgpu-plot](#using-amdgpu-plot)
 - [Using amdgpu-pac](#using-amdgpu-pac)
 - [Updating the PCI ID decode file](#updating-the-PCI-ID-decode-file)
 - [Optimizing Compute Performance-Power](#optimizing-compute-performance-power)
 - [Running Startup PAC Bash Files](#running-startup-pac-bash-files)

## Getting Started
First, this set of utilities is written and tested with Python3.6.  If you are using an older
version, you will likely see syntax errors.  Unfortunately, I don't know how to catch a
syntax error, so if you have issues, just execute:
```
./amdgpu-chk
```
and it should display a message indicating any Python or Kernel incompatibilities.  You will
also notice that there is a minimum version of the Kernel that supports these features, but be
warned, I have tested it with kernel releases no older than 4.15. There have been amdgpu features
implemented over time that span many releases of the kernel, so your experience in using these
utilities with older kernels might not be ideal.

To use any of these utilities, you must have the *amdgpu* open source driver package installed,
either the All-Open stack or Pro stack. Components of *amdgpu* are also installed when *ROCm* is 
installed.  You can check with the following commands:
```
dpkg -l 'amdgpu*'
dpkg -l 'rocm*'
```

You also must set your Linux machine to boot with the feature mask set to support the functionality
that these tools depend on.  Do do this, you must set amdgpu.ppfeaturemask=0xfffd7fff.  This
can be accomplished by adding amdgpu.ppfeaturemask=0xfffd7fff to the GRUB_CMDLINE_LINUX_DEFAULT
value in /etc/default/grub and executing *sudo update-grub* as in the following example, using *vi* or
your favorite command line editor:
```
cd /etc/default
sudo vi grub
```
Modify to include the featuremask as follows:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amdgpu.ppfeaturemask=0xfffd7fff"
```
After saving, update grub:
```
sudo update-grub
```
and then reboot.

If not running from a package installation, it is suggested run amdgpu-util in a virtual environment to avoid
dependency issues. If you don't have venv installed with python3, then execute the following (Ubuntu example):
```
sudo apt install -y python3-venv
```

Initialize your amdgpu-utils-env if it is your first time to use it.  From the project directory, execute:
```
python3 -m venv amdgpu-utils-env
source amdgpu-utils-env/bin/activate
pip install --no-cache-dir -r requirements-venv.txt
```
Use the deactivate command to leave the venv.

The amdgpu-util package can be run without a venv by pip installing the requirements.txt file:
```
sudo -H pip3 install --no-cache-dir -r requirements.txt
```


## Using amdgpu-ls
After getting your system setup to support amdgpu-utils, it is best to verify functionality by 
listing your GPU details with the *amdgpu-ls* command.  It first attempts to detect the version 
of amdgpu drivers you have installed and then check compatibility of installed AMD GPUs.  Its
default behavior is to list basic GPU details for all compatible cards:
```
Detected GPUs: INTEL: 1, AMD: 1
AMD: amdgpu version: 20.10-1048554
AMD: Wattman features enabled: 0xfffd7fff
2 total GPUs, 1 rw, 0 r-only, 0 w-only

Card Number: 0
   Vendor: INTEL
   Readable: False
   Writable: False
   Compute: False
   Card Model: Intel Corporation 8th Gen Core Processor Gaussian Mixture Model
   PCIe ID: 00:02.0
   Driver: i915
   Card Path: /sys/class/drm/card0/device

Card Number: 1
   Vendor: AMD
   Readable: True
   Writable: True
   Compute: True
   GPU UID: 
   Device ID: {'vendor': '0x1002', 'device': '0x731f', 'subsystem_vendor': '0x1da2', 'subsystem_device': '0xe411'}
   Decoded Device ID: Navi 10 [Radeon RX 5600 OEM/5600 XT / 5700/5700 XT]
   Card Model: Advanced Micro Devices, Inc. [AMD/ATI] Navi 10 [Radeon RX 5600 OEM/5600 XT / 5700/5700 XT] (rev ca)
   Display Card Model: Navi 10 [Radeon RX 5600 OEM/5600 XT / 5700/5700 XT]
   PCIe ID: 03:00.0
      Link Speed: 16 GT/s
      Link Width: 16
   ##################################################
   Driver: amdgpu
   vBIOS Version: 113-5E4111U-X4G
   Compute Platform: OpenCL 2.0 AMD-APP (3075.10)
   GPU Frequency/Voltage Control Type: CurvePts
   HWmon: /sys/class/drm/card1/device/hwmon/hwmon3
   Card Path: /sys/class/drm/card1/device
   ##################################################
   Current Power (W): 109.000
   Power Cap (W): 160.000
      Power Cap Range (W): [0, 192]
   Fan Enable: 0
   Fan PWM Mode: [2, 'Dynamic']
   Fan Target Speed (rpm): 735
   Current Fan Speed (rpm): 735
   Current Fan PWM (%): 21
      Fan Speed Range (rpm): [0, 3200]
      Fan PWM Range (%): [0, 100]
   ##################################################
   Current GPU Loading (%): 99
   Current Memory Loading (%): 84
   Current GTT Memory Usage (%): 0.953
      Current GTT Memory Used (GB): 0.057
      Total GTT Memory (GB): 5.984
   Current VRAM Usage (%): 35.269
      Current VRAM Used (GB): 2.111
      Total VRAM (GB): 5.984
   Current Temps (C): {'mem': 92.0, 'edge': 63.0, 'junction': 70.0}
      Critical Temp (C): 118.000
   Current Voltages (V): {'vddgfx': 875}
   Current Clk Frequencies (MHz): {'sclk': 1700.0, 'mclk': 875.0}
   Current SCLK P-State: [2, '1700Mhz']
      SCLK Range: ['800Mhz', '1820Mhz']
   Current MCLK P-State: [3, '875Mhz']
      MCLK Range: ['625Mhz', '930Mhz']
   Power Profile Mode: 0-BOOTUP_DEFAULT
   Power DPM Force Performance Level: manual
```

If everything is working fine, you should see no warning or errors.  The listing utility
also has other command line options:
```
usage: amdgpu-ls [-h] [--about] [--table] [--pstates] [--ppm] [--clinfo]
                 [--no_fan] [-d]

optional arguments:
  -h, --help   show this help message and exit
  --about      README
  --table      Output table of basic GPU details
  --pstates    Output pstate tables instead of GPU details
  --ppm        Output power/performance mode tables instead of GPU details
  --clinfo     Include openCL with card details
  --no_fan     do not include fan setting options
  -d, --debug  Debug output
```

The *--clinfo* option will make a call to clinfo, if it is installed, and list these parameters
along with the basic parameters.  The benefit of running this in *amdgpu-ls* is that the tool
uses the PCIe slot id to associate clinfo results with the appropriate GPU in the listing.

The *--pstates* and *--ppm* options will display the P-State definition table and the power
performance mode table.
```
./amdgpu-ls --pstate --ppm
Detected GPUs: AMD: 1, ASPEED: 1
AMD: rocm version: 3.0.6
AMD: Wattman features enabled: 0xfffd7fff
2 total GPUs, 1 rw, 0 r-only, 0 w-only

Card Number: 1
   Card Model: Vega 20
   Card Path: /sys/class/drm/card1/device
   GPU Frequency/Voltage Control Type: CurvePts
   ##################################################
   DPM States: 
   SCLK:                   MCLK:
    0:  701Mhz              0:  351Mhz  
    1:  809Mhz              1:  801Mhz  
    2:  1085Mhz             2:  1051Mhz 
    3:  1287Mhz             
    4:  1434Mhz             
    5:  1550Mhz             
    6:  1606Mhz             
    7:  1627Mhz             
    8:  1651Mhz             
   ##################################################
   PP OD States:
   SCLK:                   MCLK:
    0:  808Mhz    -         
    1:  1650Mhz   -         1:  1050Mhz   -       
   ################################################## 
   VDDC_CURVE:
    0: ['808Mhz', '724mV']
    1: ['1304Mhz', '822mV']
    2: ['1801Mhz', '1124mV']

Card Number: 1
   Card Model: Vega 20
   Card: /sys/class/drm/card1/device
   Power Performance Mode: manual
    0:   BOOTUP_DEFAULT
    1:   3D_FULL_SCREEN
    2:     POWER_SAVING
    3:            VIDEO
    4:               VR
    5:          COMPUTE
    6:           CUSTOM
   -1:             AUTO
```
Different generations of cards will provide different information with the --ppm option. Here is an example for
Ellesmere and Polaris cards:
```
./amdgpu-ls --ppm
Detected GPUs: INTEL: 1, AMD: 2
AMD: amdgpu version: 19.50-967956
AMD: Wattman features enabled: 0xfffd7fff
3 total GPUs, 2 rw, 0 r-only, 0 w-only

Card Number: 1
   Card Model: Advanced Micro Devices, Inc. [AMD/ATI] Ellesmere [Radeon RX 470/480/570/570X/580/580X/590] (rev ef)
   Card Path: /sys/class/drm/card1/device
   Power DPM Force Performance Level: manual
   NUM        MODE_NAME     SCLK_UP_HYST   SCLK_DOWN_HYST SCLK_ACTIVE_LEVEL     MCLK_UP_HYST   MCLK_DOWN_HYST MCLK_ACTIVE_LEVEL
     0   BOOTUP_DEFAULT:        -                -                -                -                -                -
     1   3D_FULL_SCREEN:        0              100               30                0              100               10
     2     POWER_SAVING:       10                0               30                -                -                -
     3            VIDEO:        -                -                -               10               16               31
     4               VR:        0               11               50                0              100               10
     5        COMPUTE *:        0                5               30                0              100               10
     6           CUSTOM:        -                -                -                -                -                -
```

## GPU Type Dependent Behavior
AMD GPU's compatible with the amdgpu open source drivers are of three different types in terms of how frequency/voltage
is managed.  GPUs of Vega10 and earlier architecture rely on the definition of specific power states to determine
the clock frequency and voltage.  The GPU will operate only at the specific Frequency/Voltage states that are defined, 
and move between states based on power, temperature, and loading.  These GPU's are classified as `Type: PStates` if
the P-state table is readable and as `Type: PSatesNE` if it is not.  For GPUs of Vega20 architecture or newer,
Voltage/Frequency curves can be defined with three points on a Voltage vs. Frequency curve.  These GPU's are
classified as `Type: CurvePts`.

With the *amdgpu-ls* tool, you can determine the type of your card. Here are examples of relevant lines from the 
output for different types of GPUs:
```
Decoded Device ID: R9 290X DirectCU II
GPU Frequency/Voltage Control Type: PStatesNE

Decoded Device ID: RX Vega64
GPU Frequency/Voltage Control Type: PStates

Decoded Device ID: Radeon VII
GPU Frequency/Voltage Control Type: CurvePts

Decoded Device ID: Navi 10 [Radeon RX 5600 OEM/5600 XT / 5700/5700 XT]
GPU Frequency/Voltage Control Type: CurvePts
```

Monitor and Control utilities will differ between the three types.
* For type Undefined, you can monitor the P-state details with monitor utilities, but you can NOT define P-states
or set P-state masks.
* For type PStates, you can monitor the P-state details with monitor utilities, and you can define P-states and set
P-state masks.
* For Type CurvePts, you can monitor current Clocks frequency and P-states, with latest amdgpu drivers.  The SCLK and
MCLK curve end points can be controlled, which has the effect of limiting the frequency range, similar to P-state
masking for Type PStates cards.  The option of p-state masking is also available for Type CurvePts cards.  You are
also able to modify the three points that define the Vddc-SCLK curve. I have not attempted to OC the card yet, but
I assume redefining the 3rd point would be the best approach.  For underclocking, lowering the SCLK end point is
effective.  I don't see a curve defined for memory clock on the Radeon VII, so setting memory clock vs. voltage
doesn't seem possible at this time.  There also appears to be an inconsistency in the defined voltage ranges for
curve points and actual default settings. 

Below is a plot of what I extracted for the Frequency vs Voltage curves of the RX Vega64 and the Radeon VII.

![](Type1vsType2.png)

## Using amdgpu-monitor
By default, *amdgpu-monitor* will display a text based table in the current terminal window that updates
every sleep duration, in seconds, as defined by *--sleep N* or 2 seconds by default. If you are using
water cooling, you can use the *--no_fans* to remove fan functionality.
```
┌─────────────┬────────────────┬────────────────┐
│Card #       │card0           │card1           │
├─────────────┼────────────────┼────────────────┤
│Model        │Radeon RX 570   │Radeon RX 570   │
│GPU Load %   │100             │100             │
│Mem Load %   │61              │91              │
│VRAM Usage % │52.64           │52.144          │
│GTT Usage %  │3.218           │3.053           │
│Power (W)    │76.2            │84.2            │
│Power Cap (W)│120.0           │120.0           │
│Energy (kWh) │0.005           │0.005           │
│T (C)        │75.0            │72.0            │
│VddGFX (mV)  │906             │906             │
│Fan Spd (%)  │54              │48              │
│Sclk (MHz)   │1071            │1071            │
│Sclk Pstate  │6               │6               │
│Mclk (MHz)   │1850            │1850            │
│Mclk Pstate  │2               │2               │
│Perf Mode    │1-3D_FULL_SCREEN│1-3D_FULL_SCREEN│
└─────────────┴────────────────┴────────────────┘
```
The fields are the same as the GUI version of the display, available with the *--gui* option.
![](amdgpu-monitor_scrshot.png)

The first row gives the card number for each GPU.  This number is the integer used by the driver for each GPU.  Most
fields are self describing.  The Power Cap field is especially useful in managing compute power efficiency, and
lowering the cap can result in more level loading and overall lower power usage for little compromise in performance. 
The Energy field is a derived metric that accumulates GPU energy usage, in kWh, consumed since the monitor started.
Note that total card power usage may be more than reported GPU power usage.  Energy is calculated as the product of
the latest power reading and the elapsed time since the last power reading. 

You will notice no clock frequencies or valid P-states for the Vega 20 card.  This is because of a limitation in
the first drivers that supported Vega 20 which have a change in the way frequency vs voltage is managed. In later
version of the drivers, actual clock frequency and P-states are readable. The P-state table for Vega 20 is a
definition of frequency vs. voltage curves, so setting P-states to control the GPU is no longer relevant, but
these concepts are used in reading current states.

The Perf Mode field gives the current power performance mode, which may be modified in with *amdgpu-pac*.  These
modes affect the how frequency and voltage are managed versus loading.  This is a very important parameter when
managing compute performance.

Executing *amdgpu-monitor* with the *--plot* option will display a continuously updating plot of the critical
GPU parameters.
![](amdgpu-plot_scrshot.png)

Having an *amdgpu-monitor* Gtx window open at startup may be useful if you run GPU compute projects that autostart
and you need to quickly confirm that *amdgpu-pac* bash scripts ran as expected at startup
(see [Using amdgpu-pac](#using-amdgpu-pac)). You can have *amdgpu-monitor --gui* automatically launch at startup
or upon reboot by using the startup utility for your distribution. In Ubuntu, for example, open *Startup Applications
Preferences* app, then in the Preferences window select *Add* and use something like this in the command field:
```
/usr/bin/python3 /home/<user>/Desktop/amdgpu-utils/amdgpu-monitor --gui
```
where `/amdgpu-utils` may be a soft link to your current distribution directory. This startup approach does not
work for the default Terminal text execution of *amdgpu-monitor*. 

## Using amdgpu-plot
In addition to being called from *amdgpu-monitor* with the *--plot* option, *amdgpu-plot* may be ran as a standalone
utility.  Just execute *amdgpu-plot --sleep N* and the plot will update at the defined interval.  It is not
recommended to run both the monitor with an independently executed plot, as it will result in twice as many reads
from the driver files.  Once the plots are displayed, individual items on the plot can be toggled by selecting the
named button on the plot display.

The *--stdin* option is used by *amdgpu-monitor --plot* in its execution of *amdgpu-plot*.  This option along
with *--simlog* option can be used to simulate a plot output using a log file generated by *amdgpu-monitor --log*. 
I use this feature when troubleshooting problems from other users, but it may also be useful in benchmarking
performance.  An example of the command line for this is as follows:
```
cat log_monitor_0421_081038.txt | ./amdgpu-plot --stdin --simlog
```

## Using amdgpu-pac
By default, *amdgpu-pac* will open a Gtk based GUI to allow the user to modify GPU performance parameters.  I strongly
suggest that you completely understand the implications of changing any of the performance settings before you use
this utility.  As per the terms of the GNU General Public License that covers this project, there is no warranty on
the usability of these tools.  Any use of this tool is at your own risk.

To help you manage the risk in using this tool, two modes are provided to modify GPU parameters.  By default, a bash
file is created that you can review and execute to implement the desired changes.  Here is an example of that file:
```
#!/bin/sh
###########################################################################
## amdgpu-pac generated script to modify GPU configuration/settings
###########################################################################

###########################################################################
## WARNING - Do not execute this script without completely
## understanding appropriate values to write to your specific GPUs
###########################################################################
#
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
###########################################################################
# 
# Card1  Advanced Micro Devices, Inc. [AMD/ATI] Vega 20 (rev c1)
# /sys/class/drm/card1/device
# 
set -x
# Power DPM Force Performance Level: [manual] change to [manual]
sudo sh -c "echo 'manual' >  /sys/class/drm/card1/device/power_dpm_force_performance_level"
# Powercap Old: 150 New: 150 Min: 0 Max: 300
sudo sh -c "echo '150000000' >  /sys/class/drm/card1/device/hwmon/hwmon2/power1_cap"
# Fan PWM Old: 0 New: 0 Min: 0 Max: 100
sudo sh -c "echo '1' >  /sys/class/drm/card1/device/hwmon/hwmon2/pwm1_enable"
sudo sh -c "echo '0' >  /sys/class/drm/card1/device/hwmon/hwmon2/pwm1"
# sclk curve end point: 0 : 808 MHz
sudo sh -c "echo 's 0 808' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# sclk curve end point: 1 : 1650 MHz
sudo sh -c "echo 's 1 1650' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# mclk curve end point: 1 : 1050 MHz
sudo sh -c "echo 'm 1 1050' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# vddc curve point: 0 : 808 MHz, 724 mV
sudo sh -c "echo 'vc 0 808 724' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# vddc curve point: 1 : 1304 MHz, 822 mV
sudo sh -c "echo 'vc 1 1304 822' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# vddc curve point: 2 : 1801 MHz, 1124 mV
sudo sh -c "echo 'vc 2 1801 1124' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# Selected: ID=5, name=COMPUTE
sudo sh -c "echo '5' >  /sys/class/drm/card1/device/pp_power_profile_mode"
sudo sh -c "echo 'c' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# Sclk P-State Mask Default: 0 1 2 3 4 5 6 7 8 New: 0 1 2 3 4 5 6 7 8
sudo sh -c "echo '0 1 2 3 4 5 6 7 8' >  /sys/class/drm/card1/device/pp_dpm_sclk"
# Mclk P-State Mask Default: 0 1 2 New: 0 1 2
sudo sh -c "echo '0 1 2' >  /sys/class/drm/card1/device/pp_dpm_mclk"
```

When you execute *amdgpu-pac*, you will notice a message bar at the bottom of the interface.  By default, it informs
you of the mode you are running in.  By default, the operation mode is to create a bash file, but with the
*--execute_pac* (or *--execute*) command line option, the bash file will be automatically executed and then deleted. 
The message bar will indicate this status.  Because the driver files are writable only by root, the commands to write
configuration settings are executed with sudo.  The message bar will display in red when credentials are pending.  Once
executed, a yellow message will remind you to check the state of the gpu with *amdgpu-monitor*.  I suggest to using
the monitor routine when executing pac to see the changes in real-time.

The command line option *--force_write* will result in all configuration parameters to be written to the bash file. 
The default behavior since v2.4.0 is to write only changes.  The *--force_write* is useful for creating a bash file
that can be execute to set your cards to a known state. As an example, you could use such a file to configure your
GPUs on boot up (see [Setting GPU Automatically at Startup](#setting-gpu-automatically-at-startup)).

### The amdgpu-pac interface for Type PStates and Type CurvePts cards
![](amdgpu-pac_scrshot.png)

In the interface, you will notice entry fields for indicating new values for specific parameters.  In most cases, the
values in these fields will be the current values, but in the case of P-state masks, it will show the default value
instead of the current value.  If you know how to obtain the current value, please let me know!

Note that when a PAC bash file is executed either manually or automatically, the resulting fan PWM (% speed) may
be slightly different from what you see in the Fan PWM entry field.  The direction and magnitude of differences
between expected and realized fan speeds can depend on card model.  You will need to experiment with different
settings to determine how it works with your card.  I recommend running these experimental settings when the GPU
is not under load.  If you know the cause of the differences between entered and final fan PWM values, let me know. 

Changes made with *amdgpu-pac* do not persist through a system reboot. To reestablish desired GPU settings after a
reboot, either re-enter them using *amdgpu-pac* or *amdgpu-pac --execute*, or execute a previously saved bash file.
*Amdgpu-pac* bash files must retain their originally assigned file name to run properly.
See [Running Startup PAC Bash Files](#running-startup-pac-bash-files) for how to run PAC bash
scripts automatically at system startup.

For Type PStates cards, while changes to power caps and fan speeds can be made while the GPU is under load, for
*amdgpu-pac* to work properly, other changes may require that the GPU not be under load, *i.e.*, that sclk
P-state and mclk P-state are 0. Possible consequences with making changes under load is that the GPU become
stuck in a 0 P-state or that the entire system becomes slow to respond, where a reboot will be needed to restore
full GPU functions. Note that when you change a P-state mask, default mask values will reappear in the field
after Save, but your specified changes will have been implemented on the card and show up in *amdgpu-monitor*.
Some changes may not persist when a card has a connected display. When changing P-state MHz or mV, the desired
P-state mask, if different from default (no masking), will have to be re-entered for clock or voltage changes to
be applied. Again, save PAC changes to clocks, voltages, or masks only when the GPU is at resting state (state 0).

For Type CurvePts cards, although changes to p-state masks cannot be made through *amdgpu-pac*, changes to all
other fields can be made on-the-fly while the card is under load.

Some basic error checking is done before writing, but I suggest you be very certain of all entries before you save
changes to the GPU.

## Updating the PCI ID decode file 
In determining the GPU display name, *amdgpu-utils* will examine two sources.  The output of *lspci -k -s nn:nn.n* is
used to generate a complete name and an algorithm is used to generate a shortened version.  From the driver files, a
set of files (vendor, device, subsystem_vendor, subsystem_device) contain a 4 parts of the Device ID are read and used
to extract a GPU model name from system pci.ids file which is sourced from
[https://pci-ids.ucw.cz/](https://pci-ids.ucw.cz/) where a comprehensive list is maintained.  The system file can
be updated from the original source with the command:
```
sudo update-pciids
```
If your GPU is not listed in the extract, the pci.id website has an interface to allow the user to request an
addition to the master list.  

## Optimizing Compute Performance-Power
The *amdgpu-utils* tools can be used to optimize performance vs. power for compute workloads by leveraging
its ability to measure power and control relevant GPU settings.  This flexibility allows one to execute a
DOE to measure the effect of GPU settings on the performance in executing specific workloads.  In SETI@Home
performance, the Energy feature has also been built into [benchMT](https://github.com/Ricks-Lab/benchMT) to
benchmark power and execution times for various work units.  This, combined with the log file produced with
*amdgpu-monitor --gui --log*, may be useful in optimizing performance.

![](https://i.imgur.com/YPuDez2l.png)

## Running Startup PAC Bash Files
If you set your system to run *amdgpu-pac* bash scripts automatically, as described in this section, note that
changes in your hardware or graphic drivers may cause potentially serious problems with GPU settings unless new
PAC bash files are generated following the changes. Review the [Using amdgpu-pac](#using-amdgpu-pac) section
before proceeding.

One approach is to execute PAC bash scripts as a systemd startup service. As with setting up files for crontab,
from *amdgpu-pac --force_write* set your optimal configurations for each GPU, then Save All. You may need to
change ownership to root of each card's bash file: `sudo chown root pac_writer*.sh`

For each bash file, you could create a symlink (soft link) that corresponds to the card number referenced in each
linked bash file, using simple descriptive names, *e.g.*, pac_writer_card1, pac_writer_card2, *etc.*. These links are
optional, but can make management of new or edited startup bash files easier. Links are used in the startup service
example, below. Don't forget to reform the link(s) each time a new PAC bash file is written for a card. 
 
Next, create a .service file named something like, amdgpu-pac-startup.service and give it the following content:
```
[Unit]
Description=run at boot amdgpu-utils PAC bash scripts

[Service]
Type=oneshot

ExecStart=/home/<user>/pac_writer_card0
ExecStart=/home/<user>/pac_writer_card1
ExecStart=/home/<user>/pac_writer_card2

[Install]
WantedBy=multi-user.target
```
The Type=oneshot service allows use of more than one ExecStart.  In this example, three bash files are used for
two cards, where two alternative files are used for one card that the system may recognize as either card0 or
card1; see further below for an explanation. 

Once your .service file is set up, execute the following commands:
```
 ~$ sudo chown root:root amdgpu-pac-startup.service 
 ~$ sudo mv amdgpu-pac-startup.service /etc/systemd/system/
 ~$ sudo chmod 664 /etc/systemd/system/amdgpu-pac-startup.service
 ~$ sudo systemctl daemon-reload
 ~$ sudo systemctl enable amdgpu-pac-startup.service
```
The last command should produce a terminal stdout like this:
`Created symlink /etc/systemd/system/multi-user.target.wants/amdgpu-pac-startup.service → /etc/systemd/system/amdgpu-pac-startup.service.`

On the next reboot or restart, the GPU(s) will be set with the PAC run parameters. If you want to test the bash
script(s) before rebooting, run: `~$ sudo systemctl start amdgpu-pac-startup.service`. 

If you have a Type PStates card where some PAC parameters can't be changed when it is under load, you will want
to make sure that the PAC bash script executes before the card begins computing. If you have a *boinc-client* that
automatically runs on startup, for example, then consider delaying it for 20 seconds using the cc_config.xml
option *<start_delay>30</start_delay>*.

One or more card numbers that are assigned by amdgpu drivers may change following a system or driver
update and restart. With subsequent updates or restarts, a card can switch back to its original number. When a
switch occurs, the bash file written for a previous card number will still be read at startup, but will have no
effect, causing the renumbered card to run at its default settings. To deal with this possibility, you can create
an alternative PAC bash file after a renumbering event and add these alternative files in your systemd service.
You will probably just need two alternative bash files for a card that is subject to amdgpu reindexing. A card's
number is shown by *amdgpu-ls* and also appears in *amdgpu-monitor* and *amdgpu-plot*. A card's PCI IDs is listed
by *amdgpu-ls*. If you know what causes GPU card index switching, let me know.

You may find a card running at startup with default power limits and Fan PWM settings instead of what is prescribed
in its startup PAC bash file. If so, it may be that the card's hwmon# is different from what is hard coded in the
bash file, because the hwmon index for devices can also change upon reboot. To work around this, you can edit a
card's bash file to define hwmon# as a variable and modify the hwmon lines to use it. Here is an example for card1:
```
set -x
HWMON=$(ls /sys/class/drm/card1/device/hwmon/)
# Powercap Old: 120 New: 110 Min: 0 Max: 180
sudo sh -c "echo '1100000000' >  /sys/class/drm/card1/device/hwmon/$HWMON/power1_cap"
# Fan PWM Old:  44 New:  47 Min:  0 Max:  100
sudo sh -c "echo '1' >  /sys/class/drm/card1/device/hwmon/$HWMON/pwm1_enable"
sudo sh -c "echo '119' >  /sys/class/drm/card1/device/hwmon/$HWMON/pwm1"
```
