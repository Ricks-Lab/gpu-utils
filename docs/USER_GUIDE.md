# amdgpu-utils - User Guide
A set of utilities for monitoring AMD GPU performance and modifying control settings.

## Getting Started
First, this set of utils is written and tested with Python3.6.  If you are using and older
version, you will likely see syntax errors.  Unfortuntately, I don't know how to catch a
syntax error, so if you have issues, just execute:
```
./amdgpu-chk
```
and it should display a message indicating any Python or Kernel incompatibilities.  You will
also notice that there as a minumum version of the Kernel that supports these features, but be
warned, I have only tested it with 4.15.

In order to use any of these utilities, you must have the *amdgpu* open source driver
package installed. You can check with the following command:
```
dpkg -l amdgpu
```

You also must first set your linux machine to boot with amdgpu.ppfeaturemask=0xffff7fff.  This
can be accomplished by adding amdgpu.ppfeaturemask=0xffff7fff to the GRUB_CMDLINE_LINUX_DEFAULT
value in /etc/default/grub and executing *sudo update-grub* as in the following example:
```
cd /etc/default
sudo vi grub
```
Modify to include the featuremask as follows:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash pcie_aspm=off amdgpu.ppfeaturemask=0xffff7fff"
```
After saving, update grub:
```
sudo update-grub
```
and then reboot.


## Using amdgpu-ls
```AMD Wattman features enabled: 0xffff7fff
amdgpu version: 18.50-725072
2 AMD GPUs detected, 2 may be compatible, checking...
2 are confirmed compatible.

UUID: 309abc9c97ea451396334b11199d0680
amdgpu-util Compatibility: Yes
Device ID: {'vendor': '0x1002', 'device': '0x687f', 'subsystem_vendor': '0x1002', 'subsystem_device': '0x0b36'}
GPU P-State Type: 1
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

## Using amdgpu-monitor
![](docs/amdgpu-monitor_scrshot.png)

## Using amdgpu-pac
![](docs/amdgpu-pac_scrshot.png)
