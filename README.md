# rtw89-8922au for iStoreOS 24.10.8 (Raspberry Pi 4)

给 **COMFAST CF-983BE（RTL8922AU / RTL8912AU，USB ID `0bda:8912`）** 编译 USB 驱动，
目标系统：**iStoreOS 24.10.8 / 树莓派 4B / 内核 6.6.144 / mac80211 backports 6.12.96**。

原项目 [gamer995/rtw89-rpi4-build](https://github.com/gamer995/rtw89-rpi4-build) 的预编译包是给
iStoreOS 24.10.5 / 内核 6.6.119 / backports 6.12.61 编的，内核模块跨版本不能混用，
所以这个仓库把同样的构建流程改到了 24.10.8。

## 用法（不需要装任何本地环境）

1. 在 GitHub 上新建一个 **public** 仓库
2. 把本文件夹里的所有内容（含 `.github` 隐藏目录）上传上去
3. 打开仓库的 **Actions** 页签 → 左侧选 `Build patched rtw89-8922au kmod for iStoreOS 24.10.8 RPi4` → **Run workflow**
4. 等大约 30-50 分钟
5. 构建成功后，到仓库的 **Releases** 页面下载 `kmod-rtw89-8922au-git_*.ipk`（公开链接，不需要登录）

## 装到设备

```sh
# 传到设备后
opkg install --force-depends /tmp/kmod-rtw89-8922au-git_*.ipk
# 固件（如果还没装）
opkg install rtl8922ae-firmware
sync && reboot
```

装完验证：

```sh
lsmod | grep rtw89            # 应有 rtw89_core_git 等 4 个模块
lsusb -t                      # 应看到 5000M 且 Driver=rtw89_8922au_git
iw dev                        # 应出现新的 phy
dmesg | grep -iE 'rtw89|failed to wait RF|timed out to flush'
```

## 构建原理

CI 会：

1. 下载 OpenWrt **24.10.8** bcm2711 SDK
2. 拉取 OpenWrt `v24.10.8` 的 mac80211 package
3. 编译 mac80211 **backports 6.12.96**
4. 拉取 morrownr/rtw89 固定 commit `73cd715afee2dda3f670cdae5e40fbeba7d9be36`
5. 应用本仓库 `package/kernel/rtw89-8922au-git/patches/` 下的 7 个补丁
6. 在编译好的 backports ABI 环境内构建 4 个 rtw89 模块
7. 校验模块依赖集合，打包成 `.ipk`，并发布到公开 Release

## 补丁列表

| 补丁 | 作用 |
|------|------|
| `010-rtw89-usb-ap-skip-mac-flush-timeouts.patch` | USB 模式跳过会导致 AP 卡死的 MAC flush 路径 |
| `020-rtw89-8922a-extend-usb-dack-wait.patch` | DACK RFK 等待窗口扩到 60s |
| `025-rtw89-openwrt-backports-ieee80211-get-sn.patch` | 避免与 backports 的 `ieee80211_get_sn()` 重复定义 |
| `030-rtw89-openwrt-backports-api-compat.patch` | 适配 OpenWrt backports API |
| `040-rtw89-openwrt-backports-6-11-api-compat.patch` | 适配 6.10/6.11 之后的 mac80211 API 差异 |
| `050-rtw89-openwrt-backports-roundup-u64-compat.patch` | 补 `roundup_u64()` |
| `060-rtw89-8922a-extend-usb-tssi-wait.patch` | TSSI RFK 等待窗口扩到 60s |
| `070-rtw89-usb-skip-hs-probe-8922a.patch` | RTL8922A 在非 SuperSpeed 速度下跳过 probe(8922AU 芯片 PAD_CTRL2 默认值会让上游 USB3 切换判断失效,HS 下 probe 必然 -71 失败并引发开机 ~90s 错误风暴) |

## 注意

- USB 网卡要插在**USB 3.0 口**（树莓派4 的蓝色口），`lsusb -t` 应显示 `5000M`；
  插在 USB 2.0 上驱动会报 `usb write32 ... fail ret=-71` 然后掉线
- 换 USB 口后 `/etc/config/wireless` 里 radio 的 `path` 会变，需要重新确认：
  `iwinfo nl80211 phyname "path=<新路径>"`，注意 **path 不能带 `platform/` 前缀**
- 许可证：rtw89 驱动 Dual BSD/GPL；补丁及脚本 MIT（沿用原项目）
