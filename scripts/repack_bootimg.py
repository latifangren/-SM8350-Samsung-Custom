#!/usr/bin/env python3
"""
Android Boot Image v3 Repacker
Replaces kernel Image in an existing Android Boot Image v3 while preserving
the original header, ramdisk, cmdline, and OS patch level.
"""

import sys
import os
import struct

def repack(base_boot_path, new_kernel_path, output_boot_path):
    if not os.path.exists(base_boot_path):
        print(f"Error: Base boot.img not found at {base_boot_path}")
        sys.exit(1)
    if not os.path.exists(new_kernel_path):
        print(f"Error: New kernel Image not found at {new_kernel_path}")
        sys.exit(1)

    with open(base_boot_path, "rb") as f:
        base_data = f.read()

    hdr = base_data[:4096]
    magic = hdr[:8]
    if magic != b"ANDROID!":
        print("Error: Not a valid Android boot image")
        sys.exit(1)

    hdr_ver = struct.unpack_from("<I", hdr, 40)[0]
    if hdr_ver not in (3, 4):
        print(f"Error: Expected header version 3 or 4, got {hdr_ver}")
        sys.exit(1)

    kernel_sz, ramdisk_sz, os_ver, hdr_sz = struct.unpack_from("<IIII", hdr, 8)
    print(f"Base boot info: header_ver={hdr_ver}, orig_kernel_sz={kernel_sz}, ramdisk_sz={ramdisk_sz}")

    # Locate ramdisk in base_data
    page_size = 4096
    k_pages = (kernel_sz + page_size - 1) // page_size
    rd_offset = page_size + k_pages * page_size
    ramdisk_data = base_data[rd_offset : rd_offset + ramdisk_sz]

    with open(new_kernel_path, "rb") as f:
        new_kernel_data = f.read()

    new_kernel_sz = len(new_kernel_data)
    print(f"New kernel size: {new_kernel_sz} bytes")

    new_hdr = bytearray(hdr)
    struct.pack_into("<I", new_hdr, 8, new_kernel_sz)

    # Padding calculations
    k_pad = (page_size - (new_kernel_sz % page_size)) % page_size
    rd_pad = (page_size - (ramdisk_sz % page_size)) % page_size

    output_data = (
        bytes(new_hdr)
        + new_kernel_data
        + (b"\x00" * k_pad)
        + ramdisk_data
        + (b"\x00" * rd_pad)
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_boot_path)), exist_ok=True)
    with open(output_boot_path, "wb") as f:
        f.write(output_data)

    print(f"Successfully generated repacked boot image at: {output_boot_path} ({len(output_data)} bytes)")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: repack_bootimg.py <base_boot.img> <new_Image> <output_boot.img>")
        sys.exit(1)
    repack(sys.argv[1], sys.argv[2], sys.argv[3])
