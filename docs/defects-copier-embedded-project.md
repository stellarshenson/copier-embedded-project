# Defects - copier-embedded-project

Defects of the template, each with its reproduction and root cause. `pm-tools` is the only way
into this file.

## Authors

- `@kj` Konrad Jelen

## Post-generation `POST`

What scripts/post_gen.py removes, links and initialises after Copier renders a project, at copy and at update

- [x] `DEF-POST-1-EEPROM-TOOL` **ESP and STM32 projects carry an unused eeprom_tool.py** - MINOR; post_gen.py never removes scripts/eeprom_tool.py, yet only Arduino and bare AVR use it, so every ESP and STM32 render carries scripts/eeprom_tool.py that no rendered file calls
  - evidence: tests/test_structure.py::test_scripts_hold_only_the_scripts_the_branch_runs (9 branches; no eeprom_tool on ESP and STM32) and tests/test_post_gen.py::test_scripts_follow_the_platform_branch (10 branches) passed; make test 2026-10-20: 546 passed, 6 skipped
  - repro: copier copy --trust --defaults --vcs-ref HEAD -d platform=esp (or -d platform=stm32 with each toolchain) from the template working tree; scripts/eeprom_tool.py exists and no rendered file outside scripts/ names it
  - test-tags: UNIT, FUNCTIONAL
  - root-cause: 2026-10-19T20:02:04Z @kj scripts/post_gen.py has no removal rule for scripts/eeprom_tool.py: the file renders on every platform, while only the Makefile of Arduino and bare AVR (eeprom = platform in [arduino, avr]) renders eeprom-backup and eeprom-restore, which call it
  - log: 2026-10-19T20:02:04Z @kj added
  - log: 2026-10-19T22:49:18Z @kj closed
- [x] `DEF-POST-2-FREERTOS-RUST` **Rust projects carry the STM32Cube build hook freertos.py** - MINOR; post_gen.py removes scripts/freertos.py only in its C/C++ branch, so AVR Rust and STM32 Rust renders carry scripts/freertos.py, a PlatformIO build hook that only STM32Cube uses; src/FreeRTOSConfig.h is already removed on Rust
  - evidence: tests/test_structure.py::test_scripts_hold_only_the_scripts_the_branch_runs[avr-rust] and [stm32-rust] and tests/test_post_gen.py::test_scripts_follow_the_platform_branch (10 branches) passed; make test 2026-10-20: 546 passed, 6 skipped
  - repro: copier copy --trust --defaults --vcs-ref HEAD -d platform=avr -d avr_language=rust (or -d platform=stm32 -d stm32_toolchain=rust) from the template working tree; scripts/freertos.py exists and no rendered file outside scripts/ names it
  - test-tags: UNIT, FUNCTIONAL
  - root-cause: 2026-10-19T20:02:09Z @kj remove_other_toolchain in scripts/post_gen.py removes scripts/freertos.py only inside the else branch of if is_rust(args) (line 134); the Rust branch removes C_ONLY_PATHS, which list src/FreeRTOSConfig.h but not scripts/freertos.py
  - log: 2026-10-19T20:02:09Z @kj added
  - log: 2026-10-19T22:49:18Z @kj closed
- [x] `DEF-POST-3-UPDATE-WRITEBACK` **copier update writes back paths that post_gen removed** - MAJOR; with no template change, copier update of an Arduino project adds .github/, data/, docs/, ltspice/, host/ (host_side No), resources/envs/firmware-esp.py, resources/envs/firmware-stm32.py and test/host/core.rs as untracked files; an update from 1.0.13 also adds scripts/freertos.py
  - evidence: tests/test_post_gen.py::test_update_removes_what_it_wrote_back_under_unselected_paths, ::test_update_keeps_tracked_and_ignored_files_under_unselected_paths, ::test_update_outside_git_removes_nothing and ::test_update_on_host_side_no_removes_only_the_written_back_host_package passed; make test 2026-10-20: 546 passed, 6 skipped; update proof: copier update 1.0.13 -> 1.0.14 of an Arduino and an STM32 Rust project exited 0 and wrote back no excluded path (/tmp/update-repair/update/*.update.log)
  - repro: copier copy --trust --defaults --vcs-ref <tag> -d platform=arduino from a template clone, git add -A and commit, then copier update --trust --defaults --vcs-ref <same tag>; git status --porcelain lists the removed paths as untracked
  - test-tags: UNIT, FUNCTIONAL
  - root-cause: 2026-10-19T20:02:28Z @kj post_gen.py runs with dry_run = (copier_operation == "update") and removes nothing on update. copier 9.19.1 update renders the new version into the project, then deletes again only the paths the project deleted that do not match _skip_if_exists (copier/_main.py:1445-1485). .github/, data/, docs/, ltspice/, host/, test/ and resources/envs/ match _skip_if_exists, so they are written back; a path new in the template, such as scripts/freertos.py after the tools/ -> scripts/ move, was never deleted in the project and is written as well
  - log: 2026-10-19T20:02:28Z @kj added; reason: the mechanism names both copier update rules that write the removed paths back
  - log: 2026-10-19T22:49:18Z @kj closed
- [x] `DEF-POST-4-UPDATE-NOTE` **Template notes say installer changes reach copier update** - MINOR; .copier/README.md, section Update behaviour, says installer changes reach an update because resources/envs/ is not skipped; copier.yml _skip_if_exists lists resources/envs/, so copier update keeps the installers of an existing project and a newer installer reaches it only through a fresh render
  - evidence: grep -n "is not skipped" .copier/README.md -> exit 1, no output; .copier/README.md Update behaviour now reads: resources/envs/ is skipped, so an existing project keeps its installers on copier update; newer installers come from a fresh copy; 2026-10-20
  - repro: clone the template; copier copy --trust --defaults --vcs-ref v1.0.13 <clone> proj -d platform=arduino -d arduino_board=uno, commit; append a line to template/resources/envs/firmware-avr.py in the clone, commit, tag v1.0.14; copier update --trust --defaults --vcs-ref v1.0.14 in proj: the line is absent there and present in a fresh copy
  - test-tags: MANUAL
  - root-cause: 2026-10-19T23:59:55Z @kj the sentence and the resources/envs/ entry of _skip_if_exists both arrived in c30d1d9 and contradict each other; rule 3 of .copier/README.md puts every component path in _skip_if_exists, resources/envs/ is the path of the env-installers component, and copier update does not overwrite an existing file that matches _skip_if_exists
  - log: 2026-10-19T22:55:46Z @kj added; reason: the text, the repro and the root cause each need the full path names
  - log: 2026-10-19T23:00:32Z @kj closed
  - log: 2026-10-19T23:59:55Z @kj root-cause updated "2026-10-19T22:55:46Z @kj the sentence and the resources/envs/ entry of _skip_if_exists both arrived in c30d1d9 and contradict each other; rule 3 of .copier/README.md puts every path post_gen owns in _skip_if_exists, env-installers owns resources/envs/, and copier update does not overwrite an existing file that matches _skip_if_exists" -> "the sentence and the resources/envs/ entry of _skip_if_exists both arrived in c30d1d9 and contradict each other; rule 3 of .copier/README.md puts every component path in _skip_if_exists, resources/envs/ is the path of the env-installers component, and copier update does not overwrite an existing file that matches _skip_if_exists"
- [x] `DEF-POST-5-READY-RUST` **STM32 Rust ready message names the stm32cube framework** - MINOR; post_gen.py prints post_gen: <name> ready on stm32 with stm32cube for an STM32 Rust project, which uses no PlatformIO framework
  - evidence: tests/test_post_gen.py::test_stm32_rust_ready_line_names_no_framework -> 1 passed; copier copy --vcs-ref HEAD -d platform=stm32 -d stm32_toolchain=rust -> last line post_gen: stm32-rust-head ready on stm32, no framework named; 2026-10-20
  - repro: copier copy --trust --defaults --vcs-ref HEAD <template> <dst> -d platform=stm32 -d stm32_toolchain=rust from the template working tree; the last line reads post_gen: <dst> ready on stm32 with stm32cube
  - test-tags: UNIT
  - root-cause: 2026-10-19T22:55:51Z @kj copier skips stm32_framework when stm32_toolchain is rust (its when names platformio) but still renders its default stm32cube into the _tasks command, so post_gen receives --stm32-framework stm32cube; main() in scripts/post_gen.py appends args.stm32_framework whenever it is non-empty (line 348) without reading stm32_toolchain
  - log: 2026-10-19T22:55:51Z @kj added
  - log: 2026-10-19T23:00:32Z @kj closed
- [x] `DEF-POST-7-UPDATE-RENAME` **copier update from v1.0.13 deletes the files of tools/ and ltspice/, edited or not** - MAJOR; after the rename of tools/ to scripts/ and ltspice/ to simulations/, copier update from v1.0.13 deletes every file that v1.0.13 rendered into tools/ and ltspice/, edited or not, and adds untracked stock copies under the new names; committed edits to those files are lost
  - evidence: copier.yml _migrations 1.0.14 before-stage git mv ltspice simulations and tools scripts; scratch copier update v1.0.13 -> v1.0.14 exit 0 on arduino with and without ltspice, stm32 stm32cube and esp32 espidf: no D for an edited file, edits kept under simulations/ and scripts/, eeprom_tool.py and freertos.py edits as UU conflicts holding the edit; gates 2026-10-20: make test 547 passed 6 skipped, make test-toolchain 9 passed, make test-functional 5 passed, make lint clean, pm-tools check 0 errors; 2026-10-20
  - repro: in a template clone with the rename committed and tagged v1.0.14: copier copy --trust --defaults --vcs-ref v1.0.13 -d platform=arduino -d components='[...,"ltspice"]' <clone> <dst>, edit and commit ltspice/circuit.cir and tools/eeprom_tool.py, copier update --trust --defaults --vcs-ref v1.0.14; git status lists D ltspice/circuit.cir and D tools/eeprom_tool.py and the edits are in no file
  - test-tags: MANUAL
  - root-cause: 2026-10-19T23:32:54Z @kj copier 9.19.1 ends an update with _remove_old_files (copier/_main.py:1985-1996): for a folder the new copy no longer renders it recurses with rm_common=True and unlinks every destination file named like a file of the old copy, whatever its content; tools/ and ltspice/ are such folders in v1.0.14
  - log: 2026-10-19T23:32:54Z @kj added
  - log: 2026-10-19T23:35:02Z @kj fix attempt: copier.yml _migrations 1.0.14 before-stage git mv ltspice simulations and tools scripts; scratch update v1.0.13 -> v1.0.14 exit 0 on arduino with and without ltspice, stm32cube and esp32; no D for an edited file, edits under simulations/ and scripts/, eeprom_tool.py and freertos.py edits as UU conflicts holding the edit
  - log: 2026-10-20T00:16:47Z @kj closed; reason: the evidence names the migration, the four update reproductions and every gate result
  - log: 2026-10-20T00:40:05Z @kj collision stop: on an arduino v1.0.13 project with ltspice, its own scripts/deploy.sh and a committed edit of tools/eeprom_tool.py, the guarded migration skipped the tools/ move, the update exited 0 and git status listed D tools/eeprom_tool.py with the edit in no file; copier.yml _migrations 1.0.14 now checks before both git mv and, when tools/ and scripts/ or ltspice/ and simulations/ both exist, prints the rename instruction to stderr and exits 1; scratch update exit 1, git status empty, edit kept in tools/eeprom_tool.py, ltspice/ not moved, same stop with an own simulations/; after git mv scripts my-scripts and a commit exit 0, renames as R, edit in a UU conflict; without own folders exit 0, renames as R; reason: the event names the reproduction input, the result before the fix and the result of each case after it

## Generated CI `CI`

The GitHub Actions workflow that the ci component renders into a generated project: build, test, collect, upload and tag release

- [x] `DEF-CI-6-AVR-ELF` **AVR Rust CI collects a firmware file that cargo does not write** - MAJOR; the Collect the firmware step of an AVR Rust project runs cp target/avr-none/release/<repo> dist/, while cargo writes target/avr-none/release/<repo>.elf, so the build job of every push and pull request and every v* tag release fail at that step; v1.0.13 shipped the same line
  - evidence: tests/test_ci.py avr-rust case now pins target/avr-none/release/board.elf: 1 failed on the old build.yml line, 14 passed after the fix; rendered AVR Rust project: make build, then the collect cp line exits 0 and dist/ holds board-after.elf; gates 2026-10-20: make test 547 passed 6 skipped, make test-toolchain 9 passed, make test-functional 5 passed, make lint clean, pm-tools check 0 errors; 2026-10-20
  - repro: copier copy --trust --defaults --vcs-ref HEAD <template> <dst>/board -d platform=avr -d avr_language=rust -d avr_mcu=atmega328p -d components=[...,"env-installers","ci"]; .github/workflows/build.yml reads cp target/avr-none/release/board dist/; make build in <dst>/board writes target/avr-none/release/board.elf and that cp exits 1 with cannot stat
  - test-tags: UNIT
  - root-cause: 2026-10-19T23:29:07Z @kj the avr_rust branch of the Collect the firmware step in template/.github/workflows/build.yml (line 48) copies target/{{ avr_target }}/release/{{ repo_name }} without a suffix; the avr-none target spec sets exe-suffix .elf, so cargo names the executable <repo>.elf, the name template/Makefile:74 and template/test/harness/board.py:13 already use. tests/test_ci.py pinned the substring target/avr-none/release/board, which the wrong line and the correct line both contain, so the test passed on the defect
  - log: 2026-10-19T23:29:07Z @kj added; reason: the text, the repro and the root cause each need the full paths and the step name
  - log: 2026-10-20T00:16:47Z @kj closed; reason: the evidence names the test, the build reproduction and every gate result
- [x] `DEF-CI-8-COPIER-PATH` **Template repository CI skips every bake test because copier is not on PATH** - MAJOR; the tests job of .github/workflows/test.yml runs make test, which runs .venv/bin/python -m pytest without .venv/bin on PATH; copier() in tests/helpers.py finds no copier through shutil.which and calls pytest.skip, so every test that renders the template skips and the job still reports success
  - evidence: tests/helpers.py copier() returns the copier beside sys.executable; env PATH=/usr/bin:/bin .venv/bin/python -m pytest tests/test_help_matrix.py: 32 skipped before the fix, 32 passed after; full suite under that PATH 538 passed 15 skipped, none of them the copier skip; gates 2026-10-20: make test 547 passed 6 skipped, make test-toolchain 9 passed, make test-functional 5 passed, make lint clean, pm-tools check 0 errors; 2026-10-20
  - repro: on a machine where copier exists only in .venv/bin: env PATH=/usr/bin:/bin .venv/bin/python -m pytest -q -rs tests/test_help_matrix.py -x -> 32 skipped, each SKIPPED tests/helpers.py:56: copier is not installed
  - test-tags: MANUAL
  - root-cause: 2026-10-19T23:46:48Z @kj copier() in tests/helpers.py resolves copier only with shutil.which, which searches PATH. make setup installs copier into .venv/bin through the dev extra of pyproject.toml, and the Makefile test target runs $(PY) -m pytest with PY = .venv/bin/python, which does not add .venv/bin to PATH; no step of .github/workflows/test.yml adds it either. On this workstation /opt/conda/bin/copier is on PATH, so a local make test renders and the skip does not show
  - log: 2026-10-19T23:46:48Z @kj added; reason: the text, the repro and the root cause each need the CI step, the Makefile variable and the helper by name
  - log: 2026-10-20T00:16:48Z @kj closed; reason: the evidence names the reproduction under a stripped PATH and every gate result

