#!/usr/bin/env python3
"""Inject probe stop points for diagnosing RTL8922AU reset during probe."""

import os
from pathlib import Path


stage = os.environ.get("RTW89_PROBE_DIAG", "").strip()
if not stage or stage == "none":
    print("probe diag disabled")
    raise SystemExit(0)


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    src = p.read_text()
    if new in src:
        print(f"{path}: already patched for {stage}")
        return
    if old not in src:
        raise SystemExit(f"{path}: pattern not found for {stage}:\n{old}")
    p.write_text(src.replace(old, new, 1))
    print(f"{path}: injected {stage}")


if stage == "before_intf_init":
    replace_once(
        "rtw89/usb.c",
        "\tret = rtw89_usb_intf_init(rtwdev, intf);\n",
        "\trtw89_err(rtwdev, \"DIAG before_intf_init: stop before USB intf init\\n\");\n"
        "\tret = -EOPNOTSUPP;\n"
        "\tgoto err_free_hw;\n"
        "\n"
        "\tret = rtw89_usb_intf_init(rtwdev, intf);\n",
    )
elif stage == "before_rx_alloc":
    replace_once(
        "rtw89/usb.c",
        "\tret = rtw89_usb_alloc_rx_bufs(rtwusb);\n",
        "\trtw89_err(rtwdev, \"DIAG before_rx_alloc: stop before RX URB allocation\\n\");\n"
        "\tret = -EOPNOTSUPP;\n"
        "\tgoto err_intf_deinit;\n"
        "\n"
        "\tret = rtw89_usb_alloc_rx_bufs(rtwusb);\n",
    )
elif stage == "before_rx_init":
    replace_once(
        "rtw89/usb.c",
        "\tret = rtw89_usb_init_rx(rtwdev);\n",
        "\trtw89_err(rtwdev, \"DIAG before_rx_init: stop before RX queue init\\n\");\n"
        "\tret = -EOPNOTSUPP;\n"
        "\tgoto err_free_rx_bufs;\n"
        "\n"
        "\tret = rtw89_usb_init_rx(rtwdev);\n",
    )
elif stage == "before_core_init":
    replace_once(
        "rtw89/usb.c",
        "\tret = rtw89_core_init(rtwdev);\n",
        "\trtw89_err(rtwdev, \"DIAG before_core_init: stop before core init\\n\");\n"
        "\tret = -EOPNOTSUPP;\n"
        "\tgoto err_deinit_rx;\n"
        "\n"
        "\tret = rtw89_core_init(rtwdev);\n",
    )
elif stage == "core_before_wiphy_work":
    replace_once(
        "rtw89/core.c",
        "\twiphy_delayed_work_init(&rtwdev->track_work, rtw89_track_work);\n",
        "\trtw89_err(rtwdev, \"DIAG core_before_wiphy_work: stop before wiphy work init\\n\");\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\twiphy_delayed_work_init(&rtwdev->track_work, rtw89_track_work);\n",
    )
elif stage == "core_after_wiphy_work":
    replace_once(
        "rtw89/core.c",
        "\trtwdev->txq_wq = alloc_workqueue(\"rtw89_tx_wq\", WQ_UNBOUND | WQ_HIGHPRI, 0);\n",
        "\trtw89_err(rtwdev, \"DIAG core_after_wiphy_work: stop after wiphy work init\\n\");\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\trtwdev->txq_wq = alloc_workqueue(\"rtw89_tx_wq\", WQ_UNBOUND | WQ_HIGHPRI, 0);\n",
    )
elif stage == "core_before_fw_work":
    replace_once(
        "rtw89/core.c",
        "\tINIT_WORK(&rtwdev->load_firmware_work, rtw89_load_firmware_work);\n",
        "\trtw89_err(rtwdev, \"DIAG core_before_fw_work: stop before firmware work init\\n\");\n"
        "\tdestroy_workqueue(rtwdev->txq_wq);\n"
        "\tmutex_destroy(&rtwdev->rf_mutex);\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\tINIT_WORK(&rtwdev->load_firmware_work, rtw89_load_firmware_work);\n",
    )
elif stage == "core_before_schedule_fw":
    replace_once(
        "rtw89/core.c",
        "\tschedule_work(&rtwdev->load_firmware_work);\n",
        "\trtw89_err(rtwdev, \"DIAG core_before_schedule_fw: stop before firmware work schedule\\n\");\n"
        "\tdestroy_workqueue(rtwdev->txq_wq);\n"
        "\tmutex_destroy(&rtwdev->rf_mutex);\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\tschedule_work(&rtwdev->load_firmware_work);\n",
    )
elif stage == "before_chip_setup":
    replace_once(
        "rtw89/usb.c",
        "\tret = rtw89_chip_info_setup(rtwdev);\n",
        "\trtw89_err(rtwdev, \"DIAG before_chip_setup: stop before chip info setup\\n\");\n"
        "\tret = -EOPNOTSUPP;\n"
        "\tgoto err_core_deinit;\n"
        "\n"
        "\tret = rtw89_chip_info_setup(rtwdev);\n",
    )
elif stage == "before_pwr_on":
    replace_once(
        "rtw89/core.c",
        "\trtw89_read_chip_ver(rtwdev);\n"
        "\n"
        "\tret = rtw89_mac_pwr_on(rtwdev);\n",
        "\trtw89_err(rtwdev, \"DIAG before_pwr_on: stop before MAC power on\\n\");\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\trtw89_read_chip_ver(rtwdev);\n"
        "\n"
        "\tret = rtw89_mac_pwr_on(rtwdev);\n",
    )
elif stage == "after_read_chip":
    replace_once(
        "rtw89/core.c",
        "\trtw89_read_chip_ver(rtwdev);\n"
        "\n"
        "\tret = rtw89_mac_pwr_on(rtwdev);\n",
        "\trtw89_read_chip_ver(rtwdev);\n"
        "\trtw89_err(rtwdev, \"DIAG after_read_chip: stop after chip version read\\n\");\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\tret = rtw89_mac_pwr_on(rtwdev);\n",
    )
elif stage == "after_pwr_on":
    replace_once(
        "rtw89/core.c",
        "\tret = rtw89_wait_firmware_completion(rtwdev);\n",
        "\trtw89_err(rtwdev, \"DIAG after_pwr_on: stop after MAC power on\\n\");\n"
        "\trtw89_mac_pwr_off(rtwdev);\n"
        "\treturn -EOPNOTSUPP;\n"
        "\n"
        "\tret = rtw89_wait_firmware_completion(rtwdev);\n",
    )
else:
    raise SystemExit(f"unknown RTW89_PROBE_DIAG={stage!r}")

print(f"SUCCESS: probe diag {stage} applied")
