# amdgpu-utils - User Guide
A set of utilities for monitoring AMD GPU performance and modifying control settings.

## Current amdgpu-utils Version: 2.7.x
 - [Getting Started](#getting-started)
 - [Using amdgpu-ls](#using-amdgpu-ls)
 - [GPU Type Dependent Behavior](#gpu-type-dependent-behavior)
 - [Using amdgpu-monitor](#using-amdgpu-monitor)
 - [Using amdgpu-plot](#using-amdgpu-plot)
 - [Using amdgpu-pac](#using-amdgpu-pac)
 - [Updating the pci.id decode file](#Updating the pci.id decode file)
 - [Optimizing Compute Performance-Power](#optimizing-compute-performance-power)
 - [Setting GPU Automatically at Startup](#setting-gpu-automatically-at-startup)

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

To use any of these utilities, you must have the *amdgpu* open source driver
package installed, either the All-Open stack or Pro stack. You can check with the following command:
```
dpkg -l 'amdgpu*'
```

You also must set your Linux machine to boot with the feature mask set to support the functionality
that these tools depend on.  Do do this, you must set amdgpu.ppfeaturemask=0xfffd7fff.  This
can be accomplished by adding amdgpu.ppfeaturemask=0xfffd7fff to the GRUB_CMDLINE_LINUX_DEFAULT
value in /etc/default/grub and executing *sudo update-grub* as in the following example, using *vi* or your favorite command line editor:
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

If not running from a package installation, it is suggested run amdgpu-util in a virtual environment to avoid dependency issues. If you don't have venv installed 
with python3, then execute the following (Ubuntu example)
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
```AMD Wattman features enabled: 0xffff7fff
amdgpu version: 18.50-725072
2 AMD GPUs detected, 2 may be compatible, checking...
2 are confirmed compatible.

UUID: 309abc9c97ea451396334b11199d0680
amdgpu-utils Compatibility: Yes
Device ID: {'vendor': '0x1002', 'device': '0x687f', 'subsystem_vendor': '0x1002', 'subsystem_device': '0x0b36'}
GPU Frequency/Voltage Control Type: 1
Decoded Device ID: RX Vega64
Card Model:  Vega 10 XT [Radeon RX Vega 64] (rev c1)
Short Card Model:  RX Vega 64
Display Card Model: RX Vega64
Card Number: 1
Card Path: /sys/class/drm/card1/device/
PCIe ID: 44:00.0
Driver: amdgpu
vBIOS Version: 113-D0500100-105
HWmon: /sys/class/drm/card1/device/hwmon/hwmon6/
Current Power (W): 118.0
Power Cap (W): 140.0
Power Cap Range (W): [0, 220]
Fan Enable: 1
Fan PWM Mode: [1, 'Manual']
Current Fan PWM (%): 0
Current Fan Speed (rpm): 0
Fan Target Speed (rpm): 0
Fan Speed Range (rpm): [400, 4900]
Fan PWM Range (%): [0, 100]
Current Temp (C): 35.0
Critical Temp (C): 91.0
Current VddGFX (mV): 1037
Vddc Range: ['800mV', '1200mV']
Current Loading (%): 99
Link Speed: 8 GT/s
Link Width: 16
Current SCLK P-State: 6
Current SCLK: 1536Mhz 
SCLK Range: ['852MHz', '2400MHz']
Current MCLK P-State: 3
Current MCLK: 945Mhz 
MCLK Range: ['167MHz', '1500MHz']
Power Performance Mode: 4-COMPUTE
Power Force Performance Level: manual
```

If everything is working fine, you should see no warning or errors.  The listing utility
also has other command line options:
```usage: amdgpu-ls [-h] [--about] [--pstates] [--ppm] [--clinfo] [--no_fan] [-d]

optional arguments:
  -h, --help   show this help message and exit
  --about      README
  --pstates    Output pstate tables instead of GPU details
  --ppm        Output power/performance mode tables instead of GPU details
  --clinfo     Include openCL with card details
  --no_fan     don't include fan setting options
  -d, --debug  Debug output
```

The *--clinfo* option will make a call to clinfo, if it is installed, and list these parameters
along with the basic parameters.  The benefit of running this in *amdgpu-ls* is that the tool
uses the PCIe slot id to associate clinfo results with the appropriate GPU in the listing.

The *--pstates* and *--ppm* options will display the P-State definition table and the power
performance mode table.
```
./amdgpu-ls --pstate --ppm
AMD Wattman features enabled: 0xffff7fff
amdgpu version: 18.50-725072
2 AMD GPUs detected, 2 may be compatible, checking...
2 are confirmed compatible.

Card: /sys/class/drm/card1/device/
SCLK:                   MCLK:
0:  852Mhz    800mV     0:  167Mhz    800mV   
1:  991Mhz    900mV     1:  500Mhz    800mV   
2:  1084Mhz   950mV     2:  800Mhz    950mV   
3:  1138Mhz   1000mV    3:  945Mhz    1100mV  
4:  1200Mhz   1050mV  
5:  1401Mhz   1100mV  
6:  1536Mhz   1150mV  
7:  1630Mhz   1200mV  

Card: /sys/class/drm/card1/device/
Power Performance Mode: manual
  0:  3D_FULL_SCREEN                70                60                 1                 3
  1:    POWER_SAVING                90                60                 0                 0
  2:           VIDEO                70                60                 0                 0
  3:              VR                70                90                 0                 0
  4:         COMPUTE                30                60                 0                 6
  5:          CUSTOM                 0                 0                 0                 0
 -1:            AUTO              Auto
```
The amdgpu driver package version: 19.30 has an additional Power mode, as seen with *--ppm* option (showing one of two GPU on a system with the amdgpu All-0pen driver stack installed instead of the amdgpu-pro stack):
```
AMD Wattman features enabled: 0xffff7fff
amdgpu version: 19.30-838629
2 AMD GPUs detected, 2 may be compatible, checking...
2 are confirmed compatible.

Card: /sys/class/drm/card1/device/
Power Performance Mode: manual
  0:  BOOTUP_DEFAULT             -             -             -             -             -             -
  1:  3D_FULL_SCREEN             0           100            30             0           100            10
  2:    POWER_SAVING            10             0            30             -             -             -
  3:           VIDEO             -             -             -            10            16            31
  4:              VR             0            11            50             0           100            10
  5:         COMPUTE             0             5            30             0           100            10
  6:          CUSTOM             -             -             -             -             -             -
 -1:            AUTO          Auto
```
## GPU Type Dependent Behavior
AMD GPU's compatible with the amdgpu open source drivers are of three different types in terms of how frequency/voltage
is managed.  GPUs of Vega10 and earlier architecture rely on the definition of specific power states to determine
the clock frequency and voltage.  The GPU will operate only at the specific Frequency/Voltage states that are defined, 
and move between states based on power, temperature, and loading.  These GPU's are of type 1, if the P-state table
is readable and type 0 if it is not.  For GPUs of Vega20 architecture or newer, it appears that Voltage/Frequency curves
are defined with three points on a Voltage vs. Frequency curve.  These GPU's are classified as type 2.

With the *amdgpu-ls* tool, you can determine if your card is of type 1 or 2. Here are the relevant lines from the 
output for and RX Vega64 GPU and the Radeon VII:
```
Decoded Device ID: R9 290X DirectCU II
GPU Frequency/Voltage Control Type: 0

Decoded Device ID: RX Vega64
GPU Frequency/Voltage Control Type: 1

Decoded Device ID: Radeon VII
GPU Frequency/Voltage Control Type: 2
```

Monitor and Control utilities will differ between the three types.
* For type 0, you can monitor the P-state details with monitor utilities, but you can NOT define P-states or set P-state masks.
* For type 1, you can monitor the P-state details with monitor utilities, and you can define P-states and set P-state masks.
* For Type 2, you can monitor current Clocks frequency and P-states, with latest amdgpu drivers.  The SCLK and MCLK curve end points can be controlled, which has the equivalent effect as P-state masking for Type 1 cards.  You are also able to modify the three points that define the Vddc-SCLK curve. I have not attempted to OC the card yet, but I assume redefining the 3rd point would be the best approach.  For underclocking, lowering the SCLK end point is effective.  I don't see a curve defined for memory clock on the Radeon VII, so setting memory clock vs. voltage doesn't seem possible at this time.  There also appears to be an inconsistency in the defined voltage ranges for curve points and actual default settings. 

Below is a plot of what I extracted for the Frequency vs Voltage curves of the RX Vega64 and the Radeon VII.

![](Type1vsType2.png)

## Using amdgpu-monitor
By default, *amdgpu-monitor* will display a text based table in the current terminal window that updates
every sleep duration, in seconds, as defined by *--sleep N* or 2 seconds by default. If you are using
water cooling, you can use the *--no_fans* to remove fan functionality.
```
┌─────────────┬────────────────┬────────────────┐
│Card #       │card1           │card0           │
├─────────────┼────────────────┼────────────────┤
│Model        │RX Vega64       │Vega 20  Radeon │
│Load %       │99              │93              │
│Power (W)    │60.0            │138.0           │
│Power Cap (W)│140.0           │140.0           │
│Energy (kWh) │1e-06           │3e-06           │
│T (C)        │30.0            │47.0            │
│VddGFX (mV)  │1037            │1062            │
│Fan Spd (%)  │0               │93              │
│Sclk (MHz)   │1536Mhz         │                │
│Sclk Pstate  │6               │-1              │
│Mclk (MHz)   │945Mhz          │                │
│Mclk Pstate  │3               │-1              │
│Perf Mode    │4-COMPUTE       │4-COMPUTE       │
└─────────────┴────────────────┴────────────────┘
```
The fields are the same as the GUI version of the display, available with the *--gui* option.
![](amdgpu-monitor_scrshot.png)

The first row gives the card number for each GPU.  This number is the integer used by the driver for each GPU.  Most fields are self describing.  The Power Cap field is especially useful in managing compute power efficiency, and lowering the cap can result in more level loading and overall lower power usage for little compromise in performance.  The Energy field is a derived metric that accumulates GPU energy usage, in kWh, consumed since the monitor started. Note that total card power usage may be more than reported GPU power usage.  Energy is calculated as the product of the latest power reading and the elapsed time since the last power reading. 

You will notice no clock frequencies or valid P-states for the Vega 20 card.  This is because of a limitation in the first drivers that supported Vega 20 which have a change in the way frequency vs voltage is managed. In later version of the drivers, actual clock frequency and P-states are readable. The P-state table for Vega 20 is a definition of frequency vs. voltage curves, so setting P-states to control the GPU is no longer relevant, but these concepts are used in reading current states.

The Perf Mode field gives the current power performance mode, which may be modified in with *amdgpu-pac*.  These modes affect the how frequency and voltage are managed versus loading.  This is a very important parameter when managing compute performance.

Executing *amdgpu-monitor* with the *--plot* option will display a continuously updating plot of the critical GPU parameters.
![](amdgpu-plot_scrshot.png)

Having an *amdgpu-monitor* Gtx window open at startup may be useful if you run GPU compute projects that autostart and you need to quickly confirm that *amdgpu-pac* bash scripts ran as expected at startup (see [Using amdgpu-pac](#using-amdgpu-pac)). You can have *amdgpu-monitor --gui* automatically launch at startup or upon reboot by using the startup utility for your system. In Ubuntu, for example, open *Startup Applications Preferences* app, then in the Preferences window select *Add* and use something like this in the command field:
```
/usr/bin/python3 /home/<user>/Desktop/amdgpu-utils/amdgpu-monitor --gui
```
where `/amdgpu-utils` may be a soft link to your current distribution directory. This startup approach does not work for the default Terminal text execution of *amdgpu-monitor*. 

## Using amdgpu-plot
In addition to being called from *amdgpu-monitor* with the *--plot* option, *amdgpu-plot* may be ran as a standalone utility.  Just execute *amdgpu-plot --sleep N* and the plot will update at the defined interval.  It is not recommended to run both the monitor with an independently executed plot, as it will result in twice as many reads from the driver files.  Once the plots are displayed, individual items on the plot can be toggled by selecting the named button on the plot display.

The *--stdin* option is used by *amdgpu-monitor --plot* in its execution of *amdgpu-plot*.  This option along with *--simlog* option can be used to simulate a plot output using a log file generated by *amdgpu-monitor --log*.  I use this feature when troubleshooting problems from other users, but it may also be useful in benchmarking performance.  An example of the command line for this is as follows:
```
cat log_monitor_0421_081038.txt | ./amdgpu-plot --stdin --simlog
```

## Using amdgpu-pac
By default, *amdgpu-pac* will open a Gtk based GUI to allow the user to modify GPU performance parameters.  I strongly suggest that you completely understand the implications of changing any of the performance settings before you use this utility.  As per the terms of the GNU General Public License that covers this project, there is no warranty on the usability of these tools.  Any use of this tool is at your own risk.

To help you manage the risk in using this tool, two modes are provided to modify GPU parameters.  By default, a bash file is created that you can review and execute to implement the desired changes.  Here is an example of that file:
```
#!/bin/sh
###########################################################################
## amdgpu-pac generated script to modify GPU configuration/settings
###########################################################################

###########################################################################
## WARNING - Do not execute this script without completely
## understanding appropriate value to write to your specific GPUs
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
# Card1   Vega 10 XT [Radeon RX Vega 64] (rev c1)
# /sys/class/drm/card1/device/
# 
set -x
# Powercap Old:  140 New:  140 Min: 0 Max: 220
sudo sh -c "echo '140000000' >  /sys/class/drm/card1/device/hwmon/hwmon6/power1_cap"
#sck p-state: 0 : 852 MHz, 800 mV
sudo sh -c "echo 's 0 852 800' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 1 : 991 MHz, 900 mV
sudo sh -c "echo 's 1 991 900' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 2 : 1084 MHz, 950 mV
sudo sh -c "echo 's 2 1084 950' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 3 : 1138 MHz, 1000 mV
sudo sh -c "echo 's 3 1138 1000' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 4 : 1200 MHz, 1050 mV
sudo sh -c "echo 's 4 1200 1050' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 5 : 1401 MHz, 1100 mV
sudo sh -c "echo 's 5 1401 1100' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 6 : 1530 MHz, 1150 mV
sudo sh -c "echo 's 6 1530 1150' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#sck p-state: 7 : 1630 MHz, 1200 mV
sudo sh -c "echo 's 7 1630 1200' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#mck p-state: 0 : 167 MHz, 800 mV
sudo sh -c "echo 'm 0 167 800' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#mck p-state: 1 : 500 MHz, 800 mV
sudo sh -c "echo 'm 1 500 800' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#mck p-state: 2 : 800 MHz, 950 mV
sudo sh -c "echo 'm 2 800 950' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
#mck p-state: 3 : 945 MHz, 1100 mV
sudo sh -c "echo 'm 3 945 1100' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# Selected: ID=4, name=COMPUTE
sudo sh -c "echo 'manual' >  /sys/class/drm/card1/device/power_dpm_force_performance_level"
sudo sh -c "echo '4' >  /sys/class/drm/card1/device/pp_power_profile_mode"
sudo sh -c "echo 'c' >  /sys/class/drm/card1/device/pp_od_clk_voltage"
# Sclk P-State Mask Default:  0 1 2 3 4 5 6 7 New:  4 5 6
sudo sh -c "echo '4 5 6' >  /sys/class/drm/card1/device/pp_dpm_sclk"
# Mclk P-State Mask Default:  0 1 2 3 New:  3
sudo sh -c "echo '3' >  /sys/class/drm/card1/device/pp_dpm_mclk"
```

When you execute *amdgpu-pac*, you will notice a message bar at the bottom of the interface.  By default, it informs you of the mode you are running in.  By default, the operation mode is to create a bash file, but with the *--execute_pac* (or *--execute*) command line option, the bash file will be automatically executed and then deleted.  The message bar will indicate this status.  Because the driver files are writable only by root, the commands to write configuration settings are executed with sudo.  The message bar will display in red when credentials are pending.  Once executed, a yellow message will remind you to check the state of the gpu with *amdgpu-monitor*.  I suggest to using the monitor routine when executing pac to see the changes in real-time.

The command line option *--force_write* will result in all configuration parameters to be written to the bash file.  The default behavior since v2.4.0 is to write only changes.  The *--force_write* is useful for creating a bash file that can be execute to set your cards to a known state. As an example, you could use such a file to configure your GPUs on boot up (see [Setting GPU Automatically at Startup](#setting-gpu-automatically-at-startup)).

### The amdgpu-pac interface for Type 1 cards
![](amdgpu-pac_type1.png)

### The amdgpu-pac interface for Type 2 cards
![](amdgpu-pac_type2.png)

In the interface, you will notice entry fields for indicating new values for specific parameters.  In most cases, the values in these fields will be the current values, but in the case of P-state masks, it will show the default value instead of the current value.  If you know how to obtain the current value, please let me know!

Note that when a PAC bash file is executed either manually or automatically, the resulting fan PWM (% speed) may be slightly different from what you see in the Fan PWM entry field.  The direction and magnitude of differences between expected and realized fan speeds can depend on card model.  You will need to experiment with different settings to determine how it works with your card.  I recommend running these experimental settings when the GPU is not under load.  If you know the cause of the differences between entered and final fan PWM values, let me know. 

Changes made with *amdgpu-pac* do not persist through a system reboot. To reestablish desired GPU settings after a reboot, either re-enter them using *amdgpu-pac* or *amdgpu-pac --execute*, or execute a previously saved bash file. *Amdgpu-pac* bash files must retain their originally assigned file name to run properly. See [Setting GPU Automatically at Startup](#setting-gpu-automatically-at-startup) for how to run PAC bash scripts automatically at system startup.

For Type 1 cards, while changes to power caps and fan speeds can be made while the GPU is under load, for *amdgpu-pac* to work properly, other changes may require that the GPU not be under load, *i.e.*, that sclk P-state and mclk P-state are 0. Possible consequences with making changes under load is that the GPU become stuck in a 0 P-state or that the entire system becomes slow to respond, where a reboot will be needed to restore full GPU functions. Note that when you change a P-state mask, default mask values will reappear in the field after Save, but your specified changes will have been implemented on the card and show up in *amdgpu-monitor*. Some changes may not persist when a card has a connected display. 

Some basic error checking is done before writing, but I suggest you be very certain of all entries before you save changes to the GPU.

## Updating the pci.id decode file
Starting in v2.7.0, the system PCI ID file is used, making the *amdgpu-pciid* command obsolete. It will be removed in
the next major release.

In determining the GPU display name, *amdgpu-utils* will examine 2 sources.  The output of *lscpi -k -s nn:nn.n* is
used to generate a complete name and an algorithm is used to generate a shortened version.  From the driver files, a
set of files (vendor, device, subsystem_vendor, subsystem_device) contain a 4 parts of the Device ID are read and used
to extract a GPU model name from system pci.ids file which is sourced from
[https://pci-ids.ucw.cz/]( https://pci-ids.ucw.cz/) where a comprehensive list is maintained.  The system file can
be updated from the original source with the command:
```
sudo update-pciids
```
If your GPU is not listed in the extract, the pci.id website has an interface to allow the user to request an
addition to the master list.  

## Optimizing Compute Performance-Power
The *amdgpu-utils* tools can be used to optimize performance vs. power for compute workloads by leveraging
its ability to measure power and control relevant GPU settings.  This flexibility allows one to execute a
DOE to measure the effect of GPU settings on the performance in executing specific workloads.  In SETI@Home performance, the Energy feature has also been built into [benchMT](https://github.com/Ricks-Lab/benchMT) to benchmark power and execution times for various work units.  This, combined with the log file produced with
*amdgpu-monitor --gui --log*, may be useful in optimizing performance.

![](https://i.imgur.com/YPuDez2l.png)

## Setting GPU Automatically at Startup
If you set your system to run *amdgpu-pac* bash scripts automatically, as described in this section, note that changes in your hardware or graphic drivers may cause potentially serious problems with GPU settings unless new PAC bash files are generated following the changes. Review the [Using amdgpu-pac](#using-amdgpu-pac) section before proceeding.

One approach to automatically execute a saved PAC bash file at startup or reboot is to run it as a cron job. To do this, first create a PAC bash file of your optimized GPU settings using the *amdgpu-pac --force-write* option. The executable file will be named *pac_writer_[string-of-characters].sh* and will be created in your current amdgpu-utils directory. A separate file is needed for each GPU card. Copy the file(s) to a convenient directory, without renaming or changing attributes. (If you leave it in the amdgpu-utils directory, then it may be lost with the next distribution update.) In the example here, two bash files were copied to a new directory, `/etc/cron.custom`. Now open crontab, the table that drives cron, using the command `~$ sudo crontab -e`. This will open crontab in your default terminal text editor. (You may be prompted to choose an editor like *nano* or *vi*.) Add a line like this, including an explicit path for each card's bash file:
```
@reboot /etc/cron.custom/pac_writer_[string for 1st card].sh
@reboot /etc/cron.custom/pac_writer_[string for 2nd card].sh
```
then save and exit. The next time you reboot, or the system restarts after a power outage, your GPU card(s) will be ready to run with optimized settings.  Because some PAC parameters can't be changed when a card is under load, you will want to make sure that the PAC bash script executes before the card begins computing. For example, if you have a *boinc-client* that automatically runs on startup, then consider delaying it for 30 seconds using the cc_config.xml option *<start_delay>30</start_delay>*.

Another approach, perhaps a more reliable one, is to execute PAC bash scripts as a systemd startup service. As with setting up files for crontab, from *amdgpu-pac --force_write* set your optimal configurations for each GPU, then Save All. Change ownership to root of each card's bash file: `sudo chown root pac_writer*.sh`

For each bash file, create a symlink (soft link) that corresponds to the card number referenced in each linked bash file, using simple descriptive names, *e.g.*, pac_writer_card1, pac_writer_card2, *etc.*. These links are optional, but can make management of new startup bash files easier. Links are used in the startup service example, below. Don't forget to reform the link(s) each time a new PAC bash file is written for a card. 
 
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
The Type=oneshot service allows use of more than one ExecStart.  In this example, three bash files are used for two cards, where two alternative files are used for one card that the system may recognize as either card0 or card1; see further below for an explanation. 

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

On the next reboot or restart, the GPU(s) will be set with the PAC run parameters. If you want to test the bash script(s) before rebooting, run: `~$ sudo systemctl start amdgpu-pac-startup.service`. 

One or more of your cards' numbers that are assigned by amdgpu drivers may change following a system or driver update and restart. With subsequent updates or restarts, a card can switch back to its original number. When a switch occurs, the bash file written for a previous card number will still be read at startup, but will have no effect, causing the renumbered card to run at its default settings. To deal with this possibility, whether using crontab or systemd, you can create an alternative PAC bash file after a renumbering event and add these alternative files in your crontab or systemd service. You will probably just need two alternative bash files for a card that is subject to amdgpu reindexing. A card's number is shown by *amdgpu-ls* and also appears in *amdgpu-monitor* and *amdgpu-plot*. Card reindexing does not affect a card's PCI ID number, which corresponds to its PCIe slot number on the motherboard. PCI IDs are listed by *amdgpu-ls*. If you know what causes GPU card index switching, let me know.  
