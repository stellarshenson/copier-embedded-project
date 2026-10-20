"""read_boot_line against fixed line lists: no board and no serial port."""

from {{ host_module }}.serial_client import read_boot_line

BOOT_LINE = "[BOOT] {{ repo_name }}"


def test_the_boot_line_is_found_among_other_lines():
    lines = ["noise\r\n", f"{BOOT_LINE}\r\n", "after\r\n"]
    assert read_boot_line(lines, BOOT_LINE, timeout=5) == BOOT_LINE


def test_no_boot_line_gives_none():
    assert read_boot_line(["noise\r\n", "more\r\n"], BOOT_LINE, timeout=5) is None


def test_the_timeout_ends_the_read_before_a_late_boot_line():
    lines = ["noise\r\n", f"{BOOT_LINE}\r\n"]
    assert read_boot_line(lines, BOOT_LINE, timeout=0) is None
