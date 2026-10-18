# copier-embedded-project

A Copier template for embedded firmware projects: Arduino, bare AVR, ESP and STM32.

## Commands

- `make setup` - create `.venv` with copier, pytest, pyyaml and ruff
- `make test` - render the platform and component matrix and run the fast tests
- `make test-toolchain` - also build the AVR branches with `firmware-avr`
- `make lint` - ruff over `scripts/` and `tests/`

## Rules

- `template/` is the rendered project; fix it there, never by editing a rendered copy
- `envs/` is the master for the firmware environment installers; `~/.local/lab-utils/envs` symlinks to it, and `make envs-sync` copies them into `template/resources/envs/`
- `scripts/post_gen.py` owns platform and component removal, the agent symlinks and git init
- Read `.copier/README.md` before changing questions, derived answers or update behaviour
- The acceptance criteria and defects of this template live in `docs/` and are written only through
  `pm-tools`
- `.agents/` is the master for agent assets; `.claude/skills` and `.claude/commands` are relative
  symlinks into it

## Layout

- `copier.yml` - questions, hidden derived answers, `_tasks`
- `template/` - project files: Makefile, PlatformIO/Cargo scaffolds, tests, harnesses, components
- `template/resources/envs/` - the conda environment installers copied from the lab
- `tests/` - tests of the template
