# amdgpu-utils
A set of utilities for monitoring and customizing GPU performance

In order to use any of these utilities, you must first set your linux machine 
to boot with amdgpu.ppfeaturemask=0xffff7fff.  This can be accomplished be adding
amdgpu.ppfeaturemask=0xffff7fff to the GRUB_CMDLINE_LINUX_DEFAULT value in 
/etc/default/grub and executing *sudo update-grub*

## amdgpu-monitor
A utility to give the current state of all compatible GPUs.  The default behavior
is to just output relevant parameters. With the *--loop* option, a table of relevant
paramters will be continuously updated.

## Development plans
* Enhance monitor tool with GTK GUI.
* Develop a tool to customize GPU settings including p-state details.
* Develop a startup utility to initialize GPU settings at boot up.
