---
name: {{ repo_name }}-device
description: Operate the {{ project_name }} board - find its port, build, upload, read the console without holding the port, and troubleshoot a failed flash. Use when building, uploading to, monitoring or debugging this board.
---
{%- if platform == 'arduino' -%}
  {%- set parts = {
    'uno': ('ATmega328P', '16 MHz', '32 KB flash, 2 KB SRAM'),
    'nano': ('ATmega328P', '16 MHz', '32 KB flash, 2 KB SRAM'),
    'mega2560': ('ATmega2560', '16 MHz', '256 KB flash, 8 KB SRAM'),
    'leonardo': ('ATmega32U4', '16 MHz', '32 KB flash, 2.5 KB SRAM'),
  } -%}
  {%- if arduino_board == 'other' -%}
    {%- set part = (arduino_board_custom, 'the board definition in PlatformIO', 'flash and RAM from its datasheet') -%}
  {%- else -%}
    {%- set part = parts[arduino_board] -%}
  {%- endif -%}
  {%- set reset_action = 'tap reset just before the upload' -%}
{%- elif platform == 'avr' -%}
  {%- set parts = {
    'atmega328p': ('ATmega328P', '32 KB flash, 2 KB SRAM'),
    'atmega32u4': ('ATmega32U4', '32 KB flash, 2.5 KB SRAM'),
    'attiny85': ('ATtiny85', '8 KB flash, 512 B SRAM'),
  } -%}
  {%- if avr_mcu == 'other' -%}
    {%- set part = (avr_mcu_custom, 'flash and RAM from its datasheet') -%}
  {%- else -%}
    {%- set part = parts[avr_mcu] -%}
  {%- endif -%}
  {%- set reset_action = 'check the programmer wiring and the target power' -%}
{%- elif platform == 'esp' -%}
  {%- set reset_action = 'hold BOOT, tap EN, release BOOT, then upload' -%}
{%- elif stm32_toolchain == 'rust' -%}
  {%- set stm32_parts = {
    'f405rg': ('STM32F405RGT6', '168 MHz'),
    'f103c8': ('STM32F103C8T6', '72 MHz'),
    'f411re': ('STM32F411RET6', '100 MHz'),
    'l476rg': ('STM32L476RGT6', '80 MHz'),
  } -%}
  {%- set part = stm32_parts[stm32_board] -%}
  {%- set reset_action = 'set BOOT0 high and reset, upload, then set BOOT0 low and reset' -%}
{%- else -%}
  {%- set stm32_parts = {
    'f405rg': ('STM32F405RGT6', '168 MHz'),
    'f103c8': ('STM32F103C8T6', '72 MHz'),
    'f411re': ('STM32F411RET6', '100 MHz'),
    'l476rg': ('STM32L476RGT6', '80 MHz'),
  } -%}
  {%- set part = stm32_parts[stm32_board] -%}
  {%- set reset_action = 'over serial, set BOOT0 high and reset; over ST-Link, check the wiring' -%}
{%- endif -%}
{%- set installer_name = 'firmware-avr' if platform in ['arduino', 'avr'] else 'firmware-' ~ platform -%}
{%- set simulator = 'simulator' in components -%}
{%- set uart = not (platform == 'avr' and avr_mcu == 'attiny85') %}

# {{ project_name }} device skill

Device facts, commands and failure modes of this board. `make help` is the command index; the
targets below are the whole development lifecycle.

## Board facts

{% if platform == 'arduino' -%}
- Platform: Arduino framework on PlatformIO
- Board: `{{ pio_board }}`
- MCU: {{ part[0] }}, {{ part[1] }}, {{ part[2] }}
- Upload: USB serial bootloader{% if arduino_board == 'nano' %}, {{ arduino_bootloader }} bootloader at {{ '57600' if arduino_bootloader == 'old' else '115200' }} baud{% endif %}
- Console: {{ serial_baud }} baud, 8N1
{%- elif platform == 'avr' -%}
- Platform: bare AVR {% if avr_language | default('c') == 'rust' %}with Cargo and avrdude{% else %}on PlatformIO{% endif %}
- Board: `{{ pio_board or avr_cpu }}`
- MCU: {{ part[0] }}, {{ avr_clock }} Hz, {{ part[1] }}
- Upload: {% if avr_language | default('c') == 'rust' %}ISP through `avrdude -c {{ 'arduinoisp' if avr_programmer == 'arduino-isp' else 'usbasp' }}`{% else %}{{ pio_upload_protocol }} programmer{% endif %}
{%- if avr_mcu == 'attiny85' %}
- Console: none; the ATtiny85 has no UART
{%- else %}
- Console: {{ serial_baud }} baud, 8N1
{%- endif %}
{%- elif platform == 'esp' -%}
- Platform: Espressif {{ esp_chip }}, framework {{ esp_framework }}
- Board: `{{ esp_board }}`
{%- if esp_chip == 'esp32' %}
- MCU: ESP32, dual-core Xtensa at 240 MHz, 4 MB flash, 520 KB SRAM
{%- else %}
- MCU: ESP8266 at 80 MHz, 4 MB flash, 80 KB SRAM
{%- endif %}
- Upload: USB serial bootloader
- Console: {{ serial_baud }} baud, 8N1
{%- elif stm32_toolchain == 'rust' -%}
- Platform: STM32, Rust embedded with Cargo
- Board: `{{ stm32_board }}`
- MCU: {{ part[0] }}, {{ part[1] }}, {{ flash_kb }} KB flash, {{ ram_kb }} KB RAM
- Upload: stm32flash over the ROM serial bootloader
- A port that refuses parity, such as a device bridge pty, needs `STM32_SERIAL_MODE=8n1` in `.env`
- Console: {{ serial_baud }} baud, 8E1 on a direct port
{%- else -%}
- Platform: STM32, framework {{ stm32_framework }} on PlatformIO
- Board: `{{ pio_board }}` ({{ stm32_board }})
- MCU: {{ part[0] }}, {{ part[1] }}, {{ flash_kb }} KB flash, {{ ram_kb }} KB RAM
- Upload: {% if stm32_upload == 'serial' %}the ROM serial bootloader through `stm32flash`{% else %}ST-Link through the debug probe{% endif %}
- Console: {{ serial_baud }} baud
{%- endif %}

## Port discovery

- List the ports: `ls /dev/ttyUSB* /dev/ttyACM*`
- With several ports, unplug the board, list again, and use the entry that disappeared
{%- if platform == 'avr' and avr_mcu == 'attiny85' %}
- The upload uses the ISP programmer and needs no port; the {{ part[0] }} has no UART, so no console port exists
{%- elif platform == 'avr' %}
- The upload uses the ISP programmer and needs no port; attach a USB-serial adapter to the UART pins for the console
{%- endif %}

## Environment

{% if 'env-installers' in components -%}
- `make create_environment` installs the conda environment `{{ env_name }}` with the toolchain of this project
{% else -%}
- This project carries no installer; run `~/.local/lab-utils/envs/{{ installer_name }}.py` to install the conda environment `{{ env_name }}`
{% endif -%}
- Every make target runs its tool inside that environment; no activation step is needed

## Build and upload

1. `make build`
2. Put the board in upload mode: {{ reset_action }}
3. `make upload PORT=<port>` - `PORT` defaults to the `PORT` set in `.env`, else `/dev/ttyUSB0`{% if uart %}, and `BAUD` to the console baud above{% endif %}
{%- if uart %}
4. Read the console until `[BOOT] {{ repo_name }}` appears, then stop
{%- else %}
4. The board has no UART; confirm the boot behaviour in the simulator
{%- endif %}

## Non-interactive console

{% if uart -%}
Read the port until the boot line appears and then stop. Do not leave an interactive monitor
running in an automated step.

```bash
conda run --no-capture-output -n {{ env_name }} python - <<'PY'
import serial

with serial.Serial("<port>", {{ serial_baud }}, timeout=1) as port:
    for _ in range(60):
        line = port.readline().decode(errors="replace").rstrip()
        if line:
            print(line)
        if "[BOOT] {{ repo_name }}" in line:
            break
PY
```
{%- if host_side == 'Yes' %}

`make host-run PORT=<port>` reads the boot line non-interactively with the host application and
prints one JSON line.
{%- endif %}
{%- else -%}
The {{ part[0] }} has no UART, so the board prints no console. Confirm the boot behaviour in the
simulator, or decode the signal pin with a logic analyser.
{%- endif %}

## Commands

| Task | Command |
|---|---|
| Create the environment | {% if 'env-installers' in components %}`make create_environment`{% else %}`~/.local/lab-utils/envs/{{ installer_name }}.py`{% endif %} |
| Build | `make build` |
| Upload | `make upload PORT=<port>` |
{%- if uart %}
| Read the console | `make monitor PORT=<port> BAUD={{ serial_baud }}` (interactive), or the read loop above |
{%- endif %}
| Run the tests | `make test` |
{%- if simulator %}
| Run the simulator tests | `make sim` |
{%- endif %}
{%- if platform in ['arduino', 'avr'] %}
| Back up the EEPROM | `make eeprom-backup PORT=<port>` |
| Restore the EEPROM | `make eeprom-restore PORT=<port>` |
{%- endif %}
| List the targets | `make help` |
| Remove build output | `make clean` |

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| No port listed | charge-only cable, missing driver, or the board is off | use a data cable; check `dmesg \| tail` after plugging |
| `Permission denied` on the port | the user is not in `dialout` | `sudo usermod -aG dialout $USER`, then log in again |
| Upload times out | the board is not in its bootloader | {{ reset_action }} |
{%- if uart %}
| Console output is garbled | wrong baud or parity | use {{ serial_baud }} baud 8N1{% if platform == 'stm32' and stm32_toolchain == 'rust' %}; the ROM serial bootloader on a direct port uses 8E1{% endif %} |
{%- endif %}
{%- if simulator %}
| The simulator test skips | the emulator does not cover this board | read the printed reason and run the test on hardware |
{%- endif %}
{%- if simulator %}

## Simulator limits

{% if platform == 'arduino' -%}
{%- if arduino_board in ['uno', 'nano'] -%}
simavr models this board; `make sim` boots the firmware and asserts the boot line.
{%- elif arduino_board == 'mega2560' -%}
HIL only: 256 KB is above simavr's documented 128 KB limit. `make sim` skips with that reason; run
the test on a board.
{%- elif arduino_board == 'leonardo' -%}
HIL only: simavr does not document the ATmega32U4. `make sim` skips; run the test on a board.
{%- else -%}
HIL only unless the MCU is documented by simavr and the flash is at most 128 KB. `make sim` skips
with the reason; run the test on a board.
{%- endif -%}
{%- elif platform == 'avr' -%}
{%- if avr_mcu == 'atmega328p' -%}
simavr models this MCU; `make sim` boots the firmware and asserts the boot line.
{%- elif avr_mcu == 'attiny85' -%}
simavr models this MCU, but it has no UART, so the boot-line test skips with that reason.
{%- else -%}
HIL only: simavr does not document this MCU. `make sim` skips; run the test on a board.
{%- endif -%}
{%- elif platform == 'esp' -%}
{%- if esp_chip == 'esp32' -%}
Espressif's QEMU fork (`qemu-system-xtensa -machine esp32`) runs the firmware, for the ESP-IDF and
Arduino frameworks. `make sim` uses it when the fork is installed and skips with the reason otherwise.
{%- else -%}
HIL only: QEMU has no ESP8266 machine. `make sim` skips; run the test on a board.
{%- endif -%}
{%- elif stm32_board == 'f405rg' -%}
QEMU `netduinoplus2` models this board. `make sim` uses it when qemu-system-arm is installed and
skips with the reason otherwise.
{%- else -%}
HIL only: QEMU has no machine for this board. `make sim` skips; run the test on a board.
{%- endif -%}
{%- endif %}
