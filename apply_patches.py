import sys

with open('rtw89/mac80211.c', 'r') as f:
    src = f.read()

orig = src

ANCHOR = '\treturn ret;\n}\n\nstatic int rtw89_ops_set_key'
HELPER = '\treturn ret;\n}\n\nstatic bool rtw89_is_usb_ap(struct rtw89_dev *rtwdev,\n\t\t\t     struct ieee80211_vif *vif)\n{\n\treturn rtwdev->hci.type == RTW89_HCI_TYPE_USB &&\n\t       vif && vif->type == NL80211_IFTYPE_AP;\n}\n\nstatic int rtw89_ops_set_key'

if 'rtw89_is_usb_ap' in src:
    print('helper already present')
elif ANCHOR in src:
    src = src.replace(ANCHOR, HELPER, 1)
    print('Inserted rtw89_is_usb_ap helper')
else:
    print('ERROR: anchor not found')
    idx = src.find('rtw89_ops_set_key')
    print(repr(src[max(0,idx-150):idx+50]))
    sys.exit(1)

OLD_KEY = '\tcase DISABLE_KEY:\n\t\trtw89_hci_flush_queues(rtwdev, BIT(rtwdev->hw->queues) - 1,\n\t\t\t\t       false);\n\t\trtw89_mac_flush_txq(rtwdev, BIT(rtwdev->hw->queues) - 1, false);\n\t\tret = rtw89_cam_sec_key_del'
NEW_KEY = '\tcase DISABLE_KEY:\n\t\tif (!rtw89_is_usb_ap(rtwdev, vif)) {\n\t\t\trtw89_hci_flush_queues(rtwdev, BIT(rtwdev->hw->queues) - 1,\n\t\t\t\t\t       false);\n\t\t\trtw89_mac_flush_txq(rtwdev, BIT(rtwdev->hw->queues) - 1, false);\n\t\t}\n\t\tret = rtw89_cam_sec_key_del'

if OLD_KEY in src:
    src = src.replace(OLD_KEY, NEW_KEY, 1)
    print('Applied DISABLE_KEY guard')
else:
    print('WARNING: DISABLE_KEY pattern not found')
    idx = src.find('case DISABLE_KEY')
    print(repr(src[idx:idx+300]))

OLD_FLUSH = '\tif (drop && !RTW89_CHK_FW_FEATURE(NO_PACKET_DROP, &rtwdev->fw))\n\t\t__rtw89_drop_packets(rtwdev, vif);\n\telse\n\t\trtw89_mac_flush_txq(rtwdev, queues, drop);\n'
NEW_FLUSH = '\tif (drop && !RTW89_CHK_FW_FEATURE(NO_PACKET_DROP, &rtwdev->fw))\n\t\t__rtw89_drop_packets(rtwdev, vif);\n\telse if (!rtw89_is_usb_ap(rtwdev, vif))\n\t\trtw89_mac_flush_txq(rtwdev, queues, drop);\n'

if OLD_FLUSH in src:
    src = src.replace(OLD_FLUSH, NEW_FLUSH, 1)
    print('Applied ops_flush guard')
else:
    print('WARNING: ops_flush pattern not found')
    idx = src.find('rtw89_ops_flush')
    print(repr(src[idx:idx+500]))

if src == orig:
    print('ERROR: no changes')
    sys.exit(1)
else:
    print('SUCCESS')
    print(f'Lines: {len(orig.splitlines())} -> {len(src.splitlines())}')
