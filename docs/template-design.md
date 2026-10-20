# Template design

Status: agreed, 2026-10-18. This document holds the decisions for the template rework. The
acceptance criteria in `docs/acc-crit-copier-embedded-project.md` are the specification; criteria
ids are cited where a decision serves one. `docs/philosophy.md` holds the principles.

## Contents

1. [Components](#1-components)
2. [Questions](#2-questions)
3. [Layout](#3-layout)
4. [Makefile](#4-makefile)
5. [Capability matrix](#5-capability-matrix)
6. [Agent files](#6-agent-files)
7. [post_gen and update behaviour](#7-post_gen-and-update-behaviour)
8. [Criteria conflicts resolved](#8-criteria-conflicts-resolved)

## 1. Components

Ten components. `components` is a multiselect; the default selection is
`notebooks, resources, references, simulator, agents, env-installers`.

| Component | Default | Renders | Removed on a fresh copy when unselected |
|---|---|---|---|
| `notebooks` | on | `notebooks/README.md`, one starter notebook, `notebooks/cache/` in `.gitignore` | `notebooks/` |
| `resources` | on | `resources/README.md`, `resources/graphics/`, `resources/external/` | those three paths, never `resources/envs/` |
| `references` | on | `references/README.md`, `references/datasheets/`, `references/notes/` | `references/` |
| `data` | off | `data/README.md`, `data/raw/`, `data/processed/`; raw contents in `.gitignore` | `data/` |
| `simulator` | on | `test/harness/`, `test/functional/`, `pytest.ini`, the `sim` target | those paths and the target |
| `docs` | off | `docs/README.md`, `docs/design.md`, `docs/acc-crit-<repo>.md`, `docs/defects-<repo>.md` | `docs/` |
| `ci` | off | `.github/workflows/build.yml`: build and test, cached environment, firmware artifact, `v*` tag release; a guard when `env-installers` is absent | `.github/` |
| `agents` | on | `.agents/skills/<repo>-device/SKILL.md`, `.agents/workflows/build-and-flash.md`, the `.claude` links | `.agents/`, `.claude/skills/`, `.claude/commands` |
| `env-installers` | on | `resources/envs/firmware_env.py`, the platform installer, the `create_environment` target | `resources/envs/`; the target is not rendered |
| `ltspice` | off | `simulations/README.md`, `simulations/circuit.cir` (ATtiny84 pin driving a gain-2 op-amp), `simulations/run.py` and `simulations/test_circuit.py`; the `ltspice` target, and `test` depends on it | `simulations/` and the target |

Always rendered, independent of `components`: `AGENTS.md`, `CLAUDE.md`, `Makefile`, `CHANGELOG.md`,
`.gitignore`, `.env.example`, `.copier-answers.yml`, `LICENSE` (unless the license answer is `No license file`),
`src/`, `lib/`, `test/host/`, `scripts/`, and the toolchain build file.

`AGENTS.md` and `CLAUDE.md` are not owned by `agents`: `ACC-TMPL-14` requires both at the repository
root in every project. The `agents` component owns the master tree and the links only.

`host/` is not a component. The `host_side` question adds it; section 3.5 holds its layout.

### 1.1 The ci component

`ci` renders `.github/workflows/build.yml` (`ACC-TMPL-52` to `ACC-TMPL-54`). The workflow is
Linux-only, because the installers are x86-64 Linux.

- Build job, on every push and pull request: checkout, uv, miniconda, then `make env` with
  `ENV_SCOPE: local`; the local scope puts the environment under `.conda/envs/` so the job can cache
  it
- Cache: `actions/cache@v4` on `.conda/envs`, keyed on `hashFiles('resources/envs/firmware-*.py')`, so
  an installer change invalidates the cache
- Build and test: `make build` and `make test`; the platform output is copied to `dist/` and uploaded
  as the `firmware` artifact. PlatformIO branches collect `.pio/build/<board>/*.bin`, `*.elf` and
  `*.hex`; AVR Rust collects `target/<target>/release/<repo>.elf` and STM32 Rust
  `target/<target>/release/<repo>`
- Failure log: an upload step with `if: failure()` collects `~/.local/*.out`, so a stopped installer
  stage is visible
- Tag release: a `v*` tag equal to `v` plus the contents of `VERSION` downloads the firmware artifact
  and creates a GitHub Release with `dist/*` and the matching CHANGELOG section; a tag that does not
  match `VERSION` fails before publishing (`ACC-TMPL-53`)
- Env-installers guard: without the `env-installers` component no step calls `make env`; one guard step
  names the missing component and exits non-zero (`ACC-TMPL-54`)

`.github/` is in `_skip_if_exists` (section 7.2), so `copier update` keeps a user's edits to the
generated workflow.

### 1.2 The template repository workflow

The template repository runs its own `.github/workflows/test.yml` (`ACC-TMPL-55`).

- `tests` job: `make setup`, `make test` and `make lint` on Python 3.14 with uv
- `toolchain` job: installs `firmware-avr` with `envs/firmware-avr.py` and runs `make test-toolchain`,
  which builds the AVR branches and runs the simavr boot test
- `make test-functional` is not a CI job: it needs every lab environment and QEMU built from source,
  so the full functional tier stays local

## 2. Questions

`platform` is the first entry in `copier.yml` and the first question asked (`ACC-TMPL-15`). The
platform-specific questions follow it, then the common questions, then `host_side` and
`host_module`, then `components` last. Derived answers use `when: false` and are never asked
(`ACC-TMPL-17`). `project_name` and `repo_name` are the exception: they use `ask: false`, so they
are computed once and recorded in the answers file, and `copier update` reuses the values instead
of recomputing them and conflicting.

### 2.1 Visible questions

| Variable | Condition | Values and default |
|---|---|---|
| `platform` | always, first | `arduino`, `avr`, `esp`, `stm32`; default `arduino` |
| `author_name` | always | free text; `Name <email>` or `Name email` |
| `description` | always | free text; default empty |
| `open_source_license` | always | `Apache-2.0`, `MIT`, `No license file`; default `MIT` |
| `git_init` | always | `Yes`, `No`; default `Yes` |
| `environment_scope` | always | `global`, `local`; sets the default of `ENV_SCOPE`; default `global` (`ACC-TMPL-42`) |
| `arduino_board` | `platform == 'arduino'` | `uno`, `nano`, `mega2560`, `leonardo`, `other`; default `uno` |
| `arduino_board_custom` | arduino and `other` | PlatformIO board id; required |
| `arduino_bootloader` | arduino and `nano` | `old`, `new`; default `old` |
| `arduino_libraries` | `platform == 'arduino'` | `No`, `Yes`; default `No`; `Yes` adds `lib/vendor/` and rows in `lib/README.md` |
| `arduino_sketch_link` | `platform == 'arduino'` | `Yes`, `No`; default `No`; `Yes` adds the root `<repo>.ino` symlink (`ACC-TMPL-47`) |
| `avr_language` | `platform == 'avr'` | `c`, `cpp`, `rust`; default `c` (`ACC-TMPL-16`) |
| `avr_mcu` | `platform == 'avr'` | `atmega328p`, `atmega32u4`, `attiny85`, `other`; default `atmega328p` |
| `avr_mcu_custom` | avr and `other` | PlatformIO board id, or the MCU name for Rust; required |
| `avr_clock` | `platform == 'avr'` | `16000000`, `8000000`; default `16000000` |
| `avr_programmer` | `platform == 'avr'` | `usbasp`, `arduino-isp`; default `usbasp` |
| `esp_chip` | `platform == 'esp'` | `esp32`, `esp8266`; default `esp32` |
| `esp_framework` | `platform == 'esp'` | esp32: `espidf`, `arduino`; esp8266: `arduino`, `esp8266-rtos-sdk`; default `espidf` or `arduino` |
| `esp_board` | `platform == 'esp'` | esp32: `esp32dev`, `esp32doit-devkit-v1`; esp8266: `nodemcuv2`, `d1_mini` |
| `stm32_toolchain` | `platform == 'stm32'` | `rust`, `platformio`; default `rust` |
| `stm32_board` | `platform == 'stm32'` | `f405rg`, `f103c8`, `f411re`, `l476rg`; default `f405rg` |
| `stm32_framework` | stm32 and `platformio` | `stm32cube`, `arduino`; default `stm32cube` |
| `stm32_upload` | stm32 and `platformio` | `stlink`, `serial`; default `serial` for f405rg, `stlink` otherwise |
| `host_side` | always, directly before `components` | `No`, `Yes`; default `No`; `Yes` adds `host/` and the host targets (section 3.5, `ACC-TMPL-59-HOST-SIDE`) |
| `host_module` | `host_side == 'Yes'` | Python module name; default `repo_name` without `-` plus `_host`, so `weather-station` gives `weatherstation_host` and `board` gives `board_host`; the validator rejects a value that is not a Python identifier (`ACC-TMPL-60-HOST-MODULE`) |
| `components` | always | multiselect of the ten; default `notebooks, resources, references, simulator, agents, env-installers` |

### 2.2 Derived answers

| Variable | Value | Condition |
|---|---|---|
| `project_name` | destination folder name | always |
| `repo_name` | `project_name.lower().replace(' ', '-')` | always |
| `author_email` | the token holding `@` and `.` in `author_name` | always |
| `author_name_clean` | `author_name` without the email token | always |
| `author_first_name` | first token of `author_name_clean` | always |
| `author_last_name` | remaining tokens of `author_name_clean`, joined | always |
| `serial_baud` | `9600` for arduino and avr, else `115200` | always |
| `env_name` | `firmware-avr`, `firmware-esp` or `firmware-stm32` (STM32 Rust and PlatformIO in one environment) | always |
| `env_local` | `1` when `environment_scope == 'local'`, else empty | always |
| `toolchain_language` | `rust` for avr+rust and stm32+rust; `cpp` when the Arduino framework is used (`platform == 'arduino'`, `esp_framework == 'arduino'`, `stm32_framework == 'arduino'`); else `c` | always |
| `crate_name` | `repo_name` with `-` replaced by `_` | Rust |
| `avr_target` | `avr-none` | avr and rust |
| `avr_cpu` | the MCU name, or `avr_mcu_custom` when `other` | avr and rust |
| `pio_platform` | `atmelavr@5.3.0`, `espressif32@7.1.3`, `espressif8266@4.2.1`, `ststm32@20.0.0` | PlatformIO branches |
| `pio_board` | the board id mapped from the answers | PlatformIO branches |
| `pio_framework` | `arduino`, `espidf`, `esp8266-rtos-sdk`, `stm32cube`, or empty for bare AVR | PlatformIO branches |
| `pio_upload_protocol` | `usbasp`/`arduinoisp`, `stlink`/`serial`, else empty | PlatformIO branches |
| `thumb_target` | `thumbv7m-none-eabi` for f103c8, else `thumbv7em-none-eabihf` | stm32 and rust |
| `flash_kb`, `ram_kb` | region sizes for f405rg, f103c8, f411re, l476rg | stm32 and rust |

The author split (`ACC-TMPL-18`): both `Konrad Jelen <konrad.jelen@gmail.com>` and
`Stellars Henson stellars.henson@ioata.com` give first name `Konrad` / `Stellars`, last name
`Jelen` / `Henson`, and the matching email. A one-token name gives an empty last name. `LICENSE`
carries `author_name_clean` and `author_email`. `author_first_name` and `author_last_name` are
available to every template that needs them.

`arduino_libraries` keeps its register role but no longer gates `lib/`; see section 8.

## 3. Layout

### 3.1 Unified tree

With all components selected, every project renders:

```
<repo>/
├── AGENTS.md
├── CLAUDE.md                  # one line: @AGENTS.md
├── CHANGELOG.md
├── LICENSE                    # unless No license file
├── Makefile
├── src/                       # the adapter root on every platform
│   ├── main.c                 # ESP-IDF adapter with app_main
│   └── <adapter helpers>
├── main -> src                # ESP-IDF only: compatibility link naming the main component
├── lib/
│   ├── README.md              # library register
│   ├── core/                  # C and C++
│   │   ├── core.c
│   │   └── core.h
│   └── vendor/                # only arduino_libraries == Yes
├── test/
│   ├── host/                  # host tests of the shared core
│   ├── harness/               # simulator wrapper and board helpers
│   └── functional/            # boot and behaviour tests, one per criterion
├── resources/
│   ├── README.md
│   ├── graphics/
│   ├── external/
│   └── envs/                  # env-installers
├── references/                # references component
│   ├── README.md
│   ├── datasheets/
│   └── notes/
├── data/                      # data component
├── docs/                      # docs component
├── notebooks/                 # notebooks component
├── scripts/                   # PC-side helper scripts; section 3.6
│   ├── README.md
│   ├── eeprom_tool.py         # Arduino and bare AVR only
│   └── freertos.py            # STM32Cube only; PlatformIO build hook
├── host/                      # host_side == Yes; section 3.5
├── .agents/                   # agents component
├── .claude/                   # agents component; links only
└── .github/                   # ci component
```

`test/host`, `test/harness` and `test/functional` are the three test tiers: host logic tests,
simulator drivers, and functional tests. `notebooks/` and `data/` hold exploration and data, not
build input.

### 3.2 Shared core and adapters

The pure logic is one module per project (`ACC-TMPL-44`):

| Language | Core | Host test | Adapter |
|---|---|---|---|
| C, C++ | `lib/core/core.c`, `lib/core/core.h` | `test/host/test_core.c` compiles `lib/core/core.c` directly | `src/main.c` (`app_main` on ESP-IDF), `src/main.cpp`, `src/<repo>.ino` |
| Rust | `src/lib.rs` | `test/host/core.rs`, wired as a Cargo `[[test]]` target | `src/bin/<repo>.rs` |

The C/C++ adapter includes `"core.h"`.

- PlatformIO adds `lib/core` to the include path as a project library
- For ESP-IDF the PlatformIO library dependency finder compiles `lib/core` as a component named `core`
- The ESP-IDF `src/main.c` includes `"core.h"`
- The host test compiles the same source with the host compiler
- A break in the core fails on the host before a board is touched

The Rust core is the package library.

- The binary calls it with `use <crate_name>::...`
- The core carries `#![cfg_attr(not(test), no_std)]`
- `cargo test` runs it on the host
- `test/host/core.rs` covers the public surface

### 3.3 Per-toolchain layouts

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

Rules per toolchain, from `docs/best-practices.md`:

- PlatformIO: `src/`, `lib/` and `test/` are the project roots. `include/` is not rendered; a
  header sits beside its source. `platformio.ini` pins the platform version the installer installs.
  Tests do not link `src/`; the core is in `lib/core` for that reason.
- Arduino: the sketch file is `src/<repo>.ino`, which PlatformIO compiles. With
  `arduino_sketch_link == Yes`, the root carries `<repo>.ino` as a symlink to it, so the project
  root is a sketch folder when its folder name is `repo_name`. PlatformIO remains the supported
  build because the shared core sits in `lib/core` and the Arduino CLI compiles only the sketch and
  `src/`.
- ESP-IDF: `src/` is the source root. PlatformIO sets `src_dir = main`, so it compiles
  `src/main.c` once through the application component; the default `src_dir = src` would add a
  second project source beside the component the link exposes, and PlatformIO rejects that build.
  `src/main.c` carries `app_main`, which creates one task that prints `[BOOT] <repo>`; the scheduler
  already runs, so the starter never calls `vTaskStartScheduler()`. A relative `main -> src` symlink
  supplies the application component name the ESP-IDF build expects; it is a link, not a second
  source root. `sdkconfig.defaults` is committed; `sdkconfig` is ignored. PlatformIO generates the
  component build files; no hand-written `CMakeLists.txt`.
- ESP8266 RTOS SDK: IDF-style sources on the RTOS SDK; `user_init` starts one task that prints the
  boot line. The RTOS SDK release is pinned to the installed framework.
- STM32Cube: `src/main.c` performs the HAL init and creates one CMSIS-RTOS task that prints the boot
  line (`ACC-TMPL-10`). `FreeRTOSConfig.h` ships beside the adapter. The CubeMX `Core/` tree is not
  reproduced: the unified tree owns the roots, and PlatformIO supplies the HAL and middleware from
  the pinned `ststm32` framework.
- Rust: the root package follows `knurling-rs/app-template`: `src/lib.rs`, `src/bin/<repo>.rs`,
  `test/host/` as the integration-test target, `memory.x` and `build.rs` for STM32 (no `memory.x`
  for AVR). `.cargo/config.toml` sets the target and the link argument; `rust-toolchain.toml` pins
  the version the installer installs.

### 3.4 Mixed roots

One build root exists per project: `platformio.ini` or `Cargo.toml`, never both. `post_gen` removes
the branch that the answers did not select, so the rendered project has exactly one build file and
one adapter. Every branch carries one real source root, `src/`; on ESP-IDF `main` is a relative
symlink to `src`, not a source root.

### 3.5 Host side

`host_side == 'Yes'` adds `host/`, a Python package that runs on the PC and talks to the board over
the serial port (`ACC-TMPL-61-HOST-SCAFFOLD`). With `No` the project has no `host/` path, no host
targets and no host text in `README.md`, `AGENTS.md` or the skills (`ACC-TMPL-59-HOST-SIDE`).

```
host/
├── pyproject.toml             # distribution <repo>-host, setuptools, src layout, pyserial, Python >= 3.10
├── src/
│   └── <host_module>/
│       ├── __init__.py
│       ├── __main__.py        # python -m <host_module> --port PORT --baud BAUD --timeout SECONDS
│       ├── serial_client.py   # read_boot_line(lines, expected, timeout), open_port(port, baud)
│       └── protocol.py        # crc8(data) -> int, the algorithm of the core CRC
└── tests/
    ├── test_serial_client.py  # read_boot_line with a fake line list: found, absent, timeout
    └── test_protocol.py       # crc8 against fixed vectors of the core algorithm
```

- `__main__.py` reads the console until `[BOOT] <repo>` and prints one JSON line with `port`,
  `boot` and `line`. It exits 0 when the boot line arrived and 1 with the reason otherwise.
- `read_boot_line` takes any iterable of text lines, so the tests need no hardware. `open_port`
  imports pyserial inside the function.
- `protocol.crc8` uses the polynomial `0x07`, the initial value `0x00` and the most significant bit
  first, the same as `core_crc8` in `lib/core/core.c` and `crc8` in `src/lib.rs`
  (`ACC-TMPL-63-HOST-CRC`).
- The package runs on the PC only. PlatformIO, ESP-IDF and Cargo never compile `host/`.
- `make host-run` imports pyserial from the project environment. `firmware-avr`, `firmware-esp`
  and `firmware-stm32` each install pyserial in their first conda stage.
- `pip install -e host` inside the environment makes the package importable from notebooks; the
  make targets set `PYTHONPATH=host/src` and need no install.
- `host/` is in `_skip_if_exists` (section 7.2), so `copier update` keeps user edits.

A Python host keeps its module under `host/src/<host_module>/`, the src layout of a Python package.
A host in another language would place its code directly in `host/src/`. The template generates the
Python form only.

Host code lives in `host/src/<package>` and not under `src/`, because everything under `src/` is
built for the board: PlatformIO compiles `src/`, ESP-IDF reaches it through `main -> src`, and
`cargo build --target` builds every file in `src/bin/`. `scripts/` stays for small non-interactive
commands that an agent runs (section 3.6).

### 3.6 Helper scripts

`scripts/` is always rendered and holds the PC-side helper scripts (`ACC-TMPL-64-SCRIPTS`).
`scripts/README.md` states the contract:

- A script runs on the PC, takes no interactive input, prints one JSON line and exits non-zero with
  a reason on failure, so an agent can run it.
- `eeprom_tool.py` serves `make eeprom-backup` and `make eeprom-restore` on Arduino and bare AVR
  (section 4.5).
- `freertos.py` is the one exception: a PlatformIO build hook that `platformio.ini` names in
  `extra_scripts = pre:scripts/freertos.py` on STM32Cube. It is not a command for a person or an
  agent.

## 4. Makefile

### 4.1 Targets

| Target | Runs | Present |
|---|---|---|
| `create_environment` | `./resources/envs/firmware-<platform>.py` on the host | `env-installers` |
| `env` | alias for `create_environment` (`ACC-TMPL-8`) | `env-installers` |
| `build` | `$(ENV_RUN) pio run`, or `cargo build` for Rust | always |
| `upload` | `pio run -t upload --upload-port $(PORT)`, `stm32flash`, or `avrdude` | always |
| `monitor` | `pio device monitor`, or `python -m serial.tools.miniterm` | always |
| `host-test` | compile and run `test/host`; no `##` line, so help does not list it | always |
| `test` | `host-test`, plus `sim` when `simulator` is selected, plus `host-app-test` when `host_side` is `Yes` | always |
| `sim` | `$(ENV_RUN) pytest test/functional -q` | `simulator` |
| `host-run` | `$(ENV_RUN) env PYTHONPATH=host/src python -m <host_module> --port $(PORT) --baud $(BAUD)` | `host_side == 'Yes'` |
| `host-app-test` | `$(ENV_RUN) env PYTHONPATH=host/src pytest host/tests -q` | `host_side == 'Yes'` |
| `eeprom-backup` | `scripts/eeprom_tool.py` reads EEPROM to `resources/eeprom/` | arduino and avr |
| `eeprom-restore` | `scripts/eeprom_tool.py` writes with avrdude `-D` and verifies the read-back | arduino and avr |
| `clean` | remove build output and caches; keep `.conda/` and `resources/eeprom/` | always |
| `help` | print the `##` line of each rendered target | always |

No target named `erase` exists.

`help` lists `create_environment`, `build`, `upload`, `monitor`, `test`, `sim`, `clean` and `help`
with their descriptions (`ACC-TMPL-7`). A target whose component is absent is not listed. With
`host_side == 'Yes'` it also lists `host-run` and `host-app-test` (`ACC-TMPL-62-HOST-TARGETS`).
`host-test` keeps its name: it tests the shared core with the host compiler, and `host-app-test`
tests the PC package. With `env-installers` unselected, `help` prints one line naming the lab
installer to run: `~/.local/lab-utils/envs/firmware-<platform>.py` (`ACC-TMPL-4`).

### 4.2 Variables

| Variable | Default | Use |
|---|---|---|
| `ENV` | `{{ env_name }}` | the conda environment name |
| `ENV_RUN` | `conda run --no-capture-output -n $(ENV)` | prefix of every toolchain command |
| `PROJECT_DIR` | the Makefile directory | paths and the local environment root |
| `PORT` | `/dev/ttyUSB0` | upload, monitor, host-run |
| `BAUD` | `{{ serial_baud }}` | monitor, upload, stm32flash, host-run |
| `STM32_SERIAL_MODE` | `8e1` | `stm32flash -m` |
| `HOST_CC` | `x86_64-conda-linux-gnu-cc` | host tests |
| `BUILD_DIR` | `build` | host test binary and Rust binary output |

`PORT`, `BAUD` and `STM32_SERIAL_MODE` take the value on the command line, then the value in `.env`,
then the default (section 6.5).

Every target that calls a toolchain program runs inside the environment through `$(ENV_RUN)`,
including `build`, `upload`, `monitor`, `test`, `sim`, the EEPROM targets and the host targets
(`ACC-TMPL-12`).
`create_environment` runs the installer directly because the environment does not exist yet;
`help` runs host `python3`.

### 4.3 Environment scope

The copier answer `environment_scope` sets the default of the Makefile variable `ENV_SCOPE`. Any
make invocation may pass `ENV_SCOPE=global` or `ENV_SCOPE=local`, and the same value goes to every
make command for the project.

The Makefile carries one run-time conditional in every render:

```
ENV_SCOPE ?= <the copier answer>
ifeq ($(ENV_SCOPE),local)
export CONDA_ENVS_PATH := $(PROJECT_DIR)/.conda/envs
endif
```

`global` scope uses the environment name as it is. The installer calls `conda create --name $(ENV)`,
so one copy lands in the conda root and every project that uses the same environment name shares it.
The copy is large.

`local` scope makes the `ifeq` export `CONDA_ENVS_PATH`, so the installer creates the environment
under `.conda/envs/` in the project. The environment is easy to use with this project, and it takes
the same large space inside the project folder. The toolchain skill asks the user for the scope and
explains the trade-off.

- In local scope every conda subprocess inherits the variable
- `conda create --name $(ENV)` creates the environment under the project in local scope
- `conda run -n $(ENV)` and `conda env list --json` resolve the same prefix
- The installer files stay byte-identical to the lab copies
- Nothing under `~/.local/lab-utils/envs` or `~/.local` is edited (`ACC-TMPL-42`)
- `.conda/` is in `.gitignore`
- The installer's own log at `~/.local/<env>.out` is unchanged installer behaviour, not a configuration edit
- With `env-installers` unselected, the Makefile still carries the `ENV_SCOPE` conditional, so a lab installer run by hand with `CONDA_ENVS_PATH` set the same way creates the environment the targets then use

### 4.4 Build, upload and monitor by branch

| Branch | Build | Upload | Monitor |
|---|---|---|---|
| Arduino, bare AVR C/C++, ESP, STM32 PlatformIO | `$(ENV_RUN) pio run` | `$(ENV_RUN) pio run -t upload --upload-port $(PORT)` | `$(ENV_RUN) pio device monitor --port $(PORT) -b $(BAUD)` |
| Bare AVR Rust | `$(ENV_RUN) cargo build --release --target avr-none` | `$(ENV_RUN) avrdude -c <programmer> -p <mcu> -P $(PORT) -U flash:w:<elf>` | `$(ENV_RUN) python -m serial.tools.miniterm $(PORT) $(BAUD)` |
| STM32 Rust | `$(ENV_RUN) cargo build --release --target {{ thumb_target }}` | `$(ENV_RUN) cargo objcopy ... -O binary`, then `$(ENV_RUN) stm32flash -b $(BAUD) -m $(STM32_SERIAL_MODE) -w <bin> -v -g 0x0 $(PORT)` | `$(ENV_RUN) python -m serial.tools.miniterm $(PORT) $(BAUD)` |

`stm32flash` needs `-m 8n1` on a port that refuses `PARENB`, such as a device bridge pty; on a
direct port the STM32 ROM bootloader uses `8e1`. `STM32_SERIAL_MODE` carries that difference in one
place, and `.env` sets it per machine.

### 4.5 EEPROM targets

`eeprom-backup` reads the EEPROM image into `resources/eeprom/<board>-<timestamp>.bin` and prints
one JSON line. `eeprom-restore` writes with `avrdude -D` and reads the image back for comparison
before it reports success. Both targets run `scripts/eeprom_tool.py` under `$(ENV_RUN)` and are
non-interactive, so an agent can run them (`ACC-TMPL-39`). They exist only for Arduino and bare AVR.

## 5. Capability matrix

Rows are platform and board; `host` means the `make test` host tier; `simulator` names the
emulator; `HIL` means upload and observe the boot line on a board on the bench (`ACC-TMPL-45`).
The generated README carries the rows for its own platform and board; `docs/best-practices.md`
carries the full table.

| Platform | Board / MCU | Host | Simulator | HIL |
|---|---|---|---|---|
| Arduino | uno (ATmega328P, 32 KB) | yes | simavr | yes |
| Arduino | nano, old or new bootloader (ATmega328P) | yes | simavr | yes |
| Arduino | mega2560 (ATmega2560, 256 KB) | yes | HIL only: 256 KB is above simavr's documented 128 KB limit | yes |
| Arduino | leonardo (ATmega32U4) | yes | HIL only: simavr does not document the ATmega32U4 | yes |
| Arduino | other | yes | HIL only unless the MCU is documented and the flash is at most 128 KB | yes |
| Bare AVR | atmega328p at 16 MHz or 8 MHz | yes | simavr | yes |
| Bare AVR | atmega32u4 | yes | HIL only: not documented by simavr | yes |
| Bare AVR | attiny85 | yes | simavr; no UART, so the boot-line test skips | yes |
| Bare AVR | other | yes | HIL only unless documented and at most 128 KB | yes |
| ESP32, ESP-IDF | esp32dev, esp32doit-devkit-v1 | yes | Espressif QEMU fork, `qemu-system-xtensa -machine esp32` | yes |
| ESP32, Arduino | esp32dev, esp32doit-devkit-v1 | yes | Espressif QEMU fork, `qemu-system-xtensa -machine esp32` | yes |
| ESP8266, Arduino | nodemcuv2, d1_mini | yes | HIL only: no ESP8266 machine | yes |
| ESP8266, RTOS SDK | nodemcuv2, d1_mini | yes | HIL only: no ESP8266 machine | yes |
| STM32, Rust or PlatformIO | f405rg (STM32F405RGT6, 1024/128 KB) | yes | QEMU `netduinoplus2` | yes |
| STM32, Rust or PlatformIO | f103c8 (STM32F103C8T6, 64/20 KB) | yes | HIL only: no QEMU machine | yes |
| STM32, Rust or PlatformIO | f411re (STM32F411RET6, 512/128 KB) | yes | HIL only: no QEMU machine | yes |
| STM32, Rust or PlatformIO | l476rg (STM32L476RGT6, 1024/128 KB) | yes | HIL only: no QEMU machine | yes |

Mainline QEMU has no ESP32 or ESP8266 machine. ESP32 emulation is Espressif's fork only; both the
ESP-IDF and Arduino images boot under `qemu-system-xtensa -machine esp32`. The simulator tier skips
with a written reason and never passes silently (`ACC-TMPL-32`, `ACC-TMPL-33`, `ACC-TMPL-37`).

## 6. Agent files

### 6.1 Root files

`AGENTS.md` is always rendered at the repository root (`ACC-TMPL-14`). It carries:

- Project name, description and platform.
- Structure: `src/`, the `main -> src` link on ESP-IDF, `lib/core`, the three test tiers,
  `resources/`, `references/`, `docs/`, `scripts/`, and `host/` with `host_side == 'Yes'`.
- Commands: `make create_environment`, `make build`, `make upload PORT=...`, `make monitor`,
  `make test`, `make sim`, `make clean`, with `make help` as the index; `make host-run` and
  `make host-app-test` with `host_side == 'Yes'`.
- Test tiers and the board's row from the capability matrix.
- Board facts: boot line `[BOOT] <repo>`, baud, upload protocol, program button or bootloader.
- Safety: ask before flashing a board that holds user data; back up EEPROM first on Arduino and
  bare AVR.

`CLAUDE.md` is always rendered at the root and contains one line, `@AGENTS.md`. Claude Code reads
`AGENTS.md` only when no `CLAUDE.md` exists; the import carries the shared instructions. There is
no `.claude/CLAUDE.md`; instructions live once.

### 6.2 Master tree and links

`.agents/` is the master for agent assets. The `agents` component renders:

- `.agents/skills/<repo>-device/SKILL.md`
- `.agents/skills/<repo>-toolchain/SKILL.md` and `references/toolchains.md`
- `.agents/workflows/build-and-flash.md`
- `.agents/workflows/release.md`
- `VERSION` and `RELEASING.md` at the root, rendered outside the `agents` component
- `.claude/skills/<repo>-device` → `../../.agents/skills/<repo>-device`
- `.claude/skills/<repo>-toolchain` → `../../.agents/skills/<repo>-toolchain`
- `.claude/commands` → `../.agents/workflows`

`post_gen` creates the links after rendering, so a copy from a filesystem without symlink support
still produces the links it can. The links are relative; the project stays portable.

### 6.3 Device skill

`SKILL.md` frontmatter names the skill and its trigger. The body carries:

- Board facts: platform, board id, MCU, clock, flash and RAM, upload protocol; on STM32 Rust, the
  rule that a port refusing parity needs `STM32_SERIAL_MODE=8n1` in `.env`.
- Port discovery: `ls /dev/ttyUSB* /dev/ttyACM*`.
- Environment: `make create_environment`, or the lab installer when the component is absent.
- Build and upload: the exact make targets, `PORT` and `BAUD`, and the board's reset sequence.
- Non-interactive console: read until `[BOOT] <repo>`; never open an interactive monitor in an
  automated step. With `host_side == 'Yes'` one line adds `make host-run PORT=<port>`, which reads
  the boot line non-interactively and prints one JSON line.
- Command table: one line per task with the command.
- Troubleshooting table: symptom, cause, action, covering no port, permission denied, bootloader
  timeout, wrong baud, and a simulator skip.
- Simulator limits for the board, from the capability matrix.

`build-and-flash.md` runs `make build`, `make upload PORT=...` (`make upload` when `.env` sets
`PORT`), reads the monitor until
`[BOOT] <repo>`, and reports the build size and the first boot line.

### 6.4 Toolchain skill

`<repo>-toolchain/SKILL.md` gives a generated project the context to manage its own tool layer. It
carries:

- A first-run procedure in order: `make help`, the installer, `make build`, `make test`, `make sim`,
  `make upload`
- Environment facts: `env_name`, the installer path, the scope, the `uv` script form, the stage
  markers and the log at `~/.local/<env>.out`
- Exact install, verification, log and removal commands
- Rules: ask before installing or removing, never install a tool outside the installer, never edit
  the project copy of the installer
- The simulator run and the emulator check for the platform
- The LTspice run with the ltspice component: `make ltspice`, the JSON fields, the pass thresholds,
  `simulations/circuit.log`, and the direct `ltspice -b` and `ngspice -b` commands
- A failure table: missing conda, a stopped stage, a missing tool, a skipped simulator or circuit test

`references/toolchains.md` lists the stages and programs of the project's installer. It names tools,
not versions: the pins sit at the top of the installer, and a copy in the skill would drift.

### 6.5 Port configuration

Every project reads its serial settings from `.env` in the project root. `.gitignore` lists `.env`,
so each machine keeps its own port out of git, and the template renders `.env.example` to copy from
(`ACC-TMPL-66-ENV-PORT`).

- The Makefile runs `-include .env` before `PORT ?= /dev/ttyUSB0`, `STM32_SERIAL_MODE ?= 8e1` and
  `BAUD ?= {{ serial_baud }}`
- Precedence: the value on the command line, then `.env`, then the Makefile default
- `.env.example` holds commented `NAME=value` lines in make syntax, without quotes: `PORT`, `BAUD`
  and, on STM32 Rust, `STM32_SERIAL_MODE`
- Only the STM32 Rust upload reads `STM32_SERIAL_MODE`, so only its `.env.example` carries the line
- A device bridge pty is one possible `PORT`: `PORT=/run/devices/tty-<vid>-<pid>`
- A port that refuses `PARENB`, such as a device bridge pty, needs `STM32_SERIAL_MODE=8n1`; a direct
  port uses the `8e1` of the STM32 ROM bootloader
- `copier update` leaves `.gitignore` unchanged (`_skip_if_exists`), so a project updated from 1.0.17
  or older adds the `.env` line itself

## 7. post_gen and update behaviour

### 7.1 Removal on a fresh copy

`scripts/post_gen.py` runs from `_tasks` with the answers joined by commas. On `_copier_operation ==
'copy'` it removes every path the answers did not select. On `update` it removes only the files the
update wrote back (section 7.2).

Component paths:

```
notebooks      notebooks
resources      resources/README.md resources/graphics resources/external
references     references
data           data
simulator      test/harness test/functional pytest.ini
docs           docs
ci             .github
agents         .agents .claude/skills .claude/commands
env-installers resources/envs
```

`resources/envs` is owned by `env-installers`, not by `resources`. A project with `resources`
unselected and `env-installers` selected keeps `resources/envs/` and loses the three resources
paths.

`host/` is removed when `host_side` is not `Yes`. `_tasks` passes the answer as `--host-side`; on
update the rule of section 7.2 applies to it, as it does to the component paths.

Toolchain paths:

- C/C++ branches remove `Cargo.toml`, `build.rs`, `memory.x`, `.cargo`, `rust-toolchain.toml`,
  `src/lib.rs`, `src/bin/` and `test/host/core.rs`. Rust branches remove `platformio.ini`,
  `src/main.c`, `src/main.cpp`, `src/*.ino`, `src/FreeRTOSConfig.h`, `lib/core/` and
  `test/host/test_core.c`.
- The adapter selection keeps exactly one of `src/main.c`, `src/main.cpp`, `src/<repo>.ino` and
  `src/bin/<repo>.rs`.
- ESP-IDF keeps `src/` and creates the relative `main -> src` symlink; every branch removes the
  `main/` source directory.
- STM32 keeps the one installer, `firmware-stm32.py`, for both toolchains; it removes every other
  platform installer. Every other platform keeps its own installer and removes the rest, so a
  render carries `firmware_env.py` and one platform installer. Installers keep the executable bit.
- Arduino with `arduino_sketch_link == Yes` creates the root `<repo>.ino` symlink after rendering.
  On update the link is left as it is.
- `git_init == Yes` runs `git init -b main`; otherwise no repository is created.

### 7.2 Update keeps user files

`update` runs the same script with `--copier-operation update`. Under every unselected path it
removes only the untracked files that git does not ignore, then the directories left empty: copier
refuses to update a destination with untracked files, so each such file was written by the update,
and tracked and ignored files stay. A starter file the project removed stays removed; the Update
behaviour section of `.copier/README.md` states how post_gen does this and its not-found fallback.
The paths in `_skip_if_exists` are never overwritten:

```
README.md
CHANGELOG.md
VERSION
RELEASING.md
AGENTS.md
CLAUDE.md
docs/README.md
notebooks/README.md
resources/README.md
references/README.md
data/README.md
resources/envs/
.gitignore
pytest.ini
test/
host/
notebooks/
resources/
references/
simulations/
data/
docs/
.github/
.agents/
.claude/
```

Component trees and user documents are protected. Build files (`Makefile`, `platformio.ini`,
`Cargo.toml`) stay template-owned so a build fix reaches an update; a user edit there can conflict
and copier reports it (`ACC-TMPL-21`). The same rule applies to the new `references/`, `data/`,
`host/`, `.agents/`, `AGENTS.md` and `CLAUDE.md` entries, so an update never overwrites a file in a
folder the user owns.

## 8. Criteria conflicts resolved

- `ACC-TMPL-23` (No leaves no `lib/`) conflicts with `ACC-TMPL-44` and `ACC-TMPL-46`: the shared
  C/C++ core lives in `lib/core`, and `lib/` is part of the shared tree. Resolution: `lib/` is
  always present; `arduino_libraries` `Yes` adds `lib/vendor/` and library rows in `lib/README.md`,
  `No` keeps `lib/core/` and a register with no vendored libraries. The "No leaves no lib/" clause
  is superseded; the criterion's register intent is kept.
- `ACC-TMPL-46` names `src/` and `test/host`; `ACC-TMPL-27` names the app-template `tests/`.
  Resolution: Rust host tests live in `test/host/core.rs` and run through a Cargo `[[test]]` target,
  so the directory name is the unified one and Cargo still runs them.
- `ACC-TMPL-4`, `ACC-TMPL-7` and `ACC-TMPL-42` name `create_environment`; `ACC-TMPL-8` names
  `make env`. Resolution: `create_environment` is canonical and listed in help; `env` is an alias
  and is not a separate help line.
- `ACC-TMPL-47` places the sketch in `src/` and offers a root symlink. PlatformIO compiles the
  `.ino` in `src/`; the root symlink serves editors and sketch-folder tooling. The supported build
  is PlatformIO because the shared core lives in `lib/core`.
