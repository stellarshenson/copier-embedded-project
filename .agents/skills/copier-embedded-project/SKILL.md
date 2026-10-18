---
name: copier-embedded-project
description: Create an embedded firmware project from the copier-embedded-project template - Arduino, bare AVR, ESP or STM32 - or change the template itself. Use when the user says new embedded project, scaffold firmware, copier embedded, or asks to add a board/platform/component to the template.
---

# copier-embedded-project

Template repository. `copier.yml` asks the questions, `template/` is the rendered project,
`scripts/post_gen.py` removes what the answers exclude.

## Create a project

```bash
copier copy --trust /home/lab/workspace/private/copier-projects/copier-embedded-project <destination>
```

- Answers: `platform`, the downstream questions of that platform, `components` (multiselect) and
  `author_name`, which may carry the email as `Name <email>` or `Name email`
- Use `--defaults -d key=value` for a scripted render; list answers need JSON, e.g.
  `-d 'components=["notebooks","simulator"]'`
- After a render, `make help` in the new project lists its targets; `make env` installs the
  toolchain from `resources/envs/`

## Create a project from lab-utils

`lab-utils` > New Project from Template lists this template through
`~/.local/lab-utils/templates/embedded-project.yml`, which names
`https://github.com/stellarshenson/copier-embedded-project.git`. The menu runs
`copier-tui copy --trust <template> <project name>` in the folder where `lab-utils` started.

## Install the environments from lab-utils

The repository's `envs/` holds the installers `firmware-avr.py`, `firmware-stm32.py`,
`firmware-esp.py` and `firmware_env.py`, the module they import. `~/.local/lab-utils/envs/`
symlinks them, so `lab-utils` > Install Virtual Environments lists them and runs one on request;
each makes the conda environment named after the file without `.py`. `template/resources/envs/`
carries the same files for a rendered project.

## Change the template

- Read `.copier/README.md` first: rendering order, `_skip_if_exists`, hidden answers and update
  behaviour
- Add a question and its derived answer in `copier.yml`; add the file removal to
  `scripts/post_gen.py`
- Add a matrix row in `tests/conftest.py` for a new platform or board
- Verify with `make test`; `make test-toolchain` builds the AVR branches when `firmware-avr` exists
- Never hand-edit a rendered project to fix the template: fix `template/` and render again
- Keep `envs/` and `template/resources/envs/` identical: lab-utils runs the first, a rendered
  project runs the second

## Limits

- ESP and STM32 builds download platforms; they are not part of the fast tests
- QEMU is absent on this workstation; the harness skip path is what the tests exercise
