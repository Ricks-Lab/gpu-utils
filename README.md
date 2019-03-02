# amdgpu-utils
A set of utilities for monitoring AMD GPU performance and modifying control settings.

In order to use any of these utilities, you must have the *amdgpu* open source driver
package installed. You also must first set your linux machine to boot with
amdgpu.ppfeaturemask=0xffff7fff.  This can be accomplished by adding
amdgpu.ppfeaturemask=0xffff7fff to the GRUB_CMDLINE_LINUX_DEFAULT value in 
/etc/default/grub and executing *sudo update-grub*

## amdgpu-ls
This utility displays most relevant parameters for installed and compatible AMD GPUs.
The default behavior is to list relevant parameters by GPU.  OpenCL platform information
is added when the *--clinfo* option is used.  The *--no_fan* can be used to ignore fan
settings.  The *--pstate* option can be used to output the p-state table for each GPU
instead of the list of basic parameters.  The *--ppm* option is used to output the table
of available power/performance modes instead of basic parameters.

## amdgpu-monitor
A utility to give the current state of all compatible AMD GPUs. The default behavior
is to continuously update a text based table in the current window unitl Ctrl-C is
pressed.  With the *--gui* option, a table of relevant parameters will be updated
in a Gtk window.  You can specify the delay between updates with the *--sleep N*
option where N is an integer > zero that specifies the number of seconds to sleep.
The *--no_fan* option can be used to disable the reading and display of fan
information.  The *--log* option is used to write all monitor data to a psv log file.
When writing to a log file, the utility will indicate this in red at the top of the 
window with a message that includes the log file name.

## amdgpu-pac
Program and Control compatible AMD GPUs with this utility.  By default, the commands to
be written to a GPU are written to a bash file for the user to inspect and run.  If you
have confidence, the *--execute_pac* option can be used to execute the bash file when saved
and then delete it. Since the GPU device files are writable only by root, sudo is used to
execute commands in the bash file, as a result, you will be prompted for credentials in the
terminal where you executed *amdgpu-pac*. The *--no_fan* option can be used to eliminate
fan details from the utility.

## amdgpu-pciid
This utility will display the version of the current pci.ids data extract
in use.  With the *--download* option, the latest pci.ids file from 
https://pci-ids.ucw.cz/ will be downloaded. With the *--install* option,
the latest pci.ids will be downloaded and filtered for AMD specific data
and written to the file used by amdgpu-utils to decode device names from the
driver provided device id.  The *--force* option can be used to update this 
file even if there is no change in version.  If your GPU model is missing
from the pci.ids file, you can use the device id of your card found with 
amdgpu-ls and make a request for the addition on the pci.ids website.

## New in this Release  -  v2.2.0
* Implemented logging option *--log* for amdgpu-monitor. A red indicator will indicate active logging and the traget filename.
* Implemented energy meter in amdgpu-monitor.
* Implemented the ability to check the extracted ID in a pci.ids for correct model name.  Implemented a function to extract only amd information for the pci.ids file and store in the file amd_pci_id.txt which is included in this distribution.
* Optimized long, short, and decoded GPU model names.
* Alpha release of a utility to update device decode data from the pci.ids website.

## New in Previous Release  -  v2.1.0
* Significant bug fixes and error proofing.  Added messages to stderr for missing driver related files.
* Added fan monitor and control features.
* Implemented --no_fan option across all tools.  This eliminates the reading and display of fan parameters and useful for those who have installed GPU waterblocks.
* Implemented P-state masking, which limits available P-states to those specified. Useful for power management.
* Fixed implementation of global variables that broke with implementation of modules in library.
* Added more validation checks before writing parameters to cards.

## New in Previous Release  -  v2.0.0
* Many bug fixes!
* First release of amdgpu-pac.
* Add check of amdgpu driver in the check of environment for all utilities.  Add display of amdgpu driver version.
* Split list functions of the original amdgpu-monitor into amdgpu-ls.
* Added --clinfo option to amdgpu-ls which will list openCL platform details for each GPU.
* Added --ppm option to amdgpu-ls which will display the table of available power/performance modes available for each GPU.
* Error messages are now output to stderr instead stdout.
* Added power cap and power/performance mode to the monitor utilities.  I have also included them in the amdgpu-ls display in addtion to the power cap limits.

## New in Previous Release  -  v1.1.0
* Added --pstates feature to display table of p-states instead of GPU details.
* Added more error checking and exit if no compatible AMD GPUs are found.

## New in Previous Release  -  v1.0.0
* Completed implementation of the GPU Monitor tool.

## Development Plans
* Write a users guide.
* Enhance formatting in Gtk monitor tool. Need to improve my Gtk skills!
* Develop a startup utility to initialize GPU settings at boot up.
* Implement an option to only write changes in amdgpu-pac.
* Implement card level compatibility flagging and use in showing only compatible cards.

## References
* Original inspiration for this project: <a href="https://www.reddit.com/r/Amd/comments/agwroj/how_to_overclock_your_amd_gpu_on_linux/?st=JSL25OVP&sh=306c2d15">Reddit</a>
* Phoronix articles including these: <a href="https://www.phoronix.com/scan.php?page=news_item&px=AMDGPU-Quick-WattMan-Cap-Test">Phoronix Power Cap</a>, <a href="https://www.phoronix.com/scan.php?page=news_item&px=AMDGPU-Linux-4.17-Round-1">Phoronix HWMon</a>
* Repositories: <a href="https://github.com/sibradzic/amdgpu-clocks">amdgpu-clocks</a>, <a href="https://github.com/BoukeHaarsma23/WattmanGTK">WattmanGTK</a>, <a href="https://github.com/RadeonOpenCompute/ROC-smi">ROC-smi</a>
* Relevant Kernel Details: <a href="https://www.kernel.org/doc/html/latest/gpu/amdgpu.html">Kernel Details</a>
* PCI ID Decode Table: <a href="https://pci-ids.ucw.cz/v2.2/pci.ids">PCI IDs</a>
