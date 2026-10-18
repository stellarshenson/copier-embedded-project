# Working on this template

Notes for an agent that changes the template.

## How a copy is produced

1. Copier renders every file under `template/` as Jinja. `_templates_suffix: ""` means there is no
   `.jinja` suffix and every file is processed, including `Makefile`, `.gitignore` and
   `.github/workflows/build.yml`. GitHub expressions must sit in `{% raw %}` blocks.
2. `_tasks` runs `scripts/post_gen.py` after the render. The script removes the files that belong to
   another platform, removes unselected components, marks the installers executable and creates the
   agent symlinks.
3. `_skip_if_exists` protects user-edited files during `copier update`. It also feeds copier's
   `git apply --exclude`, so every path that post_gen owns belongs there.

## Answer flow

- Visible questions carry the user's choices; hidden answers (`when: false`) derive board ids,
  platform pins, the baud rate and the rust target from them.
- `author_email` and `author_name_clean` split the author answer; the LICENSE consumes both.
- `pio_platform`, `pio_board`, `pio_framework` and `pio_upload_protocol` are the single source for
  `platformio.ini`; change them there, not in the template file.

## Adding a platform or a board

1. Add the choice to `copier.yml`, with any downstream question and its `when`.
2. Extend `pio_platform`, `pio_board`, `pio_framework` and, for a new toolchain, the hidden
   `thumb_target`.
3. Add the source branch in `template/src/main.c` or `main.cpp`, and the matching removal rule in
   `scripts/post_gen.py`.
4. Add the row to the matrix in `tests/conftest.py` and run `make test`.

## Testing

- `make test` renders the matrix into temporary directories and checks exact file sets, the
  Makefile help, the installers and the component selection.
- `make test-toolchain` additionally builds the AVR projects with `firmware-avr` and runs the simavr
  boot test. It skips when the environment is absent.

## Update behaviour

On `copier update` post_gen runs in dry-run mode: it removes nothing and prints what a fresh copy
would have removed. Changing the platform or the components of an existing project therefore needs a
fresh copy; installer changes still reach an update because `resources/envs/` is not skipped.
