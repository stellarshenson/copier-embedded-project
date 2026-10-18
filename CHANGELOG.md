# Changelog

## [1.0.13] - 2026-10-18

### Added

- Agent context in every generated project: `<repo>-device` and `<repo>-toolchain` skills, the
  `/release` workflow, `VERSION`, `RELEASING.md` and `make increment_version`
- The toolchain skill asks whether the conda environment is global (shared, one large copy) or
  local (under `.conda/envs/` in the project), carries `ENV_SCOPE` on every command, and `.conda/`
  is ignored by git
- Full CI/CD: the `ci` component renders a workflow that builds, tests and uploads the firmware
  artifact, caches the conda environment, and publishes a GitHub Release from a `v*` tag; the
  template repository runs its fast suite, lint and AVR toolchain build in GitHub Actions

### Changed

- `src/` is the single adapter root on every platform; the ESP-IDF adapter lives in `src/main.c`,
  and a relative `main -> src` symlink with `src_dir = main` lets PlatformIO build the application
  component
- The generated Makefile chooses the conda scope at run time with `ENV_SCOPE`, defaulting to the
  copier answer
- `project_name` and `repo_name` are recorded with `ask: false`, so `copier update` reuses them
  instead of computing empty names and conflicting
- The LTspice guidance matches the target: `make ltspice` runs pytest, the JSON comes from
  `python ltspice/run.py`, and `circuit.log` is written by LTspice only

### Fixed

- The ESP and STM32 environment installers install pytest, so `make test` and `make sim` work on a
  fresh environment
- Free text is no longer interpolated into the copier task command, so a double quote in the
  description or author name cannot abort `copier copy`
- A `ci` render without `env-installers` stops with a clear reason instead of an unknown
  `make env` target

## [1.0.12] - 2026-10-18

### Added

- One unified project structure across every platform: Makefile, src/, lib/, test/host,
  test/harness, test/functional, resources/, references/, tools/, with only the build file and one
  adapter varying by toolchain
- Shared pure-logic core per language: lib/core/core.c for C and C++, src/lib.rs for Rust
- Bare AVR in C, C++ and Rust, with the AVR Rust target and boot line verified under simavr
- Opt-in components: data, references, ltspice, env-installers and device-bridge beside
  notebooks, resources, simulator, docs, ci and agents
- The ltspice component: an ATtiny84 pin driving a gain-2 op-amp, with an LTspice-compatible
  netlist and a functional test that runs under LTspice or ngspice
- Environment scope (global or local)
- `make create_environment` with one installer per platform
- QEMU in the environment installers: `qemu-system-arm` with the netduinoplus2 machine for STM32,
  and Espressif's QEMU fork with the ESP32 machine
- ESP32 Arduino and ESP-IDF both boot in the simulator tier; ESP8266 stays HIL only
- ngspice in every firmware environment for the circuit simulation
- A master environment source in `envs/`, symlinked from `~/.local/lab-utils/envs`, and
  `make envs-sync` to copy it into the template
- One `firmware-stm32` environment with Rust and PlatformIO with both STM32 frameworks
- A capability matrix, a placement guide for schematics, resources and libraries, the
  per-platform folder tree, and functional tests for five rendered projects

### Changed

- The STM32Cube starter groups NVIC priorities instead of starting the HAL time base, because
  FreeRTOS owns SysTick
- The STM32Cube starter compiles the framework's FreeRTOS middleware through tools/freertos.py
- Library sources stay in `lib/`; `arduino_libraries=Yes` adds `lib/vendor/` for project-local
  Arduino libraries

## [0.1.0] - 2026-10-17

### Added

- Copier template for embedded projects: Arduino, bare AVR, ESP and STM32
- Downstream questions per platform, including two STM32 toolchains (Rust embedded and PlatformIO)
  and the ESP chip/framework matrix
- One multiselect `components` question: notebooks, resources, simulator, docs, CI and agents
- Generated Makefile with `env`, `build`, `upload`, `monitor`, `test`, `sim`, `clean` and `help`
- Host unit tests plus a simavr harness for AVR and QEMU harnesses for ESP and STM32 that skip when
  the emulator is absent
- The lab conda environment installers ship in `resources/envs/` of every generated project
- Author name and email decomposition for the LICENSE
- `.agents` as the master agent layout, with `.claude/skills` and `.claude/commands` relative
  symlinks into it
