#!/usr/bin/env python3
"""Patch rtw89 mac80211 call sites for iStoreOS backports-6.12.61.

iStoreOS keeps the base kernel at 6.6.119 but ships mac80211/cfg80211 from
OpenWrt backports-6.12.61. The rtw89 source gates these API shapes on
LINUX_VERSION_CODE. Patch only the mac80211-facing call sites; globally faking
LINUX_VERSION_CODE also switches unrelated core kernel APIs and breaks build.
"""

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    src = p.read_text()
    if new in src:
        print(f"{path}: already patched")
        return
    if old not in src:
        raise SystemExit(f"{path}: pattern not found:\n{old}")
    p.write_text(src.replace(old, new, 1))
    print(f"{path}: patched")


def replace_exact_count(path: str, old: str, new: str, count: int) -> None:
    p = Path(path)
    src = p.read_text()
    hits = src.count(old)
    if hits == 0 and src.count(new) == count:
        print(f"{path}: already patched {count} occurrence(s)")
        return
    if hits != count:
        raise SystemExit(f"{path}: expected {count} occurrence(s), found {hits}:\n{old}")
    p.write_text(src.replace(old, new, count))
    print(f"{path}: patched {count} occurrence(s)")


replace_once(
    "rtw89/mac80211.c",
    "#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 11, 0)\n"
    "static void rtw89_ops_stop(struct ieee80211_hw *hw, bool suspend)\n",
    "#if 1 /* iStoreOS backports-6.12.61 mac80211 API */\n"
    "static void rtw89_ops_stop(struct ieee80211_hw *hw, bool suspend)\n",
)

replace_once(
    "rtw89/mac.c",
    "#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 9, 0)\n"
    "\toper = bss_conf->chanreq.oper;\n",
    "#if 1 /* iStoreOS backports-6.12.61 mac80211 API */\n"
    "\toper = bss_conf->chanreq.oper;\n",
)

replace_once(
    "rtw89/core.c",
    "#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 9, 0) \n"
    "\t\tchannel = link_conf->chanreq.oper.chan;\n",
    "#if 1 /* iStoreOS backports-6.12.61 mac80211 API */\n"
    "\t\tchannel = link_conf->chanreq.oper.chan;\n",
)

replace_once(
    "rtw89/core.c",
    "#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 9, 0)\n"
    "\tif (!ieee80211_beacon_cntdwn_is_complete(vif)) {\n",
    "#if 0 /* iStoreOS backports-6.12.61 mac80211 API */\n"
    "\tif (!ieee80211_beacon_cntdwn_is_complete(vif)) {\n",
)

replace_once(
    "rtw89/core.c",
    "#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 9, 0)\n"
    "\t\tieee80211_csa_finish(vif);\n",
    "#if 0 /* iStoreOS backports-6.12.61 mac80211 API */\n"
    "\t\tieee80211_csa_finish(vif);\n",
)

replace_exact_count(
    "rtw89/fw.c",
    "#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 9, 0)\n"
    "\t\tu16 punct = bss_conf->chanreq.oper.punctured;\n",
    "#if 1 /* iStoreOS backports-6.12.61 mac80211 API */\n"
    "\t\tu16 punct = bss_conf->chanreq.oper.punctured;\n",
    2,
)

print("SUCCESS: backports mac80211 API call-site patch applied")
