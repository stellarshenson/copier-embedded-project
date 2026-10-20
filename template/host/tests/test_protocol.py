"""crc8 against vectors computed with the CRC-8 of the firmware core."""

import pytest

from {{ host_module }}.protocol import crc8


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"", 0x00),
        (b"123456789", 0xF4),
        (b"\x00", 0x00),
        (b"\x01", 0x07),
        (b"\xff", 0xF3),
        (b"[BOOT]", 0x94),
        (b"\xde\xad\xbe\xef", 0xCA),
    ],
)
def test_crc8_matches_the_core(data, expected):
    assert crc8(data) == expected
