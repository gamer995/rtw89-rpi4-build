#!/usr/bin/env python3
"""Use synchronous firmware completion for rtw89 on iStoreOS RPi4."""

from pathlib import Path


path = Path("rtw89/core.c")
src = path.read_text()

old = "\tschedule_work(&rtwdev->load_firmware_work);\n"
new = (
    "\t/* iStoreOS RPi4 reboots when this firmware request is deferred to\n"
    "\t * the system workqueue during USB probe. The firmware was already\n"
    "\t * requested by rtw89_early_fw_feature_recognize(); complete it in\n"
    "\t * probe context, and fall back to a synchronous request if needed.\n"
    "\t */\n"
    "\tif (rtwdev->fw.req.firmware)\n"
    "\t\tcomplete_all(&rtwdev->fw.req.completion);\n"
    "\telse\n"
    "\t\trtw89_load_firmware_work(&rtwdev->load_firmware_work);\n"
)

if new in src:
    print("sync firmware patch already applied")
elif old in src:
    path.write_text(src.replace(old, new, 1))
    print("SUCCESS: replaced async firmware work with synchronous completion")
else:
    raise SystemExit("core.c: schedule_work(load_firmware_work) pattern not found")
