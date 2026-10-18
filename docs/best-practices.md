# copier-embedded-project - Best practices v1

Status: DRAFT for internal review, 2026-10-18.

## Contents

- [1. Overview](#1.-Overview)
- [2. PlatformIO layout and tests](#2.-PlatformIO-layout-and-tests)
- [3. Arduino layout](#3.-Arduino-layout)
- [4. ESP-IDF and ESP8266 RTOS SDK](#4.-ESP-IDF-and-ESP8266-RTOS-SDK)
- [5. STM32Cube and upload](#5.-STM32Cube-and-upload)
- [6. Rust embedded](#6.-Rust-embedded)
- [7. Testing tiers and simulator limits](#7.-Testing-tiers-and-simulator-limits)
- [8. Agent instructions](#8.-Agent-instructions)
- [9. Conflicts between toolchains](#9.-Conflicts-between-toolchains)
- [10. Adopted rules](#10.-Adopted-rules)
- [11. Test capability matrix](#11.-Test-capability-matrix)

## 1. Overview

This document records the authoritative source behind each rule the template follows. Every rule line ends with its source.

## 2. PlatformIO layout and tests

- The default layout is `src/`, `include/`, `lib/` and `test/`, with `lib/` for project libraries and `test/` for test applications ([directory options](https://docs.platformio.org/en/stable/projectconf/sections/platformio/options/directory/index.html))
- Only folders named `test_*` become independent suites, and each suite needs its own `main()`, `setup()/loop()` or `app_main()` ([test hierarchy](https://docs.platformio.org/en/stable/advanced/unit-testing/structure/hierarchy.html))
- Files directly in `test/` are compiled into every suite, so shared helpers belong there ([test hierarchy](https://docs.platformio.org/en/stable/advanced/unit-testing/structure/hierarchy.html))
- Tests do not link the application `src/`; `test_build_src` defaults to `no`, and reusable logic belongs in `lib/` ([best practices](https://docs.platformio.org/en/stable/advanced/unit-testing/structure/best-practices.html), [test_build_src](https://docs.platformio.org/en/stable/projectconf/sections/env/options/test/test_build_src.html))
- Host tests use `platform = native`; embedded tests build, upload and run on the board ([runner](https://docs.platformio.org/en/latest/advanced/unit-testing/runner.html))
- There is no separate integration category; a second `test_*` suite or an external harness covers integration and HIL ([unit testing](https://docs.platformio.org/en/stable/advanced/unit-testing/index.html))

## 3. Arduino layout

- A sketch folder holds a `.ino` whose name matches the folder ([sketch specification](https://arduino.github.io/arduino-cli/1.5/sketch-specification/))
- `src/` is compiled recursively and holds bundled library-style code; `.ino` files are not supported there ([sketch specification](https://github.com/arduino/arduino-cli/blob/main/docs/sketch-specification.md))
- A reusable library needs `library.properties`, sources under `src/` and examples under lowercase `examples/` ([library specification](https://docs.arduino.cc/arduino-cli/library-specification/))
- A plain firmware sketch carries no `library.properties` ([library specification](https://docs.arduino.cc/arduino-cli/library-specification/))

## 4. ESP-IDF and ESP8266 RTOS SDK

- An ESP-IDF project has a root `CMakeLists.txt` that includes the IDF project file and names the project ([build system](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/build-system.html))
- `main/` is the application component and requires the other components; each extra component carries `idf_component_register` ([build system](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/build-system.html))
- `app_main(void)` is the entry point; the scheduler runs already, so the application never calls `vTaskStartScheduler()` ([FreeRTOS](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/freertos.html), [startup](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/startup.html))
- `sdkconfig.defaults` is committed; `sdkconfig` is machine-local ([build system](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/build-system.html))
- The ESP8266 RTOS SDK is IDF-style but Make-based, and its releases carry 18 months of support, LTS 30 months ([build system](https://docs.espressif.com/projects/esp8266-rtos-sdk/en/latest/api-guides/build-system.html), [support policy](https://github.com/espressif/ESP8266_RTOS_SDK/blob/master/SUPPORT_POLICY_EN.md))

## 5. STM32Cube and upload

- STM32CubeMX generates `Core/Inc`, `Core/Src`, `Drivers/` and `Middlewares/`; user code sits inside `USER CODE BEGIN/END` guards ([UM1718](https://www.st.com/resource/en/user_manual/dm00104712-stm32cubeide-stmicroelectronics.pdf))
- FreeRTOS enters through the CMSIS-RTOS wrapper, and `FreeRTOSConfig.h` is generated, so the configuration belongs in CubeMX ([UM1722](https://www.st.com/resource/en/user_manual/dm00105262-developing-applications-on-stm32cube-with-rtos-stmicroelectronics.pdf))
- PlatformIO `ststm32` supports Arduino, STM32Cube, CMSIS and others; `upload_protocol = stlink` is the default ([ststm32](https://docs.platformio.org/en/stable/platforms/ststm32.html), [ST-LINK](https://docs.platformio.org/en/stable/plus/debug-tools/stlink.html))
- `upload_protocol = serial` uses the ROM bootloader through stm32flash and needs BOOT0 and a UART ([board page](https://docs.platformio.org/en/latest/boards/ststm32/genericSTM32F103C8.html))

## 6. Rust embedded

- The current scaffold is `knurling-rs/app-template`; `cortex-m-quickstart` is deprecated ([app-template](https://github.com/knurling-rs/app-template), [deprecation](https://github.com/rust-embedded/cortex-m-quickstart))
- The layout is `src/lib.rs` for reusable logic, `src/bin/*.rs` for binaries, `tests/` for integration tests, plus `memory.x` and `.cargo/config.toml` ([app-template](https://github.com/knurling-rs/app-template))
- `memory.x` supplies the FLASH and RAM regions that `link.x` consumes ([cortex-m-rt](https://docs.rust-embedded.org/cortex-m-quickstart/cortex_m_rt/))
- The target is `thumbv6m-none-eabi` for M0, `thumbv7m-none-eabi` for M3, `thumbv7em-none-eabi` for M4/M7 and `thumbv7em-none-eabihf` for M4F/M7F ([quickstart](https://docs.rust-embedded.org/cortex-m-quickstart/cortex_m_quickstart/index.html))
- On-target tests use `embedded-test` with `harness = false` and `-Tembedded-test.x` ([embedded-test](https://github.com/probe-rs/embedded-test))
- Host tests cover the logic; HIL covers hardware-dependent cases ([Rust on ESP testing](https://docs.espressif.com/projects/rust/book/application-development/testing.html))

## 7. Testing tiers and simulator limits

- The host tier asserts pure logic, parsers, codecs and state machines, with no flash wear ([runner](https://docs.platformio.org/en/latest/advanced/unit-testing/runner.html))
- The simulator tier asserts boot, scheduler startup, console output, panic paths and modelled peripherals; it does not assert real electrical timing ([simavr](https://github.com/buserror/simavr))
- simavr loads an ELF and models EEPROM, timers, UART, SPI, I2C and ADC; it is stable to 128 KB of flash, its Arduino support is basic, and board hardware must be modelled by the test ([simavr](https://github.com/buserror/simavr))
- QEMU needs an explicit machine, its images are board-specific and it covers a small fraction of Arm boards ([QEMU Arm](https://www.qemu.org/docs/master/system/target-arm.html))
- ESP32 emulation exists in Espressif's QEMU fork only, with selected peripherals, through `idf.py qemu` ([ESP-IDF QEMU](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/qemu.html))
- The HIL tier asserts real peripherals, timing, power and radio, as Zephyr's twister does with `--device-testing` ([twister](https://docs.zephyrproject.org/latest/develop/twister/index.html))

## 8. Agent instructions

- `AGENTS.md` sits at the repository root; nested files apply by proximity and the closest file wins ([agents.md](https://agents.md/))
- Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists; with both present it reads `CLAUDE.md` only, and a CLAUDE.md that merely points at AGENTS.md is not enough ([Claude memory](https://code.claude.com/docs/en/memory))
- Claude Code reads `CLAUDE.md`; the `@AGENTS.md` import line carries the shared instructions ([Claude memory](https://code.claude.com/docs/en/memory))
- Project skills live in `.claude/skills/<name>/SKILL.md`, and symlinked folders are allowed ([Claude skills](https://code.claude.com/docs/en/skills))
- `.agents/skills/<name>/SKILL.md` is Antigravity's convention; no vendor-neutral specification makes `.agents/` the master ([Antigravity](https://antigravity.google/docs/migration/workflows-to-skills))

## 9. Conflicts between toolchains

- The runtime roots differ: PlatformIO `src/`, Arduino sketch root plus `src/`, ESP-IDF `main/` and `components/`, STM32Cube `Core/Src`, and Cargo `src/bin`
- The test roots differ: PlatformIO `test/test_*`, ESP-IDF component tests and Cargo `tests/` are incompatible
- Shared logic therefore lives in a toolchain-neutral module that each target compiles and the host tests cover
- Mainline QEMU documents no ESP32 or ESP8266 machine; ESP32 needs Espressif's fork, and ESP8266 has no machine
- simavr documents no ATmega32U4 even though a core file exists, so the Leonardo and ESP8266 simulator claims need a capability test
- `.agents/` as the master is a project choice, not a vendor standard

## 10. Adopted rules

- Shared logic in a toolchain-neutral module; per-target adapters keep each toolchain's roots (`ACC-TMPL-44`)
- `src/` stays the adapter master for ESP-IDF; `main -> src` is a relative compatibility symlink that supplies the component name, and PlatformIO sets `src_dir = main` to build through it
- A capability matrix states which targets run host, simulator and HIL tests (`ACC-TMPL-45`)
- The simulator tier names the boards the emulator supports and skips the rest with a reason (`ACC-TMPL-32`, `ACC-TMPL-33`)
- The Rust scaffold follows `app-template`: `src/lib.rs`, `src/bin/*.rs`, `tests/`, `memory.x` (`ACC-TMPL-27`)
- The root `CLAUDE.md` imports `AGENTS.md` with `@AGENTS.md` (`ACC-TMPL-14`)
- PlatformIO projects keep `lib/` for project libraries; host tests stay a separate tier driven by `make test` (`ACC-TMPL-11`, `ACC-TMPL-33`)
- Generated projects publish firmware artifacts on `v` tags; the template repository runs its fast suite, lint and the AVR toolchain build; the full functional tier stays local because it needs every lab environment (`ACC-TMPL-52`, `ACC-TMPL-53`, `ACC-TMPL-55`)

## 11. Test capability matrix

Rows are platform and board; `Host` is the `make test` host tier, `Simulator` names the emulator and machine, and `HIL` is upload and observation of the boot line on a board on the bench (`ACC-TMPL-45`). The generated README carries the row for its own platform and board, and this table carries every row.

| Platform | Board / MCU | Host | Simulator | HIL |
|---|---|---|---|---|
| Arduino | uno (ATmega328P, 32 KB) | yes | simavr | yes |
| Arduino | nano, old or new bootloader (ATmega328P) | yes | simavr | yes |
| Arduino | mega2560 (ATmega2560, 256 KB) | yes | HIL only: 256 KB is above simavr's documented 128 KB limit | yes |
| Arduino | leonardo (ATmega32U4) | yes | HIL only: simavr does not document the ATmega32U4 | yes |
| Bare AVR | atmega328p at 16 MHz or 8 MHz | yes | simavr | yes |
| Bare AVR | atmega32u4 | yes | HIL only: not documented by simavr | yes |
| Bare AVR | attiny85 | yes | simavr; no UART, so the boot-line test skips | yes |
| ESP32, ESP-IDF | esp32dev, esp32doit-devkit-v1 | yes | Espressif QEMU fork, `qemu-system-xtensa -machine esp32` | yes |
| ESP32, Arduino | esp32dev, esp32doit-devkit-v1 | yes | Espressif QEMU fork, `qemu-system-xtensa -machine esp32` | yes |
| ESP8266, Arduino | nodemcuv2, d1_mini | yes | HIL only: no ESP8266 machine | yes |
| ESP8266, RTOS SDK | nodemcuv2, d1_mini | yes | HIL only: no ESP8266 machine | yes |
| STM32, Rust or PlatformIO | f405rg (STM32F405RGT6, 1024/128 KB) | yes | `qemu-system-arm -machine netduinoplus2` | yes |
| STM32, Rust or PlatformIO | f103c8 (STM32F103C8T6, 64/20 KB) | yes | HIL only: no QEMU machine | yes |
| STM32, Rust or PlatformIO | f411re (STM32F411RET6, 512/128 KB) | yes | HIL only: no QEMU machine | yes |
| STM32, Rust or PlatformIO | l476rg (STM32L476RGT6, 1024/128 KB) | yes | HIL only: no QEMU machine | yes |
