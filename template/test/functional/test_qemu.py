"""Boot behaviour under QEMU, skipped with the written reason when no machine supports the board.

ACC-BOOT-1: the board prints its boot line once at startup. The board-to-machine support is the
capability matrix of `docs/best-practices.md`: `netduinoplus2` for the STM32F405RG, Espressif's
`qemu-system-xtensa -machine esp32` for ESP-IDF, and HIL only for every board without a machine.
"""

import pytest

import qemu


def test_the_firmware_starts_under_qemu():
    """ACC-BOOT-1 the firmware starts under QEMU and prints one boot line on its console."""
    result = qemu.run(seconds=5.0)
    if not result.ran:
        pytest.skip(result.reason)

    assert qemu.BOOT_LINE in result.output, result.output
