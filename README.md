# rtw89-rpi4-build

为 iStoreOS (Raspberry Pi 4) 构建 patched 版 **COMFAST CF-983BE** (RTL8922AU / WiFi 7) USB 网卡内核模块。

[![Build rtw89-8922au kmod](https://github.com/gamer995/rtw89-rpi4-build/actions/workflows/build-rtw89-kmod.yml/badge.svg)](https://github.com/gamer995/rtw89-rpi4-build/actions/workflows/build-rtw89-kmod.yml)

## 硬件

| 项目 | 规格 |
|------|------|
| 网卡 | COMFAST CF-983BE |
| 芯片 | Realtek RTL8922AU |
| 协议 | Wi-Fi 7 (802.11be) |
| 接口 | USB 3.0 (兼容 USB 2.0) |
| 平台 | Raspberry Pi 4 |
| 系统 | iStoreOS 24.10 (OpenWrt, kernel 6.6.119) |

## 背景

原版 [morrownr/rtw89](https://github.com/morrownr/rtw89) 驱动在 AP 模式下存在 bug：当客户端断开连接触发密钥删除 (`DISABLE_KEY`) 时，会调用 `rtw89_mac_flush_txq` / `rtw89_hci_flush_queues` 刷新 USB 队列，这可能导致 USB 固件挂起（"key disable flush" hang），WiFi 掉线。

本仓库的 `apply_patches.py` 对 `mac80211.c` 打两个补丁：

1. **`DISABLE_KEY` 守卫** — 在 AP 模式下跳过队列刷新，避免 USB 挂起
2. **`ops_flush` 守卫** — 同上，覆盖另一个调用路径

补丁通过新增的 `rtw89_is_usb_ap()` 辅助函数判断是否需要跳过。

## 当前修复目标

当前 r3 包能启动 AP，但仍能观察到两个稳定性问题：

- `failed to wait RF DACK`：RTL8922A RFK DACK 等待窗口对 USB 太短，后续校准可能追着未完成的 DACK 跑。
- `timed out to flush queues`：mac80211 station teardown 会触发 `ops_flush`，r3 没有覆盖这个断站 flush 路径。

本仓库的 r4 构建使用 OpenWrt 24.10.5 bcm2711 SDK 编译源码，并加入：

- `010-rtw89-usb-ap-skip-mac-flush-timeouts.patch`
- `020-rtw89-8922a-extend-usb-dack-wait.patch`

## 稳定基线

当前可用版本是仓库内的 r3 稳定基线包：

```text
known-good/kmod-rtw89-8922au-git_6.6.119_d2f175ea-r3_kernel-5642ee_iStoreOS-AP-fix_2026-03-17.ipk
```

这个包已在 iStoreOS 24.10.5 / Raspberry Pi 4 / kernel `6.6.119~5642ee3ae5a6da3ce336f51cf968083c-r1` 上验证：

- `rtw89_core_git.ko` / `rtw89_usb_git.ko` / `rtw89_8922a_git.ko` / `rtw89_8922au_git.ko` 可加载
- `.gnu.linkonce.this_module` 大小为 `0x280`
- USB3 `5000M` 下可创建 AP，SSID `RaspberryPi`
- 已包含 USB AP 队列 flush 修复

此前的裸 Linux kbuild CI 产物虽然能绕过 `struct module` 大小错误，但不是用 iStoreOS/OpenWrt 的 kbuild 和 mac80211 符号环境产出，实际加载 RTL8922AU 时会出现固件下载失败或重启。后续源码构建必须走 OpenWrt/iStoreOS SDK package 流程。

## 快速使用

### 下载预构建 .ipk

从 [GitHub Actions](https://github.com/gamer995/rtw89-rpi4-build/actions) 最新成功运行的 Artifacts 下载 `kmod-rtw89-8922au-patched-r4-istoreos-5642ee`。

### 安装

```bash
# 上传到设备
scp kmod-rtw89-8922au-git_*.ipk root@<IP>:/tmp/

# 安装（需要 --force-depends 因为内核 ABI 校验）
ssh root@<IP> 'opkg install --force-depends /tmp/kmod-rtw89-8922au-git_*.ipk'
```

### 验证

```bash
# 检查模块是否加载
lsmod | grep rtw89

# 查看固件版本
dmesg | grep "Firmware version"

# 查看 USB 连接速度
lsusb -t | grep rtw89
```

### iStoreOS overlayfs 特殊说明

iStoreOS 使用 overlayfs，`cp -f` 到 `/lib/modules/` 可能报 "File exists"。如需手动安装模块，直接写入 overlay upper 层：

```bash
# 提取 .ipk
cd /tmp && mkdir kmod && cd kmod
tar -xf ../kmod-rtw89-8922au-git_*.ipk && tar -xf data.tar.gz

# 直接写入 upper 层
cp lib/modules/6.6.119/*.ko /overlay/upper/lib/modules/6.6.119/

# 刷新缓存
sync && echo 3 > /proc/sys/vm/drop_caches
reboot
```

## 无线配置

在 `/etc/config/wireless` 中配置 radio（以 USB 3.0 为例）：

```
config wifi-device 'radio2'
    option type 'mac80211'
    option path 'scb/fd500000.pcie/pci0000:00/.../usb2/2-1/2-1:1.0'
    option band '5g'
    option channel '36'
    option htmode 'EHT80'
    option country 'CN'
    option disabled '0'
    option he '1'
    option eht '1'

config wifi-iface 'default_radio2'
    option device 'radio2'
    option network 'lan'
    option mode 'ap'
    option ssid 'RaspberryPi'
    option encryption 'psk2'
    option key '<password>'
```

> **注意**：USB 路径 (`path`) 会因插入的 USB 口不同而变化。可通过 `readlink /sys/class/ieee80211/phy*/device` 获取当前路径，更新为 `usb1/...` 或 `usb2/...`。

## 驱动参数

| 参数 | 模块 | 默认值 | 说明 |
|------|------|--------|------|
| `disable_ps_mode` | rtw89_core_git | Y | 禁用省电模式（AP 建议开启） |
| `switch_usb_mode` | rtw89_usb_git | Y | 自动切换 USB 3 模式 |

## 仓库结构

```
├── apply_patches.py          # AP 模式补丁脚本
├── rtw89_stability_monitor.sh # 稳定性监控脚本
├── .github/workflows/         # CI 自动构建
├── *.patch                    # 待应用的补丁文件
├── *.ipk                      # 预构建的驱动包
└── *.txt                      # 版本说明
```

## CI (GitHub Actions)

推送代码到 `main` 分支即自动触发构建。Workflow 会：

1. 下载 OpenWrt 24.10.5 bcm2711 SDK
2. 拉取 morrownr/rtw89 固定 commit `d2f175e`
3. 应用 r4 稳定性补丁
4. 编译四个目标模块
5. 验证 `struct module` section 大小为 `0x280`
6. 验证模块依赖仍包含 `mac80211` / `cfg80211`
7. 将 control 中的 kernel ABI 归一化为 iStoreOS 当前 `5642ee...`
8. 上传 patched `.ipk` Artifact

不要使用裸 Linux 6.6.119 kbuild 直接生成生产模块。

## 许可证

- rtw89 驱动：[Dual BSD/GPL](https://github.com/morrownr/rtw89/blob/main/LICENSE)
- 本仓库补丁及脚本：MIT
