"""Read the console of the board.

read_boot_line works on any iterable of text lines, so the tests pass a list and need no board.
open_port supplies the lines of a real serial port.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Iterator


def read_boot_line(lines: Iterable[str], expected: str, timeout: float) -> str | None:
    """Return the first line that contains `expected`.

    None means the lines ended, or `timeout` seconds passed, before that line.
    """
    deadline = time.monotonic() + timeout
    for line in lines:
        if expected in line:
            return line.strip()
        if time.monotonic() >= deadline:
            return None
    return None


def open_port(port: str, baud: int) -> Iterator[str]:
    """Yield the decoded lines of the serial port; an empty line marks a read without data."""
    import serial  # pyserial is needed only for a real port

    with serial.Serial(port, baud, timeout=0.5) as connection:
        while True:
            yield connection.readline().decode("utf-8", errors="replace")
