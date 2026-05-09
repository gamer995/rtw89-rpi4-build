#!/usr/bin/env python3
"""
Patch kernel 6.6.119's mac80211.h to add vif_add_debugfs field.

iStoreOS mac80211.ko is compiled from backports-6.12.61 which has one
extra debugfs callback (vif_add_debugfs) before link_add_debugfs.
This single field shift affects all later fields in struct ieee80211_ops.

Combined with NL80211_TESTMODE=n in kernel config (removing 2 testmode
fields), the net effect keeps wake_tx_queue at field 96 while also
correctly positioning sta_state at field 41, sta_add at field 33, etc.

Note: can_activate_links and can_neg_ttlm are NOT added because rtw89
handles them via LINUX_VERSION_CODE conditional compilation.
"""
import sys

def patch(path):
    content = open(path).read()

    # Add vif_add_debugfs before link_add_debugfs
    anchor = '\tvoid (*link_add_debugfs)(struct ieee80211_hw *hw,'
    if 'vif_add_debugfs' in content:
        print("Already patched: vif_add_debugfs")
        return
    if anchor not in content:
        print("ERROR: anchor 'link_add_debugfs' not found!")
        sys.exit(1)

    insert = (
        '\tvoid (*vif_add_debugfs)(struct ieee80211_hw *hw,\n'
        '\t\t\t\t struct ieee80211_vif *vif);\n'
    )
    content = content.replace(anchor, insert + anchor, 1)
    open(path, 'w').write(content)
    print("Patched: added vif_add_debugfs (before link_add_debugfs)")

    # Verify
    final = open(path).read()
    count = final.count('vif_add_debugfs')
    print(f"  vif_add_debugfs: {count} occurrence(s)")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: patch_mac80211.py <path/to/mac80211.h>")
        sys.exit(1)
    patch(sys.argv[1])
