# Working on this template

Notes for an agent that changes the template.

## How a copy is produced

1. Copier renders every file under `template/` as Jinja. `_templates_suffix: ""` means there is no
   `.jinja` suffix and every file is processed, including `Makefile`, `.gitignore` and
   `.github/workflows/build.yml`. GitHub expressions must sit in `{% raw %}` blocks.
2. `_tasks` runs `scripts/post_gen.py` after the render. The script removes the files that belong to
   another platform, removes unselected components, removes `host/` when `host_side` is `No`, marks
   the installers executable and creates the agent symlinks.
3. `_skip_if_exists` protects user-edited files during `copier update`. It also feeds copier's
   `git apply --exclude`. It lists the user-owned files and folders, every component path and
   `host/` among them. The template-owned files that post_gen removes on some branches, such as
   `platformio.ini`, `Cargo.toml`, `src/main.c`, `scripts/freertos.py` and
   `scripts/eeprom_tool.py`, are not listed, so a template fix reaches an update. On update,
   post_gen removes what the update wrote back under the paths the answers exclude (see Update
   behaviour).

`template/scripts/` is the generated project's helper-script folder and is a different folder from
this repository's `scripts/`, which holds `post_gen.py` and is never rendered. A generated script
runs on the PC, takes no interactive input, prints one JSON line and exits non-zero with a reason on
failure, so an agent can run it. The one exception is `template/scripts/freertos.py`, the STM32Cube
build hook that `platformio.ini` runs through `extra_scripts`; post_gen removes it from every other
branch, Rust included, and removes `eeprom_tool.py` on every platform but Arduino and bare AVR.

## Answer flow

- Visible questions carry the user's choices; hidden answers (`when: false`) derive board ids,
  platform pins, the baud rate and the rust target from them.
- `project_name` and `repo_name` use `ask: false` instead: they are computed once and recorded in
  the answers file, so `copier update` reuses them instead of recomputing them and conflicting.
- `author_email` and `author_name_clean` split the author answer; the LICENSE consumes both.
- `pio_platform`, `pio_board`, `pio_framework` and `pio_upload_protocol` are the single source for
  `platformio.ini`; change them there, not in the template file.
- `host_side` (`No` or `Yes`, default `No`) and `host_module` sit directly before `components`, so
  `components` stays the last visible question. `host_module` carries
  `when: "{{ host_side == 'Yes' }}"`, so it is asked only for a host side. Its default is
  `repo_name` without hyphens plus `_host`: `weather-station` gives `weatherstation_host`.
- The `host_module` validator rejects a value that is not a Python identifier, because the answer
  names the package folder `template/host/src/{{ host_module }}/` and the `python -m` module.
- `host/` is in `_skip_if_exists`; `_tasks` passes `--host-side` to post_gen, which removes `host/`
  on `No`.

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

On `copier update` post_gen removes, under every path the answers exclude, only the untracked files
that git does not ignore, then the directories left empty. Copier refuses to update a destination
with untracked files, so each such file came from the update; tracked and ignored files stay, and
outside a git work tree post_gen removes nothing. Changing the platform, or turning a component or
`host_side` off, therefore needs a fresh copy. post_gen also removes each untracked file that
copier's render of the old version holds outside the components and `host/` the old answers
excluded, because the project had removed it and copier writes it back under `_skip_if_exists`;
post_gen finds that render as the temporary `copier._main.old_copy.*` directory whose git
alternates name the project's objects directory, and when it is not found, post_gen says so and
the removed starter files come back. `resources/envs/` is skipped, so an existing project
keeps its installers on `copier update`; newer installers come from a fresh copy. The `1.0.14`
before-stage entry of `_migrations` in `copier.yml` moves `tools/` to `scripts/` and `ltspice/` to
`simulations/` with `git mv`, because copier deletes every file the old version rendered into a
folder the new template no longer renders, edited or not.
