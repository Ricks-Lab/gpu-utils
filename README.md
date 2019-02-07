# amdgpu-utils
A set of utilities for monitoring and customizing GPU performance

In order to use any of these utilities, you must have *amdgpu* open source driver
package installed. You also must first set your linux machine to boot with
amdgpu.ppfeaturemask=0xffff7fff.  This can be accomplished by adding
amdgpu.ppfeaturemask=0xffff7fff to the GRUB_CMDLINE_LINUX_DEFAULT value in 
/etc/default/grub and executing *sudo update-grub*

## amdgpu-ls
This utility displays most relevant parameters for installed AMD GPUs.  The default
behavior is to list relevant parameters by GPU.  OpenCL platform information is added
when the *--clinfo* option is used.  The *--pstate* option can be used to output the
p-state table for each GPU instead of the list of basic parameters.  The *--ppm* option
is used to output the table of available power/performance modes instead of basic
parameters.

## amdgpu-monitor
A utility to give the current state of all compatible AMD GPUs. The default behavior
is to continuously update a text based table in the current window unitl Ctrl-C is
pressed.  With the *--gui* option, a table of relevant parameters will be
updated in a Gtk window.  You can specify the delay between updates with the
*--sleep N* option where N is an integer > zero that specifies the number of seconds
to sleep.

## New in this Release  -  v2.0.0
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
* Enhance formatting in Gtk monitor tool. Need to improve my Gtk skills!
* Add the capability for amdgpu-ls to display power/performance modes.
* Develop a tool to customize GPU settings including p-state details, power cap, and power/performance modes.
* Develop a startup utility to initialize GPU settings at boot up.
