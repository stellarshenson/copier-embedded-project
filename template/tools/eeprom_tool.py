#!/usr/bin/env python3
"""Non-interactive EEPROM backup and restore for Arduino and bare AVR boards.

The tool drives avrdude, never prompts, prints exactly one JSON line on stdout, and exits
non-zero when the operation fails. A restore reads the image back and compares it with the
backup before it reports success.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EEPROM_DIR = ROOT / "resources" / "eeprom"

# PlatformIO board id -> avrdude part, programmer and upload baud. A bare AVR project passes the
# part and the programmer explicitly; the map is consulted only for values not given.
BOARDS = {
    "uno": ("atmega328p", "arduino", "115200"),
    "nanoatmega328": ("atmega328p", "arduino", "57600"),
    "nanoatmega328new": ("atmega328p", "arduino", "115200"),
    "pro8MHzatmega328": ("atmega328p", "arduino", "57600"),
    "megaatmega2560": ("atmega2560", "arduino", "115200"),
    "leonardo": ("atmega32u4", "avr109", "57600"),
    "attiny85": ("attiny85", "usbasp", ""),
}


def emit(payload: dict) -> None:
    print(json.dumps(payload, sort_keys=True))


def fail(action: str, message: str) -> None:
    emit({"ok": False, "action": action, "error": message})
    raise SystemExit(1)


def resolve(args: argparse.Namespace) -> tuple[str, str, str]:
    part, programmer, baud = BOARDS.get(args.board, ("", "", ""))
    part = args.mcu or part
    programmer = args.programmer or programmer
    baud = args.baud or baud
    if not part:
        fail(args.action, f"unknown board '{args.board}'; pass --mcu")
    if not programmer:
        fail(args.action, f"unknown board '{args.board}'; pass --programmer")
    return part, programmer, baud


def avrdude(
    action: str, part: str, programmer: str, port: str, baud: str, *extra: str
) -> None:
    command = ["avrdude", "-c", programmer, "-p", part, "-P", port]
    if programmer in ("arduino", "avr109") and baud:
        command += ["-b", baud]
    command += list(extra)
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        fail(action, "avrdude is not installed in the environment")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        fail(action, detail[-1] if detail else f"avrdude exited {result.returncode}")


def backup(args: argparse.Namespace, part: str, programmer: str, baud: str) -> None:
    EEPROM_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    image = EEPROM_DIR / f"{args.board or part}-{stamp}.bin"
    avrdude(args.action, part, programmer, args.port, baud, "-U", f"eeprom:r:{image}:r")
    if not image.is_file():
        fail("backup", "avrdude did not write the image")
    emit(
        {
            "ok": True,
            "action": "backup",
            "board": args.board or part,
            "file": str(image),
            "bytes": image.stat().st_size,
        }
    )


def newest_image() -> Path:
    images = sorted(
        EEPROM_DIR.glob("*.bin"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    if not images:
        fail("restore", f"no backup in {EEPROM_DIR}")
    return images[0]


def restore(args: argparse.Namespace, part: str, programmer: str, baud: str) -> None:
    image = Path(args.image) if args.image else newest_image()
    if not image.is_file():
        fail("restore", f"image not found: {image}")
    expected = image.read_bytes()
    avrdude(
        args.action, part, programmer, args.port, baud, "-D", "-U", f"eeprom:w:{image}:r"
    )
    with tempfile.TemporaryDirectory() as temporary:
        readback = Path(temporary) / "readback.bin"
        avrdude(
            args.action,
            part,
            programmer,
            args.port,
            baud,
            "-U",
            f"eeprom:r:{readback}:r",
        )
        actual = readback.read_bytes() if readback.is_file() else b""
    if actual != expected:
        fail(
            "restore",
            f"read-back does not match {image}: {len(actual)} of {len(expected)} bytes",
        )
    emit(
        {
            "ok": True,
            "action": "restore",
            "file": str(image),
            "bytes": len(expected),
            "verified": True,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("--board", default="", help="PlatformIO board id")
    parser.add_argument("--mcu", default="", help="avrdude part name")
    parser.add_argument("--programmer", default="", help="avrdude programmer id")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", default="", help="upload baud of a serial bootloader")
    parser.add_argument(
        "--image", default="", help="image to restore; newest backup by default"
    )
    args = parser.parse_args()
    part, programmer, baud = resolve(args)
    if args.action == "backup":
        backup(args, part, programmer, baud)
    else:
        restore(args, part, programmer, baud)


if __name__ == "__main__":
    main()
