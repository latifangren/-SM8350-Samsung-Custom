# Columbina Kernel with DroidSpaces for Samsung Galaxy Z Flip3 (SM-F711B / b2q)

Custom kernel builder and configuration pipeline to enable full [DroidSpaces](https://github.com/ravindu644/Droidspaces) / Linux container support on the **Samsung Galaxy Z Flip3 5G** (`b2q` / Snapdragon 888 / `sm8350`).

Specially tailored for devices running **X-ROM (Galaxy Z Flip5 Port to Z Flip3 / Android 16 / One UI 8.0)** by **AlexFurina**.

---

## 🚀 Features Enabled

Stock Samsung kernels omit core containerization namespaces and IPC primitives. This project enables all DroidSpaces required and recommended features while strictly preserving kernel ABI (kABI) compatibility:

| Feature / Subsystem | Config Option | Status | Description |
|---|---|---|---|
| **PID Namespace** | `CONFIG_PID_NS` | ✅ Enabled | Process isolation for containers |
| **IPC Namespace** | `CONFIG_IPC_NS` | ✅ Enabled | SysV IPC isolation (kABI-patched) |
| **SysV IPC** | `CONFIG_SYSVIPC` | ✅ Enabled | System V message queues & semaphores |
| **POSIX Message Queues**| `CONFIG_POSIX_MQUEUE` | ✅ Enabled | POSIX IPC mechanisms (kABI-patched) |
| **User Namespace** | `CONFIG_USER_NS` | ✅ Enabled | Unprivileged container sandboxing |
| **Device Filesystem** | `CONFIG_DEVTMPFS` | ✅ Enabled | Hardware device nodes inside containers |
| **Network Namespace** | `CONFIG_NET_NS` | ✅ Enabled | Virtual network stack isolation |
| **Virtual Ethernet** | `CONFIG_VETH` | ✅ Enabled | Virtual ethernet pairs for routing |
| **Bridge Networking** | `CONFIG_BRIDGE` / `CONFIG_BRIDGE_NETFILTER` | ✅ Enabled | Bridged container networking |
| **Macvlan** | `CONFIG_MACVLAN` | ✅ Enabled | Direct LAN IP assignment |
| **IPv6 NAT (NAT66)** | `CONFIG_IP6_NF_NAT` / `CONFIG_IP6_NF_TARGET_MASQUERADE` | ✅ Enabled | Full IPv6 container routing |
| **TTL Target / Match** | `CONFIG_NETFILTER_XT_TARGET_HL` / `XT_MATCH_HL` | ✅ Enabled | TTL modification for tethering / routing |
| **Firewall Support** | `CONFIG_IP_SET` / `CONFIG_NETFILTER_XT_SET` | ✅ Enabled | UFW & Fail2ban support inside containers |
| **OverlayFS & POSIX ACL**| `CONFIG_OVERLAY_FS` / `CONFIG_TMPFS_POSIX_ACL` | ✅ Enabled | Volatile container mode & NixOS support |

---

## 🛡️ kABI Safety (Zero-Bootloop Guarantee)

On Android 5.4 GKI / QGKI, vendor modules (`qcacld-3.0` WiFi, `touchscreen_zinitix`, audio, battery) are compiled against stock kernel structures with module version CRC verification (`CONFIG_MODVERSIONS=y`).

Enabling `CONFIG_SYSVIPC` and `CONFIG_POSIX_MQUEUE` without padding alters the memory offsets of `struct task_struct` and `struct user_struct`, which causes stock vendor modules to fail loading (`disagrees about version of symbol`) or immediately trigger a bootloop.

This project incorporates the upstream DroidSpaces GKI kABI padding patches:
* **`patches/001-fix-sysvipc-kabi.patch`**: Redirects `sysvsem` and `sysvshm` into reserved padding slots (`ANDROID_KABI_RESERVE(6, 7, 8)`) in `include/linux/sched.h`.
* **`patches/002-fix-posix-mqueue-kabi.patch`**: Redirects `mq_bytes` into reserved padding slot `ANDROID_KABI_USE(1)` in `include/linux/sched/user.h`.

> **Note on Resource Limits**: `CONFIG_CFS_BANDWIDTH` and `CONFIG_CGROUP_PIDS` are intentionally kept disabled to preserve the global scheduler/cgroup structure layouts without breaking stock vendor modules.

---

## 📁 Repository Structure

```
.
├── .github/
│   └── workflows/
│       └── build-kernel.yml       # GitHub Actions CI/CD automated build workflow
├── anykernel/
│   └── anykernel.sh               # AnyKernel3 packaging template configured for b2q
├── config/
│   └── droidspaces.config         # DroidSpaces Kconfig fragment (kABI-safe)
├── docs/
│   └── ANALISIS_KERNEL_FLIP3_DROIDSPACES.md  # Detailed technical analysis report
├── patches/
│   ├── 001-fix-sysvipc-kabi.patch # kABI fix for SYSVIPC
│   └── 002-fix-posix-mqueue-kabi.patch # kABI fix for POSIX_MQUEUE
└── scripts/
    └── repack_bootimg.py          # Android Boot Image v3 kernel repacker
```

---

## 🔨 How to Build (GitHub Actions)

Kernel compilation is fully automated via GitHub Actions using the official **Neutron Clang 18** toolchain.

1. Fork or push this repository to GitHub.
2. In your GitHub repository, navigate to the **Actions** tab.
3. Select **"Build Columbina DroidSpaces Kernel for Galaxy Z Flip3 (b2q)"**.
4. Click **Run workflow**:
   * **Kernel Source**: `https://github.com/AlexFurina/android_kernel_samsung_sm8350`
   * **Kernel Branch**: `Flip3-Android16`
   * **Kernel Commit**: `9e6bd77c825e1c7c025b18584f6c8acd660ea155` (Columbina 5.4.302 base commit matching X-ROM v3.2)
   * **Defconfig**: `vendor/b2q_kor_singlex_defconfig`
   * **LOCALVERSION**: `-Columbina-Droidspaces`
5. Click **Run workflow** to start compilation.
6. Once finished (~15–20 min), download the artifacts:
   * **`Columbina-Droidspaces-b2q-AnyKernel3.zip`**: Universal recovery flashable zip.
   * **`Columbina-Droidspaces-b2q-boot.img`**: Pre-repacked boot image (if `default/boot.img` is present).
   * **`Image`** & **`.config`**: Raw compiled kernel and configuration log.

---

## 📲 Installation

### Method 1: Recovery / Kernel Flasher (Recommended)
1. Download `Columbina-Droidspaces-b2q-AnyKernel3.zip` from GitHub Actions Artifacts.
2. Flash the zip via:
   * **TWRP Recovery** -> Install -> Select Zip -> Swipe to confirm, OR
   * **Franco Kernel Manager / KernelFlasher** app with root.
3. Reboot device.

### Method 2: Fastboot / Direct Boot Image Flash
If you downloaded `Columbina-Droidspaces-b2q-boot.img`:
```bash
# Via fastboot / fastbootd
fastboot flash boot Columbina-Droidspaces-b2q-boot.img
fastboot reboot
```
Or via root terminal on the phone:
```sh
su -c 'dd if=/sdcard/Download/Columbina-Droidspaces-b2q-boot.img of=/dev/block/by-name/boot bs=4096'
su -c 'reboot'
```

---

## 🔍 Verification

After booting the new kernel:
1. Open the **DroidSpaces** app.
2. Navigate to **Settings** -> **Requirements** -> **Check Requirements**.
3. All core namespaces, IPC, devtmpfs, veth, bridge, and overlayfs checks will show **Passed (Green)**.
4. Verify kernel version in Settings -> About Phone -> Software information:
   ```text
   5.4.302-Columbina-Droidspaces
   ```

---

## 📜 Credits & Acknowledgments

* **AlexFurina**: Developer of [X-ROM ZFlip5 Port](https://xdaforums.com/t/rom-16-oneui8-0-zflip3-x-rom-zflip5-port-v3-2.4741371/) and [android_kernel_samsung_sm8350](https://github.com/AlexFurina/android_kernel_samsung_sm8350) (Columbina Kernel).
* **ravindu644**: Creator of [DroidSpaces](https://github.com/ravindu644/Droidspaces) and [Droidspaces-OSS](https://github.com/ravindu644/Droidspaces-OSS).
* **nullptr-t-oss** & **lateautumn233**: Authors of GKI kABI padding patches for SYSVIPC and POSIX_MQUEUE.
* **osm0sis**: Creator of [AnyKernel3](https://github.com/osm0sis/AnyKernel3).
* **Dakkshesh**: Maintainer of [Neutron Clang Toolchain](https://github.com/Neutron-Toolchains).
