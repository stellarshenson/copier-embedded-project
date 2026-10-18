{%- set installer_name = 'firmware-avr' if platform in ['arduino', 'avr'] else 'firmware-' ~ platform -%}
# {{ installer_name }} toolchain

The stages of the project's installer and the programs each one leaves in the environment. Versions
are pins at the top of `resources/envs/{{ installer_name }}.py`; read them there, not here.

{% if platform in ['arduino', 'avr'] -%}
| Stage | Source | Leaves |
|---|---|---|
| C compiler, pyserial | conda-forge | the host compiler, `python`, `pyserial` |
| Rust with rust-src | static.rust-lang.org | `cargo`, `rustc`, the Rust source for the AVR core |
| avr-gcc | downloads.arduino.cc | `avr-gcc`, `avr-objcopy`, `avr-size` |
| avrdude | downloads.arduino.cc | `avrdude` |
| PlatformIO with atmelavr | registry.platformio.org | `pio`, the AVR toolchain, the Arduino AVR core, `tool-simavr`, `pytest` |
| ngspice | conda-forge | `ngspice` for `ltspice/circuit.cir` |

Checks: `cargo --version`, `avr-gcc --version`, `avrdude -v`, `pio --version`, `pytest --version`,
`ngspice --version`.
{% elif platform == 'esp' -%}
| Stage | Source | Leaves |
|---|---|---|
| C compiler, pyserial, esptool | conda-forge | the host compiler, `python`, `pyserial`, `esptool` |
| Rust | static.rust-lang.org | `cargo`, `rustc` for the RISC-V chips |
| Espressif Rust for Xtensa | github.com | the `esp` toolchain, `cargo +esp`, `xtensa-esp32-elf-gcc` |
| espflash | github.com | `espflash` |
| PlatformIO with espressif8266 | registry.platformio.org | `pio`, the ESP8266 toolchain and Arduino core |
| ESP8266 RTOS SDK | registry.platformio.org | FreeRTOS for the ESP8266 on the same platform |
| ESP-IDF | registry.platformio.org | the ESP32 toolchain, ESP-IDF and FreeRTOS |
| Espressif QEMU | github.com | `qemu-system-xtensa` with the `esp32` machine |
| ngspice | conda-forge | `ngspice` for `ltspice/circuit.cir` |

Checks: `cargo --version`, `cargo +esp --version`, `xtensa-esp32-elf-gcc --version`,
`espflash --version`, `esptool version`, `pio --version`, `qemu-system-xtensa --version`,
`ngspice --version`.
{% else -%}
| Stage | Source | Leaves |
|---|---|---|
| C compiler, make, pyserial | conda-forge | the host compiler, `make`, `python`, `pyserial` |
| Rust with Cortex-M targets | static.rust-lang.org | `cargo`, `rustc`, `rust-analyzer`, the six Cortex-M standard libraries |
| cargo-binutils | crates.io | `cargo objcopy`, `cargo size`, the other LLVM front ends |
| PlatformIO with ststm32 | registry.platformio.org | `pio`, the STM32 toolchain, STM32Cube and the Arduino core |
| stm32flash | sourceforge.net | `stm32flash` |
| QEMU | download.qemu.org | `qemu-system-arm` with the `netduinoplus2` machine, built from source |
| ngspice | conda-forge | `ngspice` for `ltspice/circuit.cir` |

Checks: `cargo --version`, `rustc --version`, `rust-analyzer --version`, `cargo objcopy --version`,
`pio --version`, `stm32flash` (it has no version option), `qemu-system-arm --version`,
`ngspice --version`.
{% endif -%}
