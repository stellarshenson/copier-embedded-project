{%- set platform_name = {'arduino': 'Arduino', 'avr': 'bare AVR', 'esp': 'ESP', 'stm32': 'STM32'}[platform] -%}
{%- set is_avr_rust = platform == 'avr' and (avr_language | default('c')) == 'rust' -%}
{%- set is_stm32_rust = platform == 'stm32' and (stm32_toolchain | default('rust')) == 'rust' -%}
{%- set is_rust = is_avr_rust or is_stm32_rust -%}
{%- set has_installers = 'env-installers' in components -%}
{%- set has_simulator = 'simulator' in components -%}
{%- set has_eeprom = platform in ['arduino', 'avr'] -%}
{%- set installer = 'firmware-avr' if platform in ['arduino', 'avr'] else 'firmware-' ~ platform -%}
{%- set has_ltspice = 'ltspice' in components -%}
{%- set has_host = (host_side | default('No')) == 'Yes' -%}
{%- set environment_scope = environment_scope | default('global') -%}
{%- set repo = repo_name -%}
{%- set avr_target = avr_target | default('avr-none') -%}
{%- set avr_programmer_id = ('arduinoisp' if avr_programmer == 'arduino-isp' else 'usbasp') if platform == 'avr' else '' -%}
{%- if platform == 'arduino' -%}
{%- set board_label = arduino_board_custom if arduino_board == 'other' else arduino_board -%}
{%- set mcu_label = {'uno': 'ATmega328P', 'nano': 'ATmega328P', 'mega2560': 'ATmega2560', 'leonardo': 'ATmega32U4'}[arduino_board] if arduino_board != 'other' else 'the board MCU' -%}
{%- set memory_label = {'uno': '32 KB flash, 2 KB RAM', 'nano': '32 KB flash, 2 KB RAM', 'mega2560': '256 KB flash, 8 KB RAM', 'leonardo': '32 KB flash, 2.5 KB RAM'}[arduino_board] if arduino_board != 'other' else 'board dependent' -%}
{%- set clock_label = '16 MHz' -%}
{%- set toolchain = 'Arduino (PlatformIO, framework arduino)' -%}
{%- set build_file = '`platformio.ini`' -%}
{%- set adapter = '`src/' ~ repo ~ '.ino` with `setup()` and `loop()`' -%}
{%- set core = '`lib/core/core.c` and `lib/core/core.h`; the host test is `test/host/test_core.c`' -%}
{%- set upload_label = 'PlatformIO over the Arduino bootloader on `PORT`' -%}
{%- set reset_label = 'The board resets when the host opens the serial port; wait about 2 s before the first command.' -%}
{%- if (arduino_sketch_link | default('No')) == 'Yes' -%}
{%- set variation = 'the sketch is `src/' ~ repo ~ '.ino`, and the root `' ~ repo ~ '.ino` links to it' -%}
{%- else -%}
{%- set variation = 'none beyond the sketch name' -%}
{%- endif -%}
{%- if arduino_board in ['uno', 'nano'] -%}
{%- set simulator_cell = 'yes: simavr' -%}
{%- set simulator_limit = 'simavr models the AVR core and the ATmega328P peripherals up to 128 KB of flash. It does not model the board circuit or real electrical timing, so the harness records a pin or a timer bit as a pseudo-pin when the firmware depends on one.' -%}
{%- set simulator_workaround = 'When a case needs the circuit, upload to the board and observe the boot line.' -%}
{%- elif arduino_board == 'mega2560' -%}
{%- set simulator_cell = 'HIL only: 256 KB is above the 128 KB simavr limit' -%}
{%- set simulator_limit = 'No supported emulator. simavr is stable to 128 KB of flash, and the ATmega2560 has 256 KB.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- elif arduino_board == 'leonardo' -%}
{%- set simulator_cell = 'HIL only: simavr does not document the ATmega32U4' -%}
{%- set simulator_limit = 'No supported emulator. simavr documents no ATmega32U4.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- else -%}
{%- set simulator_cell = 'HIL only: no emulator documents this board' -%}
{%- set simulator_limit = 'No supported emulator. A board is simulated only when its MCU is documented and the flash is at most 128 KB.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- endif -%}
{%- elif platform == 'avr' and not is_avr_rust -%}
{%- set board_label = avr_mcu_custom if avr_mcu == 'other' else avr_mcu -%}
{%- set mcu_label = board_label -%}
{%- set memory_label = {'atmega328p': '32 KB flash, 2 KB RAM', 'atmega32u4': '32 KB flash, 2.5 KB RAM', 'attiny85': '8 KB flash, 512 B RAM'}[avr_mcu] if avr_mcu != 'other' else 'board dependent' -%}
{%- set clock_label = (avr_clock | int // 1000000) ~ ' MHz' -%}
{%- set toolchain = 'Bare AVR C' if (avr_language | default('c')) == 'c' else 'Bare AVR C++' -%}
{%- set build_file = '`platformio.ini`' -%}
{%- set adapter = '`src/main.c`' if (avr_language | default('c')) == 'c' else '`src/main.cpp`' -%}
{%- set core = '`lib/core/core.c` and `lib/core/core.h`; the host test is `test/host/test_core.c`' -%}
{%- set upload_label = 'PlatformIO with the `' ~ pio_upload_protocol ~ '` programmer' -%}
{%- set reset_label = 'Connect the programmer to the ICSP header; the firmware starts after the reset.' -%}
{%- set variation = 'none' -%}
{%- if avr_mcu == 'atmega328p' -%}
{%- set simulator_cell = 'yes: simavr' -%}
{%- set simulator_limit = 'simavr models the AVR core and the ATmega328P peripherals up to 128 KB of flash. It does not model the board circuit or real electrical timing, so the harness records a pin or a timer bit as a pseudo-pin when the firmware depends on one.' -%}
{%- set simulator_workaround = 'When a case needs the circuit, upload to the board and observe the boot line.' -%}
{%- elif avr_mcu == 'attiny85' -%}
{%- set simulator_cell = 'yes: simavr; no UART, so the boot-line test skips' -%}
{%- set simulator_limit = 'simavr models the ATtiny85 core and peripherals up to 128 KB of flash, but not the board circuit. The ATtiny85 has no UART, so the boot-line test skips with that reason.' -%}
{%- set simulator_workaround = 'Use a pin-level case in the simulator, or observe the pin on hardware.' -%}
{%- elif avr_mcu == 'atmega32u4' -%}
{%- set simulator_cell = 'HIL only: simavr does not document the ATmega32U4' -%}
{%- set simulator_limit = 'No supported emulator. simavr documents no ATmega32U4.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- else -%}
{%- set simulator_cell = 'HIL only: no emulator documents this MCU' -%}
{%- set simulator_limit = 'No supported emulator. An MCU is simulated only when it is documented and the flash is at most 128 KB.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- endif -%}
{%- elif is_avr_rust -%}
{%- set board_label = avr_mcu_custom if avr_mcu == 'other' else avr_mcu -%}
{%- set mcu_label = board_label -%}
{%- set memory_label = {'atmega328p': '32 KB flash, 2 KB RAM', 'atmega32u4': '32 KB flash, 2.5 KB RAM', 'attiny85': '8 KB flash, 512 B RAM'}[avr_mcu] if avr_mcu != 'other' else 'board dependent' -%}
{%- set clock_label = (avr_clock | int // 1000000) ~ ' MHz' -%}
{%- set toolchain = 'Bare AVR Rust' -%}
{%- set build_file = '`Cargo.toml`, `.cargo/config.toml` and `rust-toolchain.toml`' -%}
{%- set adapter = '`src/bin/' ~ repo ~ '.rs`' -%}
{%- set core = '`src/lib.rs`; the host test is `test/host/core.rs`, a Cargo test target' -%}
{%- set upload_label = '`avrdude -c ' ~ avr_programmer_id ~ '` on `PORT`' -%}
{%- set reset_label = 'Connect the programmer to the ICSP header; the firmware starts after the reset.' -%}
{%- set variation = '`src/bin/` for Cargo' -%}
{%- if avr_mcu == 'atmega328p' -%}
{%- set simulator_cell = 'yes: simavr' -%}
{%- set simulator_limit = 'simavr models the AVR core and the ATmega328P peripherals up to 128 KB of flash. It does not model the board circuit or real electrical timing, so the harness records a pin or a timer bit as a pseudo-pin when the firmware depends on one.' -%}
{%- set simulator_workaround = 'When a case needs the circuit, upload to the board and observe the boot line.' -%}
{%- elif avr_mcu == 'attiny85' -%}
{%- set simulator_cell = 'yes: simavr; no UART, so the boot-line test skips' -%}
{%- set simulator_limit = 'simavr models the ATtiny85 core and peripherals up to 128 KB of flash, but not the board circuit. The ATtiny85 has no UART, so the boot-line test skips with that reason.' -%}
{%- set simulator_workaround = 'Use a pin-level case in the simulator, or observe the pin on hardware.' -%}
{%- elif avr_mcu == 'atmega32u4' -%}
{%- set simulator_cell = 'HIL only: simavr does not document the ATmega32U4' -%}
{%- set simulator_limit = 'No supported emulator. simavr documents no ATmega32U4.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- else -%}
{%- set simulator_cell = 'HIL only: no emulator documents this MCU' -%}
{%- set simulator_limit = 'No supported emulator. An MCU is simulated only when it is documented and the flash is at most 128 KB.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- endif -%}
{%- elif platform == 'esp' -%}
{%- set board_label = esp_board -%}
{%- set mcu_label = 'ESP32' if esp_chip == 'esp32' else 'ESP8266' -%}
{%- set memory_label = '4 MB flash and 520 KB SRAM, board dependent' if esp_chip == 'esp32' else '4 MB flash and 80 KB DRAM, board dependent' -%}
{%- set clock_label = '240 MHz' if esp_chip == 'esp32' else '80 MHz' -%}
{%- set upload_label = 'PlatformIO over USB on `PORT`' -%}
{%- set reset_label = 'If the board does not enter the bootloader, hold BOOT and tap EN.' -%}
{%- if esp_framework == 'espidf' -%}
{%- set toolchain = 'ESP32 ESP-IDF (PlatformIO)' -%}
{%- set build_file = '`platformio.ini` and `sdkconfig.defaults`' -%}
{%- set adapter = '`src/main.c` with `app_main`' -%}
{%- set core = '`lib/core/core.c` and `lib/core/core.h`; the host test is `test/host/test_core.c`' -%}
{%- set variation = '`main -> src` compatibility symlink' -%}
{%- set simulator_cell = 'yes: Espressif QEMU fork, `qemu-system-xtensa -machine esp32`' -%}
{%- set simulator_limit = 'The Espressif QEMU fork models selected ESP32 peripherals. It does not model the radio or the full board circuit.' -%}
{%- set simulator_workaround = '`make sim` prints the written reason and exits 0 when qemu-system-xtensa is absent; use the board for radio and timing cases.' -%}
{%- elif esp_framework == 'esp8266-rtos-sdk' -%}
{%- set toolchain = 'ESP8266 RTOS SDK' -%}
{%- set build_file = '`platformio.ini` and `sdkconfig.defaults`' -%}
{%- set adapter = '`src/main.c` with `user_init`' -%}
{%- set core = '`lib/core/core.c` and `lib/core/core.h`; the host test is `test/host/test_core.c`' -%}
{%- set variation = 'none' -%}
{%- set simulator_cell = 'HIL only: QEMU documents no ESP8266 machine' -%}
{%- set simulator_limit = 'No supported emulator. QEMU documents no ESP8266 machine.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- else -%}
{%- set toolchain = 'ESP32 Arduino' if esp_chip == 'esp32' else 'ESP8266 Arduino' -%}
{%- set build_file = '`platformio.ini`' -%}
{%- set adapter = '`src/main.cpp`' -%}
{%- set core = '`lib/core/core.c` and `lib/core/core.h`; the host test is `test/host/test_core.c`' -%}
{%- set variation = 'none' -%}
{%- if esp_chip == 'esp32' -%}
{%- set simulator_cell = 'yes: Espressif QEMU fork, `qemu-system-xtensa -machine esp32`' -%}
{%- set simulator_limit = 'The Espressif QEMU fork models selected ESP32 peripherals. It does not model the radio or the full board circuit.' -%}
{%- else -%}
{%- set simulator_cell = 'HIL only: QEMU documents no ESP8266 machine' -%}
{%- set simulator_limit = 'No supported emulator. QEMU documents no ESP8266 machine.' -%}
{%- endif -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- endif -%}
{%- elif is_stm32_rust -%}
{%- set board_label = {'f405rg': 'f405rg (STM32F405RGT6)', 'f103c8': 'f103c8 (STM32F103C8T6)', 'f411re': 'f411re (STM32F411RET6)', 'l476rg': 'l476rg (STM32L476RGT6)'}[stm32_board] -%}
{%- set mcu_label = {'f405rg': 'STM32F405RGT6', 'f103c8': 'STM32F103C8T6', 'f411re': 'STM32F411RET6', 'l476rg': 'STM32L476RGT6'}[stm32_board] -%}
{%- set memory_label = flash_kb ~ ' KB flash, ' ~ ram_kb ~ ' KB RAM' -%}
{%- set clock_label = {'f405rg': '168 MHz', 'f103c8': '72 MHz', 'f411re': '100 MHz', 'l476rg': '80 MHz'}[stm32_board] -%}
{%- set toolchain = 'STM32 Rust' -%}
{%- set build_file = '`Cargo.toml`, `build.rs`, `memory.x`, `.cargo/config.toml` and `rust-toolchain.toml`' -%}
{%- set adapter = '`src/bin/' ~ repo ~ '.rs`' -%}
{%- set core = '`src/lib.rs`; the host test is `test/host/core.rs`, a Cargo test target' -%}
{%- set upload_label = '`stm32flash` over the UART on `PORT` with `8e1`' -%}
{%- set reset_label = 'Set BOOT0 high, reset the board, flash, then set BOOT0 low and reset.' -%}
{%- set variation = '`src/bin/` for Cargo' -%}
{%- if stm32_board == 'f405rg' -%}
{%- set simulator_cell = 'yes: QEMU `netduinoplus2` (STM32F405)' -%}
{%- set simulator_limit = 'QEMU models the STM32F405 SoC, not the board circuit or real electrical timing.' -%}
{%- set simulator_workaround = '`make sim` prints the written reason and exits 0 when qemu-system-arm or the machine is absent; use the board for the circuit and timing.' -%}
{%- else -%}
{%- set simulator_cell = 'HIL only: no QEMU machine for this MCU' -%}
{%- set simulator_limit = 'No supported emulator. QEMU has no machine for this MCU.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- endif -%}
{%- else -%}
{%- set board_label = {'f405rg': 'f405rg (STM32F405RGT6)', 'f103c8': 'f103c8 (STM32F103C8T6)', 'f411re': 'f411re (STM32F411RET6)', 'l476rg': 'l476rg (STM32L476RGT6)'}[stm32_board] -%}
{%- set mcu_label = {'f405rg': 'STM32F405RGT6', 'f103c8': 'STM32F103C8T6', 'f411re': 'STM32F411RET6', 'l476rg': 'STM32L476RGT6'}[stm32_board] -%}
{%- set memory_label = flash_kb ~ ' KB flash, ' ~ ram_kb ~ ' KB RAM' -%}
{%- set clock_label = {'f405rg': '168 MHz', 'f103c8': '72 MHz', 'f411re': '100 MHz', 'l476rg': '80 MHz'}[stm32_board] -%}
{%- set upload_label = 'PlatformIO with the `' ~ pio_upload_protocol ~ '` protocol' -%}
{%- set reset_label = 'Set BOOT0 high and reset for the serial bootloader; connect ST-LINK for the default protocol.' -%}
{%- if stm32_framework == 'stm32cube' -%}
{%- set toolchain = 'STM32 PlatformIO STM32Cube' -%}
{%- set build_file = '`platformio.ini` and `src/FreeRTOSConfig.h`' -%}
{%- set adapter = '`src/main.c`' -%}
{%- else -%}
{%- set toolchain = 'STM32 PlatformIO Arduino' -%}
{%- set build_file = '`platformio.ini`' -%}
{%- set adapter = '`src/main.cpp`' -%}
{%- endif -%}
{%- set core = '`lib/core/core.c` and `lib/core/core.h`; the host test is `test/host/test_core.c`' -%}
{%- set variation = 'none' -%}
{%- if stm32_board == 'f405rg' -%}
{%- set simulator_cell = 'yes: QEMU `netduinoplus2` (STM32F405)' -%}
{%- set simulator_limit = 'QEMU models the STM32F405 SoC, not the board circuit or real electrical timing.' -%}
{%- set simulator_workaround = '`make sim` prints the written reason and exits 0 when qemu-system-arm or the machine is absent; use the board for the circuit and timing.' -%}
{%- else -%}
{%- set simulator_cell = 'HIL only: no QEMU machine for this MCU' -%}
{%- set simulator_limit = 'No supported emulator. QEMU has no machine for this MCU.' -%}
{%- set simulator_workaround = '`make sim` skips with that reason; upload to the board and observe the boot line.' -%}
{%- endif -%}
{%- endif -%}
Generated projects share one structure, with the same Makefile, source roots, test tiers and
top-level folders, and only the build file and one adapter vary by toolchain, so moving between
boards keeps the same commands and the same folders. Optional folders are components chosen at
generation. The Makefile is the entry point for the environment, the build, upload, monitor, tests
and the simulator. Each toolchain follows its published layout, pure logic lives in one shared
module, and the README states which test tiers the board can run and which emulator supports it.

# {{ project_name }}

{{ description or 'Firmware for ' + platform_name + '.' }}

## Development flow

{% if has_installers -%}
1. `make create_environment` - run `resources/envs/{{ installer }}.py` and create the
   conda environment `{{ env_name }}`.
{% else -%}
1. Run `~/.local/lab-utils/envs/{{ installer }}.py` - create the conda environment
   `{{ env_name }}`. This project carries no installer copy.
{% endif -%}
2. `make build` - build the firmware.
3. `make upload PORT=/dev/ttyUSB0` - write the firmware to the board.
4. `make monitor PORT=/dev/ttyUSB0` - print the console at {{ serial_baud }} baud.
5. `make test` - run the host tests{% if has_host %} and the host application tests{% endif %}{% if has_simulator %} and the simulator tests{% endif %}.

Copy `.env.example` to `.env` and set `PORT` and `BAUD` of this machine; the Makefile reads `.env`,
and a value on the command line wins.

`make help` lists the rendered targets; every target that calls a toolchain program runs inside
`{{ env_name }}` with `conda run`, and no documented step calls `pio`, `cargo`, `avrdude` or
`stm32flash` directly.

The Makefile's `ENV_SCOPE` variable chooses where the environment lives: `{{ environment_scope }}`
by default, `global` in the conda root, `local` under `.conda/envs/` in this project. Local scope
exports `CONDA_ENVS_PATH=$(PROJECT_DIR)/.conda/envs`. Pass the same `ENV_SCOPE` to every make
command.

## Targets

| Target | Effect |
|---|---|
{% if has_installers -%}
| `make create_environment` | run `resources/envs/{{ installer }}.py`; `ENV_SCOPE` chooses `global` or `local` |
| `make env` | alias for `make create_environment` |
{% endif -%}
| `make build` | build the firmware |
| `make upload` | write the firmware to the board on `PORT` |
| `make monitor` | open the console on `PORT` at `BAUD` |
| `make test` | run the host tests{% if has_host %} and the host application tests{% endif %}{% if has_simulator %} and the simulator tests{% endif %}{% if has_ltspice %} and the circuit test{% endif %} |
{% if has_simulator -%}
| `make sim` | run the firmware in the simulator |
{% endif -%}
{% if has_host -%}
| `make host-run` | read the boot line from the board on `PORT` with the host application and print one JSON line |
| `make host-app-test` | run the host application tests in `host/tests/` |
{% endif -%}
{% if has_ltspice -%}
| `make ltspice` | simulate the surrounding circuit with LTspice or ngspice |
{% endif -%}
{% if has_eeprom -%}
| `make eeprom-backup` | read the EEPROM into `resources/eeprom/<board>-<timestamp>.bin` and print one JSON line |
| `make eeprom-restore` | write the newest image with `avrdude -D` and verify the read-back |
{% endif -%}
| `make clean` | remove build output and caches; keep `.conda/` and `resources/eeprom/` |
| `make help` | print this list |

## Releasing

A release increments `VERSION`, moves the `Unreleased` entries in `CHANGELOG.md` under the new
version heading, commits both files, tags the commit and pushes it. `RELEASING.md` carries the
full process and its rules.

1. `make increment_version`
2. Move the `Unreleased` entries in `CHANGELOG.md` under the new version heading with the date
3. Commit `VERSION` and `CHANGELOG.md`
4. Tag `v<version>`
5. Push the commit and the tag
{% if 'ci' in components %}
## Continuous integration

Every push and pull request builds and tests the firmware in `.github/workflows/build.yml`. The
firmware files are uploaded as the `firmware` artifact. A `v*` tag publishes a GitHub Release. The
conda environment is cached under `.conda/envs`, keyed on the installer files. CI requires the
`env-installers` component; a project without it stops the workflow with that reason.
{% endif %}
## Folder structure

```text
{{ repo }}/
├── AGENTS.md                      # instructions for coding agents
├── CLAUDE.md                      # one line: @AGENTS.md
├── CHANGELOG.md                   # Keep a Changelog form, Unreleased section
├── RELEASING.md                   # release process
├── VERSION                        # project version read by every toolchain
{% if open_source_license != 'No license file' -%}
├── LICENSE
{% endif -%}
├── Makefile                       # the development entry point
├── .copier-answers.yml            # the answers that generated this project
├── .env.example                   # serial settings to copy to .env
├── .gitignore
{% if has_simulator -%}
├── pytest.ini                     # simulator test configuration
{% endif -%}
{% if platform == 'esp' and esp_framework == 'espidf' -%}
├── src/
│   └── main.c                     # adapter: app_main
├── main -> src                    # compatibility symlink; the ESP-IDF component name
├── sdkconfig.defaults
{% elif platform == 'esp' and esp_framework == 'esp8266-rtos-sdk' -%}
├── src/
│   └── main.c                     # adapter: user_init
├── sdkconfig.defaults
{% elif is_rust -%}
├── src/
│   ├── lib.rs                     # the shared core
│   └── bin/
│       └── {{ repo }}.rs{{ ' ' * (23 - ((repo ~ '.rs') | length)) }}# adapter
├── Cargo.toml
├── .cargo/
│   └── config.toml                # target, linker and rustflags
├── rust-toolchain.toml            # the compiler the installer pins
{% if platform == 'stm32' -%}
├── build.rs                       # places memory.x for the linker
├── memory.x                       # flash and RAM of the board
{% endif -%}
{% elif platform == 'arduino' -%}
├── src/
│   └── {{ repo }}.ino             # adapter: setup() and loop()
{% if arduino_sketch_link == 'Yes' -%}
├── {{ repo }}.ino -> src/{{ repo }}.ino   # sketch-folder symlink
{% endif -%}
├── platformio.ini
{% else -%}
├── src/
│   └── {{ 'main.cpp' if platform == 'esp' else 'main.c' }}  # adapter
├── platformio.ini
{% endif -%}
├── lib/
{% if is_rust -%}
│   └── README.md                  # library register; the shared core is src/lib.rs
{% else -%}
│   ├── README.md                  # library register
{% if platform == 'arduino' and arduino_libraries == 'Yes' -%}
│   ├── core/
│   │   ├── core.c                 # the shared core
│   │   └── core.h
│   └── vendor/                    # project-local Arduino libraries
{% else -%}
│   └── core/
│       ├── core.c                 # the shared core
│       └── core.h
{% endif -%}
{% endif -%}
├── test/
│   ├── host/                      # host tests of the shared core
{% if has_simulator -%}
│   ├── harness/                   # simulator wrapper and board helpers
│   └── functional/                # simulator tests
{% endif -%}
├── scripts/                       # PC-side helper scripts; README states the contract
{% if has_eeprom -%}
│   ├── README.md
│   └── eeprom_tool.py             # EEPROM backup and restore
{% elif platform == 'stm32' and stm32_toolchain == 'platformio' and stm32_framework == 'stm32cube' -%}
│   ├── README.md
│   └── freertos.py                # PlatformIO build hook, run through extra_scripts
{% else -%}
│   └── README.md
{% endif -%}
{% if has_host -%}
├── host/                          # PC-side Python package; never built for the board
│   ├── pyproject.toml             # distribution {{ repo }}-host, dependency pyserial
│   ├── src/
│   │   └── {{ host_module }}/
│   │       ├── __init__.py
│   │       ├── __main__.py        # python -m {{ host_module }}: boot line as one JSON line
│   │       ├── serial_client.py   # read_boot_line, open_port
│   │       └── protocol.py        # crc8, the same algorithm as the core
│   └── tests/                     # make host-app-test
{% endif -%}
{% if 'resources' in components or has_installers or has_eeprom -%}
├── resources/
{%- set resource_children = [] -%}
{%- if 'resources' in components -%}
{%- set _ = resource_children.extend([('README.md', 'folder guide'), ('graphics/', 'diagrams and images'), ('external/', 'vendor files and logs')]) -%}
{%- endif -%}
{%- if has_installers -%}
{%- set _ = resource_children.append(('envs/', 'conda installers for ' ~ env_name)) -%}
{%- endif -%}
{%- if has_eeprom -%}
{%- set _ = resource_children.append(('eeprom/', 'images from make eeprom-backup')) -%}
{%- endif -%}
{%- for entry, note in resource_children %}
│   {{ '└──' if loop.last else '├──' }} {{ entry }}{{ ' ' * (27 - (entry | length)) }}# {{ note }}
{%- endfor %}
{% endif -%}
{% if 'references' in components -%}
├── references/
│   ├── README.md
│   ├── datasheets/
│   ├── notes/
│   └── schematics/                # PCB schematic, board files, pin map
{% endif -%}
{% if 'data' in components -%}
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
{% endif -%}
{% if has_ltspice -%}
├── simulations/
│   ├── README.md
│   ├── circuit.cir                # ATtiny84 pin driving a gain-2 op-amp
│   ├── run.py                     # LTspice or ngspice runner
│   └── test_circuit.py            # functional test
{% endif -%}
{% if 'docs' in components -%}
├── docs/
│   ├── README.md
│   ├── design.md
│   ├── acc-crit-{{ repo }}.md
│   └── defects-{{ repo }}.md
{% endif -%}
{% if 'notebooks' in components -%}
├── notebooks/
│   ├── README.md
│   └── cache/                     # executed notebook cache, gitignored
{% endif -%}
{% if 'agents' in components -%}
├── .agents/
│   ├── skills/{{ repo }}-device/SKILL.md
│   ├── skills/{{ repo }}-toolchain/SKILL.md
│   ├── workflows/build-and-flash.md
│   └── workflows/release.md
├── .claude/
│   ├── skills/
│   │   ├── {{ repo }}-device -> ../../.agents/skills/{{ repo }}-device
│   │   └── {{ repo }}-toolchain -> ../../.agents/skills/{{ repo }}-toolchain
│   └── commands -> ../.agents/workflows
{% endif -%}
{% if 'ci' in components -%}
└── .github/
    └── workflows/build.yml       # CI: build, test and tag release
{% endif -%}
```

Selected components: `{{ components | join('`, `') }}`. A folder owned by a component is present
only when that component was selected. `AGENTS.md`, `CLAUDE.md`, `CHANGELOG.md`, `Makefile`,
`src/`, `lib/`, `test/host/` and `scripts/` are always present. `src/` is the master source root on
every platform; on ESP-IDF, `main` is a relative symlink to `src` that supplies the component
name, and the build reads the same files once.

## Where things go

| Content | Folder |
|---|---|
{% if 'references' in components -%}
| PCB schematic, board files, Gerbers, connector pin map | `references/schematics/` |
| Vendor datasheets and manuals | `references/datasheets/` |
| Register maps, timing tables, errata extracts | `references/notes/` |
{% endif -%}
{% if 'resources' in components -%}
| Diagrams, screenshots and images for documents | `resources/graphics/` |
| Vendor files, captured logs, third-party binaries | `resources/external/` |
{% endif -%}
{% if has_eeprom -%}
| EEPROM backup images | `resources/eeprom/` |
{% endif -%}
| Project-local Arduino libraries | `lib/vendor/` when `arduino_libraries` is `Yes` |
| Other project libraries | `lib/<name>/`, with one row per library in `lib/README.md` |
{% if is_rust -%}
| Shared pure logic | `src/lib.rs` |
{% else -%}
| Shared pure logic | `lib/core/core.c` and `lib/core/core.h` |
{% endif -%}
| Firmware adapter for the board | `src/` |
| Host, simulator and functional tests | `test/host/`, `test/harness/`, `test/functional/` |
| PC-side helper scripts: no interactive input, one JSON line, a non-zero exit with a reason | `scripts/` |
{% if has_host -%}
| PC-side code that talks to the board, and its tests | `host/src/{{ host_module }}/`, `host/tests/` |
{% endif -%}
{% if has_ltspice -%}
| Circuit netlist and its runner | `simulations/` |
{% endif -%}
{% if 'data' in components -%}
| Raw and processed data | `data/raw/`, `data/processed/` |
{% endif -%}
{% if 'notebooks' in components -%}
| Exploration notebooks | `notebooks/` |
{% endif -%}
{% if 'docs' in components -%}
| Design notes, acceptance criteria, defects | `docs/` |
{% endif -%}

Never put build input outside `src/` and `lib/`: the toolchain compiles those folders only.

## Toolchain

This project uses {{ toolchain }}:

- Build file: {{ build_file }}
- Adapter: {{ adapter }}
- Shared core: {{ core }}
- Required variation: {{ variation }}

The documented variations across toolchains are:

| Toolchain | Build file | Adapter | Required variation |
|---|---|---|---|
| Arduino (PlatformIO, framework arduino) | `platformio.ini` | `src/<repo>.ino` with `setup()` and `loop()` | the sketch name; optional root `<repo>.ino` symlink |
| Bare AVR C | `platformio.ini` | `src/main.c` | none |
| Bare AVR C++ | `platformio.ini` | `src/main.cpp` | none |
| Bare AVR Rust | `Cargo.toml`, `.cargo/config.toml`, `rust-toolchain.toml` | `src/bin/<repo>.rs` | `src/bin/` for Cargo |
| ESP32 ESP-IDF (PlatformIO) | `platformio.ini`, `sdkconfig.defaults` | `src/main.c` with `app_main` | `main -> src` compatibility symlink |
| ESP32 Arduino | `platformio.ini` | `src/main.cpp` | none |
| ESP8266 Arduino | `platformio.ini` | `src/main.cpp` | none |
| ESP8266 RTOS SDK | `platformio.ini`, `sdkconfig.defaults` | `src/main.c` with `user_init` | none |
| STM32 Rust | `Cargo.toml`, `build.rs`, `memory.x`, `.cargo/config.toml`, `rust-toolchain.toml` | `src/bin/<repo>.rs` | `src/bin/` for Cargo |
| STM32 PlatformIO STM32Cube | `platformio.ini`, `src/FreeRTOSConfig.h` | `src/main.c` | none |
| STM32 PlatformIO Arduino | `platformio.ini` | `src/main.cpp` | none |

Moving between boards keeps this table's first column structure: the build file and the adapter
change, and the targets, the test tiers and the folders stay the same.

## Test capability

| Tier | Command | This board |
|---|---|---|
| Host | `make test` | yes: `test/host/` compiles the shared core with the host compiler |
| Simulator | `make sim` | {% if has_simulator %}{{ simulator_cell }}{% else %}not generated: the simulator component was not selected{% endif %} |
| HIL | `make upload`, then `make monitor` | yes: the board prints `[BOOT] {{ repo }}` |

{% if has_simulator -%}
## Simulator limits

{{ simulator_limit }}

{{ simulator_workaround }}
{% endif -%}

{% if has_ltspice -%}
## Circuit simulation

`simulations/circuit.cir` models the ATtiny84 pin as a 0-5 V pulse at 1 kHz driving a non-inverting
op-amp with gain 2. The firmware is not co-simulated: the pin is the voltage source the firmware
produces, and the analog circuit is simulated around it. `simulations/` holds circuit simulations
(LTspice or ngspice), while the simulator component runs the firmware under simavr or QEMU in
`test/harness/`.

- `make ltspice` runs the netlist with LTspice when it is on PATH, otherwise ngspice
- `make ltspice` fails when the measured output does not follow the pin
- Without either simulator the test skips with that reason
{% endif -%}

{% if has_host %}
## Host side

`host/` holds the Python package `{{ host_module }}`. It runs on the PC and talks to the board
over the serial port. The firmware build never compiles `host/`.

- `make host-run PORT=<port>` reads the console until `[BOOT] {{ repo }}` and prints one JSON
  line with `port`, `boot` and `line`; it exits 1 with the reason when the boot line does not
  arrive
- `make host-app-test` runs `host/tests/` without a board; `make test` runs it as well
- `protocol.crc8` uses the polynomial, the initial value and the bit order of
  {{ '`crc8` in `src/lib.rs`' if is_rust else '`core_crc8` in `lib/core/core.c`' }}, so the PC and the firmware compute the same checksum
- The make targets set `PYTHONPATH=host/src` and need no install

Install the package into the environment to import `{{ host_module }}` from a notebook:

```bash
{{ 'CONDA_ENVS_PATH=.conda/envs ' if environment_scope == 'local' else '' }}conda run -n {{ env_name }} pip install -e host
```

{% endif -%}

## Hardware facts

| Fact | Value |
|---|---|
| Platform | {{ platform_name }} |
| Board | {{ board_label }} |
| MCU | {{ mcu_label }} |
| Clock | {{ clock_label }} |
| Memory | {{ memory_label }} |
| Serial console | {{ serial_baud }} baud, 8N1, on `PORT` |
| Upload | {{ upload_label }} |
| Boot line | `[BOOT] {{ repo }}` |
| Reset | {{ reset_label }} |

## Safety

- `make upload` writes flash. It does not erase the EEPROM; there is no erase target.
- Ask before flashing a board that holds data you did not create.
{% if has_eeprom -%}
- Back up the EEPROM with `make eeprom-backup` before flashing firmware that changes its layout.
  `make eeprom-restore` writes with `avrdude -D` and verifies the read-back before it reports
  success.
{% endif -%}
