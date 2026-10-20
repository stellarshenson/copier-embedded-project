"""Checksums shared with the firmware.

crc8 mirrors {% if toolchain_language == 'rust' %}crc8 in src/lib.rs{% else %}core_crc8 in lib/core/core.c{% endif %}: polynomial 0x07, initial value 0x00,
most significant bit first, no reflection and no final XOR.
"""


def crc8(data: bytes) -> int:
    """CRC-8 of a byte buffer, polynomial 0x07, initial value 0x00."""
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc
