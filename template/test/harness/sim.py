"""Python binding of the simavr harness: one AVR board that runs this project's firmware."""

from __future__ import annotations

import ctypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / ".pio/simharness/libsimharness.so"

CPU_DONE, CPU_CRASHED = 6, 7

_lib = ctypes.CDLL(str(LIBRARY))
_lib.sim_new.restype = ctypes.c_void_p
_lib.sim_new.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
_lib.sim_run_us.restype = ctypes.c_int
_lib.sim_run_us.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
_lib.sim_uart_text.restype = ctypes.c_char_p
_lib.sim_uart_text.argtypes = [ctypes.c_void_p]
_lib.sim_free.argtypes = [ctypes.c_void_p]


class Board:
    """The simulated board, loaded with an ELF.

    Args:
        elf: the firmware ELF; the simulator tests use the build output
        frequency: the AVR clock in Hz
    """

    def __init__(self, elf: Path, frequency: int):
        self._sim = _lib.sim_new(str(elf).encode(), frequency)
        if not self._sim:
            raise RuntimeError(f"simavr could not load {elf}")

    def __enter__(self) -> "Board":
        return self

    def __exit__(self, *exc_info: object) -> None:
        _lib.sim_free(self._sim)
        self._sim = None

    def run(self, seconds: float) -> None:
        """Run the firmware for a number of simulated seconds, much faster than real time."""
        state = _lib.sim_run_us(self._sim, int(seconds * 1e6))
        assert state not in (CPU_DONE, CPU_CRASHED), f"firmware stopped (state {state})"

    @property
    def serial(self) -> str:
        """Everything the firmware has written to its UART so far."""
        return _lib.sim_uart_text(self._sim).decode(errors="replace")
