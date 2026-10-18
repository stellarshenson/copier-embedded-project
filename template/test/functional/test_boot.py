"""Boot behaviour of the starter firmware, checked on the simavr board model.

ACC-BOOT-1: the board prints its boot line once at startup. simavr runs the boards it documents
and at most 128 KB of flash; a board it does not document skips with the reason, and the boot check
runs on hardware (HIL) instead.
"""

{%- set runs_on_simavr = (platform == 'arduino' and arduino_board in ['uno', 'nano'])
    or (platform == 'avr' and avr_mcu in ['atmega328p', 'attiny85']) %}
{%- if not runs_on_simavr %}
import pytest

{%- if platform == 'arduino' and arduino_board == 'mega2560' %}
pytest.skip(
    "simavr documents at most 128 KB of flash; the ATmega2560 has 256 KB. Run the boot check on "
    "hardware (HIL).",
    allow_module_level=True,
)
{%- elif platform == 'arduino' and arduino_board == 'leonardo' %}
pytest.skip(
    "simavr does not document the ATmega32U4. Run the boot check on hardware (HIL).",
    allow_module_level=True,
)
{%- elif platform == 'arduino' and arduino_board == 'other' %}
pytest.skip(
    "the template carries no simavr model for the board {{ arduino_board_custom }}. A board is "
    "simulated when its MCU is documented and the flash is at most 128 KB; run the boot check on "
    "hardware (HIL).",
    allow_module_level=True,
)
{%- elif platform == 'avr' and avr_mcu == 'atmega32u4' %}
pytest.skip(
    "simavr does not document the ATmega32U4. Run the boot check on hardware (HIL).",
    allow_module_level=True,
)
{%- elif platform == 'avr' %}
pytest.skip(
    "the template carries no simavr model for the MCU {{ avr_mcu_custom }}. An MCU is simulated "
    "when it is documented and the flash is at most 128 KB; run the boot check on hardware (HIL).",
    allow_module_level=True,
)
{%- else %}
pytest.skip(
    "simavr runs AVR firmware only; this board has no simavr model. The simulator tier runs under "
    "QEMU, or the boot check runs on hardware (HIL).",
    allow_module_level=True,
)
{%- endif %}
{%- else %}
import pytest

import board
import sim


def test_the_firmware_runs_on_the_simulator():
    """ACC-BOOT-1 the firmware runs on the simavr model without stopping or crashing."""
    with sim.Board(board.FIRMWARE, board.FREQUENCY) as device:
        device.run(0.2)


{%- if platform == 'avr' and avr_mcu == 'attiny85' %}
def test_the_firmware_prints_its_boot_line():
    """ACC-BOOT-1 the ATtiny85 has no UART, so the boot line is not checked."""
    pytest.skip("the ATtiny85 has no UART")
{%- else %}
def test_the_firmware_prints_its_boot_line():
    """ACC-BOOT-1 the board boots and prints one boot line on its UART."""
    with sim.Board(board.FIRMWARE, board.FREQUENCY) as device:
        device.run(0.2)
        text = device.serial

    assert board.BOOT_LINE in text, f"serial output: {text!r}"
{%- endif %}
{%- endif %}
