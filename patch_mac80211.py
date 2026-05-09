#!/usr/bin/env python3
"""
This helper is intentionally a no-op.

The previous version patched struct ieee80211_ops directly, but that pushed
wake_tx_queue to the wrong offset for iStoreOS. The active fix is now in the
kernel build configuration: CONFIG_IPV6 must be disabled so mac80211.h does
not include ipv6_addr_change, which keeps wake_tx_queue at the offset
expected by the device's mac80211.ko.
"""
import sys

def patch(path):
    _ = path
    print("patch_mac80211.py is deprecated; no file changes are made.")
    print("Use CONFIG_IPV6=n in the kernel build so wake_tx_queue keeps the expected offset.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: patch_mac80211.py <path/to/mac80211.h>")
        sys.exit(1)
    patch(sys.argv[1])
