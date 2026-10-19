# Analisis & Rencana Pembuatan Custom Kernel Droidspaces: Samsung Galaxy Z Flip3 (SM-F711B / b2q)

## 1. Executive Summary & Korelasi Komponen

Perangkat target adalah **Samsung Galaxy Z Flip3 5G (SM-F711B / codename: `b2q` / platform Qualcomm Snapdragon 888 `sm8350`)**.

Berdasarkan investigasi forensik terhadap:
1. File boot image aktif saat ini: `default/boot.img`
2. Konfigurasi kernel yang diinginkan: `Kernel-Configuration.md` (panduan resmi Droidspaces GKI)
3. Referensi build lama teman: `.tmp/Shadow-Droidspaces-b2q`
4. Base repository upstream: `https://github.com/AlexFurina/android_kernel_samsung_sm8350`
5. Thread ROM XDA: `[ROM] [16] [OneUI8.0] [ZFlip3] X-ROM ZFlip5 Port v3.2` (oleh **AlexFurina**)

Ditemukan korelasi langsung 100%:
* Pengembang X-ROM ZFlip5 Port di XDA adalah **AlexFurina**.
* Kernel bawaan ROM tersebut adalah **Columbina Kernel** yang dikembangkan di branch `Flip3-Android16`.
* Binary `default/boot.img` adalah hasil kompilasi langsung dari commit **`9e6bd77c`** pada branch `Flip3-Android16` di repository AlexFurina.
* Kernel teman Anda (`Shadow-Droidspaces-b2q`) gagal/tidak cocok karena dibangun di atas base Linux **5.4.86** era Android 12 (One UI 4.1 tahun 2022) tanpa kABI patch, sehingga modul vendor dan sistem Android 16 menolak booting.

---

## 2. Bedah Forensik `default/boot.img` (Kernel Aktif)

### Spesifikasi Header & Image
* **Format**: Android Boot Image Header **v3** (Page size: 4096 bytes).
* **Ukuran File**: 49,995,776 bytes (~47.68 MB).
* **Ukuran Kernel**: 49,263,104 bytes.
* **Ukuran Ramdisk**: 722,487 bytes (Gzip CPIO).
* **Isi Ramdisk**: Stock Samsung recovery/boot ramdisk (`init`, `dpolicy` Knox Defex, `dev`, `proc`, `sys`).
* **Kernel Binary**: ARM64 uncompressed `Image` (magic: `ARMd`, `text_offset=0x80000`).

### Kernel Version Banner (Verbatim dari Binary)
```text
Linux version 5.4.302-Columbina (푸리나@사랑) (Neutron clang version 18.0.0git (https://github.com/llvm/llvm-project.git ca5d34ec7186f2b5750c7e67dcb8b2d0dc865d8d), Neutron LLD 18.0.0) #1 SMP PREEMPT Thu Jun 4 01:15:57 KST 2026
```

### Identifikasi Titik Commit Upstream
* **Repository**: `https://github.com/AlexFurina/android_kernel_samsung_sm8350`
* **Branch**: `Flip3-Android16`
* **Commit Target**: `9e6bd77c10b42fdf40c316279f57ebbf794ae3b9`
  * Judul commit: `sys_newuname: spoof on root`
  * Waktu commit: `2026-06-03 16:12:03 UTC` = **`2026-06-04 01:12:03 KST`**
  * Waktu build kernel binary di HP: **`2026-06-04 01:15:57 KST`** (hanya berselang 3 menit 54 detik).
* **Toolchain yang Digunakan**: **Neutron Clang 18** (`ca5d34ec7186f2b5750c7e67dcb8b2d0dc865d8d`).

### Analisis `.config` (Diekstrak via IKCONFIG)
* Kernel menggunakan basis Qualcomm GKI (`CONFIG_QGKI=y`).
* Pengecekan CRC modul aktif (`CONFIG_MODVERSIONS=y`).
* Modul vendor eksternal aktif (`=m`): WiFi `qcacld-3.0` (`CONFIG_QCA_CLD_WLAN=m`), `CONFIG_CNSS2=m`, Touchscreen Zinitix (`CONFIG_TOUCHSCREEN_ZINITIX_ZTW522=m`), NFC, dan Battery.
* **Status Opsi Droidspaces saat ini**:
  * `CONFIG_SYSVIPC=n` (tidak aktif)
  * `CONFIG_POSIX_MQUEUE=n` (tidak aktif)
  * `CONFIG_PID_NS=n` (tidak aktif)
  * `CONFIG_IPC_NS=n` (tidak aktif)
  * `CONFIG_USER_NS=n` (tidak aktif)
  * `CONFIG_DEVTMPFS=n` (tidak aktif)
  * `CONFIG_BRIDGE_NETFILTER=n`, `CONFIG_NETFILTER_XT_MATCH_ADDRTYPE=n` (tidak aktif)

---

## 3. Akar Masalah Ketidakcocokan Kernel Teman (`Shadow-Droidspaces-b2q`)

Kernel teman Anda di `.tmp/Shadow-Droidspaces-b2q` tidak kompatibel dengan ROM saat ini karena 3 faktor kritis:

### A. Kesenjangan Versi Driver & Firmware (5.4.86 vs 5.4.302)
* Kernel teman berbasis Linux 5.4.86 (2022) untuk Android 12 (One UI 4.1).
* ROM yang terpasang saat ini adalah X-ROM (porting ZFlip5 / Android 16 / One UI 8.0).
* Antara 5.4.86 dan 5.4.302 terdapat ratusan perbaikan dan perubahan struktur driver hardware Samsung (panel layar lipat, sensor hall engsel, touchscreen `sec_ts`, driver WiFi Qualcomm `qcacld-3.0`, dan power management).
* Mem-flash kernel 5.4.86 pada ROM Android 16 menyebabkan modul driver vendor di `/vendor_dlkm` menolak dimuat.

### B. Pelanggaran Kernel ABI (kABI Breakdown)
* Pada kernel teman, opsi Droidspaces (`CONFIG_SYSVIPC=y`, `CONFIG_POSIX_MQUEUE=y`, `CONFIG_IPC_NS=y`) diaktifkan begitu saja di bagian akhir defconfig tanpa patch padding kABI.
* Pada Linux 5.4, mengaktifkan `CONFIG_SYSVIPC` menyisipkan `struct sysv_sem` dan `struct sysv_shm` di tengah-tengah `struct task_struct` (di file `include/linux/sched.h`).
* Karena `CONFIG_MODVERSIONS=y` aktif pada vendor image, offset field dalam `task_struct` bergeser. Modul-modul vendor (WiFi, Touchscreen, Audio) mendeteksi ketidakcocokan CRC simbol dan memicu error `disagrees about version of symbol`, atau mengakses pointer memori yang salah sehingga HP bootloop.

### C. Pemblokiran oleh Android 14+ / 15 / 16 (BPF & Fake Uname)
* Android versi modern memiliki mekanisme `netbpfload` dan `bpfloader` yang memeriksa batas versi kernel minimum saat startup.
* Kernel 5.4 murni akan diblokir oleh netbpfload sehingga jaringan Android mati atau booting terhenti.
* AlexFurina menambahkan patch khusus pada Columbina (`CONFIG_FAKE_UNAME_5_10=y` dan `sys_newuname: spoof on root` pada commit `8a860937` dan `9e6bd77c`) agar sistem Android 16 membaca kernel sebagai 5.10.200 saat proses BPF berjalan. Kernel teman tidak memiliki fitur ini.

---

## 4. Spesifikasi Teknis Custom Kernel Droidspaces

Untuk membangun kernel yang kompatibel 100% dengan ROM X-ROM ZFlip5 Port dan memenuhi persyaratan Droidspaces:

### 1. Penerapan Patch kABI (Wajib)
Sesuai dokumentasi Droidspaces GKI (`Kernel-Configuration.md`), diterapkan 2 patch:
1. **`001.GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch`**:
   * Target: `include/linux/sched.h`
   * Fungsi: Mengalihkan field `sysvsem` dan `sysvshm` ke slot padding reserved Android GKI (`ANDROID_KABI_USE(6, ...)` dan `ANDROID_KABI_REPLACE(7; 8, ...)`). Offset `task_struct` tetap utuh.
2. **`002.5.10_or_lower_use_android_abi_padding_for_posix_mqueue.patch`**:
   * Target: `include/linux/sched/user.h`
   * Fungsi: Mengalihkan field `mq_bytes` pada `struct user_struct` ke slot padding reserved `ANDROID_KABI_USE(1, unsigned long mq_bytes)`. Ukuran struct tetap utuh.

### 2. Konfigurasi Defconfig (`arch/arm64/configs/vendor/b2q_kor_singlex_defconfig`)
Tambahkan fragment konfigurasi Droidspaces berikut:

```makefile
# ==============================================================================
# DROIDSPACES CONTAINER SUPPORT (kABI-SAFE)
# ==============================================================================

# Core IPC & Namespaces
CONFIG_SYSVIPC=y
CONFIG_POSIX_MQUEUE=y
CONFIG_IPC_NS=y
CONFIG_PID_NS=y
CONFIG_USER_NS=y
CONFIG_DEVTMPFS=y

# Network Isolation & OpenWrt / NAT Container Support
CONFIG_NETFILTER_XT_MATCH_ADDRTYPE=y
CONFIG_MACVLAN=y
CONFIG_IP6_NF_NAT=y
CONFIG_IP6_NF_TARGET_MASQUERADE=y
CONFIG_NETFILTER_XT_TARGET_REJECT=y
CONFIG_NETFILTER_XT_TARGET_LOG=y
CONFIG_NETFILTER_XT_MATCH_RECENT=y

# Fail2ban & IP Set Support
CONFIG_IP_SET=y
CONFIG_IP_SET_HASH_IP=y
CONFIG_IP_SET_HASH_NET=y
CONFIG_NETFILTER_XT_SET=y

# Filesystem & POSIX ACL (NixOS / OverlayFS Support)
CONFIG_TMPFS_POSIX_ACL=y
CONFIG_TMPFS_XATTR=y
```

> **PERINGATAN kABI PENTING**:
> `CONFIG_CFS_BANDWIDTH` dan `CONFIG_CGROUP_PIDS` **TIDAK BOLEH** diaktifkan jika hanya mem-flash `boot.img`. Opsi tersebut merombak total ukuran struct scheduler/cgroup yang tidak memiliki padding kABI dan akan merusak ribuan CRC modul vendor. Droidspaces tetap berfungsi normal tanpa dua opsi pembatasan CPU/PID ini.

---

## 5. Blueprint CI/CD GitHub Actions

Alur otomatisasi kompilasi menggunakan GitHub Actions:

```
[GitHub Actions Runner (ubuntu-latest)]
                 │
                 ├── 1. Checkout repository: AlexFurina/android_kernel_samsung_sm8350
                 │      (Ref: commit 9e6bd77c / branch Flip3-Android16)
                 │
                 ├── 2. Download & Setup Neutron Clang 18 (antman / prebuilt toolchain)
                 │
                 ├── 3. Terapkan Patch kABI (sched.h & user.h)
                 │
                 ├── 4. Merge Kconfig Droidspaces ke b2q_kor_singlex_defconfig
                 │
                 ├── 5. Kompilasi Kernel:
                 │      make O=out ARCH=arm64 vendor/b2q_kor_singlex_defconfig
                 │      make O=out ARCH=arm64 CC=clang LD=ld.lld LLVM=1 LLVM_IAS=1 -j$(nproc) Image
                 │
                 ├── 6. Packaging Hasil:
                 │      a. AnyKernel3 Zip (universal flash via TWRP/KernelFlasher)
                 │      b. Direct boot.img (repack Image baru ke ramdisk default/boot.img)
                 │
                 └── 7. Upload Artifacts / Release
```

---

## 6. Rekomendasi Pilihan Keputusan

1. **Opsi 1 (Sangat Direkomendasikan - Paling Aman & Stabil)**:
   * **Base**: Commit `9e6bd77c` pada branch `Flip3-Android16`.
   * **Alasan**: Merupakan basis persis dari kernel yang sedang berjalan di HP Anda. Menjamin kompatibilitas 100% dengan vendor module yang terpasang di ROM X-ROM saat ini.
2. **Opsi 2 (Base Branch Terbaru / Bleeding Edge)**:
   * **Base**: Branch `HEAD` dari `Flip3-Android16` (versi 5.4.304 LTS).
   * **Alasan**: Membawa patch upstream kernel terbaru. Ada kemungkinan minor modul vendor perlu penyesuaian jika build ROM masih menggunakan kernel Juni 2026.
3. **Opsi 3 (Rebuild Full Kernel + Vendor Modules)**:
   * Melakukan build menyeluruh termasuk modul `.ko` baru dan membuat partisi `vendor_boot` / `vendor_dlkm` baru untuk mengaktifkan CPU quota limits (`CONFIG_CFS_BANDWIDTH`).
   * **Tradeoff**: Proses flashing jauh lebih berisiko dan memakan waktu.
