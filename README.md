# Ricks-Lab GPU Utilities

![](https://img.shields.io/github/license/Ricks-Lab/gpu-utils)
[![PyPI version](https://badge.fury.io/py/rickslab-gpu-utils.svg)](https://badge.fury.io/py/rickslab-gpu-utils)
[![Downloads](https://pepy.tech/badge/rickslab-gpu-utils)](https://pepy.tech/project/rickslab-gpu-utils)
![GitHub commit activity](https://img.shields.io/github/commit-activity/y/Ricks-Lab/gpu-utils)
![GitHub last commit](https://img.shields.io/github/last-commit/Ricks-Lab/gpu-utils)

## rickslab-gpu-utils

A set of utilities for monitoring GPU performance and modifying control settings.

In order to get maximum capability of these utilities, you should be running with a kernel that
provides support of the GPUs you have installed.  If using AMD GPUs, installing the latest amdgpu
driver package or the latest ROCm release, may provide additional capabilities. If you have Nvidia
GPUs installed, you should have `nvidia-smi` installed in order for the utility reading of the cards
to be possible.  Writing to GPUs is currently only possible for AMD GPUs, and only with compatible
cards and with the the AMD ppfeaturemask set to 0xfffd7fff. This can be accomplished by adding
`amdgpu.ppfeaturemask=0xfffd7fff` to the `GRUB_CMDLINE_LINUX_DEFAULT` value in
`/etc/default/grub` and executing `sudo update-grub`

Check out the [User Guide](https://github.com/Ricks-Lab/gpu-utils/blob/master/docs/USER_GUIDE.md)!

## Installation

### Debian Package Installation

First, remove any previous PyPI installation and exit that terminal:
```
pip uninstall rickslab-gpu-utils
exit
```
Also, remove any previous ricks-amdgpu-utils installation:
```
sudo apt purge ricks-amdgpu-utils
sudo apt autoremove
```
Next, add the *rickslab-gpu-utils* repository:
```
wget -q -O - https://debian.rickslab.com/PUBLIC.KEY | sudo apt-key add -

echo 'deb [arch=amd64] https://debian.rickslab.com/gpu-utils/ eddore main' | sudo tee /etc/apt/sources.list.d/rickslab-gpu-utils.list

sudo apt update
```
Then install the package with apt:
```
sudo apt install rickslab-gpu-utils
```

### PyPI Installation

Install the latest package from [PyPI](https://pypi.org/project/rickslab-gpu-utils/) with the following
commands:
```
pip3 install rickslab-gpu-utils
```
Or, use the pip upgrade option if you have already installed a previous version:
```
pip3 install rickslab-gpu-utils -U
```

If you have issues, try uninstalling the original package first.  You should also make sure
that any previous install of *ricks-amdgpu-utils* is removed:
```
pip3 uninstall rickslab-gpu-utils
pip3 uninstall ricks-amdgpu-utils
```

If you still get an old version, then specify not to use cached files:
```
pip3 install --no-cache-dir rickslab-gpu-utils
```

## gpu-chk

This utility verifies if the environment is compatible with **rickslab-gpu-utils**.

## gpu-ls

This utility displays most relevant parameters for installed and compatible GPUs. The
default behavior is to list relevant parameters by GPU.  OpenCL platform information is
added when the *--clinfo* option is used.  A brief listing of key parameters is available
with the *--short* command line option.  A simplified table of current GPU state is
displayed with the *--table* option. The *--no_fan* can be used to ignore fan settings.
The *--pstate* option can be used to output the p-state table for each GPU instead of
the list of basic parameters.  The *--ppm* option is used to output the table of available
power/performance modes instead of basic parameters.

## gpu-mon

A utility to give the current state of all compatible GPUs. The default behavior
is to continuously update a text based table in the current window until Ctrl-C is
pressed.  With the *--gui* option, a table of relevant parameters will be updated
in a Gtk window.  You can specify the delay between updates with the *--sleep N*
option where N is an integer > zero that specifies the number of seconds to sleep
between updates.  The *--no_fan* option can be used to disable the reading and display
of fan information.  The *--log* option is used to write all monitor data to a psv log
file.  When writing to a log file, the utility will indicate this in red at the top of
the window with a message that includes the log file name. The *--plot* will display a
plot of critical GPU parameters which updates at the specified *--sleep N* interval. If
you need both the plot and monitor displays, then using the --plot option is preferred
over running both tools as a single read of the GPUs is used to update both displays.
The *--ltz* option results in the use of local time instead of UTC.

## gpu-plot

A utility to continuously plot the trend of critical GPU parameters for all compatible
GPUs. The *--sleep N* can be used to specify the update interval.  The *gpu-plot*
utility has 2 modes of operation.  The default mode is to read the GPU driver
details directly, which is useful as a standalone utility.  The *--stdin* option
causes *gpu-plot* to read GPU data from stdin.  This is how *gpu-mon* produces the
plot and can also be used to pipe your own data into the process.  The *--simlog*
option can be used with the *--stdin* when a monitor log file is piped as stdin.
This is useful for troubleshooting and can be used to display saved log results.
The *--ltz* option results in the use of local time instead of UTC.  If you plan
to run both *gpu-plot* and *gpu-mon*, then the *--plot* option of the *gpu-mon*
utility should be used instead of both utilities in order reduce data reads by
a factor of 2.

## gpu-pac

Program and Control compatible GPUs with this utility.  By default, the commands to
be written to a GPU are written to a bash file for the user to inspect and run.  If you
have confidence, the *--execute_pac* option can be used to execute and then delete the
saved bash file.  Since the GPU device files are writable only by root, sudo is used to
execute commands in the bash file, as a result, you will be prompted for credentials in the
terminal where you executed *gpu-pac*. The *--no_fan* option can be used to eliminate
fan details from the utility. The *--force_write* option can be used to force all configuration
parameters to be written to the GPU.  The default behavior is to only write changes.

## New in Development -  v3.5.9

* Optimize *gpu-mon* table size.
* Toggle button color to match enable/disable status of plot line.
* When install type is repository, force use of repository *gpu-plot* from *gpu-mon*.

## Development Plans

* Optimize plot utilities for performance.
* Add status read capabilities for Intel GPUs.
* Add pac capabilities for Nvidia GPUs.

## Known Issues

* Some windows do not support scrolling or resize, making it unusable for lower resolution installations.
* I/O error when selecting CUSTOM ppm.  Maybe it requires arguments to specify the custom configuration.
* Doesn't work well with Fiji ProDuo cards.
* P-state mask gets intermittently reset for GPU used as display output.
* Utility *gpu-pac* doesn't show what the current P-state mask is.  Not sure if that can be read back.
* Utility *gpu-pac* fan speed setting results in actual fan speeds a bit different from setting and pac interface shows actual values instead of set values.

## References

* Original inspiration for this project: [Reddit](https://www.reddit.com/r/Amd/comments/agwroj/how_to_overclock_your_amd_gpu_on_linux/?st=JSL25OVP&sh=306c2d15)
* Phoronix articles including these: [PowerCap](https://www.phoronix.com/scan.php?page=news_item&px=AMDGPU-Quick-WattMan-Cap-Test), [HWMon](https://www.phoronix.com/scan.php?page=news_item&px=AMDGPU-Linux-4.17-Round-1)
* Repositories: [amdgpu-clocks](https://github.com/sibradzic/amdgpu-clocks), [WattmanGTK](https://github.com/BoukeHaarsma23/WattmanGTK), [ROC-smi](https://github.com/RadeonOpenCompute/ROC-smi)
* Relevant Kernel Details: [Kernel Details](https://www.kernel.org/doc/html/latest/gpu/amdgpu.html)
* PCI ID Decode Table: [PCI IDs](https://pci-ids.ucw.cz/v2.2/pci.ids)
* Radeon VII discussion on Reddit: [Radeon VII OC](https://www.reddit.com/r/linux_gaming/duplicates/au7m3x/radeon_vii_on_linux_overclocking_undervolting/)
* Example use cases: [wiki.archlinux.org](https://wiki.archlinux.org/index.php/AMDGPU)

## History

## New in Previous Release -  v3.5.8

* Fixed bug in determining AMD GPU card type.  Now it properly identifies APU and Legacy types.

## New in Previous Release -  v3.5.7

* More robust determination of install type and display this with *--about* and in logger.
* Implementation of scroll within PAC window.
* Fixed plot crash for invalid ticker increment.
* Code robustness improvements with more typing for class variables.

## New in Previous Release -  v3.5.6

* Fixed issue in reading AMD FeatureMask for Kernel 5.11

## New in Previous Release -  v3.5.5

* Include debian release package.
* Check gtk initialization for errors and handle nicely.
* Use logger to output plot exceptions.
* Check number of compatible and readable GPUs at utility start.
* Minor User Guide and man page improvements.
* Use minimal python packages in requirements.

### New in Previous Release -  [v3.5.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v3.5.0)

* Utilities now include reading of NV GPUs with full gpu-ls, gpu-mon, and gpu-plot support!
* Update name from **amdgpu-utils** to **rickslab-gpu-utils**.
* Improved PyPI packaging.
* Updated User Guide to cover latest features and capabilities.
* Improved robustness of NV read by validating sensor support for each query item the first time read.  This will assure functionality on older model GPUs.
* Fixed issue in setting display model name for NV GPUs.
* Improved how lack of voltage readings for NV is handled in the utilities.
* Fixed an issue in assessing compute capability when GPUs of multiple vendors are installed.

### New in Previous Release  -  [v3.3.14](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v3.3.14)

* Display card path details in logger whenever card path exists.
* Implemented read capabilities for Nvidia.  Now supported by all utilities except pac.
* Added APU type and tuned parameters read/displayed for AMD APU integrated GPU.
* Read generic pcie sensors for all types of GPUs.
* Improved lspci search by using a no-shell call and using compiled regex.
* Implement PyPI package for easy installation.
* More robust handling of missing Icon and PCIID files.

#### New in Previous Release  -  [v3.2.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v3.2.0)

* Fixed CRITICAL issue where Zero fan speed could be written when invalid fan speed was read from the GPU.
* Fixed issue in reading pciid file in Gentoo (@CH3CN).
* Modified setup to indicate minimum instead of absolute package versions (@smoe).
* Modified requirements to include min/max package versions for major packages.
* Fixed crash for missing pci-ids file and add location for Arch Linux (@berturion).
* Fixed a crash in *amdgpu-pac* when no fan details could be read (laptop GPU).
* Fixed deprecation warnings for several property setting functions.  Consolidated all property setting to a single function in a new module, and ignore warnings for those that are deprecated.  All deprecated actions are marked with FIXME in GPUgui.py.
* Replaced deprecated set properties statement for colors with css formatting.
* Implemented a more robust string format of datetime to address datetime conversion for pandas in some installations.
* Implemented dubug logging across the project.  Activated with --debug option and output saved to a .log file.
* Updated color scheme of Gtk applications to work in Ubuntu 20.04. Unified color scheme across all utilities.
* Additional memory parameters added to utilities.
* Read ID information for all GPUs and attempt to decode GPU name.  For cards with no card path entry, determine system device path and use for reading ID.  Report system device path in *amdgpu-ls*.  Add *amdgpu-ls --short* report to give brief description of all installed GPUs.

#### New in Previous Release  -  [v3.0.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v3.0.0)

* Style and code robustness improvements
* Deprecated  *amdgpu-pciid*  and removed all related code.
* Complete rewrite based on benchMT learning.  Simplified code with ObjDict for GpuItem parameters and use of class variables for generic behavior parameters.
* Use lspci as the starting point for developing GPU list and classify by vendor, readability, writability, and compute capability.  Build in potential to be generic GPU util, instead of AMD focused.
* Test for readability and writability of all GPUs and apply utilities as appropriate.
* Add assessment of compute capability.
* Eliminated the use of lshw to determine driver compatibility and display of driver details is now informational with no impact on the utilities.
* Add p-state masking capability for Type 2 GPUs.
* Optimized pac writing to GPUs.

#### New in Previous Release  -  [v2.7.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.7.0)

* Initial release of man pages
* Modifications to work with distribution installation
* Use system pci.ids file and make *amdgpu-pciid* obsolete
* Update setup.py file for successful installation.

#### New in Previous Release  -  [v2.6.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.6.0)

* PEP8 style modifications
* Fixed a bug in monitor display.
* Implement requirements file for with and without a venv.
* Found and fixed a few minor bugs.
* Fixed issue with *amdgpu-plot* becoming corrupt over time.
* Implemented clean shutdown of monitor and better buffering to plot. This could have caused in problems in systems with many GPUs.

#### New in Previous Release  -  [v2.5.2](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.5.2)

* Some preparation work for [Debian package](https://tracker.debian.org/pkg/ricks-amdgpu-utils) (@smoe).
* Added *--ltz* option to use local times instead of UTC for logging and plot data.
* Added 0xfffd7fff to valid amdgpu.ppfeaturemask values (@pastaq).
* Updates to User Guide to include instructions to apply PAC conditions on startup (@csecht).

#### New in Previous Release  -  [v2.5.1](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.5.1)

* Fixed a compatibility issue with matplotlib 3.x.  Converted time string to a datetime object.
* Display version information for pandas, matplotlib, and numpy with the *--about* option for *amdgpu-plot*

#### New in Previous Release  -  [v2.5.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.5.0)

* Implemented the *--plot* option for amdgpu-monitor.  This will display plots of critical GPU parameters that update at an interval defined by the *--sleep N* option.
* Errors in reading non-critical parameters will now show a warning the first time and are disabled for future reads.
* Fixed a bug in implementation of compatibility checks and improved usage of try/except.

#### New in Previous Release  -  [v2.4.0](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.4.0)

* Implemented *amdgpu-pac* feature for type 2 Freq/Voltage controlled GPUs, which includes the Radeon VII.
* Implemented the *amdgpu-pac --force_write* option, which writes all configuration parameters to the GPU, even if unchanged.  The default behavior is changed to now only write changed configuration parameters.
* Indicate number of changes to be written by PAC, and if no changes, don't execute bash file.  Display execute complete message in terminal, and update messages in PAC message box.
* Implemented a new GPU type 0, which represent some older cards whose p-states can not be changed.
* Tuned *amdgpu-pac* window format.

#### New in Previous Release  -  [v2.3.1](https://github.com/Ricks-Lab/amdgpu-utils/releases/tag/v2.3.1)

* Fixed and improved Python/Kernel compatibility checks.
* Added Python2 compatible utility to check *amdgpu-utils* compatibility.
* Fixed confusing mode/level fileptr names.
* Removed CUSTOM PPM mode until I figure out syntax.
* Implemented classification of card type based on how it implements frequency/voltage control.  This is reported by *amdgpu-ls* and alters the behavior of both *amdgpu-pac* and *amdgpu-monitor*.
* Changed dpkg error to a warning to handle custom driver installs.
* Initial [User Guide](docs/USER_GUIDE.md) - [Need contributors!](https://github.com/Ricks-Lab/amdgpu-utils/issues/13)

#### New in Previous Release  -  v2.3.0

* Implemented a message box in amdgpu-pac to indicate details of PAC execution and indicate if sudo is pending credential entry.
* Implement more robust classification of card compatibility and only use compatible GPUs in the utilities.
* Official release of amdgpu-pciid which updates a local list of GPU names from the official pci.ids website.
* Optimized refresh of data by moving static items to a different function and only read those that are dynamic.
* Power Cap and Fan parameters can be reset by setting to -1 in the *amdgpu-pac* interface.
* Initial basic functionality for Radeon VII GPU!

#### New in Previous Release  -  v2.2.0

* Major bug fix in the way HWMON directory was determined.  This fixes an issue in not seeing sensor files correctly when a some other card is resident in a PCIe slot.
* Implemented logging option *--log* for amdgpu-monitor. A red indicator will indicate active logging and the target filename.
* Implemented energy meter in amdgpu-monitor.
* Implemented the ability to check the GPU extracted ID in a pci.ids file for correct model name.  Implemented a function to extract only AMD information for the pci.ids file and store in the file amd_pci_id.txt which is included in this distribution.
* Optimized long, short, and decoded GPU model names.
* Alpha release of a utility to update device decode data from the pci.ids website.

#### New in Previous Release  -  v2.1.0

* Significant bug fixes and error proofing.  Added messages to stderr for missing driver related files.
* Added fan monitor and control features.
* Implemented --no_fan option across all tools.  This eliminates the reading and display of fan parameters and useful for those who have installed GPU waterblocks.
* Implemented P-state masking, which limits available P-states to those specified. Useful for power management.
* Fixed implementation of global variables that broke with implementation of modules in library.
* Added more validation checks before writing parameters to cards.

#### New in Previous Release  -  v2.0.0

* Many bug fixes!
* First release of amdgpu-pac.
* Add check of amdgpu driver in the check of environment for all utilities.  Add display of amdgpu driver version.
* Split list functions of the original amdgpu-monitor into amdgpu-ls.
* Added --clinfo option to amdgpu-ls which will list openCL platform details for each GPU.
* Added --ppm option to amdgpu-ls which will display the table of available power/performance modes available for each GPU.
* Error messages are now output to stderr instead stdout.
* Added power cap and power/performance mode to the monitor utilities.  I have also included them in the amdgpu-ls display in addtion to the power cap limits.

#### New in Previous Release  -  v1.1.0

* Added --pstates feature to display table of p-states instead of GPU details.
* Added more error checking and exit if no compatible AMD GPUs are found.

#### New in Previous Release  -  v1.0.0

* Completed implementation of the GPU Monitor tool.
