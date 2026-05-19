# rtw89-rpi4-build

为 iStoreOS Raspberry Pi 4 构建 patched 版 COMFAST CF-983BE USB 无线网卡驱动。

[![Build rtw89-8922au kmod](https://github.com/gamer995/rtw89-rpi4-build/actions/workflows/build-rtw89-kmod.yml/badge.svg)](https://github.com/gamer995/rtw89-rpi4-build/actions/workflows/build-rtw89-kmod.yml)

## 硬件与目标系统

| 项目 | 规格 |
|------|------|
| 网卡 | COMFAST CF-983BE |
| 芯片 | Realtek RTL8922AU / USB ID `0bda:8912` |
| 接口 | USB 3.0 |
| 平台 | Raspberry Pi 4 |
| 系统 | iStoreOS 24.10.5 |
| 内核 | Linux `6.6.119` |
| 架构 | `aarch64_cortex-a72` |

## 当前修复候选版

当前候选版基于 [morrownr/rtw89](https://github.com/morrownr/rtw89) commit:

```text
f2e2a70eef253b4d3fc8906c99311dbc4d9f6aab
```

这次上游更新包含多项 RTL8922AU USB 吞吐路径修复：

```text
5148d7f wifi: rtw89: usb: Enable RX aggregation for RTL8922AU
464ae08 wifi: rtw89: Let hfc_param_ini have separate settings for USB 2/3
f93ba28 wifi: rtw89: Add missing TX queue mappings for RTL8922AU
d3cb9b2 wifi: rtw89: phy: increase RF calibration timeouts for USB transport
18436ff wifi: rtw89: usb: fix TX flow control by tracking in-flight URBs
```

上一版已部署验证的仓库提交：

```text
185a31e fix: apply RTL8922A normal TSSI wait broadly
```

部署到 Raspberry Pi 4 后的模块 md5:

```text
c98341a58833e72205c6743905d92321  rtw89_8922a_git.ko
327440849561e4fa14d64f7c852f2718  rtw89_8922au_git.ko
46cc3182fee68d0fbc1e1c144dfbf7c8  rtw89_core_git.ko
563c3f949adc9dc4fd337037ede26b42  rtw89_usb_git.ko
```

上一版设备侧验证结果：

- USB 连接为 SuperSpeed `5000M`
- AP `RaspberryPi` 可启动，5 GHz channel 36，`EHT80`
- `failed to wait RF DACK/TSSI/IQK/DPK/RX_DCK` 未复发
- `timed out to flush queues` 未复发
- 主测速客户端已协商到 `1200.9 MBit/s 80MHz HE-MCS 11 HE-NSS 2`

## 修复内容

这个仓库不是单纯回退到旧 r3，而是在 OpenWrt/iStoreOS 的 mac80211 backports ABI 环境里构建 morrownr/rtw89，并叠加以下补丁：

| 补丁 | 作用 |
|------|------|
| `010-rtw89-usb-ap-skip-mac-flush-timeouts.patch` | USB 模式跳过会导致 AP 卡死的 MAC flush 路径，覆盖 key 删除、station teardown、ops flush 和 core stop |
| `020-rtw89-8922a-extend-usb-dack-wait.patch` | 将 RTL8922A DACK RFK 等待窗口扩到 60 秒，避免 USB 固件路径下 DACK 轮询过早超时 |
| `030-rtw89-openwrt-backports-api-compat.patch` | 适配 OpenWrt 24.10.5 mac80211 backports 6.12.61 API |
| `040-rtw89-openwrt-backports-6-11-api-compat.patch` | 适配 backports 中 6.10/6.11 之后的 mac80211 API 差异 |
| `050-rtw89-openwrt-backports-roundup-u64-compat.patch` | 避免 backports 头文件缺失 `roundup_u64()` |
| `060-rtw89-8922a-extend-usb-tssi-wait.patch` | 将 RTL8922A normal TSSI RFK 等待窗口扩到 60 秒，修复 AP 启动后 TX rate 被压低的问题 |

## 已确认的问题根因

旧 r3 能启动 AP，但仍存在两个关键问题：

- RFK 等待太短：USB 固件路径比 PCIe 慢，DACK/TSSI 20 ms 级等待会过早超时，导致射频校准状态不完整。
- flush 路径覆盖不全：早期补丁只覆盖 key disable，一些 station disconnect/flush 路径仍会触发 `timed out to flush queues`。

这两个问题会表现为 Wi-Fi 信号消失、beacon 停发、测速只有几十 Mbps，或者 station dump 中 AP TX rate 被压在 20 MHz / 50 Mbps 左右。

## 安装

从 [GitHub Actions](https://github.com/gamer995/rtw89-rpi4-build/actions/workflows/build-rtw89-kmod.yml) 下载最新成功运行的 artifact。

上传到设备：

```bash
scp kmod-rtw89-8922au-git_*.ipk root@<IP>:/tmp/
```

安装：

```bash
ssh root@<IP> 'opkg install --force-depends /tmp/kmod-rtw89-8922au-git_*.ipk'
```

iStoreOS overlayfs 下也可以手动替换模块：

```bash
cd /tmp
mkdir -p rtw89-kmod
cd rtw89-kmod
tar -xzf ../kmod-rtw89-8922au-git_*.ipk
tar -xzf data.tar.gz
cp lib/modules/6.6.119/rtw89_*_git.ko /overlay/upper/lib/modules/6.6.119/
sync
reboot
```

建议替换模块后冷重启。热卸载/热加载可能留下 RFK/USB 状态，导致误判。

## 验证

检查模块：

```bash
md5sum /overlay/upper/lib/modules/6.6.119/rtw89_*_git.ko
strings /overlay/upper/lib/modules/6.6.119/rtw89_core_git.ko | grep -E 'extend RF|skip MAC flush'
```

检查 USB3：

```bash
lsusb -t | grep -A2 rtw89
```

检查 AP：

```bash
wifi status radio2
iw dev phy*-ap0 info
ubus call hostapd.phy1-ap0 get_status
```

检查错误日志：

```bash
dmesg | grep -Ei 'failed to wait RF|timed out to flush queues|rtw89|DACK|TSSI'
```

检查测速客户端链路：

```bash
iw dev phy1-ap0 station dump
iwinfo phy1-ap0 assoclist
```

健康的高速客户端应至少看到类似：

```text
tx bitrate: 1200.9 MBit/s 80MHz HE-MCS 11 HE-NSS 2
```

如果某个客户端仍显示 `20MHz`、`65.0 MBit/s`、`72.2 MBit/s`，那是该客户端自身协商到低速链路，不能用来判断驱动是否恢复到高速。

## 无线配置示例

`/etc/config/wireless` 示例：

```text
config wifi-device 'radio2'
    option type 'mac80211'
    option path 'scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb2/2-1/2-1:1.0'
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

USB path 会随插口变化，可用下面命令确认：

```bash
readlink /sys/class/ieee80211/phy*/device
```

## CI

Workflow 会：

1. 下载 OpenWrt 24.10.5 bcm2711 SDK
2. 拉取 OpenWrt `v24.10.5` 的 mac80211 package
3. 编译 OpenWrt mac80211 backports 6.12.61
4. 拉取 morrownr/rtw89 固定 commit `d2f175eafa0a4ef9cc65e7073a77e60238cae614`
5. 应用本仓库补丁
6. 在已编译的 OpenWrt backports ABI 环境内构建四个 rtw89 模块
7. 验证 `.gnu.linkonce.this_module == 0x280`
8. 验证模块依赖集合
9. 打包并上传 `.ipk` artifact

不要用裸 Linux 6.6.119 kbuild 直接生成生产模块。iStoreOS/OpenWrt 的 mac80211/backports 符号环境必须匹配，否则可能出现模块能编译但加载后固件下载失败、struct module mismatch 或运行时重启。

## 许可证

- rtw89 驱动：Dual BSD/GPL
- 本仓库补丁及脚本：MIT
