# Philosophy

Status: agreed, 2026-10-18. `docs/template-design.md` holds the choices that follow from these
principles. The generated README opens with the paragraph in section 7.

## 1. One structure, small variations

Every generated project uses the same top-level structure.

- `Makefile`, `src/`, `lib/`, `test/host/`, `test/harness/`, `test/functional/`, `resources/`, `references/`, `docs/` and `scripts/`
- `scripts/` holds PC-side helper scripts: each takes no interactive input, prints one JSON line and exits non-zero with a reason on failure, so an agent can run it; the STM32Cube `scripts/freertos.py` is the one exception, a PlatformIO build hook
- A component folder is present when its component is chosen and absent otherwise
- `host/` is present when the `host_side` answer is `Yes`; it holds the PC-side package, and the firmware build never compiles it
- A toolchain adds its build file and one adapter
- Two variations, listed in the design: `src/bin/` for Cargo and the sketch name for Arduino
- `src/` is the one adapter root on every platform; for ESP-IDF a relative `main -> src` symlink supplies the component name the build expects, and it is not a second source root
- Moving between boards keeps the folders, the make targets and the test tiers; only the answers and the build file change

## 2. Components opt in

Every optional tree except `host/` is a component chosen in the questionnaire: `notebooks`, `resources`, `references`, `data`, `simulator`, `docs`, `ci`, `agents`, `env-installers` and `ltspice`.

- An unselected component leaves no folder and no target
- A project with only the always-on parts still builds, uploads, monitors and runs its host tests

## 3. The Makefile drives development

The generated Makefile is the only entry point.

- Core targets: `create_environment`, `build`, `upload`, `monitor`, `test`, `sim`, `clean` and `help`
- `eeprom-backup` and `eeprom-restore` exist for Arduino and bare AVR
- `ltspice` exists with the `ltspice` component, and `test` depends on it
- Every target that calls a toolchain program runs under `conda run` in the project's environment
- `create_environment` runs the installer with the host tool because the environment does not exist yet
- `help` prints text and runs on the host
- `PORT` and `BAUD` are variables
- No documented step calls `pio`, `cargo`, `avrdude` or `stm32flash` directly

## 4. Each toolchain follows its best practices

The layout follows `docs/best-practices.md`, and every rule there names its source.

- PlatformIO: `src/`, `lib/` and `test/`
- Arduino: the sketch layout
- ESP-IDF: `main/` and `app_main`
- STM32Cube: the HAL through PlatformIO
- Rust: the knurling-rs `app-template` layout
- Where toolchains conflict, the shared structure resolves the conflict
- Roots are never mixed inside one project

## 5. Pure logic is shared

Hardware-free logic lives in one module.

- C and C++: `lib/core/core.c` and `lib/core/core.h`
- Rust: `src/lib.rs`
- The module includes no register, HAL or Arduino header
- The host tests compile it
- One thin adapter per target calls it
- The same logic is never copied into an adapter

## 6. Simulator support is stated honestly

The capability matrix in `docs/template-design.md` names the test tiers and the emulator for each platform and board.

- The matrix states whether tests run on the host, in a simulator or only on hardware
- A board with no supported emulator says `HIL only`
- The simulator tier skips with a written reason and never passes silently
- A limit found by a test is recorded in the generated README

## 7. The paragraph the generated README opens with

Generated projects share one structure, with the same Makefile, source roots, test tiers and
top-level folders, and only the build file and one adapter vary by toolchain, so moving between
boards keeps the same commands and the same folders. Optional folders are components chosen at
generation. The Makefile is the entry point for the environment, the build, upload, monitor, tests
and the simulator. Each toolchain follows its published layout, pure logic lives in one shared
module, and the README states which test tiers the board can run and which emulator supports it.
