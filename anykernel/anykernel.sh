### AnyKernel3 Configuration for Samsung Galaxy Z Flip 3 (b2q)
### Columbina Kernel + Droidspaces

# Properties
properties() { '
kernel.string=Columbina Kernel with DroidSpaces for Galaxy Z Flip3 (b2q)
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=b2q
device.name2=b2qxxx
device.name3=SM-F711B
device.name4=SM-F711N
device.name5=SM-F711U
device.name6=SM-F711W
device.name7=SM-F7110
supported.versions=11 - 16
supported.patchlevels=
'; }

# Shell Variables
block=/dev/block/by-name/boot;
is_slot_device=0;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;

# Import functions/variables and setup env
. tools/ak3-core.sh;

# Dump boot image and flash kernel
split_boot;
flash_boot;
