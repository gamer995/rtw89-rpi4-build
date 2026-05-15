include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=rtw89-8922au-git
PKG_VERSION:=2026.03.05~d2f175ea
PKG_RELEASE:=4

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/morrownr/rtw89.git
PKG_SOURCE_VERSION:=d2f175eafa0a4ef9cc65e7073a77e60238cae614
PKG_MIRROR_HASH:=skip
PKG_BUILD_DIR:=$(KERNEL_BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)

include $(INCLUDE_DIR)/package.mk

define KernelPackage/rtw89-8922au-git
  SUBMENU:=Wireless Drivers
  TITLE:=Realtek RTL8912AU/RTL8922AU USB support (third-party rtw89)
  DEPENDS:=+kmod-cfg80211 +kmod-mac80211 +kmod-usb-core
  FILES:= \
	$(PKG_BUILD_DIR)/rtw89_core_git.ko \
	$(PKG_BUILD_DIR)/rtw89_usb_git.ko \
	$(PKG_BUILD_DIR)/rtw89_8922a_git.ko \
	$(PKG_BUILD_DIR)/rtw89_8922au_git.ko
  AUTOLOAD:=$(call AutoProbe,rtw89_8922au_git)
endef

define KernelPackage/rtw89-8922au-git/description
  Realtek RTL8912AU/RTL8922AU USB Wi-Fi driver from morrownr/rtw89,
  patched for iStoreOS Raspberry Pi 4 USB AP stability.
endef

define Build/Compile
	$(KERNEL_MAKE) M="$(PKG_BUILD_DIR)" KBUILD_MODPOST_WARN=1 modules
endef

$(eval $(call KernelPackage,rtw89-8922au-git))
