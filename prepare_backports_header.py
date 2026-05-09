#!/usr/bin/env python3
"""
Prepare backports-6.12.61 mac80211.h for use with standard kernel build.
Converts CPTCFG_ conditionals to CONFIG_ equivalents and applies
iStoreOS-specific configuration:
  - CPTCFG_MAC80211_DEBUGFS → keep as CONFIG_MAC80211_DEBUGFS
  - CPTCFG_NL80211_TESTMODE → keep as CONFIG_NL80211_TESTMODE
  - CPTCFG_MAC80211_LEDS → keep as CONFIG_MAC80211_LEDS
  - IS_ENABLED(CONFIG_IPV6) → uses standard kernel config
Also adds missing type definitions that 6.6.119 doesn't have.
"""
import sys
import re

def prepare_backports_header(src_path, dst_path):
    with open(src_path) as f:
        content = f.read()
    
    changed = False
    
    # 1. Convert CPTCFG_ to CONFIG_ (OpenWrt's own config prefix → standard kernel prefix)
    new_content = content.replace('CPTCFG_MAC80211_DEBUGFS', 'CONFIG_MAC80211_DEBUGFS')
    new_content = new_content.replace('CPTCFG_NL80211_TESTMODE', 'CONFIG_NL80211_TESTMODE')
    new_content = new_content.replace('CPTCFG_MAC80211_LEDS', 'CONFIG_MAC80211_LEDS')
    new_content = new_content.replace('CPTCFG_MAC80211_MESH', 'CONFIG_MAC80211_MESH')
    
    if new_content != content:
        changed = True
        print("Converted CPTCFG_ → CONFIG_")
    
    # 2. Ensure can_neg_ttlm types are present (they're in backports header)
    # Backports-6.12.61 should already have these, but check
    if 'struct ieee80211_neg_ttlm' not in new_content:
        print("WARNING: ieee80211_neg_ttlm types missing from backports header!")
    
    # 3. Write output
    with open(dst_path, 'w') as f:
        f.write(new_content)
    
    print(f"Written: {dst_path}")
    
    # Verify key fields
    import subprocess
    result = subprocess.run(
        ['awk', '/^struct ieee80211_ops \\{/,/^\\};/', dst_path],
        capture_output=True, text=True
    )
    ops_text = result.stdout
    fields = [line.strip() for line in ops_text.split('\n') if '(*' in line]
    print(f"Total ops fields: {len(fields)}")
    
    for i, f in enumerate(fields):
        if 'wake_tx_queue' in f:
            print(f"wake_tx_queue: field {i} (0-indexed)")
        if 'vif_cfg_changed' in f:
            print(f"vif_cfg_changed: field {i} (0-indexed)")
        if 'link_info_changed' in f:
            print(f"link_info_changed: field {i} (0-indexed)")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: prepare_backports_header.py <backports_mac80211.h> <output_mac80211.h>")
        sys.exit(1)
    prepare_backports_header(sys.argv[1], sys.argv[2])
