#!/usr/bin/env python3
"""
Patch kernel 6.6.119's mac80211.h to add 3 fields present in backports-6.12.61
but missing from 6.6.119. This fixes the struct ieee80211_ops layout mismatch
that causes ieee80211_alloc_hw_nm to WARN and return NULL when loading the driver
on iStoreOS (kmod-mac80211 6.6.119.6.12.61-r1 = backports-6.12.61).

Fields added:
  1. vif_add_debugfs  (position 35: before link_add_debugfs)
  2. can_activate_links (position 120: before change_vif_links)
  3. can_neg_ttlm     (position 125: at end of struct)

With these additions, struct ieee80211_ops has 125 function pointers,
matching backports-6.12.61 exactly. wake_tx_queue moves from slot 97 to
slot 98, which is where backports-6.12.61 mac80211.ko expects it.
"""
import sys

def patch(path):
    content = open(path).read()
    changed = False

    # Patch 1: insert vif_add_debugfs before link_add_debugfs
    anchor1 = '\tvoid (*link_add_debugfs)(struct ieee80211_hw *hw,'
    if anchor1 in content and 'vif_add_debugfs' not in content:
        insert1 = (
            '\tvoid (*vif_add_debugfs)(struct ieee80211_hw *hw,\n'
            '\t\t\t\t struct ieee80211_vif *vif);\n'
        )
        content = content.replace(anchor1, insert1 + anchor1, 1)
        print("Inserted: vif_add_debugfs (before link_add_debugfs)")
        changed = True
    else:
        print("Skip: vif_add_debugfs (already present or anchor not found)")

    # Patch 2: insert can_activate_links before change_vif_links
    anchor2 = '\tint (*change_vif_links)(struct ieee80211_hw *hw,'
    if anchor2 in content and 'can_activate_links' not in content:
        insert2 = (
            '\tbool (*can_activate_links)(struct ieee80211_hw *hw,\n'
            '\t\t\t\t   struct ieee80211_vif *vif,\n'
            '\t\t\t\t   u16 active_links);\n'
        )
        content = content.replace(anchor2, insert2 + anchor2, 1)
        print("Inserted: can_activate_links (before change_vif_links)")
        changed = True
    else:
        print("Skip: can_activate_links (already present or anchor not found)")

    # Patch 3: add type defs + can_neg_ttlm at end of struct ieee80211_ops
    # The struct ends with: "                            void *type_data);\n};"
    anchor3 = '\t\t\t    void *type_data);\n};'
    if anchor3 in content and 'can_neg_ttlm' not in content:
        type_defs = (
            '\n'
            '/* Backports-6.12.61 compat: TID-to-link mapping types */\n'
            '#define IEEE80211_TTLM_NUM_TIDS 8\n'
            'struct ieee80211_neg_ttlm {\n'
            '\tu16 downlink[IEEE80211_TTLM_NUM_TIDS];\n'
            '\tu16 uplink[IEEE80211_TTLM_NUM_TIDS];\n'
            '\tbool valid;\n'
            '};\n'
            'enum ieee80211_neg_ttlm_res {\n'
            '\tNEG_TTLM_RES_ACCEPT,\n'
            '\tNEG_TTLM_RES_REJECT,\n'
            '\tNEG_TTLM_RES_SUGGEST_PREFERRED\n'
            '};\n'
        )
        ops_field = (
            '\tenum ieee80211_neg_ttlm_res\n'
            '\t(*can_neg_ttlm)(struct ieee80211_hw *hw, struct ieee80211_vif *vif,\n'
            '\t\t\t struct ieee80211_neg_ttlm *ttlm);\n'
        )
        content = content.replace('struct ieee80211_ops {', type_defs + 'struct ieee80211_ops {', 1)
        content = content.replace(
            anchor3,
            '\t\t\t    void *type_data);\n' + ops_field + '};',
            1
        )
        print("Inserted: can_neg_ttlm + ieee80211_neg_ttlm types")
        changed = True
    else:
        print("Skip: can_neg_ttlm (already present or anchor not found)")

    if changed:
        open(path, 'w').write(content)
        print("Written:", path)
    else:
        print("No changes needed.")

    # Verify
    final = open(path).read()
    for field in ('vif_add_debugfs', 'can_activate_links', 'can_neg_ttlm'):
        count = final.count(field)
        print(f"  {field}: {count} occurrence(s)")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: patch_mac80211.py <path/to/mac80211.h>")
        sys.exit(1)
    patch(sys.argv[1])
