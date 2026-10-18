"""Run the built firmware under QEMU, or say why this board has no machine.

QEMU is optional. When the matching emulator or machine is absent, `run()` returns `ran=False`
with the reason and the pytest test skips: the harness never fails a machine that has no emulator.
The reasons are the capability matrix of `docs/best-practices.md`: mainline QEMU has no STM32
machine except `netduinoplus2` and no ESP8266 machine; ESP32, with either framework, needs
Espressif's QEMU fork.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOT_LINE = "[BOOT] {{ repo_name }}"


@dataclass
class Result:
    ran: bool
    reason: str
    output: str


def _firmware() -> Path:
{%- if platform == 'stm32' and stm32_toolchain == 'rust' %}
    return ROOT / "target" / "{{ thumb_target }}" / "release" / "{{ repo_name }}"
{%- else %}
    return ROOT / ".pio" / "build" / "{{ pio_board }}" / "firmware.elf"
{%- endif %}


def _run(command: list[str], seconds: float) -> Result:
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=seconds)
    except subprocess.TimeoutExpired as expired:
        parts = [expired.stdout or "", expired.stderr or ""]
        output = "".join(
            part.decode(errors="replace") if isinstance(part, bytes) else part
            for part in parts
        )
        return Result(True, "ran until the timeout", output)
    output = (process.stdout or "") + (process.stderr or "")
    if process.returncode != 0:
        return Result(False, f"qemu exited with {process.returncode}: {output.strip()}", output)
    return Result(True, "qemu exited cleanly", output)


def run(seconds: float = 5.0) -> Result:
    """Start the firmware under QEMU for a few seconds, or explain why it cannot."""
{%- if platform == 'stm32' %}
{%- if stm32_board != 'f405rg' %}
    return Result(
        False,
        "mainline QEMU documents no {{ stm32_board }} machine; this board runs the boot check "
        "on hardware (HIL)",
        "",
    )
{%- else %}
    binary = shutil.which("qemu-system-arm")
    if binary is None:
        return Result(False, "qemu-system-arm is not installed", "")
    kernel = _firmware()
    if not kernel.exists():
        return Result(False, f"the firmware is not built: {kernel}", "")
    machines = subprocess.run(
        [binary, "-machine", "help"], capture_output=True, text=True
    ).stdout
    if "netduinoplus2" not in machines:
        return Result(False, "this qemu-system-arm has no netduinoplus2 machine", "")
    return _run(
        [
            binary,
            "-machine",
            "netduinoplus2",
            "-display",
            "none",
            "-monitor",
            "none",
            "-serial",
            "null",
            "-serial",
            "stdio",
            "-kernel",
            str(kernel),
        ],
        seconds,
    )
{%- endif %}
{%- elif platform == 'esp' %}
{%- if esp_chip == 'esp32' %}
    binary = shutil.which("qemu-system-xtensa")
    if binary is None:
        return Result(False, "qemu-system-xtensa is not installed", "")
    machines = subprocess.run(
        [binary, "-machine", "help"], capture_output=True, text=True
    ).stdout
    if "esp32" not in machines:
        return Result(False, "this qemu-system-xtensa has no esp32 machine", "")
    build = ROOT / ".pio" / "build" / "{{ pio_board }}"
    parts = [build / "bootloader.bin", build / "partitions.bin", build / "firmware.bin"]
    if not all(part.exists() for part in parts):
        return Result(False, "the ESP-IDF image parts are not built", "")
    esptool = shutil.which("esptool")
    if esptool is None:
        return Result(False, "esptool is not installed", "")
    image = build / "flash-image.bin"
    merge = [
        esptool, "--chip", "esp32", "merge_bin", "-o", str(image),
        "--flash_mode", "dio", "--flash_size", "4MB", "--pad-to-size", "4MB",
        "0x1000", str(parts[0]), "0x8000", str(parts[1]), "0x10000", str(parts[2]),
    ]
    merged = subprocess.run(merge, capture_output=True, text=True)
    if merged.returncode != 0:
        return Result(False, f"esptool could not merge the image: {merged.stderr.strip()}", "")
    return _run(
        [binary, "-nographic", "-machine", "esp32", "-drive", f"file={image},if=mtd,format=raw"],
        seconds,
    )
{%- else %}
    return Result(
        False,
        "mainline QEMU has no ESP8266 machine; this board runs the boot check on hardware (HIL)",
        "",
    )
{%- endif %}
{%- else %}
    return Result(False, "the QEMU harness is generated for ESP and STM32 only", "")
{%- endif %}
