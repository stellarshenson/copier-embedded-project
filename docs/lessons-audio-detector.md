# copier-embedded-project - Lessons from audio-detector v1

Status: DRAFT for internal review, 2026-10-18.

## Contents

- [1. Overview](#1.-Overview)
- [2. Build and environment](#2.-Build-and-environment)
- [3. Simulator harness](#3.-Simulator-harness)
- [4. Test layout](#4.-Test-layout)
- [5. Safety and data](#5.-Safety-and-data)
- [6. Documentation and agents](#6.-Documentation-and-agents)
- [7. Adopted in the template](#7.-Adopted-in-the-template)

## 1. Overview

This document records what the audio-detector project at `/home/lab/workspace/private/embedded-projects/audio-detector` teaches the template and the file that shows each lesson.

## 2. Build and environment

- Every Makefile target runs in the platform conda environment through `conda run --no-capture-output -n firmware-avr`, with no activation step (`Makefile`)
- The `atmelavr@5.3.0` platform in `platformio.ini` matches the conda environment's platform version (`platformio.ini`, journal entry 3)
- `make test` depends on the firmware build, the simulator wrapper and a second firmware used as a tool, then runs pytest (`Makefile`)

## 3. Simulator harness

- `test/harness/simharness.c` wraps libsimavr from the PlatformIO package `tool-simavr`, compiled with the environment's cross compiler (`Makefile`, journal entry 4)
- `sim.py` binds the wrapper with ctypes and drives the board pins: the ADC in millivolts against AVCC, a button with contact bounce, the IR receiver and the serial line (`README.md`, `test/harness/sim.py`)
- Time-based tests jump `timer0_millis` instead of waiting, running the suite about 8 times faster than real time (journal entry 4)
- simavr does not toggle OC2B in phase-correct PWM; the harness records the carrier from the timer register instead (journal entry 4)
- A crash guard compares the simavr state with `cpu_Done` and `cpu_Crashed`; the first version compared the wrong constant (journal entry 7)
- Each simulator limit is written down and worked around in one place (`README.md`, `test/harness`)

## 4. Test layout

- `test/harness/` holds the simulator wrapper and pin helpers; `test/unit/` holds host tests of the pure helpers; `test/functional/` holds the tests, one or more per criterion (`README.md`)
- The functional tests name their acceptance-criterion id in the docstring (`test/functional/test_start.py`, `test/functional/test_enabled.py`)
- Eight deliberately broken firmware copies each turned a named test red (`logs/mutants.log`, journal entry 7)
- A test that only waited for a banner could not fail; the help test now asserts every command line (journal entry 8)

## 5. Safety and data

- EEPROM backup and restore are Makefile targets with a non-interactive tool that prints one JSON line (`Makefile`, `tools/eeprom_tool.py`, journal entry 9)
- Restore writes with avrdude `-D` and verifies the read-back; the board's flash image is saved before a bridge firmware is flashed (`journal entry 11`)
- Libraries are vendored in `lib/`, their versions are listed in the README, and nested `.git` directories are removed (`journal entry 2`, `README.md`)

## 6. Documentation and agents

- The README states the build and test commands and the board's bootloader variant (`README.md`)
- The project skill `.claude/skills/audio-detector-device/SKILL.md` covers port discovery, build, upload, the non-interactive console, the command table and a troubleshooting table (`journal entry 10`)
- A model of the analog front end in `notebooks/` is the source design decisions cite (`journal entry 6`)

## 7. Adopted in the template

- Every generated Makefile target runs inside the project's conda environment (`ACC-TMPL-12`)
- `lib/` carries a README that lists each library and its version (`ACC-TMPL-23`)
- The test tree splits into host unit tests, the harness and functional tests, and `make test` runs them (`ACC-TMPL-11`, `ACC-TMPL-33`)
- Simulator limits are written down for each platform (`ACC-TMPL-37`)
- The generated device skill names port discovery, build, upload, console and troubleshooting (`ACC-TMPL-38`)
- Arduino and bare AVR projects have EEPROM backup and restore targets (`ACC-TMPL-39`)
- The generated README documents the structure and the development flow (`ACC-TMPL-40`)
- Every generated project ships a CHANGELOG.md skeleton (`ACC-TMPL-41`)
