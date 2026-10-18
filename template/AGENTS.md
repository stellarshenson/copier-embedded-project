{%- set espidf = platform == 'esp' and esp_framework == 'espidf' -%}
{%- set rust = toolchain_language == 'rust' -%}
{%- set avr_programmer_id = ('arduinoisp' if avr_programmer == 'arduino-isp' else 'usbasp') if platform == 'avr' else '' -%}
{%- set simulator = 'simulator' in components -%}
{%- set installers = 'env-installers' in components -%}
{%- set eeprom = platform in ['arduino', 'avr'] -%}
{%- if platform == 'avr' -%}
{%- set board_id = pio_board or avr_cpu -%}
{%- elif platform == 'stm32' and stm32_toolchain != 'platformio' -%}
{%- set board_id = stm32_board -%}
{%- else -%}
{%- set board_id = pio_board -%}
{%- endif -%}
# {{ project_name }}

{{ description or 'Firmware for ' ~ platform }}

- Platform: {% if platform == 'arduino' %}Arduino{% elif platform == 'avr' %}bare AVR{% elif platform == 'esp' %}{{ 'ESP32' if esp_chip == 'esp32' else 'ESP8266' }}{% else %}STM32{% endif %}

- Board: `{{ board_id }}`

- Boot line: `[BOOT] {{ repo_name }}`

- Console baud: {{ serial_baud }}

## Structure

- `{% if espidf %}main/{% else %}src/{% endif %}` - the application adapter
{% if rust -%}
- `src/lib.rs` - the shared core; `src/bin/{{ repo_name }}.rs` calls it
{% else -%}
- `lib/core/core.c` and `lib/core/core.h` - the shared core; the adapter includes `"core.h"`
{% endif -%}
- `test/host/` - host unit tests of the shared core
{% if simulator -%}
- `test/harness/` - simulator wrapper and board helpers
- `test/functional/` - boot and behaviour tests
{% endif -%}
{% if 'resources' in components or installers or eeprom -%}
- `resources/` - graphics, external files{% if installers %}, and `resources/envs/`{% endif %}{% if eeprom %}, and `resources/eeprom/`{% endif %}
{% endif -%}

{% if 'references' in components -%}
- `references/` - datasheets and notes
{% endif -%}
{% if 'docs' in components -%}
- `docs/` - design, acceptance criteria and defects
{% endif -%}
- `tools/` - non-interactive project tools{% if eeprom %}, including `tools/eeprom_tool.py`{% endif %}
- `Makefile` - the entry point for every development command
{% if 'agents' in components -%}
- `.agents/skills/{{ repo_name }}-device` - board facts, upload, console and safety
- `.agents/skills/{{ repo_name }}-toolchain` - environment, simulators and LTspice
{% endif -%}

## Commands

- `make help` - list the rendered targets
{% if installers -%}
- `make create_environment` (alias `make env`) - install the conda environment `{{ env_name }}`
{% else -%}
- `~/.local/lab-utils/envs/firmware-{% if platform in ['arduino', 'avr'] %}avr{% else %}{{ platform }}{% endif %}.py` - install the toolchain; this project carries no installer
{% endif -%}
- `make build` - build the firmware
- `make upload PORT=/dev/ttyUSB0` - flash the board
- `make monitor PORT=/dev/ttyUSB0 BAUD={{ serial_baud }}` - open the serial console
- `make test` - run the host unit tests{% if simulator %} and the simulator tests{% endif %}

{% if simulator -%}
- `make sim` - run the functional tests against the emulator
{% endif -%}
{% if eeprom -%}
- `make eeprom-backup` - save the EEPROM under `resources/eeprom/` and print one JSON line
- `make eeprom-restore` - write a backup and verify the read-back
{% endif -%}
- `make clean` - remove build output and caches
- `make increment_version` - increment the patch version in `VERSION`
- `RELEASING.md` - the release process, from the version increment to the push
- `CHANGELOG.md` - record changes under `[Unreleased]` until a release moves them under the version heading
{% if 'agents' in components -%}
- `/release` - run the release process as an agent workflow; it asks for approval before the commit, the tag and the push
{% endif -%}

Every command runs inside the conda environment through the Makefile. Do not call a toolchain program directly.

## Test tiers and emulator

| Tier | Where | Command |
|---|---|---|
| Host | `test/host/` | `make test` |
{% if simulator -%}
| Simulator | `test/functional/` with `test/harness/` | `make sim` |
{% endif -%}
| HIL | the board on the bench | `make upload`, then read `[BOOT] {{ repo_name }}` |

| Platform | Board / MCU | Host | Simulator | HIL |
|---|---|---|---|---|
{% if platform == 'arduino' -%}
{% if arduino_board == 'uno' -%}
| Arduino | uno (ATmega328P, 32 KB) | yes | simavr | yes |
{% elif arduino_board == 'nano' -%}
| Arduino | nano, old or new bootloader (ATmega328P) | yes | simavr | yes |
{% elif arduino_board == 'mega2560' -%}
| Arduino | mega2560 (ATmega2560, 256 KB) | yes | HIL only: 256 KB is above simavr's documented 128 KB limit | yes |
{% elif arduino_board == 'leonardo' -%}
| Arduino | leonardo (ATmega32U4) | yes | HIL only: simavr does not document the ATmega32U4 | yes |
{% else -%}
| Arduino | other | yes | HIL only unless the MCU is documented and the flash is at most 128 KB | yes |
{% endif -%}
{% elif platform == 'avr' -%}
{% if avr_mcu == 'atmega328p' -%}
| Bare AVR | atmega328p at 16 MHz or 8 MHz | yes | simavr | yes |
{% elif avr_mcu == 'atmega32u4' -%}
| Bare AVR | atmega32u4 | yes | HIL only: not documented by simavr | yes |
{% elif avr_mcu == 'attiny85' -%}
| Bare AVR | attiny85 | yes | simavr; no UART, so the boot-line test skips | yes |
{% else -%}
| Bare AVR | other | yes | HIL only unless documented and at most 128 KB | yes |
{% endif -%}
{% elif platform == 'esp' -%}
{% if esp_chip == 'esp32' and esp_framework == 'espidf' -%}
| ESP32, ESP-IDF | esp32dev, esp32doit-devkit-v1 | yes | Espressif QEMU fork, `qemu-system-xtensa -machine esp32` | yes |
{% elif esp_chip == 'esp32' -%}
| ESP32, Arduino | esp32dev, esp32doit-devkit-v1 | yes | Espressif QEMU fork, `qemu-system-xtensa -machine esp32` | yes |
{% elif esp_framework == 'esp8266-rtos-sdk' -%}
| ESP8266, RTOS SDK | nodemcuv2, d1_mini | yes | HIL only: no ESP8266 machine | yes |
{% else -%}
| ESP8266, Arduino | nodemcuv2, d1_mini | yes | HIL only: no ESP8266 machine | yes |
{% endif -%}
{% else -%}
{% if stm32_board == 'f405rg' -%}
| STM32, {% if stm32_toolchain == 'rust' %}Rust{% else %}PlatformIO{% endif %} | f405rg (STM32F405RGT6, 1024/128 KB) | yes | QEMU `netduinoplus2` | yes |
{% elif stm32_board == 'f103c8' -%}
| STM32, {% if stm32_toolchain == 'rust' %}Rust{% else %}PlatformIO{% endif %} | f103c8 (STM32F103C8T6, 64/20 KB) | yes | HIL only: no QEMU machine | yes |
{% elif stm32_board == 'f411re' -%}
| STM32, {% if stm32_toolchain == 'rust' %}Rust{% else %}PlatformIO{% endif %} | f411re (STM32F411RET6, 512/128 KB) | yes | HIL only: no QEMU machine | yes |
{% else -%}
| STM32, {% if stm32_toolchain == 'rust' %}Rust{% else %}PlatformIO{% endif %} | l476rg (STM32L476RGT6, 1024/128 KB) | yes | HIL only: no QEMU machine | yes |
{% endif -%}
{% endif -%}

## Board facts

- Boot line: `[BOOT] {{ repo_name }}` on the console
- Console baud: {{ serial_baud }}
{% if platform == 'arduino' -%}
- Upload protocol: the board's USB serial bootloader{% if arduino_board == 'nano' %}; the old bootloader runs at 57600 baud and the new one at 115200{% elif arduino_board == 'leonardo' %}; the bootloader runs at 57600 baud{% endif %}

- Program button: press reset before `make upload`{% if arduino_board == 'leonardo' %}; the reset opens the bootloader for a few seconds{% endif %}

{% elif platform == 'avr' -%}
- Upload protocol: ISP through `{{ avr_programmer_id }}`; the board has no bootloader
- Program button: none; connect the programmer to the ISP header
- Console baud: {{ serial_baud }} over the UART pins
{% elif platform == 'esp' -%}
- Upload protocol: the serial bootloader through `esptool`
- Program button: {% if esp_chip == 'esp32' %}hold BOOT, press EN, release both, then run `make upload`{% else %}no button; the bootloader starts on reset{% endif %}

{% elif stm32_toolchain == 'rust' -%}
- Upload protocol: the STM32 ROM serial bootloader through `stm32flash`
- Program button: move BOOT0 to 1, press reset, run `make upload`, then move BOOT0 back
{% elif stm32_upload == 'stlink' -%}
- Upload protocol: ST-Link through the debug probe
- Program button: none; connect the ST-Link to the SWD header
{% else -%}
- Upload protocol: the STM32 ROM serial bootloader; PlatformIO drives `stm32flash`
- Program button: move BOOT0 to 1, press reset, run `make upload`, then move BOOT0 back
{% endif %}
## Safety

- Ask before flashing a board that holds user data.
{% if eeprom -%}
- Run `make eeprom-backup` before the first upload of a new firmware, so the EEPROM can be restored with `make eeprom-restore`.
{% endif %}
