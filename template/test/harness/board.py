"""Facts of the board this project builds: the firmware, the clock and the serial line.

The frequency is the AVR clock answered for a bare AVR project and 16 MHz for the Arduino boards
this harness models. A board without a UART keeps the values; its boot-line test skips instead.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
{%- if platform == 'avr' and avr_language | default('c') == 'rust' %}
FIRMWARE = ROOT / "target" / "{{ avr_target }}" / "release" / "{{ repo_name }}.elf"
{%- else %}
FIRMWARE = ROOT / ".pio/build/{{ pio_board }}/firmware.elf"
{%- endif %}
FREQUENCY = {{ avr_clock if platform == 'avr' else '16000000' }}
BAUD = {{ serial_baud }}
BOOT_LINE = "[BOOT] {{ repo_name }}"
