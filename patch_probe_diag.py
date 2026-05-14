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


if stage == "before_chip_setup":
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
